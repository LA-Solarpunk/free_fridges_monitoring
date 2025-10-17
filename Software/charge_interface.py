from renogymodbus import RenogyChargeController
import minimalmodbus
import logging


class ChargeInterface:
    def __init__(self):
        self.setup_controller()

    def setup_controller(self, serial_port="/dev/ttySerial0"):
        logging.info("Setting up charge controller")
        controller = RenogyChargeController(serial_port, 255)
        if self._try_address(controller, 255):
            self.controller = controller
            return
        elif self._try_address(controller, 1):
            self.controller = controller
            return
        else:
            for i in range(1, 255):
                if self._try_address(controller, i):
                    self.controller = controller
                    return

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
    
    def get_charge_data(self):
        return self.controller.get_battery_state_of_charge()



    