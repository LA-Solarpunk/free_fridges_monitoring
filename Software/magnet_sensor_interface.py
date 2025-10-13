import RPi.GPIO as GPIO
from enum import Enum
import time


DOOR_PIN_NO = 20
DOOR_PIN_NC = 21

class MagnetSensorState(Enum):
    CONNECTED = 1
    DISCONNECTED = 2
    ERROR = 3

def is_door_open() -> MagnetSensorState:
    door_no = GPIO.input(DOOR_PIN_NO)
    door_nc = GPIO.input(DOOR_PIN_NC)
    if door_no == GPIO.HIGH and door_nc == GPIO.LOW:
        return MagnetSensorState.CONNECTED
    elif door_no == GPIO.LOW and door_nc == GPIO.HIGH:
        return MagnetSensorState.DISCONNECTED
    else:
        return MagnetSensorState.ERROR
    
def setup_magnet_sensors():
    GPIO.setup(DOOR_PIN_NC, GPIO.IN, pull_up_down=GPIO.PUD_UP)


def main():
    while True:
        print(f"Door state {is_door_open()}")

if __name__ == "__main__":
    main()
