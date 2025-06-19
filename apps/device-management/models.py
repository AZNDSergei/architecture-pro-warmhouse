from enum import Enum as PyEnum
from datetime import datetime
import uuid

from sqlalchemy import (
    Column,
    String,
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from database import Base

# ---------------------------------------------------------------------
# ENUMS
# ---------------------------------------------------------------------

class DeviceType(PyEnum):
    SENSOR = "SENSOR"
    CAMERA = "CAMERA"


class TriggerType(PyEnum):
    SENSOR = "SENSOR"
    TIME = "TIME"


class ActionType(PyEnum):
    TURN_ON = "TURN_ON"
    TURN_OFF = "TURN_OFF"


# ---------------------------------------------------------------------
# USER
# ---------------------------------------------------------------------

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, nullable=False)
    name = Column(String, nullable=False)
    registered_at = Column(DateTime, default=datetime.utcnow)
    phone = Column(String)

    # relationships
    homes = relationship(
        "Home", back_populates="owner", cascade="all, delete-orphan"
    )
    scenarios = relationship(
        "AutomationScenario", back_populates="user", cascade="all, delete-orphan"
    )
    devices = relationship(
        "Device", back_populates="owner", cascade="all, delete-orphan"
    )
    notices = relationship(
        "Notification", back_populates="user", cascade="all, delete-orphan"
    )


# ---------------------------------------------------------------------
# HOME / ROOM
# ---------------------------------------------------------------------

class Home(Base):
    __tablename__ = "homes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    address = Column(String)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))

    # relationships
    owner = relationship("User", back_populates="homes")
    rooms = relationship(
        "Room", back_populates="home", cascade="all, delete-orphan"
    )
    devices = relationship(
        "Device", back_populates="home", cascade="all, delete-orphan"
    )


class Room(Base):
    __tablename__ = "rooms"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String)
    info = Column(String)
    home_id = Column(UUID(as_uuid=True), ForeignKey("homes.id"))

    # relationships
    home = relationship("Home", back_populates="rooms")
    devices = relationship(
        "Device", back_populates="room", cascade="all, delete-orphan"
    )


# ---------------------------------------------------------------------
# DEVICE
# ---------------------------------------------------------------------

class Device(Base):
    __tablename__ = "devices"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    type = Column(Enum(DeviceType), nullable=False)
    model = Column(String, nullable=False)
    firmware_version = Column(String, nullable=False, default="legacy-1.0")
    status = Column(String, nullable=False, default="inactive")
    location = Column(String, nullable=False, default="Default room")
    unit = Column(String, nullable=False, default="Default room")
    room_id = Column(UUID(as_uuid=True), ForeignKey("rooms.id", ondelete="SET NULL"))
    home_id = Column(UUID(as_uuid=True), ForeignKey("homes.id", ondelete="SET NULL"))
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))

    activation_code = Column(String)
    is_activated = Column(Boolean, default=False, nullable=False)
    activated_at = Column(DateTime)

    # relationships
    room = relationship("Room", back_populates="devices")
    home = relationship("Home", back_populates="devices")
    owner = relationship("User", back_populates="devices")
    rules = relationship("AutomationRule", back_populates="device")


# ---------------------------------------------------------------------
# SENSOR DATA
# ---------------------------------------------------------------------

class SensorData(Base):
    __tablename__ = "sensor_data"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    device_id = Column(UUID(as_uuid=True), ForeignKey("devices.id"))
    timestamp = Column(DateTime)
    type = Column(String)
    value = Column(String)

    device = relationship("Device")


# ---------------------------------------------------------------------
# AUTOMATION
# ---------------------------------------------------------------------

class AutomationScenario(Base):
    __tablename__ = "automation_scenarios"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="scenarios")
    rules = relationship(
        "AutomationRule",
        back_populates="scenario",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class AutomationRule(Base):
    __tablename__ = "automation_rules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scenario_id = Column(
        UUID(as_uuid=True),
        ForeignKey("automation_scenarios.id", ondelete="CASCADE"),
    )
    trigger_type = Column(Enum(TriggerType))
    trigger_condition = Column(String)
    action_type = Column(Enum(ActionType))
    action_target = Column(UUID(as_uuid=True), ForeignKey("devices.id", ondelete="SET NULL"))

    scenario = relationship("AutomationScenario", back_populates="rules")
    device = relationship("Device", back_populates="rules")


# ---------------------------------------------------------------------
# NOTIFICATION
# ---------------------------------------------------------------------

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    title = Column(String)
    body = Column(String)
    sent_at = Column(DateTime, default=datetime.utcnow)
    read = Column(Boolean, default=False)

    user = relationship("User", back_populates="notices")
