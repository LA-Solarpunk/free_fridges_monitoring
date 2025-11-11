from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import os
import sys

# --- TOML parser (tomllib on 3.11+, else tomli) ---
try:
    import tomllib as _toml  # Python 3.11+
except ModuleNotFoundError:  # <3.11
    import tomli as _toml

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

# -------- Loader --------
_PLACEHOLDER = "__REPLACEME__"

def _is_missing_or_placeholder(v) -> bool:
    if v is None:
        return True
    if isinstance(v, str) and v.strip() == _PLACEHOLDER:
        return True
    return False

def load_settings(path: Path | None = None) -> Settings:
    cfg_path = path or default_config_path()
    try:
        with open(cfg_path, "rb") as f:
            raw = _toml.load(f)
    except FileNotFoundError:
        sys.exit(f"Config not found: {cfg_path}\n"
                 f"Create it (copy your template) and fill in required values.")

    d = raw.get("device", {}) or {}
    a = raw.get("airtable", {}) or {}
    g = raw.get("gdrive", {}) or {}
    m = raw.get("mqtt", {}) or {}
    app = raw.get("app", {}) or {}

    # Required keys (hard fail if missing/placeholder)
    required = {
        "device.device_id": d.get("device_id"),
        "mqtt.broker": m.get("broker"),
        "mqtt.port": m.get("port"),
        "mqtt.data_topic": m.get("data_topic"),
        "mqtt.username": m.get("username"),
        "mqtt.password": m.get("password"),
    }
    missing = [k for k, v in required.items() if _is_missing_or_placeholder(v)]
    if missing:
        sys.exit("Missing or placeholder config values:\n  - " + "\n  - ".join(missing)
                 + f"\n(Replace '{_PLACEHOLDER}' with real values.)")

    # Gentle warnings for optional secrets set to placeholder
    warnings = []
    if _is_missing_or_placeholder(a.get("airtable_api_key")):
        warnings.append("airtable.airtable_api_key is not set; Airtable features will be disabled.")
    if _is_missing_or_placeholder(g.get("fridge_gdrive_credentials")):
        warnings.append("gdrive.fridge_gdrive_credentials is not set; GDrive features will be disabled.")
    if warnings:
        for w in warnings:
            print(f"WARNING: {w}", file=sys.stderr)

    try:
        mqtt_port = int(m["port"])
    except (TypeError, ValueError):
        sys.exit("mqtt.port must be an integer.")

    settings = Settings(
        device=DeviceCfg(device_id=str(d["device_id"]).strip()),
        airtable=AirtableCfg(airtable_api_key=a.get("airtable_api_key")),
        gdrive=GDriveCfg(fridge_gdrive_credentials=g.get("fridge_gdrive_credentials")),
        mqtt=MqttCfg(
            broker=str(m["broker"]).strip(),
            port=mqtt_port,
            data_topic=str(m["data_topic"]).strip(),
            username=str(m["username"]).strip(),
            password=str(m["password"]),
        ),
        app=AppCfg(log_level=str(app.get("log_level", "INFO")).upper()),
    )
    return settings

# -------- Example usage --------
if __name__ == "__main__":
    S = load_settings()
    print(f"Loaded config for device '{S.device.device_id}' → MQTT {S.mqtt.broker}:{S.mqtt.port} topic '{S.mqtt.data_topic}'")
