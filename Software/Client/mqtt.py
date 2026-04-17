from paho.mqtt import client as mqtt_client
import os
import logging
import time
from messages import SensorEntry, MagnetSensorState
import config

logger = logging.getLogger(__name__)

CONFIG = config.load_settings()
CLIENT_ID = CONFIG.device.device_id
USERNAME = CONFIG.mqtt.username
PASSWORD = CONFIG.mqtt.password
BROKER = CONFIG.mqtt.broker
PORT = CONFIG.mqtt.port
DATA_TOPIC = CONFIG.mqtt.data_topic

FIRST_RECONNECT_DELAY = 1
RECONNECT_RATE = 2
MAX_RECONNECT_COUNT = 12
MAX_RECONNECT_DELAY = 60

def connect_mqtt():
    def on_connect(client, userdata, flags, rc, properties):
        if rc == 0:
            print("Connected to MQTT Broker!")
        else:
            print("Failed to connect, return code %d\n", rc)

    client = mqtt_client.Client(client_id=CLIENT_ID, callback_api_version=mqtt_client.CallbackAPIVersion.VERSION2)
    client.username_pw_set(USERNAME, PASSWORD)
    client.on_connect = on_connect
    client.connect(BROKER, PORT)

    client.loop_start()
    client.on_disconnect = on_disconnect
    return client

def on_disconnect(client, userdata, rc):
    logger.info("Disconnected with result code: %s", rc)
    reconnect_count, reconnect_delay = 0, FIRST_RECONNECT_DELAY
    while reconnect_count < MAX_RECONNECT_COUNT:
        logger.info("Reconnecting in %d seconds...", reconnect_delay)
        time.sleep(reconnect_delay)

        try:
            client.reconnect()
            logger.info("Reconnected successfully!")
            return
        except Exception as err:
            logger.error("%s. Reconnect failed. Retrying...", err)

        reconnect_delay *= RECONNECT_RATE
        reconnect_delay = min(reconnect_delay, MAX_RECONNECT_DELAY)
        reconnect_count += 1
    logger.info("Reconnect failed after %s attempts. Exiting...", reconnect_count)

def publish_data(client: mqtt_client.Client, data: SensorEntry):
    result = client.publish(DATA_TOPIC, data.get_json_string(), qos=1)
    return result

if __name__ == "__main__":
    import sys
    logger.setLevel(logging.INFO)
    stream_handler = logging.StreamHandler(stream=sys.stdout)
    logger.addHandler(stream_handler)
    logger.info(CONFIG)

    data = SensorEntry(26.0, 79.0, MagnetSensorState.CONNECTED, "test fridge", "") 
    client = connect_mqtt()
    publish_data(client, data)