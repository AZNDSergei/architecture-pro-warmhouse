from enum import Enum

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