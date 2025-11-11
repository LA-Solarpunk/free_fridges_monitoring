import sys
sys.path.append("..") # Adds higher directory to python modules path.
from monitor_client import get_entry
import time


"""
Populate an entry object from real sensor data attached to the device and print to the terminal every 5 seconds

TODO(Heidt) convert to package, adding .. to sys is a code smell
"""

def main():
    while True:
        entry = get_entry()
        print(f"Got entry {entry}")
        time.sleep(5.0)

if __name__ == "__main__":
    main()