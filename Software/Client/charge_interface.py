from renogymodbus import RenogyChargeController, find_slaveaddress
import minimalmodbus
import logging
import time
import board
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
from messages import SensorReading

# 4-20mA hall effect current sensor (0-100A range) shunted through a 165ohm
# resistor, read by an ADS1115 on the i2c bus.
SHUNT_RESISTANCE_OHMS = 165.0
HALL_SENSOR_MIN_CURRENT_MA = 4.0
HALL_SENSOR_MAX_CURRENT_MA = 20.0
HALL_SENSOR_MAX_RATED_AMPS = 100.0

ADS1115_ADDRESS = 0x48
ADS1115_CHANNELS = {0: ADS.P0, 1: ADS.P1, 2: ADS.P2, 3: ADS.P3}


class CurrentMonitor:
    def __init__(self, address=ADS1115_ADDRESS, channel=0):
        i2c = busio.I2C(board.SCL, board.SDA)
        # gain=1 -> +/-4.096V range, which comfortably covers the shunt's 0-3.3V output
        self.ads = ADS.ADS1115(i2c, address=address, gain=1)
        self.chan = AnalogIn(self.ads, ADS1115_CHANNELS[channel])

    def read_current(self) -> SensorReading:
        """Read the DC current (in Amps) flowing through the hall effect sensor."""
        try:
            shunt_voltage = self.chan.voltage
        except OSError:
            return SensorReading(None, "Issue reading current sensor")

        sense_current_ma = (shunt_voltage / SHUNT_RESISTANCE_OHMS) * 1000.0
        amps = (
            (sense_current_ma - HALL_SENSOR_MIN_CURRENT_MA)
            / (HALL_SENSOR_MAX_CURRENT_MA - HALL_SENSOR_MIN_CURRENT_MA)
            * HALL_SENSOR_MAX_RATED_AMPS
        )
        return SensorReading(amps, None)


class ChargeInterface:
    def __init__(self, serial_port="/dev/serial0"):
        self.serial_port = serial_port
        self.controller = None
        self.setup_controller()
        self.current_monitor = CurrentMonitor()

        self.fridge_watt_hours = 0.0
        self.load_watt_hours = 0.0
        self.last_watt_hour_update = None

    def setup_controller(self):
        logging.info("Setting up charge controller")
        self.controller = RenogyChargeController(self.serial_port, 255)
        if self._try_address(self.controller, 255):
            return
        elif self._try_address(self.controller, 1):
            return
        else:
            logging.info("Performing wide scan of addresses")
            addresses = find_slaveaddress(self.serial_port)
            if addresses:
                # just use the first address in the weird case there are multiple on the bus
                self.controller.address = addresses[0]
            else:
                logging.error("Could not find any device!")

    def _try_address(self, controller: RenogyChargeController, address: int):
        controller.address = address
        try:
            voltage = controller.get_battery_voltage()
            logging.info(f"Found charge controller at address {address}, battery voltage: {voltage}")
            self.controller = controller
            return True
        except minimalmodbus.NoResponseError:
            logging.warning(f"Could not find charge controller at address {address}")
        return False

    def get_charge_data(self) -> SensorReading:
        charge_data = 0.0
        errors = None
        try:
            charge_data = self.controller.get_battery_state_of_charge()
        except minimalmodbus.NoResponseError:
            errors = "No response from charge controller"
        return SensorReading(charge_data, errors)

    def update_watt_hours(self):
        """
        Reads the fridge's inverter current and the charge controller's load power,
        and integrates them into cumulative watt-hour totals since this process started.
        Call this periodically (e.g. once a second) to keep the totals up to date.
        """
        now = time.time()
        elapsed_hours = 0.0 if self.last_watt_hour_update is None else (now - self.last_watt_hour_update) / 3600.0
        self.last_watt_hour_update = now

        current_reading = self.current_monitor.read_current()
        if current_reading.error is None:
            try:
                battery_voltage = self.controller.get_battery_voltage()
                fridge_watts = battery_voltage * current_reading.value
                self.fridge_watt_hours += fridge_watts * elapsed_hours
            except minimalmodbus.NoResponseError:
                logging.warning("No response from charge controller while updating fridge watt-hours")
        else:
            logging.warning(f"Skipping fridge watt-hour update: {current_reading.error}")

        try:
            load_watts = self.controller.get_load_power()
            self.load_watt_hours += load_watts * elapsed_hours
        except minimalmodbus.NoResponseError:
            logging.warning("No response from charge controller while updating load watt-hours")

    def get_fridge_watt_hours(self) -> SensorReading:
        return SensorReading(self.fridge_watt_hours, None)

    def get_load_watt_hours(self) -> SensorReading:
        return SensorReading(self.load_watt_hours, None)


def main():
    charger = ChargeInterface()
    while True:
        charger.update_watt_hours()
        print(charger.get_charge_data())
        print(f"Fridge watt-hours: {charger.get_fridge_watt_hours()}")
        print(f"Load watt-hours: {charger.get_load_watt_hours()}")
        time.sleep(1)

if __name__ == "__main__":
    main()
