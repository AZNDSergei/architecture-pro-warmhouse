# schemas.py
from pydantic import BaseModel, UUID4, Field
from datetime import datetime
from enum import Enum
from typing import Optional, List

class DeviceType(str, Enum):
    SENSOR = "SENSOR"
    CAMERA = "CAMERA"
    SWITCH = "SWITCH"

class TriggerType(str, Enum):
    SENSOR = "SENSOR"
    TIME = "TIME"

class ActionType(str, Enum):
    TURN_ON = "TURN_ON"
    TURN_OFF = "TURN_OFF"

class UserBase(BaseModel):
    email: str
    name: str
    phone: Optional[str] = None

class UserCreate(UserBase):
    pass

class UserResponse(UserBase):
    id: UUID4
    registered_at: datetime

    class Config:
        orm_mode = True

class HomeBase(BaseModel):
    name: str
    address: Optional[str] = None
    owner_id: UUID4

class HomeResponse(HomeBase):
    id: UUID4

    class Config:
        orm_mode = True

class RoomBase(BaseModel):
    name: str
    info: Optional[str] = None
    home_id: UUID4

class RoomResponse(RoomBase):
    id: UUID4

    class Config:
        orm_mode = True

class DeviceBase(BaseModel):
    name: str
    type: DeviceType
    model: str
    firmware_version: Optional[str] = None
    status: Optional[str] = None
    room_id: Optional[UUID4] = None
    home_id: Optional[UUID4] = None
    activation_code: Optional[str] = None
    is_activated: bool = False
    activated_at: Optional[datetime] = None


class DeviceCreate(DeviceBase):
    pass


class DeviceResponse(DeviceBase):
    id: UUID4

    class Config:
        orm_mode = True

class DeviceActivationRequest(BaseModel):
    activation_code: str
    home_id: UUID4
    room_id: UUID4

class SensorDataBase(BaseModel):
    device_id: UUID4
    timestamp: datetime
    type: str
    value: str

class SensorDataResponse(SensorDataBase):
    id: UUID4

    class Config:
        orm_mode = True

class ScenarioBase(BaseModel):
    name: str
    user_id: UUID4
    enabled: bool = True

class ScenarioResponse(ScenarioBase):
    id: UUID4
    created_at: datetime

    class Config:
        orm_mode = True

class RuleBase(BaseModel):
    scenario_id: Optional[UUID4] = None
    trigger_type: TriggerType
    trigger_condition: str
    action_type: ActionType
    action_target: UUID4

class RuleResponse(RuleBase):
    id: UUID4

    class Config:
        orm_mode = True

class ScenarioWithRulesCreate(ScenarioBase):
    rules: List[RuleBase]

class ScenarioWithRulesResponse(ScenarioResponse):
    rules: List[RuleResponse]

class NotificationBase(BaseModel):
    user_id: UUID4
    title: str
    body: str
    sent_at: datetime
    read: bool = False

class NotificationResponse(NotificationBase):
    id: UUID4

    class Config:
        orm_mode = True

class EventLogBase(BaseModel):
    device_id: UUID4
    event_type: str
    description: str
    timestamp: datetime

class EventLogResponse(EventLogBase):
    id: UUID4

    class Config:
        orm_mode = True