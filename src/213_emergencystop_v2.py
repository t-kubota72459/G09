"""
令和 7 年度 技能検定 3 級相当
自動モード確認用プログラム

【注意】
本来は SS0 が「自動」側であることを確認してから
自動モードの処理を行う必要がある。

この確認用プログラムでは、自動サイクルの動作確認に集中するため、
SS0 の入力判定は省略している。

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

RY1 : コンベア左行
RY2 : コンベア右行
"""
from machine import Pin
import time

# -------------------------
# 入力
# -------------------------
PB1 = Pin(19, Pin.IN)    # 自動サイクル開始
PB3 = Pin(18, Pin.IN)    # 終了要求
PB4 = Pin(23, Pin.IN)    # 非常停止解除
PB5 = Pin(27, Pin.IN)	   # 非常停止
LS1 = Pin(21, Pin.IN)    # コンベア右端
LS2 = Pin(22, Pin.IN)    # コンベア左端

# -------------------------
# 出力
# -------------------------
RY1 = Pin(2, Pin.OUT)    # コンベア左行
RY2 = Pin(4, Pin.OUT)    # コンベア右行
PL2 = Pin(5, Pin.OUT)    # 未使用   
PL3 = Pin(12, Pin.OUT)   # 未使用   
PL1 = Pin(13, Pin.OUT)   # 自動運転表示
PL4 = Pin(14, Pin.OUT)   # 非常停止表示

# -------------------------
# 出力初期化
# -------------------------
for output in [RY1, RY2, PL1, PL2, PL3, PL4]:
    output.off()

# -------------------------
# 状態・カウンタ
# -------------------------
state = "OFF"

waiting_left_start = None       # 左端計測開始時間
waiting_right_start = None      # 右端計測開始時間
pb3_start = None		       	    # PB3 を押した時間
pl1_start = None         		    # PL1 点滅開始時間

finish_flag = False  # 終了要求

print("*** AUTO MODE RUN /with emergency stop ***")

while True:
    if PB5.value() == 0:
        state = "EMERGENCY_STOP"
        
    # ==================================================
    # EMERGENCY_STOP：非常停止
    # ==================================================
    if state == "EMERGENCY_STOP":

        RY1.off()
        RY2.off()
        PL1.off()
        PL4.on()
        
        if PB4.value() == 1:	# 非常停止解除
            PL4.off()
            state = "OFF"
            
    # ==================================================
    # OFF：自動サイクル停止中
    # ==================================================
    elif state == "OFF":

        RY1.off()
        RY2.off()
        PL1.off()

        finish_flag = False
        pb3_start = None
        pl1_start = None
        waiting_left_start = None
        waiting_right_start = None
        
        # パレットが右端にあり、PB1 を押したら開始
        if LS1.value() == 1 and PB1.value() == 1:
            print("AUTO START")
            state = "MOVE_LEFT"


    # ==================================================
    # ① コンベア左行
    # ==================================================
    elif state == "MOVE_LEFT":

        RY2.off()
        RY1.on()

        # 左端に到着
        if LS2.value() == 1:
            RY1.off()
            state = "WAIT_LEFT"

    # ==================================================
    # ② 左端で約 1 秒停止
    # ==================================================
    elif state == "WAIT_LEFT":
        if waiting_left_start is None:
            waiting_left_start = time.ticks_ms()
        else:
            if time.ticks_diff(time.ticks_ms(), waiting_left_start) >= 1000:
                waiting_left_start = None
                state = "MOVE_RIGHT"


    # ==================================================
    # ③ コンベア右行
    # ==================================================
    elif state == "MOVE_RIGHT":

        RY1.off()
        RY2.on()

        # 右端に到着
        if LS1.value() == 1:
            RY2.off()
            state = "WAIT_RIGHT"


    # ==================================================
    # ④ 右端で約 3 秒停止
    # ==================================================
    elif state == "WAIT_RIGHT":
        if waiting_right_start is None:
            waiting_right_start = time.ticks_ms()
        else:
            if time.ticks_diff(time.ticks_ms(), waiting_right_start) >= 3000:	# 約 3 秒経過
                waiting_right_start = None
                if finish_flag:             # 終了要求があればサイクル終了
                    print("AUTO FINISH")
                    state = "OFF"
                else:                       # 終了要求がなければ次のサイクル
                    state = "MOVE_LEFT"

    # ==================================================
    # 自動サイクル中の共通処理
    # ==================================================

    if state != "OFF" and state != "EMERGENCY_STOP":

        # ----------------------------------------------
        # PB3 を約 2 秒押し続けたら終了要求
        # ----------------------------------------------
        if not finish_flag:
            if PB3.value() == 1:
                if pb3_start is None:
                    pb3_start = time.ticks_ms()
                else:
                    if time.ticks_diff(time.ticks_ms(), pb3_start) >= 2000:                   
                        finish_flag = True
                        print("FINISH REQUEST")
                        pb3_start = None
            else:
                pb3_start = None

        # ----------------------------------------------
        # PL1 表示
        # ----------------------------------------------

        if not finish_flag:
            # 通常運転中
            PL1.on()

        else:
            # 終了要求後は約 0.5 秒ごとに反転
            if pl1_start is None:
                pl1_start = time.ticks_ms()
            else:
                
                if time.ticks_diff(time.ticks_ms(), pl1_start) >= 500:
                    PL1.value(not PL1.value())
                    pl1_start = None
    
        time.sleep_ms(10)

