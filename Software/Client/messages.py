from dataclasses import dataclass
from enum import Enum
import json

class DoorStateEnum(Enum):
    OPEN = 0
    CLOSED = 1
    UNKNOWN = 2

@dataclass
class Config:
    threshold: Threshold

@dataclass 
class Threshold: 
    fridge_open_time_limit: float
    freezer_open_time_limit: float
    fridge_temp_threshold: float
    freezer_temp_threshold: float

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
        self.dirty = False

        #check fridge and freezer temperatures
        fridge_temp_threshold = config.threshold.fridge_temp_threshold
        freezer_temp_threshold = config.threshold.freezer_temp_threshold
        fridge_open_time_threshold = config.threshold.fridge_open_time_limit 
        freezer_open_time_threshold = config.threshold.freezer_open_time_limit
        
        self.alert_info = {}

        self.alert_data = {
            "fridge": {
                "open_time": data.fridge_door_open_time,
                "temp": data.fridge_temperature,
                "device_threshold": {
                    "open_time": fridge_open_time_threshold,
                    "temp": fridge_temp_threshold
                },
                "trigger": {
                    "open_time": data.fridge_door_open_time > fridge_open_time_threshold,
                    "temp": data.fridge_temperature > fridge_temp_threshold
                }
            },
            "freezer": {
                "open_time": data.freezer_door_open_time,
                "temp": data.freezer_temperature,
                "device_threshold": {
                    "open_time": freezer_open_time_threshold,
                    "temp": freezer_temp_threshold
                },
                "trigger": {
                    "open_time": data.freezer_door_open_time > freezer_open_time_threshold,
                    "temp": data.freezer_temperature > freezer_temp_threshold
                }
            }
        }

        if(data.fridge_temperature > fridge_temp_threshold):
            self.alert_info = self.alert_info | {
                f"Fridge Threshold ({fridge_temp_threshold})" : f"Triggered alert at temperature {self.data.fridge_temperature}"
            }
        
        if(data.freezer_temperature > freezer_temp_threshold):
            self.alert_info = self.alert_info | {
                f"Freezer Threshold ({freezer_temp_threshold})" : f"Triggered alert at temperature {self.data.freezer_temperature}"
            }
        
        if(data.fridge_door_open_time > fridge_open_time_threshold):
            self.alert_info = self.alert_info | {
                f"Fridge Open Time Threshold ({fridge_open_time_threshold})" : f"Triggered alert at {self.data.fridge_door_open_count} seconds"
            }
        
        if(data.freezer_door_open_time > freezer_open_time_threshold):
            self.alert_info = self.alert_info | {
                f"Freezer Open Time Threshold ({freezer_open_time_threshold})" : f"Triggered alert at {self.data.freezer_door_open_count} seconds"
            }
        
        
        

        if(len(self.alert_data) > 0):
            self.dirty = True 
        

    def doPublish():
        return self.dirty

    def get_json_string(self):
        return json.dumps(self.alert_data)   

if __name__ == "__main__":
    data = SensorEntry(
        70.0, # fridge temp
        15.0, # freezer temp
        79.0, # charge 
        1, # fridge open status
        0, # fridge open count
        10.0, # fridge open time
        1, # freezer open status
        0, # freezer open count
        10.0, # freezer open time
        "test fridge", #fridge ID
    )
    
    config = Config(
        threshold = Threshold(
            fridge_open_time_limit=180.0,
            freezer_open_time_limit=180.0,
            fridge_temp_threshold=60.0,
            freezer_temp_threshold=10.0
        )
    )
    

    alert = AlertEntry(data, config)

    val = alert.get_json_string()

    print(val)
