import os
import glob
import logging
from messages import SensorReading
import config


"""
TODOS:
- there's hopefully a better way of mapping pins to sensors than the implicit ordering in config.txt...
"""

CONFIG = config.load_settings()
THRESHOLD_CONFIG = CONFIG.threshold

class TempInterface: 
    def __init__(self, gpio_pins):
        self.sensor_map = get_w1_pin_map(gpio_pins)

    def get_w1_pin_map(gpio_pins: list[int]) -> dict[str, int]:
        """
        Returns a dict mapping sensor ID (e.g. '28-abcdef012345') to its GPIO pin.
        
        gpio_pins: ordered list of GPIO pins as specified in config.txt overlays,
                e.g. [4, 17] if you have gpiopin=4 loaded before gpiopin=17.
        """
        masters_base = "/sys/bus/w1/devices"
        
        masters = sorted(glob.glob(os.path.join(masters_base, "w1_bus_master*")))
        
        if len(masters) != len(gpio_pins):
            raise RuntimeError(
                f"Found {len(masters)} W1 master(s) but expected {len(gpio_pins)}. "
                f"Check your /boot/config.txt overlays."
            )
        
        sensor_to_pin = {}
    
        for master_path, gpio_pin in zip(masters, gpio_pins):
            slaves_file = os.path.join(master_path, "w1_master_slaves")
            
            with open(slaves_file, "r") as f:
                slaves = [line.strip() for line in f if line.strip()]
            
            for slave_id in slaves:
                if slave_id.startswith("28-"):  # DS18B20 family code
                    sensor_to_pin[slave_id] = gpio_pin
                    logging.info(f"  Sensor {slave_id}  →  GPIO{gpio_pin}")
        
        return sensor_to_pin


    def read_temperature(sensor_id: str) -> float | None:
        """Read temperature in Celsius from a DS18B20 by its sensor ID."""
        device_file = f"/sys/bus/w1/devices/{sensor_id}/w1_slave"
        
        with open(device_file, "r") as f:
            lines = f.readlines()
        
        if lines[0].strip().endswith("YES"):
            temp_str = lines[1].split("t=")[1].strip()
            return float(temp_str) / 1000.0
        
        return None  # CRC check failed

    def get_temperatures():
        """
        Returns a dict mapping gpio pin to temperature
        
        gpio_pins: ordered list of GPIO pins as specified in config.txt overlays,
                e.g. [4, 17] if you have gpiopin=4 loaded before gpiopin=17.
        """
        temperatures = {}
        for sensor_id, pin in self.sensor_map.items():
            temp = read_temperature(sensor_id)
            error = "Issue reading temp sensor" if temp is None else None
            temperatures[pin] = SensorReading(temp, error)

        
        return temperatures
    
    def print_temperatures(): 
        for sensor_id, pin in self.sensor_map.items():
            temp = read_temperature(sensor_id)
            print(f"  GPIO{pin} | {sensor_id} | {temp:.3f}°C")


if __name__ == "__main__":
    # Match the order of dtoverlay lines in config.txt
    GPIO_PINS = [5, 6]
    
    print("Discovering sensors...")
    temp_interface = TempInterface(GPIO_PINS)
    
    
    print("\nTemperature readings:")
    temp_interface.print_temperatures()

