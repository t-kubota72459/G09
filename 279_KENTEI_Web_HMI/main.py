"""KENTEI Web HMI / STA版 — DSW × 3 を DPL に表示する試験プログラム。

既存の物理I/Oには触れません。Wi-Fiの接続情報はwifi_config.pyへ。
"""
import time
from hmi import WebHMI
from wifi_config import WIFI_SSID, WIFI_PASSWORD

hmi = WebHMI(ssid=WIFI_SSID, password=WIFI_PASSWORD)
hmi.start()   # 教室Wi-FiへSTA接続 → DHCP取得 → URLをShellへ表示

while True:
    hmi.web_shori()            # HTTP要求を最大1件処理
    suuji = hmi.read_dsw()     # Web DSW: 0～9
    hmi.dpl_hyouji(suuji * 3)  # Web DPL: 00～27を表示するデモ
    time.sleep_ms(20)
