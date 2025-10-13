import os
import time
import logging
from datetime import datetime

import schedule

import temperature_interface
import magnet_sensor_interface
import charge_interface
import airtable
import google_drive

"""
This is the main file for the monitoring client. It creates a basic hourly and monthly scheduler to
pull data hourly and save that data to gdrive monthly.

TODO(Heidt) - hourly schedules are ok if missed, but monthly is bad. If there's an issue, a month may not
              get logged. Should maybe make a database or just simple local log to determine when things have
              happened and use that as reference.
"""

logger = logging.getLogger(__name__)
logging.basicConfig(
    format="%(asctime)s [%(levelname)s] - %(message)s", level=logging.INFO
)
FRIDGE_ID = os.environ["FRIDGE_ID"]


def send_data():
    temperature_data = temperature_interface.read_temp()[0]
    charge_data = charge_interface.get_charge_data()
    door_state = magnet_sensor_interface.is_door_open()
    entry = airtable.Entry(temperature_data, charge_data, door_state, FRIDGE_ID)
    logger.info(f"Publishing new entry to airtable: {entry.get_json_string()}")
    airtable.send_data_to_airtable(entry)

def save_data_to_drive():
    # only run on the first of the month
    if datetime.today().day != 1:
        return
    fridgename = airtable.get_fridge_name(FRIDGE_ID)
    filename = f"{fridgename}_{datetime.now().isoformat()}.csv"
    logger.info(f"Saving {filename} to google drive")
    airtable_data = airtable.airtable_recent_rows_by_id_to_csv(FRIDGE_ID)
    google_drive.upload_csv_to_drive(airtable_data, filename)


def main():
    logger.info("Starting monitoring client")
    schedule.every().hour.at("00:00").do(send_data)
    schedule.every().day.at("02:00").do(save_data_to_drive)

    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == "__main__":
    main()
