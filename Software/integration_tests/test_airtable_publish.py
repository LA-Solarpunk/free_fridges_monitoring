import sys
sys.path.append("..") # Adds higher directory to python modules path.
from monitor_client import send_data
import time


"""
Populate an entry object from real sensor data attached to the device and print to the terminal every 5 seconds

TODO(Heidt) convert to package, adding .. to sys is a code smell
"""

def main():
    print("sending data")
    time.sleep(5.0)
    send_data()

if __name__ == "__main__":
    main()
