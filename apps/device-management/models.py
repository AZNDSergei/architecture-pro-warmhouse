from sqlalchemy import Column, String, Boolean, DateTime, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, declarative_base
from enum import Enum as PyEnum
from datetime import datetime
import uuid
from database import Base

class DeviceType(PyEnum):
    SENSOR = "SENSOR"
    CAMERA = "CAMERA"

class TriggerType(PyEnum):
    SENSOR = "SENSOR"
    TIME = "TIME"

class ActionType(PyEnum):
    TURN_ON = "TURN_ON"
    TURN_OFF = "TURN_OFF"

class User(Base):
    __tablename__ = 'users'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, nullable=False)
    name = Column(String, nullable=False)
    registered_at = Column(DateTime, default=datetime.utcnow)
    phone = Column(String)

class Home(Base):
    __tablename__ = 'homes'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    address = Column(String)
    owner_id = Column(UUID(as_uuid=True), ForeignKey('users.id'))

class Room(Base):
    __tablename__ = 'rooms'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String)
    info = Column(String)
    home_id = Column(UUID(as_uuid=True), ForeignKey('homes.id'))

class Device(Base):
    __tablename__ = "devices"
    id               = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name             = Column(String, nullable=False)
    type             = Column(Enum(DeviceType), nullable=False)
    model            = Column(String, nullable=False)
    firmware_version = Column(String, nullable=False, default="legacy-1.0")
    status           = Column(String, nullable=False, default="inactive")
    room_id = Column(UUID(as_uuid=True),
                     ForeignKey("rooms.id", ondelete="SET NULL"),
                     nullable=True)

    home_id = Column(UUID(as_uuid=True),
                     ForeignKey("homes.id", ondelete="SET NULL"),
                     nullable=True)
    activation_code = Column(String, unique=False, nullable=True)
    is_activated    = Column(Boolean, default=False, nullable=False)
    activated_at    = Column(DateTime, nullable=True)

class SensorData(Base):
    __tablename__ = 'sensor_data'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    device_id = Column(UUID(as_uuid=True), ForeignKey('devices.id'))
    timestamp = Column(DateTime)
    type = Column(String)
    value = Column(String)

class AutomationScenario(Base):
    __tablename__ = 'automation_scenarios'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'))
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class AutomationRule(Base):
    __tablename__ = 'automation_rules'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scenario_id = Column(UUID(as_uuid=True), ForeignKey('automation_scenarios.id'))
    trigger_type = Column(Enum(TriggerType))
    trigger_condition = Column(String)
    action_type = Column(Enum(ActionType))
    action_target = Column(UUID(as_uuid=True), ForeignKey('devices.id'))

class Notification(Base):
    __tablename__ = 'notifications'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'))
    title = Column(String)
    body = Column(String)
    sent_at = Column(DateTime, default=datetime.utcnow)
    read = Column(Boolean, default=False)