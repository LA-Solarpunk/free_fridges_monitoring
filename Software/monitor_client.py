import os
import time
import logging
from datetime import datetime

import schedule
import minimalmodbus

import temperature_interface
import magnet_sensor_interface
import charge_interface
import mqtt
import messages
import google_drive

"""
This is the main file for the monitoring client. It creates a basic hourly and monthly scheduler to
pull data hourly and save that data to gdrive monthly.

TODO(Heidt) - hourly schedules are ok if missed, but monthly is bad. If there's an issue, a month may not
              get logged. Should maybe make a database or just simple local log to determine when things have
              happened and use that as reference.
TODO(Heidt) - should probably move away from script approach to module approach to aid testing
"""

logger = logging.getLogger(__name__)
logging.basicConfig(
    format="%(asctime)s [%(levelname)s] - %(message)s", level=logging.INFO
)
FRIDGE_ID = os.environ["FRIDGE_ID"]

charge_controller = charge_interface.ChargeInterface()
magnet_sensor_interface.setup_magnet_sensors()
mqtt_client = mqtt.connect_mqtt()

def get_entry():
    #TODO(Heidt) probably make a data aggregator type class to put all this logic
    errors = ""
    temperature_data = temperature_interface.read_temp()[0]
    charge_data = 0
    try:
        charge_data = charge_controller.get_charge_data()
    except minimalmodbus.NoResponseError:
        errors += "No response from charge controller\n"
    door_state = magnet_sensor_interface.is_door_open()
    entry = messages.SensorEntry(temperature_data, charge_data, door_state, FRIDGE_ID, errors)
    return entry

def send_data():
    entry =  get_entry()
    logger.info(f"Publishing new entry to airtable: {entry.get_json_string()}")
    mqtt.publish_data(mqtt_client, entry)

def main():
    logger.info("Starting monitoring client")
    schedule.every().hour.at("00:00").do(send_data)

    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == "__main__":
    main()
