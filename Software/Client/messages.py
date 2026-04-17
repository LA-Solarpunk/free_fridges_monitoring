
from magnet_sensor_interface import MagnetSensorState 
from dataclasses import dataclass
import json

@dataclass
class SensorEntry:
    temperature: float
    charge_status: float
    door_status: MagnetSensorState
    fridge_id: str
    errors: str

    def get_json_string(self):
        status = "Closed"
        if self.door_status == MagnetSensorState.DISCONNECTED:
            status = "Open"
        elif self.door_status == MagnetSensorState.ERROR:
            status = "Error"
        new_entry = {
            "Fridge": [self.fridge_id],
            "Temperature (°C)": self.temperature,
            "Charge Status (%)": self.charge_status,
            "Door Status": status,
            "Errors": self.errors
        }
        return json.dumps(new_entry)