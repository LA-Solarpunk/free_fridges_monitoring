import os
import glob
import time
import logging
from messages import SensorReading


def discover_sensors() -> list[str]:
    """
    Returns a list of sensor IDs (e.g. '28-abcdef012345') found across all
    w1 bus master(s) on the system.
    """
    masters_base = "/sys/bus/w1/devices"
    masters = sorted(glob.glob(os.path.join(masters_base, "w1_bus_master*")))

    if not masters:
        raise RuntimeError(
            f"Found no W1 master under {masters_base}. Check your /boot/config.txt overlay."
        )

    sensor_ids = []

    for master_path in masters:
        slaves_file = os.path.join(master_path, "w1_master_slaves")

        with open(slaves_file, "r") as f:
            slaves = [line.strip() for line in f if line.strip()]

        for slave_id in slaves:
            if slave_id.startswith("28-"):  # DS18B20 family code
                sensor_ids.append(slave_id)
                logging.info(f"  Found sensor {slave_id}")

    return sensor_ids


def read_temperature(sensor_id: str) -> float | None:
    """Read temperature in Celsius from a DS18B20 by its sensor ID."""
    device_file = f"/sys/bus/w1/devices/{sensor_id}/w1_slave"

    with open(device_file, "r") as f:
        lines = f.readlines()

    if lines[0].strip().endswith("YES"):
        temp_str = lines[1].split("t=")[1].strip()
        return float(temp_str) / 1000.0

    return None  # CRC check failed


def get_temperatures(rom_ids: list[str]) -> dict[str, SensorReading]:
    """
    Returns a dict mapping sensor ROM ID to its SensorReading.

    rom_ids: list of sensor IDs (e.g. '28-abcdef012345') to read.
    """
    temperatures = {}
    for rom_id in rom_ids:
        temp = read_temperature(rom_id)
        error = "Issue reading temp sensor" if temp is None else None
        temperatures[rom_id] = SensorReading(temp, error)
    return temperatures


if __name__ == "__main__":
    print("Discovering sensors...")
    sensor_ids = discover_sensors()

    print("\nTemperature readings (Ctrl+C to stop):")
    while True:
        temperatures = get_temperatures(sensor_ids)
        for rom_id, reading in temperatures.items():
            if reading.error:
                print(f"{rom_id}: {reading.error}")
            else:
                print(f"{rom_id}: {reading.value:.3f}")
        time.sleep(1)
