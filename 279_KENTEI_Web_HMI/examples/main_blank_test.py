"""KENTEI HMI v0.7: DPL1 8 -> (BCD12: blank) -> 4 test.

Copy this example to ESP32 /main.py *only for the display test*.
Keep a backup of your working main.py. No conveyor GPIO is used.
"""
import time
from hmi import WebHMI
from wifi_config import WIFI_SSID, WIFI_PASSWORD

hmi = WebHMI(ssid=WIFI_SSID, password=WIFI_PASSWORD)
hmi.start()

# MSB first: [8,4,2,1]. DPL1 is the units digit.
patterns = (
    [1, 0, 0, 0],  # 8: lit
    [1, 1, 0, 0],  # 12: blank (raw 1100 still present)
    [0, 1, 0, 0],  # 4: lit again
)
phase = 0
hmi.dpl2_hyouji([0, 0, 0, 0])
hmi.dpl1_hyouji(patterns[phase])
changed_at = time.ticks_ms()

while True:
    hmi.web_shori()  # Keep browser responsive even during test
    now = time.ticks_ms()
    if time.ticks_diff(now, changed_at) >= 3000:
        phase = (phase + 1) % len(patterns)
        hmi.dpl1_hyouji(patterns[phase])
        changed_at = now
    time.sleep_ms(20)
