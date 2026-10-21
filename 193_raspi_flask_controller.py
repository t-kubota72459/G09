# マイコン実習 第19回
# Flask から Web AGV の AUTO 運転を開始する

from flask import Flask
import socket
import time

app = Flask(__name__)

PICO_IP = "192.168.4.1"
TURN_TIME = 0.8      # B-5 で調整した値に変更する


def send(path):
    request = (
        "GET {} HTTP/1.1\r\n"
        "Host: {}\r\n"
        "Connection: close\r\n"
        "\r\n"
    ).format(path, PICO_IP)

    s = socket.socket()
    s.connect((PICO_IP, 80))
    s.sendall(request.encode())
    s.recv(1024)
    s.close()


@app.route("/")
def index():
    return """
    <h1>Web AGV AUTO</h1>
    <a href="/auto"><button style="font-size:48px;">AUTO START</button></a>
    """


@app.route("/auto")
def auto():
    # 2秒前進 → STOP → 右へ約90度 → STOP を4回
    for _ in range(4):
        send("/forward")
        time.sleep(2)
        send("/stop")

        send("/right")
        time.sleep(TURN_TIME)
        send("/stop")

    return '<h1>AUTO COMPLETE</h1><a href="/">BACK</a>'


app.run(host="0.0.0.0", port=5000)
