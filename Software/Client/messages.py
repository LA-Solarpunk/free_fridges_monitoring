from dataclasses import dataclass
from enum import Enum
import json

class DoorStateEnum(Enum):
    OPEN = 0
    CLOSED = 1
    UNKNOWN = 2

@dataclass
class SensorEntry:
    fridge_temperature: float
    freezer_temperature: float
    charge_status: float
    fridge_door_status: DoorStateEnum
    freezer_door_status: DoorStateEnum
    fridge_id: str
    errors: str

    def get_doorstatus_string(self, door_status: DoorStateEnum):
        status_string = "Closed"
        if door_status == DoorStateEnum.OPEN:
            status_string = "Open"
        elif door_status == DoorStateEnum.UNKNOWN:
            status_string = "Error"
        return status_string

    def get_json_string(self):
        new_entry = {
            "Fridge": [self.fridge_id],
            "Fridge Temperature (°C)": self.fridge_temperature,
            "Freezer Temperature (°C)": self.freezer_temperature,
            "Charge Status (%)": self.charge_status,
            "Fridge Door Status": self.get_doorstatus_string(self.fridge_door_status),
            "Freezer Door Status": self.get_doorstatus_string(self.freezer_door_status),
            "Errors": self.errors
        }
        return json.dumps(new_entry)
    
class SensorReading:
    value: int | float
    error: str