# SignGuard AI - Board Setup (final kit)

Components: **Raspberry Pi, ESP32, 16x2 I2C LCD, buzzer.**

Role split:
- **Raspberry Pi** = detection gateway. Real USB detection via pyudev; also
  runs the software-simulated attacks. Publishes to signguard/events.
- **ESP32** = signage output node. Drives the LCD + buzzer from Layer 2's
  commands on signguard/commands. No sensors.
- **Laptop (or Pi)** = runs the MQTT broker + Layer 2 + the Layer 1 dashboard.

Flow: USB inserted on Pi (or a simulated content attack) -> Layer 2 decides ->
command to ESP32 -> LCD shows BLOCKED + buzzer sounds.

```
edge_node/hardware/
├── requirements.txt        (Pi)
├── pi_config.py            (Pi)
├── pi_usb_monitor.py       (Pi)
└── esp32/
    ├── config.example.py   -> copy to config.py
    ├── lcd_api.py
    ├── i2c_lcd.py
    └── main.py
```

---

## Step 0 - one network + broker

Put the broker host (laptop or Pi), the Pi, and the ESP32 on the same Wi-Fi.
Find the broker host IP: `hostname -I` (Linux) / `ipconfig` (Windows).

Start the broker (on the broker host, needs Docker):
```
docker compose up -d
```
Watch every message in another terminal:
```
mosquitto_sub -h <broker-ip> -t 'signguard/#' -v
```

---

## Step 1 - Raspberry Pi (real USB detection)

```
sudo apt update && sudo apt install -y mosquitto-clients
pip3 install -r edge_node/hardware/requirements.txt
```
Edit `pi_config.py`: set `BROKER_HOST` to the broker IP (or "localhost" if the
broker runs on the Pi). Optionally add trusted USB serials.

Run it (sudo may be needed for udev):
```
sudo python3 edge_node/hardware/pi_usb_monitor.py
```
Plug in a USB stick -> you should see an `unauthorized_usb` event on the watcher.

---

## Step 2 - ESP32 (LCD + buzzer)

### 2a. Wire it
```
LCD  VCC -> 5V (VIN)    GND -> GND    SDA -> GPIO21    SCL -> GPIO22
Buzzer +  -> GPIO26          -  -> GND
```
Common grounds. If running the LCD backpack at 5V worries you about the 3.3V
I2C pins, add a logic level shifter - but most kits work wired directly.

### 2b. Flash MicroPython (one time, from your laptop)
```
pip install esptool mpremote
esptool.py --chip esp32 erase_flash
esptool.py --chip esp32 write_flash -z 0x1000 esp32-<version>.bin
```
(Get the .bin from micropython.org/download.)

### 2c. Find the LCD's I2C address
Open a REPL (`mpremote`) and run:
```python
from machine import Pin, I2C
i2c = I2C(0, scl=Pin(22), sda=Pin(21))
print([hex(a) for a in i2c.scan()])
```
If you see `0x3f` instead of `0x27`, set `LCD_ADDR = 0x3F` in config.py.

### 2d. Upload the files
```
mpremote mip install umqtt.simple
cp edge_node/hardware/esp32/config.example.py config.py   # edit Wi-Fi + BROKER_IP
mpremote fs cp config.py :config.py
mpremote fs cp edge_node/hardware/esp32/lcd_api.py :lcd_api.py
mpremote fs cp edge_node/hardware/esp32/i2c_lcd.py :i2c_lcd.py
mpremote fs cp edge_node/hardware/esp32/main.py :main.py
```
(Thonny works too: set interpreter to MicroPython (ESP32) and save each file
to the device.)

### 2e. Run
```
mpremote run edge_node/hardware/esp32/main.py     # watch the console
```
On boot the LCD should show "SignGuard: OK / Content verified" once connected.
It auto-runs on power-up because the file is named main.py.

---

## Step 3 - Test the loop by hand (no Layer 2 needed yet)

Publish a fake command and watch the ESP32 react:
```
mosquitto_pub -h <broker-ip> -t signguard/commands \
  -m '{"device_id":"SG-ESP-001","command":"safe_fallback","timestamp":"now"}'
```
The LCD should switch to "** BLOCKED **" and the buzzer should beep. Try
`render` and `isolate` too. When it reacts correctly, the output node is done.

---

## Step 4 - Full demo

1. Broker + Layer 2 running on the laptop.
2. Pi publishing real `unauthorized_usb` events (Step 1).
3. ESP32 showing status on the LCD (Step 2).
4. Insert an unauthorized USB (or trigger a simulated content mismatch) ->
   Layer 2 blocks -> ESP32 shows BLOCKED + buzzer. That is the money moment.

Keep the software simulator ready: if a board misbehaves on stage, publish the
same MQTT shapes from software and the demo continues unchanged.
