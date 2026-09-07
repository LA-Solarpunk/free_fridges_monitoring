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
    fridge_door_open_count: SensorReading
    fridge_door_open_time: SensorReading
    freezer_door_status: SensorReading
    freezer_door_open_count: SensorReading
    freezer_door_open_time: SensorReading
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
        # TODO(Heidt) need a better way to go through sensor readings looking for errors...
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
            "Fridge Open Count": self.fridge_door_open_count.value,
            "Fridge Open Time": self.fridge_door_open_time.value,
            "Freezer Door Status": self.get_doorstatus_string(self.freezer_door_status.value),
            "Freezer Open Count": self.freezer_door_open_count.value,
            "Freezer Open Time": self.freezer_door_open_time.value,
            "Errors": errors
        }
        return json.dumps(new_entry)

class AlertEntry: 

    def __init__(self, data, config):
        self.data = data
        self.dirty = false

        #check fridge and freezer temperatures
        fridge_temp_threshold = config.threshold.fridge_temp_threshold
        freezer_temp_threshold = config.threshold.freezer_temp_threshold
        fridge_open_time_threshold = config.threshold.fridge_open_time_limit 
        freezer_open_time_threshold = config.threshold.freezer_open_time_limit
        
        self.alert_info = {}

        if(data.fridge_temperature > fridge_temp_threshold) {
            self.alert_info = self.alert_info | {
                f"Fridge Threshold ({fridge_temp_threshold})" : f"Triggered alert at temperature {self.data.fridge_temperature.value}"
            }
        }
        if(data.freezer_temperature > freezer_temp_threshold) {
            self.alert_info = self.alert_info | {
                f"Freezer Threshold ({freezer_temp_threshold})" : f"Triggered alert at temperature {self.data.freezer_temperature.value}"
            }
        }
        if(data.fridge_door_open_time > fridge_open_time_threshold) {
            self.alert_info = self.alert_info | {
                f"Fridge Open Time Threshold ({fridge_open_time_threshold})" : f"Triggered alert at {self.data.fridge_door_open_count.value} seconds"
            }
        }
        if(data.freezer_door_open_time > freezer_open_time_threshold) {
            self.alert_info = self.alert_info | {
                f"Freezer Open Time Threshold ({freezer_open_time_threshold})" : f"Triggered alert at {self.data.freezer_door_open_count.value} seconds"
            }
        }

        if(len(alert_info) > 0)  {
            self.dirty = true 
        }

    def doPublish()
        return self.dirty

    def get_json_string() 
        return json.dumps(self.alert_info)        
