# Server setup

Config for the server side of the fridge monitoring system. Fridges publish sensor
readings over MQTT, Telegraf reads them off the broker and writes them into InfluxDB.

These instructions assume a fresh Arch Linux machine with sudo access. Replace
`<server-hostname>` throughout with the hostname of your machine.

## 1. Install packages

```bash
sudo pacman -S mosquitto influxdb influx-cli git base-devel
```

Telegraf is in the AUR:

```bash
git clone https://aur.archlinux.org/yay.git && cd yay && makepkg -si
yay -S telegraf
```

Clone this repo somewhere on the server. The paths below assume `~/monitoringsystem`.

## 2. Tailscale

This system assumes everything is connected over tailscale so set this up before the broker.

```bash
sudo pacman -S tailscale
sudo systemctl enable --now tailscaled
sudo tailscale up
```

In the Tailscale admin console, tag the server `fridge` and add an ACL rule granting
fridge users access to that tag. Remove the default `any:any` rule so accounts can
only reach tagged devices. Also consider disabling key expiry as it can be a pain if things
expire while still in use.

Note the server's Tailscale hostname. Fridges use it as their broker address.

## 3. Mosquitto

Copy the config:

```bash
sudo cp mosquitto/mosquitto.conf /etc/mosquitto/
sudo mkdir -p /etc/mosquitto/conf.d
sudo cp mosquitto/conf.d/la_fridges.conf /etc/mosquitto/conf.d/
sudo cp mosquitto/fridge_aclfile /etc/mosquitto/
```

Create the Telegraf broker user. Pick a password and keep it for step 5.

```bash
sudo mosquitto_passwd -c /etc/mosquitto/passwd telegraf
```

Fix ownership. Mosquitto refuses to load an ACL file that is world readable:

```bash
sudo chown mosquitto:mosquitto /etc/mosquitto/passwd /etc/mosquitto/fridge_aclfile
sudo chmod 640 /etc/mosquitto/passwd
sudo chmod 600 /etc/mosquitto/fridge_aclfile
```

Install the systemd drop-in:

```bash
sudo mkdir -p /etc/systemd/system/mosquitto.service.d
sudo cp systemd/mosquitto.service.d/override.conf /etc/systemd/system/mosquitto.service.d/
sudo systemctl daemon-reload
sudo systemctl enable --now mosquitto
```

The drop-in orders Mosquitto after `tailscaled` and sets `StateDirectory=mosquitto`.
Arch does not ship `/var/lib/mosquitto`, and without it the broker fails to write its
persistence database.

## 4. InfluxDB

```bash
sudo mkdir -p /etc/influxdb
sudo cp influxdb/config.toml /etc/influxdb/
sudo sed -i 's/archlinux/<server-hostname>/' /etc/influxdb/config.toml
sudo systemctl enable --now influxdb
```

Run the initial setup. Use org `lasolarpunk` and bucket `freefridges`:

```bash
influx setup
```

Create a token scoped to the bucket and save the output for step 5:

```bash
influx auth create --org lasolarpunk --write-bucket $(influx bucket list --name freefridges --hide-headers | awk '{print $1}')
```

## 5. Telegraf

```bash
sudo cp telegraf/telegraf.conf /etc/telegraf/
sudo mkdir -p /etc/telegraf/telegraf.d
sudo cp telegraf/telegraf.d/telegraf.conf /etc/telegraf/telegraf.d/
sudo cp telegraf/telegraf.env.example /etc/telegraf/telegraf.env
```

Edit `/etc/telegraf/telegraf.env` and fill in the Influx token from step 4 and the
Telegraf broker password from step 3.

```bash
sudo chown root:root /etc/telegraf/telegraf.env
sudo chmod 600 /etc/telegraf/telegraf.env
```

The file can be root-only because systemd reads it as PID 1 before dropping
privileges. The Telegraf service user never needs to open it.

Install the drop-in and start:

```bash
sudo mkdir -p /etc/systemd/system/telegraf.service.d
sudo cp systemd/telegraf.service.d/override.conf /etc/systemd/system/telegraf.service.d/
sudo systemctl daemon-reload
sudo systemctl enable --now telegraf
```

## 6. Verify

Check that all three services are running:

```bash
systemctl status mosquitto influxdb telegraf
```

Publish a test reading and confirm it lands in InfluxDB:

```bash
mosquitto_pub -h localhost -t fridges/sensor_data -u telegraf -P '<password>' \
  -m '{"fridge_name":"test","fridge_temp":4.0}'

influx query 'from(bucket:"freefridges") |> range(start:-5m)'
```

If the point does not appear, `journalctl -u telegraf -n 50` usually shows either an
auth failure against the broker or a rejected write to Influx.

## 7. Adding a fridge

Each fridge gets its own broker user so a compromised Pi can't read or write another
fridge's data.

Create the user:

```bash
sudo mosquitto_passwd /etc/mosquitto/passwd <fridge-name>
```

Add a matching block to `/etc/mosquitto/fridge_aclfile`:

```
user <fridge-name>
topic readwrite fridges/sensor_data
topic write fridges/alerts
```

Reload the broker:

```bash
sudo systemctl reload mosquitto
```

Commit the ACL change back to this repo. Do not commit `/etc/mosquitto/passwd`.

On the fridge's Raspberry Pi, set `broker` to the server's Tailscale hostname and
`username` and `password` to the credentials you just created. See the client README
for the rest of the Pi setup.

## Secrets

Three files hold credentials, do not commit them to git:

- `/etc/mosquitto/passwd`
- `/etc/telegraf/telegraf.env`
- the fridge's `client.toml` on the Pi

`telegraf.env.example` is tracked as a template. Copy it rather than editing the
tracked file, so a `git pull` on a live server doesn't collide with real values.
