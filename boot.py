from machine import Pin
import network
import time

# Hold both driver inputs low before starting the LED or buzzer.
# motor_in1 = Pin(1, Pin.OUT, value=0)
# motor_in2 = Pin(42, Pin.OUT, value=0)

from src.buzzer import buzz

led = Pin(38, Pin.OUT, value=0)
buzzer = Pin(37, Pin.OUT, value=0)

print("LED on; buzzer on at 2 kHz")
led.on()
buzz(buzzer)
led.off()
print("Boot complete; LED and buzzer off")

# Bring up the recovery channel before main.py starts the robot application.
# webrepl_setup creates webrepl_cfg.py on the board with the password.
from wifi_config import WIFI_SSID, WIFI_PASSWORD

wlan = network.WLAN(network.WLAN.IF_STA)
wlan.active(True)
if not wlan.isconnected():
    wlan.connect(WIFI_SSID, WIFI_PASSWORD)
    started = time.ticks_ms()
    while not wlan.isconnected() and time.ticks_diff(time.ticks_ms(), started) < 15000:
        time.sleep_ms(100)
if wlan.isconnected():
    print("Robot IP:", wlan.ifconfig()[0])
else:
    print("Wi-Fi unavailable at boot; main.py will retry")

try:
    import webrepl
    webrepl.start()
except (ImportError, OSError) as exc:
    print("WebREPL unavailable:", exc)
