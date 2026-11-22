import argparse
import logging
import time

import temperature_interface
import door_sensor_interface
import charge_interface

"""
Manual hardware checks to run during fridge installation/bring-up. Each hardware
subcommand loops printing live readings until Ctrl+C, so you can watch a value
change as you wiggle a wire or warm a sensor. `send-data` instead runs the real
end-to-end publish path once.
"""

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] - %(message)s", level=logging.INFO
)


def test_temperature():
    print("Discovering sensors on the 1-Wire bus...")
    sensor_ids = temperature_interface.discover_sensors()

    print("\nTemperature readings (Ctrl+C to stop):")
    while True:
        temperatures = temperature_interface.get_temperatures(sensor_ids)
        for rom_id, reading in temperatures.items():
            if reading.error:
                print(f"{rom_id}: {reading.error}")
            else:
                print(f"{rom_id}: {reading.value:.3f}")
        time.sleep(1)


def test_doors():
    manager = door_sensor_interface.DoorSensorManager()
    print("Door sensor readings (Ctrl+C to stop):")
    while True:
        print(f"Fridge door: {manager.get_fridge_door()}")
        print(f"Freezer door: {manager.get_freezer_door()}")
        time.sleep(0.2)


def test_charge():
    charger = charge_interface.ChargeInterface()
    print("Charge controller readings (Ctrl+C to stop):")
    while True:
        print(f"Battery SOC: {charger.get_charge_data()}")
        print(f"Battery voltage: {charger.controller.get_battery_voltage()}V")
        print(f"Load voltage: {charger.controller.get_load_voltage()}V")
        print(f"Load current: {charger.controller.get_load_current()}A")
        print(f"Load power: {charger.controller.get_load_power()}W")
        time.sleep(1)


def test_current():
    monitor = charge_interface.CurrentMonitor()
    print("Hall effect current sensor readings (Ctrl+C to stop):")
    while True:
        print(monitor.read_current())
        time.sleep(1)


def test_send_data():
    import monitor_client

    print("Sending one entry through the real end-to-end path...")
    monitor_client.send_data()
    print("Done. Check the server to confirm the reading arrived.")


TESTS = {
    "temperature": (test_temperature, "Discover 1-Wire sensors and print ID: temp readings every second."),
    "doors": (test_doors, "Print fridge/freezer door open/closed state every 0.2s."),
    "charge": (test_charge, "Print Renogy charge controller battery SOC, battery voltage, and load voltage/current/power every second."),
    "current": (test_current, "Print the ADS1115 hall effect current sensor reading every second."),
    "send-data": (test_send_data, "Run the real end-to-end path once: build a SensorEntry and publish it over MQTT."),
}


def main():
    test_list = "\n".join(f"  {name:<12} {description}" for name, (_, description) in TESTS.items())
    parser = argparse.ArgumentParser(
        description="Standalone hardware checks for fridge installation.",
        epilog=f"Tests:\n{test_list}",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("test", choices=TESTS.keys(), help="Which hardware element (or end-to-end path) to test.")
    args = parser.parse_args()

    test_func, _ = TESTS[args.test]
    try:
        test_func()
    except KeyboardInterrupt:
        print("\nStopping.")


if __name__ == "__main__":
    main()
