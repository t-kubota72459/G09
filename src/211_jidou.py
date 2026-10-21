"""
令和 7 年度 技能検定 3 級相当
自動モード確認用プログラム

【注意】
本来は SS0 が「自動」側であることを確認してから
自動モードの処理を行う必要がある。

この確認用プログラムでは、自動サイクルの動作確認に集中するため、
SS0 の入力判定は省略している。

また、非常停止機能はまだ実装していない。

【自動サイクル】
1. パレットが右端にある状態で PB1 を押すと開始
2. コンベア左行
3. 左端で約 1 秒停止
4. コンベア右行
5. 右端で約 3 秒停止
6. 2 ～ 5 を繰り返す

PB3 を約 2 秒間押し続けると終了要求を受け付ける。
終了要求後も現在のサイクルを最後まで実行し、
右端で約 3 秒停止した後に終了する。

PL1
    点灯 : 自動サイクル運転中
    点滅 : 終了要求受付済み
    消灯 : 自動サイクル停止中

RY1 ON : コンベア左行
RY2 ON : コンベア右行
"""

from machine import Pin
import time


# 入力
PB1 = Pin(19, Pin.IN)    # 自動サイクル開始
PB3 = Pin(18, Pin.IN)    # 終了要求

LS1 = Pin(21, Pin.IN)    # コンベア右端
LS2 = Pin(22, Pin.IN)    # コンベア左端


# 出力
RY1 = Pin(2, Pin.OUT)    # コンベア左行
RY2 = Pin(4, Pin.OUT)    # コンベア右行
PL1 = Pin(13, Pin.OUT)   # 自動運転表示


# 出力初期化
for output in [RY1, RY2, PL1]:
    output.off()


# 状態
state = "OFF"

# 時間カウント
count_left = 0       # 左端停止時間
count_right = 0      # 右端停止時間
count_pb3 = 0        # PB3 を押している時間
count_pl1 = 0        # PL1 点滅用

# 終了要求
finish_flag = False


print("*** AUTO MODE RUN ***")


while True:

    # --------------------------------
    # OFF：自動サイクル停止中
    # --------------------------------
    if state == "OFF":

        RY1.off()
        RY2.off()
        PL1.off()

        finish_flag = False
        count_pb3 = 0
        count_pl1 = 0

        # 右端にパレットがあり、PB1 を押したら開始
        if LS1.value() == 1 and PB1.value() == 1:
            print("AUTO START")
            state = "MOVE_LEFT"


    # --------------------------------
    # ① コンベア左行
    # --------------------------------
    elif state == "MOVE_LEFT":

        RY2.off()
        RY1.on()

        # 左端に到着
        if LS2.value() == 1:
            RY1.off()
            count_left = 0
            state = "WAIT_LEFT"


    # --------------------------------
    # ② 左端で約 1 秒停止
    # --------------------------------
    elif state == "WAIT_LEFT":

        count_left += 1

        # 100 ms × 10 = 約 1 秒
        if count_left >= 10:
            count_left = 0
            state = "MOVE_RIGHT"


    # --------------------------------
    # ③ コンベア右行
    # --------------------------------
    elif state == "MOVE_RIGHT":

        RY1.off()
        RY2.on()

        # 右端に到着
        if LS1.value() == 1:
            RY2.off()
            count_right = 0
            state = "WAIT_RIGHT"


    # --------------------------------
    # ④ 右端で約 3 秒停止
    # --------------------------------
    elif state == "WAIT_RIGHT":

        count_right += 1

        # 100 ms × 30 = 約 3 秒
        if count_right >= 30:
            count_right = 0

            if finish_flag:
                print("AUTO FINISH")
                state = "OFF"
            else:
                state = "MOVE_LEFT"


    # --------------------------------
    # 自動サイクル中の共通処理
    # --------------------------------
    if state != "OFF":

        # PB3 を約 2 秒押したら終了要求
        if not finish_flag:

            if PB3.value() == 1:
                count_pb3 += 1

                # 100 ms × 20 = 約 2 秒
                if count_pb3 >= 20:
                    finish_flag = True
                    count_pl1 = 0
                    print("FINISH REQUEST")

            else:
                count_pb3 = 0


        # 終了要求なし：PL1 点灯
        if not finish_flag:
            PL1.on()

        # 終了要求あり：PL1 点滅
        else:
            count_pl1 += 1

            # 100 ms × 5 = 約 0.5 秒
            if count_pl1 >= 5:
                PL1.value(not PL1.value())
                count_pl1 = 0


    # 1 ループ約 100 ms
    time.sleep_ms(100)