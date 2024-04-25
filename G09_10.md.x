# PWM パルス幅変調

Arduino (マイコン制御) で学習したが、Raspberry Pi でも PWM 制御は利用できる。
ただし、書き方が少し異なる。
Python 特有の書き方になるので、C言語 (Arduino) では「あー書いて、Python (Raspberry Pi) ではこー書くのかぁ」と思ってほしい。

- **PWM** を忘れた人へ：  
デジタル (0 or 1) しか出せないコンピュータで **擬似的に** アナログ値を出す方法。高速に 0/1 を切り替える。切り替えるときに 0 (OFF) の時間と 1 (ON) の時間の比率を変えてアナログ値を作る。

**パルス (ON) の期間と周期の比率 (パーセントで示したもの) を「デューティー比」という** 例えば、周期すべてが H ならデューティ比 100 である。周期すべてが L ならデューティ比が 0 である。H の期間と L の期間が半々ならばデューティ比は 50 である。

<div style="text-align: center;">
    <img src="./images/image40.png" width="70%"></br>
</div>

# 回路図

<div style="text-align: center;">
    <img src="./images/image27.png" width="70%"></br>
</div>

# プログラム

以下は Arduino でもやった「だんだん明るく、だんだん暗く」を繰り返す LED 調光プログラムである。書き方に違いはあるが、行なっていること、プログラムの処理のながれなどは、Arduino とほとんど (まったく) 同じという点に注目してほしい：

```python
import RPi.GPIO as GPIO     # RPi.GPIO モジュールを GPIO という名前で使う
from time import sleep      # time モジュールから sleep という関数を使う

GPIO.setmode(GPIO.BCM)      # BCM モードでピン番号を指定する
GPIO.setup(25, GPIO.OUT)    # 25 ピンを出力設定にする

p = GPIO.PWM(25, 50)        # 25 ピンを PWM 出力にする (周波数 50Hz) 

p.start(0)                  # 0% で出力開始

duty = 0.0                  # デューティ比は 0.0 ~ 100.0 (1000 分割)
change = -10                # 変化量 (初期値をマイナスにしておくと処理が楽)
try:
    while True:
        p.ChangeDutyCycle(duty)      # デューティー比を設定する
        sleep(0.1)                   # 100 ms やすむ
        
        # デューティ (明るさ) を変更
        if duty <= 0 or duty >= 100:
            change = -change
        duty = duty + change

except KeyboardInterrupt: # ctrl-c で止めた
    pass                  # エラー処理を特にしない

p.stop()                  # PWM を停止する
GPIO.cleanup()            # GPIO の終了をする
```

# RGB フルカラー LED を点灯させる

```python
import RPi.GPIO as GPIO     # RPi.GPIO モジュールを GPIO という名前で使う
from time import sleep      # time モジュールから sleep という関数を使う

GPIO.setmode(GPIO.BCM)      # BCM モードでピン番号を指定する

GPIO.setup(23, GPIO.OUT)    # 23 ピンを出力設定にする
GPIO.setup(24, GPIO.OUT)    # 24 ピンを出力設定にする
GPIO.setup(25, GPIO.OUT)    # 25 ピンを出力設定にする

p1 = GPIO.PWM(23, 50)       # 23 ピンに周波数 50Hz の PWM を設定
p2 = GPIO.PWM(24, 50)       # 24 ピンに周波数 50Hz の PWM を設定
p3 = GPIO.PWM(25, 50)       # 25 ピンに周波数 50Hz の PWM を設定

p1.start(0)
p2.start(0)
p3.start(0)

duty = 0.0                  # デューティ比 0.0 ~ 100.0
change = -10                # 変化量 (初期値をマイナスにしておくと処理が楽)
try:
    while True:
        p1.ChangeDutyCycle(duty)      # デューティー比を設定する  
        p2.ChangeDutyCycle(duty)
        p3.ChangeDutyCycle(duty)
        sleep(0.1)                   # 100 ms やすむ
        # デューティ (明るさ) を変更
        if duty <= 0 or duty >= 100:
            change = -change
        duty += change
except KeyboardInterrupt:
    pass                            # エラー処理を特にしない
p1.stop()                           # PWM 停止
p2.stop()                           # PWM 停止
p3.stop()                           # PWM 停止
GPIO.cleanup()                      # GPIO (汎用ピン) の後処理をする
```