from uuid import UUID
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from aiokafka import AIOKafkaProducer

from database import get_db
from models import AutomationScenario, AutomationRule, User
from schemas import (
    ScenarioBase,
    ScenarioResponse,
    RuleBase,
    RuleResponse,
)

from kafka import get_kafka_producer

router = APIRouter(
    prefix="/automation-scenarios",
    tags=["AutomationScenarios"],
)

# ---------------------------------------------------------------------------
class ScenarioWithRulesCreate(ScenarioBase):
    rules: List[RuleBase]


class ScenarioWithRulesResponse(ScenarioResponse):
    rules: List[RuleResponse]


def _scenario_payload(
    scenario: AutomationScenario,
    rules: List[AutomationRule],
) -> dict:
    """Преобразуем ORM-объект + правила в JSON-совместимый dict."""
    return {
        "id": str(scenario.id),
        "name": scenario.name,
        "user_id": str(scenario.user_id),
        "enabled": scenario.enabled,
        "created_at": scenario.created_at.isoformat(),
        "rules": [
            {
                "id": str(rule.id),
                "trigger_type": rule.trigger_type.value,
                "trigger_condition": rule.trigger_condition,
                "action_type": rule.action_type.value,
                "action_target": str(rule.action_target),
            }
            for rule in rules
        ],
    }

# ---------------------------------------------------------------------------
@router.get("/", response_model=List[ScenarioResponse])
def list_scenarios(db: Session = Depends(get_db)):
    return db.query(AutomationScenario).all()


@router.get("/{scenario_id}", response_model=ScenarioWithRulesResponse)
def get_scenario(scenario_id: UUID, db: Session = Depends(get_db)):
    scenario = (
        db.query(AutomationScenario)
        .filter(AutomationScenario.id == scenario_id)
        .first()
    )
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")

    rules = (
        db.query(AutomationRule)
        .filter(AutomationRule.scenario_id == scenario.id)
        .all()
    )
    return ScenarioWithRulesResponse(**scenario.__dict__, rules=rules)

# ---------------------------------------------------------------------------
@router.post("/", response_model=ScenarioWithRulesResponse, status_code=status.HTTP_201_CREATED)
async def create_scenario(
    data: ScenarioWithRulesCreate,
    db: Session = Depends(get_db),
    producer: AIOKafkaProducer = Depends(get_kafka_producer),
):
    # проверяем пользователя
    user = db.query(User).filter(User.id == data.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # создаём сценарий
    new_scenario = AutomationScenario(**data.dict(exclude={"rules"}))
    db.add(new_scenario)
    db.commit()
    db.refresh(new_scenario)

    # создаём правила
    created_rules: List[AutomationRule] = []
    for rule_data in data.rules:
        rule = AutomationRule(**rule_data.dict(), scenario_id=new_scenario.id)
        db.add(rule)
        created_rules.append(rule)

    db.commit()
    [db.refresh(r) for r in created_rules]

    # отправляем событие в Kafka
    try:
        await producer.send_and_wait(
            topic="autoCommand",
            key=str(new_scenario.id),
            value=_scenario_payload(new_scenario, created_rules),
        )
        print("[Kafka] autoCommand sent")
    except Exception as e:
        print(f"[Kafka] Failed to send message: {e}")

    return ScenarioWithRulesResponse(**new_scenario.__dict__, rules=created_rules)

# ---------------------------------------------------------------------------
@router.put("/{scenario_id}", response_model=ScenarioResponse)
def update_scenario(
    scenario_id: UUID,
    data: ScenarioBase,
    db: Session = Depends(get_db),
):
    scenario = (
        db.query(AutomationScenario).filter(AutomationScenario.id == scenario_id).first()
    )
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")

    for field, value in data.dict(exclude_unset=True).items():
        setattr(scenario, field, value)

    db.commit()
    db.refresh(scenario)
    return scenario

# ---------------------------------------------------------------------------
@router.delete("/{scenario_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_scenario(scenario_id: UUID, db: Session = Depends(get_db)):
    scenario = (
        db.query(AutomationScenario).filter(AutomationScenario.id == scenario_id).first()
    )
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")

    db.query(AutomationRule).filter(
        AutomationRule.scenario_id == scenario.id
    ).delete()
    db.delete(scenario)
    db.commit()
