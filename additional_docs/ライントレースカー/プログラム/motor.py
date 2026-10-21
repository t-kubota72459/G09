from machine import Pin, PWM
import math
import time

# ==========================================
# 1. ピン定義
# ==========================================
# 左モーターのピン (IN1, IN2)
PIN_L1 = PWM(Pin(7))		# AIN1
PIN_L2 = PWM(Pin(6))		# AIN2

# 右モーターのピン (IN1, IN2)
PIN_R1 = PWM(Pin(5))		# BIN1
PIN_R2 = PWM(Pin(4))		# BIN2

# PWM周波数の設定
FREQ = 5000

PIN_L1.freq(FREQ)
PIN_L2.freq(FREQ)
PIN_R1.freq(FREQ)
PIN_R2.freq(FREQ)

# ==========================================
# 2. 裏方の処理
# ==========================================

def _drive_drv8835(pin_a, pin_b, speed):
    """
    DRV8835 (IN/INモード) 用の共通関数
    speed: -100 (後退最大) 〜 0 (停止) 〜 100 (前進最大)
    """
    # スピード制限 (-100 ~ 100 に収める)
    if speed > 100: speed = 100
    if speed < -100: speed = -100
    
    # パーセントを 16bit値 (0~65535) に変換
    duty = int(abs(speed) * 65535 / 100)
    # print(duty)
    
    if speed > 0:
        # 正転: AにPWM, Bを0(GND)
        pin_a.duty_u16(duty)
        pin_b.duty_u16(0)
    elif speed < 0:
        # 逆転: Aを0(GND), BにPWM
        pin_a.duty_u16(0)
        pin_b.duty_u16(duty)
    else:
        # 停止: 両方0 (空転/コースト)
        # ※ ブレーキにしたい場合は両方65535ですが、ライントレースなら空転で十分です
        pin_a.duty_u16(0)
        pin_b.duty_u16(0)

# ==========================================
# 3. ラッパー関数
# -100% ~ +100%
# ==========================================
def run_left(speed):
    # 左モーターを指定して動かす
    # もし回転方向が逆なら、ここを (PIN_L2, PIN_L1, speed) に入れ替えるだけで直る！
    _drive_drv8835(PIN_L1, PIN_L2, speed)

def run_right(speed):
    # 右モーターを指定して動かす
    _drive_drv8835(PIN_R1, PIN_R2, speed)

def stop():
    # 全停止
    run_left(0)
    run_right(0)

