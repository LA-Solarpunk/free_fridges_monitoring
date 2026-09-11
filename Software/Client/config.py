from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
import os
import logging
import pprint

logger = logging.getLogger(__name__)


# -------- Paths --------
def default_config_path() -> Path:
    p = os.environ.get("SPF_CONFIG")
    return Path(p).expanduser()


# -------- Models --------
@dataclass(frozen=True)
class DeviceCfg:
    device_id: str


@dataclass(frozen=True)
class MqttCfg:
    broker: str
    port: int
    data_topic: str
    username: str
    password: str = field(repr=False)


@dataclass(frozen=True)
class AppCfg:
    log_level: str = "INFO"


@dataclass(frozen=True)
class Settings:
    device: DeviceCfg
    mqtt: MqttCfg
    app: AppCfg


def load_settings() -> Settings:
    device_config = DeviceCfg(os.environ["FRIDGE_DEVICE_ID"])
    mqtt_config = MqttCfg(
        broker=os.environ["MQTT_BROKER"],
        port=int(os.environ["MQTT_PORT"]),
        data_topic=os.environ["MQTT_TOPIC"],
        username=os.environ["MQTT_USERNAME"],
        password=os.environ["MQTT_PASSWORD"],
    )
    app_config = AppCfg(os.environ["FRIDGE_LOGLEVEL"])

    settings = Settings(
        device=device_config,
        mqtt=mqtt_config,
        app=app_config,
    )
    logger.info(f"Loaded new config \n{pprint.pformat(settings)}")
    
    return settings


# -------- Example usage --------
if __name__ == "__main__":
    S = load_settings()
    print(
        f"Loaded config for device '{S.device.device_id}' → MQTT {S.mqtt.broker}:{S.mqtt.port} topic '{S.mqtt.data_topic}'"
    )
