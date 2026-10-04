#
# マイコン実習 第18回
# 復旧用基準版 Web AGV
#
# 第17回終了時の最低限の状態：
#   FORWARD / BACK / STOP をWebから操作できる
#
# 第18回で追加する SPEED UP / SPEED DOWN は、まだ入れていない。
#

from machine import Pin, PWM
import network
import time
import socket


# =========================================================
# Wi-Fi の設定
# =========================================================

SSID = "PICO_AGV_00"       # 00 の部分を自分の出席番号にする
PASSWORD = "picoagv00"     # 00 の部分を自分の出席番号にする（8文字以上）


# =========================================================
# モータの設定
# =========================================================
#
# 標準配線
#   左モータ AIN1 : GP19
#   左モータ AIN2 : GP18
#   右モータ BIN1 : GP17
#   右モータ BIN2 : GP16
#
# 授業前に、実機で前進・後退の向きを確認しておくこと。
# モータの配線方向が異なる場合は、各関数内で
# duty_u16() を入れる側を入れ替える。
#

MOTOR_PWM_FREQ = 20000
DRIVE_SPEED = 30000

left_in1 = PWM(Pin(19))
left_in2 = PWM(Pin(18))
right_in1 = PWM(Pin(17))
right_in2 = PWM(Pin(16))

left_in1.freq(MOTOR_PWM_FREQ)
left_in2.freq(MOTOR_PWM_FREQ)
right_in1.freq(MOTOR_PWM_FREQ)
right_in2.freq(MOTOR_PWM_FREQ)


# =========================================================
# モータ制御関数
# =========================================================

def stop():
    left_in1.duty_u16(0)
    left_in2.duty_u16(0)
    right_in1.duty_u16(0)
    right_in2.duty_u16(0)

def go_forward(speed):
    # 左モータ：AIN1側へPWM
    left_in1.duty_u16(speed)
    left_in2.duty_u16(0)

    # 右モータ：BIN1側へPWM
    right_in1.duty_u16(speed)
    right_in2.duty_u16(0)

def go_back(speed):
    # 左モータ：AIN2側へPWM
    left_in1.duty_u16(0)
    left_in2.duty_u16(speed)

    # 右モータ：BIN2側へPWM
    right_in1.duty_u16(0)
    right_in2.duty_u16(speed)

# 起動時は必ず停止状態から始める
stop()

# =========================================================
# PicoをWi-Fiアクセスポイントにする
# =========================================================

ap = network.WLAN(network.AP_IF)
ap.active(True)

ap.config(
    essid=SSID,
    password=PASSWORD
)

ap.ifconfig((
    "192.168.4.1",
    "255.255.255.0",
    "192.168.4.1",
    "192.168.4.1"
))

while not ap.active():
    time.sleep(0.1)

print("SSID:", SSID)
print("Web AGV: http://192.168.4.1/")


# =========================================================
# Webサーバーの設定
# =========================================================

addr = socket.getaddrinfo("0.0.0.0", 80)[0][-1]

server = socket.socket()
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind(addr)
server.listen(1)


# =========================================================
# request を待つ
# =========================================================
state = "STOP"
while True:
    client = None

    try:
        client, client_addr = server.accept()

        request = client.recv(1024).decode()
        first_line = request.split("\r\n")[0]

        print(first_line)

        # -------------------------------------------------
        # Webからの入力を判断して、状態を確定する
        # -------------------------------------------------
        if "GET /forward " in first_line:
            state = "FORWARD"

        elif "GET /back " in first_line:
            state = "BACK"

        elif "GET /stop " in first_line:
            state = "STOP"

        elif "GET /SPEED_UP " in first_line:
            DRIVE_SPEED += 1000
            # 65535 を越えない
            if DRIVE_SPEED > 65535:
                DRIVE_SPEED = 65535

        elif "GET /SPEED_DOWN " in first_line:
            DRIVE_SPEED -= 1000
            # 0 を越えない
            if DRIVE_SPEED < 0:
                DRIVE_SPEED = 0
        
        elif "GET /favicon.ico " in first_line:
            # ブラウザが自動で要求する場合がある
            # モータの状態は変更しない
            pass

        # 状態を動作に反映する
        if state == "FORWARD":
            go_forward(DRIVE_SPEED)
        elif state == "BACK":
            go_back(DRIVE_SPEED)

        # -------------------------------------------------
        # Webページを作る
        # -------------------------------------------------

        html = """
        <html>
          <body>
            <h1 style="font-size: 64px;">Pico Web AGV</h1>
            <div style="text-align: center;">
              <p>
                <a href="/forward">
                  <button style="font-size: 48px;">前進⏫️</button>
                </a>
              </p>
              <p>
                <a href="/stop">
                  <button style="font-size: 48px;">停止⏹️</button>
                </a>
              </p>
              <p>
                <a href="/back">
                  <button style="font-size: 48px;">後退⏬️</button>
                </a>
              </p>
            </div>

            <hr/>

            <div style="text-align: center;">
              <p>
                <a href="/speed_up">
                  <button style="font-size: 48px;">加速➕️</button>
                </a>
              </p>
              <p>
                <a href="/speed_up">
                  <button style="font-size: 48px;">減速➖️</button>
                </a>
              </p>
            </div>
          </body>
        </html>
        """

        body = html.encode()

        # -------------------------------------------------
        # HTTP response
        # -------------------------------------------------

        header = (
            "HTTP/1.1 200 OK\r\n"
            "Content-Type: text/html; charset=utf-8\r\n"
            "Cache-Control: no-store\r\n"
            "Content-Length: {}\r\n"
            "Connection: close\r\n"
            "\r\n"
        ).format(len(body)).encode()

        client.sendall(header + body)

    except OSError as e:
        print("socket error:", e)

    finally:
        if client is not None:
            try:
                client.close()
            except OSError:
                pass
