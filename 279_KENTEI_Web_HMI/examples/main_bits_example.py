"""学習用サンプル：DSWの4ビットを、そのままDPL1へ渡す。

DSWを3にすると dsw_bits_yomu() は [0,0,1,1] を返し、
DPL1に3が表示されます。BCDの演算課題はここから発展させます。

使う場合は、既存main.pyをバックアップしてから、この内容を
ESP32の /main.py として保存してください。
"""
import time
from hmi import WebHMI
from wifi_config import WIFI_SSID, WIFI_PASSWORD

hmi = WebHMI(ssid=WIFI_SSID, password=WIFI_PASSWORD)
hmi.start()

while True:
    hmi.web_shori()

    bits = hmi.dsw_bits_yomu()    # MSB先頭 [8,4,2,1]
    hmi.dpl1_hyouji(bits)        # DSW入力を一の位へそのまま渡す
    hmi.dpl2_hyouji([0,0,0,0])   # 十の位は0にする

    # TODO（発展）: ビット列を数値に直し、+1してBCDに戻す。
    #              DSWが9ならDPLを10にするには？
    time.sleep_ms(20)
