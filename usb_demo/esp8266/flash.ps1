# SignGuard AI - NodeMCU ESP-12E (ESP8266) one-command flasher.
#
# Flashes MicroPython + uploads all SignGuard files to the board.
# Run from anywhere:  powershell -ExecutionPolicy Bypass -File flash.ps1
# Optional:           ... -Port COM5   (skip auto-detect)
#
# BEFORE running: copy config.example.py to config.py in THIS folder and edit
# WIFI_SSID / WIFI_PASS / BROKER_IP.

param([string]$Port = "")

$ErrorActionPreference = "Stop"
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $here

$fw = Join-Path $here "firmware\ESP8266_GENERIC-v1.28.0.bin"
$cfg = Join-Path $here "config.py"

# --- checks ---
if (-not (Test-Path $fw))  { Write-Host "Firmware missing: $fw" -ForegroundColor Red; exit 1 }
if (-not (Test-Path $cfg)) {
    Write-Host "config.py not found. Copy config.example.py -> config.py and edit your Wi-Fi + BROKER_IP first." -ForegroundColor Red
    exit 1
}

# --- find the port ---
if (-not $Port) {
    $p = Get-CimInstance Win32_PnPEntity | Where-Object { $_.Name -match "CH340|CP210|USB-SERIAL|Silicon Labs|FTDI" } | Select-Object -First 1
    if ($p -and $p.Name -match "\((COM\d+)\)") { $Port = $Matches[1] }
}
if (-not $Port) {
    Write-Host "No CH340/CP210x USB-serial port found. Is the NodeMCU plugged in and the driver installed?" -ForegroundColor Red
    Write-Host "Install the CH340 driver, replug, then re-run (or pass -Port COMx)." -ForegroundColor Yellow
    exit 1
}
Write-Host "Using port $Port" -ForegroundColor Cyan

# --- 1. erase + flash MicroPython ---
Write-Host "`n[1/4] Erasing flash..." -ForegroundColor Green
python -m esptool --port $Port --chip esp8266 erase_flash
Write-Host "`n[2/4] Writing MicroPython firmware..." -ForegroundColor Green
python -m esptool --port $Port --chip esp8266 write_flash --flash_size=detect 0 $fw
Write-Host "Waiting for the board to reboot..." -ForegroundColor Green
Start-Sleep -Seconds 5

# --- 3. upload the library + app files ---
Write-Host "`n[3/4] Uploading umqtt library + drivers + app..." -ForegroundColor Green
python -m mpremote connect $Port fs mkdir :umqtt
python -m mpremote connect $Port fs cp "lib_umqtt\simple.py" :umqtt/simple.py
python -m mpremote connect $Port fs cp "lcd_api.py"  :lcd_api.py
python -m mpremote connect $Port fs cp "i2c_lcd.py"  :i2c_lcd.py
python -m mpremote connect $Port fs cp "config.py"   :config.py
python -m mpremote connect $Port fs cp "main.py"     :main.py

# --- 4. done ---
Write-Host "`n[4/4] Done. Power-cycle the NodeMCU." -ForegroundColor Green
Write-Host "On boot the LCD should show SYSTEM SECURE and the green LED should light." -ForegroundColor Cyan
Write-Host "Watch its logs with:  python -m mpremote connect $Port" -ForegroundColor DarkGray
