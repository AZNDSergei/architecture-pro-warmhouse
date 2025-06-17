
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List
import json
from models import AutomationScenario, AutomationRule
from database import get_db
from schemas import ScenarioBase, ScenarioResponse, RuleBase, RuleResponse
from kafka import get_kafka_producer
from aiokafka import AIOKafkaProducer

router = APIRouter(
    prefix="/automation-scenarios",
    tags=["AutomationScenarios"]
)

class ScenarioWithRulesCreate(ScenarioBase):
    rules: List[RuleBase]

class ScenarioWithRulesResponse(ScenarioResponse):
    rules: List[RuleResponse]

@router.get("/", response_model=List[ScenarioResponse])
def list_scenarios(db: Session = Depends(get_db)):
    return db.query(AutomationScenario).all()

@router.get("/{scenario_id}", response_model=ScenarioWithRulesResponse)
def get_scenario(scenario_id: UUID, db: Session = Depends(get_db)):
    scenario = db.query(AutomationScenario).filter(AutomationScenario.id == scenario_id).first()
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")
    rules = db.query(AutomationRule).filter(AutomationRule.scenario_id == scenario.id).all()
    return ScenarioWithRulesResponse(**scenario.__dict__, rules=rules)

from models import User  # Не забудьте импортировать модель User

@router.post("/", response_model=ScenarioWithRulesResponse, status_code=status.HTTP_201_CREATED)
async def create_scenario(
    data: ScenarioWithRulesCreate,
    db: Session = Depends(get_db),
    producer: AIOKafkaProducer = Depends(get_kafka_producer)
):
    # Проверка существования пользователя
    user = db.query(User).filter(User.id == data.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Создание сценария
    rules_data = data.rules
    scenario_data = data.dict(exclude={"rules"})
    new_scenario = AutomationScenario(**scenario_data)
    db.add(new_scenario)
    db.commit()
    db.refresh(new_scenario)

    # Создание правил
    created_rules = []
    for rule_data in rules_data:
        rule = AutomationRule(**rule_data.dict(), scenario_id=new_scenario.id)
        db.add(rule)
        created_rules.append(rule)

    db.commit()
    for rule in created_rules:
        db.refresh(rule)

    # Отправка в Kafka
    try:
        await producer.send_and_wait(
            topic="autoCommand",
            key=str(new_scenario.id).encode(),
            value=json.dumps({
                "id": str(new_scenario.id),
                "name": new_scenario.name,
                "user_id": str(new_scenario.user_id),
                "enabled": new_scenario.enabled,
                "created_at": new_scenario.created_at.isoformat(),
                "rules": [
                    {
                        "id": str(rule.id),
                        "trigger_type": rule.trigger_type.value,
                        "trigger_condition": rule.trigger_condition,
                        "action_type": rule.action_type.value,
                        "action_target": str(rule.action_target)
                    }
                    for rule in created_rules
                ]
            }).encode("utf-8")
        )
    except Exception as e:
        print(f"Failed to send Kafka message: {e}")

    return ScenarioWithRulesResponse(**new_scenario.__dict__, rules=created_rules)


@router.put("/{scenario_id}", response_model=ScenarioResponse)
def update_scenario(scenario_id: UUID, data: ScenarioBase, db: Session = Depends(get_db)):
    scenario = db.query(AutomationScenario).filter(AutomationScenario.id == scenario_id).first()
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")
    for field, value in data.dict().items():
        setattr(scenario, field, value)
    db.commit()
    db.refresh(scenario)
    return scenario

@router.delete("/{scenario_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_scenario(scenario_id: UUID, db: Session = Depends(get_db)):
    scenario = db.query(AutomationScenario).filter(AutomationScenario.id == scenario_id).first()
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")
    db.query(AutomationRule).filter(AutomationRule.scenario_id == scenario.id).delete()
    db.delete(scenario)
    db.commit()
    return
