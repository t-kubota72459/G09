# マイコン実習 第19回
# Raspberry Pi 4 から Pico Web AGV へ HTTP request を送る
#
# ねらい：
#   ブラウザが送っていた HTTP request を、Python から直接送ってみる。
#   「GET /forward HTTP/1.1」という文字列を自分の目で確認する。

import socket
import time

PICO_IP = "192.168.4.1"
PICO_PORT = 80


def send_http(request_text):
    """HTTP request の文字列を、そのまま Pico へ送る。"""
    print("----- SEND -----")
    print(request_text)

    s = socket.socket()
    s.connect((PICO_IP, PICO_PORT))
    s.sendall(request_text.encode())

    response = s.recv(1024)

    print("----- RESPONSE -----")
    print(response.decode())

    s.close()


# =========================================================
# 1. FORWARD を送る
# =========================================================

forward_request = (
    "GET /forward HTTP/1.1\r\n"
    "Host: 192.168.4.1\r\n"
    "Connection: close\r\n"
    "\r\n"
)

send_http(forward_request)
time.sleep(1)


# =========================================================
# 2. STOP を送る
# =========================================================

stop_request = (
    "GET /stop HTTP/1.1\r\n"
    "Host: 192.168.4.1\r\n"
    "Connection: close\r\n"
    "\r\n"
)

send_http(stop_request)


# =========================================================
# TODO
# =========================================================
# /right や /left の HTTP request を自分で作って、
# B-5 の動作シーケンスへ発展させる。
