# Free Fridge Monitoring

The city of LA has a network of (free community fridges)[https://www.lacommunityfridges.com/] 
that serve as distributed food pantries for the city. The (K-Town fridge)[https://www.lacommunityfridges.com/fridge/koreatown-solar/r/recZlfyUDA3hGEN5D] is a solar powered version. We're working with
the solar fridge group to build a remote monitoring system for them.

A cloudy week or a door left ajar can spoil everything inside before anyone
notices. This system reports temperature, door state, and battery charge from each
fridge to a central server.

## How it works

A Raspberry Pi at each fridge reads its sensors and publishes a JSON reading once a
minute over MQTT. The Pi reaches the server over Tailscale, so no fridge needs a public
IP or a port forward.

```
Fridge Pi ──> MQTT over Tailscale──> Mosquitto ──> Telegraf ──> InfluxDB
```

Mosquitto is the broker. Telegraf subscribes to `fridges/sensor_data`, parses the JSON,
and writes points into the `freefridges` bucket in InfluxDB. Each fridge has its own
broker account and ACL entry, so a stolen Pi can only publish as itself.

There is a second topic, `fridges/alerts`, that fridges are permitted to write to.
Nothing consumes it yet.


## Server setup

See [ServerConfig/README.md](ServerConfig/README.md). That covers Tailscale, the three
services, and adding a broker account for a new fridge.

## Fridge setup

### 1. Operating system

Flash Raspberry Pi OS 32-bit to a Pi Zero W.

### 2. Enable 1-Wire and serial

Add both temperature bus overlays to `/boot/firmware/config.txt`:

```
dtoverlay=w1-gpio,gpiopin=5
dtoverlay=w1-gpio,gpiopin=6
```

Order matters. The client maps bus masters to GPIO pins by their sorted order on the
filesystem, so pin 5 has to be declared first.

Then run `sudo raspi-config`, go to Interface Options, and enable the serial port
hardware while leaving the serial login shell disabled. The charge controller needs the
UART, and a login shell on it will conflict.

Reboot.

### 3. Tailscale

```bash
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up
```

Ask a Tailscale admin to apply the `fridge` tag to the device.

### 4. Install the client

```bash
git clone https://github.com/LA-Solarpunk/free_fridges_monitoring.git ~/monitoringsystem
cd ~/monitoringsystem/Software
python -m venv venv
./venv/bin/pip install -r Client/requirements.txt
```

### 5. Configure

The client reads its settings from environment variables. Create `/home/pi/fridge.env`:

```
FRIDGE_DEVICE_ID=<fridge name>
MQTT_BROKER=<server tailscale hostname>
MQTT_PORT=1883
MQTT_TOPIC=fridges/sensor_data
MQTT_USERNAME=<fridge broker user>
MQTT_PASSWORD=<fridge broker password>
FRIDGE_LOGLEVEL=INFO
AIRTABLE_API_KEY=unused
FRIDGE_GDRIVE_CREDENTIALS=unused
```

`FRIDGE_DEVICE_ID` is also used as the MQTT client ID, so it has to be unique across
fridges. The broker credentials come from step 7 of the server setup.

The last two variables are required by the config loader even though nothing in the
current data path reads them. See Known gaps below.

Lock the file down, since it holds the broker password:

```bash
chmod 600 /home/pi/fridge.env
```

### 6. Install the service

```bash
sudo cp ~/monitoringsystem/Software/fridge-monitor.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now fridge-monitor
```

### 7. Verify

```bash
journalctl -u fridge-monitor -f
```

The client logs each reading before publishing it. If temperatures come back as errors,
check that both W1 bus masters appeared:

```bash
ls /sys/bus/w1/devices/
```

You should see two `w1_bus_master*` entries and a `28-*` entry per probe. If the charge
controller reports no response, the client scans the Modbus address range at startup and
logs what it finds, so the log will say whether it saw the device at all.

Confirm the reading reached the server by querying InfluxDB there.

## Known gaps

**The TOML config is not wired up.** `Client/client.example.toml` and the `SPF_CONFIG`
path helper in `config.py` describe a file-based config that `load_settings()` does not
use. It reads environment variables instead, and every one is a bare lookup with no
default, so a missing variable is a startup crash rather than a warning. Moving to the
TOML file is an open task.

**Airtable and Google Drive are legacy.** `airtable.py` and `google_drive.py` predate
the MQTT pipeline and are no longer imported by `monitor_client.py`. Their config
variables are still required at startup, which is why the env file above sets them to
dummy values.

**The JSON field names came from Airtable.** Keys look like
`Fridge Temperature (°C)`, and `Fridge` is a single-element list rather than a string.
Telegraf flattens these into InfluxDB field names as they are, spaces and degree signs
included, which makes queries awkward. Renaming them means changing `messages.py` and
migrating the existing data.

**Nothing alerts yet.** Sensor data lands in InfluxDB and stops there. Alerting logic,
the shock sensor, the H2 sensor for SLA battery installs, and the audible alarm are all
still unselected or unwritten.
