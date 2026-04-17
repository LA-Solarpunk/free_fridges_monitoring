
from magnet_sensor_interface import MagnetSensorState 
from dataclasses import dataclass
import json

@dataclass
class SensorEntry:
    fridge_temperature: float
    freezer_temperature: float
    charge_status: float
    fridge_door_status: MagnetSensorState
    freezer_door_status: MagnetSensorState
    fridge_id: str
    errors: str

    def get_doorstatus_string(self, status: MagnetSensorState):
        status = "Closed"
        if status == MagnetSensorState.DISCONNECTED:
            status = "Open"
        elif status == MagnetSensorState.ERROR:
            status = "Error"
        return status

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