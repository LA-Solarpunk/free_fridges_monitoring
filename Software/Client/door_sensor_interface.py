import RPi.GPIO as GPIO
from dataclasses import dataclass
from messages import SensorReading, DoorStateEnum
from enum import Enum
from typing import Tuple

import time

"""
TODOs:
- (Heidt) deduplicate fridge/freezer door checks
- (Heidt) should setup a config file to be able to customize pins
"""

@dataclass
class HallSensorPins:
    NC: int
    NO: int

@dataclass
class HallPinState:
    NC: int
    NO: int

FRIDGE_DOOR_PIN_NO = 26
FRIDGE_DOOR_PIN_NC = 19

FREEZER_DOOR_PIN_NO = 16
FREEZER_DOOR_PIN_NC = 20

fridge_pins = HallSensorPins(FRIDGE_DOOR_PIN_NC, FRIDGE_DOOR_PIN_NO)
freezer_pins = HallSensorPins(FREEZER_DOOR_PIN_NC, FREEZER_DOOR_PIN_NO)

def _check_door(pins: HallSensorPins):
    door_no = GPIO.input(pins.NO)
    door_nc = GPIO.input(pins.NC)
    new_reading = HallPinState(door_nc, door_no)
    return new_reading

def _configure_pins(pins: HallSensorPins):
    GPIO.setup(pins.NO, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(pins.NC, GPIO.IN, pull_up_down=GPIO.PUD_UP)

def setup_magnet_sensors():
    GPIO.setmode(GPIO.BCM)
    _configure_pins(fridge_pins)
    _configure_pins(freezer_pins)

class MagnetErrorEnum(Enum):
    FUNCTIONING = 0
    NC_BROKEN = 1
    NO_BROKEN = 2
    BROKEN_PINS = 3


class MagnetManager:
    def __init__(self, pins: HallSensorPins):
        self.pins = pins
        self.last_reading = _check_door(pins)
        if self.last_reading.NC == self.last_reading.NO:
            self.error = MagnetErrorEnum.BROKEN_PINS
            self.door_state = DoorStateEnum.UNKNOWN
        else:
            self.error = MagnetErrorEnum.FUNCTIONING
            self.door_state = DoorStateEnum.CLOSED if self.last_reading.NC == GPIO.HIGH else DoorStateEnum.OPEN

    def read(self) -> tuple[DoorStateEnum, MagnetErrorEnum]:
        reading = _check_door(self.pins)
        # If the door has changed state, keeps error if no change
        if reading != self.last_reading:
            # if they're both different, we can assume things are working
            if reading.NC != reading.NO:
                self.door_state = DoorStateEnum.CLOSED if reading.NC == GPIO.HIGH else DoorStateEnum.OPEN
                # if both pins have switched, everything is working correctly
                if reading.NC != self.last_reading.NC and reading.NO != self.last_reading.NO:
                    self.error = MagnetErrorEnum.FUNCTIONING
            else:
                if reading.NC == self.last_reading.NC and not self.error == MagnetErrorEnum.NO_BROKEN:
                    self.error = MagnetErrorEnum.NC_BROKEN
                    self.door_state = DoorStateEnum.CLOSED if reading.NO == GPIO.LOW else DoorStateEnum.OPEN
                else:
                    self.error = MagnetErrorEnum.NO_BROKEN
                    self.door_state = DoorStateEnum.CLOSED if reading.NC == GPIO.HIGH else DoorStateEnum.OPEN
        self.last_reading = reading
        return self.door_state, self.error
    
def error_to_string(error: MagnetErrorEnum):
    if error == MagnetErrorEnum.FUNCTIONING:
        return None
    elif error == MagnetErrorEnum.NC_BROKEN:
        return "Door sensor NC line broken"
    else:
        return "Door sensor NO line broken"
    
class DoorStatsManager:
    def __init__(self, magnet_manager: MagnetManager):
        self.magnet_manager = magnet_manager
        self.last_state = self.magnet_manager.door_state
        self.open_count = 0
        self.open_for = 0.0
        self.open_time = None

    def update(self):
        state, error = self.magnet_manager.read()
        if state == DoorStateEnum.OPEN and self.last_state == DoorStateEnum.CLOSED:
            self.open_count += 1
            self.open_time = time.time()
        elif state == DoorStateEnum.CLOSED and self.last_state == DoorStateEnum.OPEN:
            self.open_time = None
        self.last_state = state

    def get_values(self):
        open_count = self.open_count
        open_time = 0 if self.open_time is None else time.time() - self.open_time
        self.open_count = 0
        return open_count, open_time
        
class DoorSensorManager:
    def __init__(self):
        setup_magnet_sensors()
        self.fridge = MagnetManager(fridge_pins)
        self.freezer = MagnetManager(freezer_pins)
        self.fridge_stats = DoorStatsManager(self.fridge)
        self.freezer_stats = DoorStatsManager(self.freezer)

    def update_status(self):
        self.fridge_stats.update()
        self.freezer_stats.update()

    def get_fridge_door(self) -> SensorReading:
        result = self.fridge.read()
        open_count, open_time = self.fridge_stats.get_values()
        door_state = SensorReading(result[0], error_to_string(result[1]))
        open_time_reading = SensorReading(open_time, None)
        open_count_reading = SensorReading(open_count, None)
        return door_state, open_count_reading, open_time_reading
    
    def get_freezer_door(self) -> SensorReading:
        result = self.freezer.read()
        open_count, open_time = self.freezer_stats.get_values()
        door_state = SensorReading(result[0], error_to_string(result[1]))
        open_time_reading = SensorReading(open_time, None)
        open_count_reading = SensorReading(open_count, None)
        return door_state, open_count_reading, open_time_reading
         
def main():
    manager = DoorSensorManager()
    while True:
        print(f"Fridge Door state {manager.get_fridge_door()}")
        print(f"Freezer Door state {manager.get_freezer_door()}")
        time.sleep(0.2)

if __name__ == "__main__":
    main()
