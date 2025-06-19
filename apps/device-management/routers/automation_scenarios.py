from uuid import UUID
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from aiokafka import AIOKafkaProducer

from database import get_db
from models import AutomationScenario, AutomationRule, User, Device
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
# helpers
class ScenarioWithRulesResponse(ScenarioResponse):
    rules: List[RuleResponse]

    model_config = {
        "from_attributes": True,  # позволяем кормить ORM-объекты
    }


class ScenarioWithRulesCreate(ScenarioBase):
    rules: List[RuleBase]


def _build_response(
    scenario: AutomationScenario,
    rules: List[AutomationRule],
) -> ScenarioWithRulesResponse:
    """Конвертируем ORM-объекты в DTO, безопасно для Pydantic-v2."""
    return ScenarioWithRulesResponse(
        id=scenario.id,
        name=scenario.name,
        user_id=scenario.user_id,
        enabled=scenario.enabled,
        created_at=scenario.created_at,
        rules=[RuleResponse.model_validate(r, from_attributes=True) for r in rules],
    )

# ---------------------------------------------------------------------------
@router.get("/", response_model=List[ScenarioResponse])
def list_scenarios(db: Session = Depends(get_db)):
    return db.query(AutomationScenario).all()


@router.get("/{scenario_id}", response_model=ScenarioWithRulesResponse)
def get_scenario(scenario_id: UUID, db: Session = Depends(get_db)):
    scenario = db.query(AutomationScenario).filter(
        AutomationScenario.id == scenario_id
    ).first()
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")

    return _build_response(scenario, scenario.rules)

# ---------------------------------------------------------------------------
@router.post(
    "/",
    response_model=ScenarioWithRulesResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_scenario(
    data: ScenarioWithRulesCreate,
    db: Session = Depends(get_db),
    producer: AIOKafkaProducer = Depends(get_kafka_producer),
):
    """Создать сценарий + правила и отправить событие в Kafka."""

    # 1. валидируем пользователя
    if not db.query(User).filter(User.id == data.user_id).first():
        raise HTTPException(status_code=404, detail="User not found")

    try:
        # 2. создаём сценарий
        new_scenario = AutomationScenario(**data.dict(exclude={"rules"}))
        db.add(new_scenario)
        db.flush()  # сразу получаем new_scenario.id

        # 3. создаём правила
        created_rules: List[AutomationRule] = []
        for rule_data in data.rules:
            # проверяем существование устройства
            if rule_data.action_target:
                if not db.query(Device).filter(Device.id == rule_data.action_target).first():
                    raise HTTPException(
                        status_code=400,
                        detail=f"Device {rule_data.action_target} not found",
                    )

            rule = AutomationRule(
                **rule_data.dict(exclude={"scenario_id"}),
                scenario_id=new_scenario.id,
            )
            db.add(rule)
            created_rules.append(rule)

        # 4. фиксируем транзакцию
        db.commit()

    except HTTPException:
        db.rollback()
        raise
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail="Database integrity error") from e

    # 5. рефрешим объекты
    db.refresh(new_scenario)
    for r in created_rules:
        db.refresh(r)

    # 6. шлём событие в Kafka (не критично при ошибке)
    try:
        await producer.send_and_wait(
            topic="autoCommand",
            key=str(new_scenario.id),
            value={
                "id": str(new_scenario.id),
                "name": new_scenario.name,
                "user_id": str(new_scenario.user_id),
                "enabled": new_scenario.enabled,
                "created_at": new_scenario.created_at.isoformat(),
                "rules": [
                    {
                        "id": str(r.id),
                        "trigger_type": r.trigger_type.value,
                        "trigger_condition": r.trigger_condition,
                        "action_type": r.action_type.value,
                        "action_target": str(r.action_target),
                    }
                    for r in created_rules
                ],
            },
        )
    except Exception as e:
        print(f"[Kafka] Failed to send message: {e}")

    # 7. отдаём DTO клиенту
    return _build_response(new_scenario, created_rules)

# ---------------------------------------------------------------------------
@router.put("/{scenario_id}", response_model=ScenarioResponse)
def update_scenario(
    scenario_id: UUID,
    data: ScenarioBase,
    db: Session = Depends(get_db),
):
    scenario = db.query(AutomationScenario).filter(
        AutomationScenario.id == scenario_id
    ).first()
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
    scenario = db.query(AutomationScenario).filter(
        AutomationScenario.id == scenario_id
    ).first()
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")

    db.delete(scenario)  # cascade=\"all, delete-orphan\" удалит правила
    db.commit()
