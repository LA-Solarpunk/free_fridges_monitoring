import os
import time
import logging
from datetime import datetime

import schedule

import temperature_interface
import door_state_interface
import charge_interface
import airtable

logger = logging.getLogger(__name__)
logging.basicConfig(
    format="%(asctime)s [%(levelname)s] - %(message)s", level=logging.INFO
)
fridge_id = os.environ["FRIDGE_ID"]


def send_data():
    temperature_data = temperature_interface.read_temp()[0]
    charge_data = charge_interface.get_charge_data()
    door_state = door_state_interface.is_door_open()
    entry = airtable.Entry(temperature_data, charge_data, door_state, fridge_id)
    logger.info(f"Publishing new entry to airtable: {entry.get_json_string()}")
    airtable.send_data_to_airtable(entry)


def main():
    logger.info("Starting monitoring client")
    schedule.every().hour.at("00:00").do(send_data)

    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == "__main__":
    main()
