from __future__ import annotations
from dataclasses import dataclass
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
class AirtableCfg:
    airtable_api_key: str | None = None

@dataclass(frozen=True)
class GDriveCfg:
    fridge_gdrive_credentials: str | None = None


@dataclass(frozen=True)
class MqttCfg:
    broker: str
    port: int
    data_topic: str
    username: str
    password: str


@dataclass(frozen=True)
class AppCfg:
    log_level: str = "INFO"


@dataclass(frozen=True)
class Settings:
    device: DeviceCfg
    airtable: AirtableCfg
    gdrive: GDriveCfg
    mqtt: MqttCfg
    app: AppCfg


def load_settings() -> Settings:
    device_config = DeviceCfg(os.environ["FRIDGE_DEVICE_ID"])
    airtable_config = AirtableCfg(os.environ["AIRTABLE_API_KEY"])
    gdrive_config = GDriveCfg(os.environ["FRIDGE_GDRIVE_CREDENTIALS"])
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
        airtable=airtable_config,
        gdrive=gdrive_config,
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
