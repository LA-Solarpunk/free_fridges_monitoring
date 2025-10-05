import os

from pyairtable import Api
from datetime import datetime

api = Api(os.environ['AIRTABLE_API_KEY'])

table = api.table('app3C7ktuj4lyrQS6', 'tbluQQWvULLlvZ2KY')

print(table.all())

new_entry = {
    "Fridge": ['recsvT3QAhS953Vin'],
    "Timestamp": "2025-9-30",
    "Temperature (°C)": 25,
    "Charge Status (%)": 80,
    "Door Status": "Closed",
}

table.create(new_entry)