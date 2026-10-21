import time
from machine import Pin, ADC

PIN_SENSOR_L = 2  # 左センサー
PIN_SENSOR_R = 3  # 右センサー

# ADCの初期化
adc_l = ADC(Pin(PIN_SENSOR_L))
adc_r = ADC(Pin(PIN_SENSOR_R))

# 重要：入力レンジを広げる (約0〜2.6Vまで測れるようになる)
# ※3V入力だと最大値で張り付きますが、ライン判定にはOKです
adc_l.atten(ADC.ATTN_11DB)
adc_r.atten(ADC.ATTN_11DB)

print("センサー値チェック開始 (Ctrl+C で停止)")
print("Left, Right")

try:
    s_l = s_r = 0
    for i in range(1000):
        # 0 〜 65535 の値を読み取る
        val_l = adc_l.read_u16()
        val_r = adc_r.read_u16()
        
        # ログを見やすく整形して表示
        # 黒(ライン)に乗ると数値が上がり(>50000)、白(床)だと下がる(<10000)はず
        print(f"L: {val_l:5d}  |  R: {val_r:5d}")
        
        time.sleep(0.1)
        s_l += val_l
        s_r += val_r

    print(f"avg(L) = {s_l/10000}")
    print(f"avg(R) = {s_r/10000}")

except KeyboardInterrupt:
    print("停止")
