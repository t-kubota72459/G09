#
# マイコン実習 第17回
# 動作確認済み標準版 web_agv.py
#
# 第17回の最初は、このプログラムから開始する。
# RED / BLUE の動作を確認したあと、BLACKを学生自身で追加する。
#

import network
import time
import socket


# =========================================================
# Wi-Fi の設定
# =========================================================

SSID = "PICO_AGV_00"       # 00 の部分を自分の出席番号にする
PASSWORD = "picoagv00"     # 00 の部分を自分の出席番号にする（8文字以上）

ap = network.WLAN(network.AP_IF)  # PicoをAPとして使う
ap.active(True)                   # AP機能を有効にする

ap.config(
    essid=SSID,
    password=PASSWORD
)

ap.ifconfig((
    "192.168.4.1",          # Pico自身のIPアドレス
    "255.255.255.0",        # サブネットマスク
    "192.168.4.1",          # ゲートウェイ
    "192.168.4.1"           # DNS
))

while not ap.active():
    time.sleep(0.1)


# =========================================================
# Web サーバーの設定
# =========================================================

addr = socket.getaddrinfo("0.0.0.0", 80)[0][-1]

server = socket.socket()
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind(addr)
server.listen(1)


# =========================================================
# Webページに表示する状態
# =========================================================

color = "black"
size = "96px"


# =========================================================
# request を待つ
# =========================================================

while True:
    client = None

    try:
        client, client_addr = server.accept()

        request = client.recv(1024).decode()

        # HTTP request の先頭行だけを表示する
        # 例：GET /red HTTP/1.1
        first_line = request.split("\r\n")[0]
        print(first_line)

        # -------------------------------------------------
        # request を判断して、状態を変更する
        # -------------------------------------------------

        if "GET /red " in first_line:          # REDボタン
            color = "red"

        elif "GET /blue " in first_line:       # BLUEボタン
            color = "blue"

        elif "GET /favicon.ico " in first_line:
            # ブラウザが自動で要求する場合がある
            # 色などの状態は変更しない
            pass

        # -------------------------------------------------
        # 現在の状態を使ってHTMLを作る
        # -------------------------------------------------

        html = """
        <html>
          <body>
            <h1 style="color: {}; font-size: {};">Pico Web AGV</h1>

            <a href="/red"><button>RED</button></a>
            <a href="/blue"><button>BLUE</button></a>
          </body>
        </html>
        """.format(color, size)

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
        # スマホやブラウザが途中で接続を切った場合など、
        # socketのエラーでWebサーバー全体が止まりにくくする
        print("socket error:", e)

    finally:
        # 通信が終わったらクライアントとの接続を閉じる
        if client is not None:
            try:
                client.close()
            except OSError:
                pass
