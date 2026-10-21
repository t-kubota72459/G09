"""
令和 7 年度 技能検定 3 級相当
手動モード確認用プログラム

【注意】
本来は SS0 が「手動」側であることを確認してから
手動モードの処理を行う必要がある。

この確認用プログラムでは、手動モードの動作確認に集中するため、
SS0 の入力判定は省略している。

【動作】
PB2 押下      : PL2 点灯、コンベア右行
PB3 押下      : PL3 点灯、コンベア左行
PB2 + PB3     : PB3 を優先し、コンベア左行
どちらもOFF   : コンベア停止、PL2 / PL3 消灯

RY1 ON : コンベア左行
RY2 ON : コンベア右行
"""

from machine import Pin
import time


# 入力
PB2 = Pin(17, Pin.IN)
PB3 = Pin(18, Pin.IN)


# 出力
RY1 = Pin(2, Pin.OUT)    # コンベア左行
RY2 = Pin(4, Pin.OUT)    # コンベア右行
PL2 = Pin(5, Pin.OUT)
PL3 = Pin(12, Pin.OUT)


# 出力初期化
for output in [RY1, RY2, PL2, PL3]:
    output.off()


print("*** MANUAL MODE RUN ***")


while True:

    # PB3 を優先
    if PB3.value() == 1:
        RY1.on()     # 左行
        RY2.off()

        PL2.off()
        PL3.on()

    elif PB2.value() == 1:
        RY1.off()
        RY2.on()     # 右行

        PL2.on()
        PL3.off()

    else:
        # ボタンを離したら停止
        RY1.off()
        RY2.off()

        PL2.off()
        PL3.off()

    time.sleep_ms(50)
