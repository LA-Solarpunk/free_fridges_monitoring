import os
import time
import logging
from datetime import datetime

import schedule
import minimalmodbus

import temperature_interface
import door_sensor_interface
import charge_interface
import mqtt
import messages
import google_drive
import config

"""
This is the main file for the monitoring client. It creates a basic hourly and monthly scheduler to
pull data hourly and save that data to gdrive monthly.

TODO(Heidt) - hourly schedules are ok if missed, but monthly is bad. If there's an issue, a month may not
              get logged. Should maybe make a database or just simple local log to determine when things have
              happened and use that as reference.
TODO(Heidt) - should probably move away from script approach to module approach to aid testing
TODO(Heidt) - add error messaging for each sensor
"""

logger = logging.getLogger(__name__)
logging.basicConfig(
    format="%(asctime)s [%(levelname)s] - %(message)s", level=logging.INFO
)
settings = config.load_settings()
FRIDGE_ID = settings.device.device_id

charge_controller = charge_interface.ChargeInterface()
door_sensors = door_sensor_interface.DoorSensorManager()
mqtt_client = mqtt.connect_mqtt()

# assuming fridge, freezer ordering
gpio_pins = [5, 6]


def get_entry():
    # TODO(Heidt) probably make a data aggregator type class to put all this logic
    temperature_data = temperature_interface.get_temperatures(gpio_pins)

    charge_reading = charge_controller.get_charge_data()        
    fridge_door_state = door_sensors.get_fridge_door()
    freezer_door_state = door_sensors.get_freezer_door()

    entry = messages.SensorEntry(
        temperature_data[gpio_pins[0]],
        temperature_data[gpio_pins[1]],
        charge_reading,
        fridge_door_state,
        freezer_door_state,
        FRIDGE_ID
    )
    return entry


def send_data():
    entry = get_entry()
    logger.info(f"Publishing new entry to mqtt: {entry.get_json_string()}")
    mqtt.publish_data(mqtt_client, entry)


def main():
    logger.info("Starting monitoring client")
    schedule.every(1).minutes.do(send_data)

    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == "__main__":
    main()
