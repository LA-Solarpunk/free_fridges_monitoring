import os
import json
from pyairtable import Api
from dataclasses import dataclass

BASE_NAME = "app3C7ktuj4lyrQS6" 
READINGS_TABLE_NAME = "tbluQQWvULLlvZ2KY"
FRIDGE_TABLE_NAME = "tbl6qhf2XkHFyNKrg"

@dataclass
class Entry:
    temperature: float
    charge_status: float
    door_status: bool
    fridge_id: str

    def get_json_string(self):
        status = "Open" if self.door_status else "Closed"
        new_entry = {
            "Fridge": [self.fridge_id],
            "Temperature (°C)": self.temperature,
            "Charge Status (%)": self.charge_status,
            "Door Status": status,
        }
        return new_entry

def send_data_to_airtable(entry: Entry):
    api = Api(os.environ["AIRTABLE_API_KEY"])
    table = api.table(BASE_NAME, READINGS_TABLE_NAME)
    table.create(entry.get_json_string())

def get_fridge_ids():
    api = Api(os.environ["AIRTABLE_API_KEY"])
    table = api.table(BASE_NAME, FRIDGE_TABLE_NAME)
    return table.all(fields=["Fridge Name"])

def main():
    json_data = get_fridge_ids()
    print(json.dumps(json_data, indent=4))

if __name__ == "__main__":
    main()