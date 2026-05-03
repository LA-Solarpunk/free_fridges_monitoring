from renogymodbus import RenogyChargeController, find_slaveaddress
import minimalmodbus
import logging
from messages import SensorReading

class ChargeInterface:
    def __init__(self, serial_port="/dev/serial0"):
        self.serial_port = serial_port
        self.controller = None
        self.setup_controller()

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


def main():
    charger = ChargeInterface()
    print(charger.get_charge_data())

if __name__ == "__main__":
    main()

    
