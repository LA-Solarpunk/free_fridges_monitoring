from dataclasses import dataclass
from enum import Enum
import json

class DoorStateEnum(Enum):
    OPEN = 0
    CLOSED = 1
    UNKNOWN = 2
@dataclass    
class SensorReading:
    value: int | float | str
    error: str

@dataclass
class SensorEntry:
    fridge_temperature: SensorReading
    freezer_temperature: SensorReading
    charge_status: SensorReading
    fridge_door_status: SensorReading
    freezer_door_status: SensorReading
    fridge_id: str

    def get_doorstatus_string(self, door_status: DoorStateEnum):
        status_string = "Closed"
        if door_status == DoorStateEnum.OPEN:
            status_string = "Open"
        elif door_status == DoorStateEnum.UNKNOWN:
            status_string = "Error"
        return status_string

    def get_json_string(self):
        errors = ""
        readings = [self.fridge_temperature, self.freezer_temperature, self.charge_status, self.fridge_door_status, self.freezer_door_status]
        for reading in readings:
            if reading.error:
                errors += reading.error + "\n"
        new_entry = {
            "Fridge": [self.fridge_id],
            "Fridge Temperature (°C)": self.fridge_temperature.value,
            "Freezer Temperature (°C)": self.freezer_temperature.value,
            "Charge Status (%)": self.charge_status.value,
            "Fridge Door Status": self.get_doorstatus_string(self.fridge_door_status.value),
            "Freezer Door Status": self.get_doorstatus_string(self.freezer_door_status.value),
            "Errors": errors
        }
        return json.dumps(new_entry)
