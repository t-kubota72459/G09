"""KENTEI Web HMI prototype -- ESP32 / MicroPython.

The *virtual* terminals implement the wiring diagram's BCD interface:
  DSW input  TB 13=1,14=2,15=4,16=8
  DPL1 output TB 26=1,27=2,28=4,29=8
  DPL2 output TB 30=10,31=20,32=40,33=80

No physical GPIO is reserved by this module. ESP32 joins classroom Wi-Fi
(STA mode) and serves index.html from the DHCP-assigned IP address.
Call web_shori() frequently from the existing state-machine's main loop.
Student-facing BCD bit lists use MSB-first [8,4,2,1] order. Existing
terminal-order (LSB-first) low-level methods stay available for compatibility.
This is teaching equipment, not a safety-rated controller.
"""
try:
    import ujson as json
except ImportError:
    import json
import socket
import select


def encode_bcd(digit):
    """LEGACY: Decimal digit -> tuple in terminal [1,2,4,8] order."""
    if type(digit) is not int or not 0 <= digit <= 9:
        raise ValueError("BCD digit must be an integer 0..9")
    return tuple((digit >> i) & 1 for i in range(4))


def decode_bcd(bits):
    """LEGACY: terminal [1,2,4,8] bit order -> decimal digit."""
    if len(bits) != 4:
        raise ValueError("Exactly four BCD bits required")
    number = 0
    for i, bit in enumerate(bits):
        if type(bit) is not int or bit not in (0, 1):
            raise ValueError("Each BCD bit must be 0 or 1")
        number |= bit << i
    if number > 9:
        raise ValueError("Invalid BCD pattern 10..15")
    return number


def _read_nibble_msb(bits):
    """Read any four-bit [8,4,2,1] pattern as an integer 0..15.

    10..15 are valid *wire* patterns, although the decimal KENTEI DPL
    cannot display them. Only malformed Python bit lists raise ValueError.
    """
    if not isinstance(bits, (list, tuple)) or len(bits) != 4:
        raise ValueError("BCD must be a list/tuple of four bits [8,4,2,1]")
    number = 0
    for bit in bits:
        if type(bit) is not int or bit not in (0, 1):
            raise ValueError("Each BCD bit must be 0 or 1")
        number = (number << 1) | bit
    return number


def _raw_bits_lsb(value):
    """Return TB terminal-order bits for a four-bit *raw* output 0..15."""
    return tuple((value >> i) & 1 for i in range(4))


class WebHMI:
    """One ESP32 / one browser-operated virtual DSW + 2-digit DPL."""

    def __init__(self, ssid=None, password=None, port=80, connect_timeout_ms=15000):
        self.port = port
        self.ssid = ssid
        self.password = password
        self.connect_timeout_ms = connect_timeout_ms
        self.dsw = 0
        self.dpl1 = 0  # units: physical DPL1, TB 26..29
        self.dpl2 = 0  # tens:  physical DPL2, TB 30..33
        self._warned_dpl1 = False  # Only one Shell warning per invalid run
        self._warned_dpl2 = False
        self.wlan = None
        self.server = None
        self.poller = None
        self.ip = None

    # --- Learning-facing API: no physical GPIO mapping needed ---
    def read_dsw(self):
        """Return decimal 0..9 selected by the browser DSW."""
        return self.dsw

    def read_dsw_bits(self):
        """Virtual TB inputs (13,14,15,16) in that order."""
        return encode_bcd(self.dsw)

    def set_dpl(self, number):
        """Show 00..99 on DPL2(tens) + DPL1(units)."""
        if type(number) is not int or not 0 <= number <= 99:
            raise ValueError("DPL value must be an integer 0..99")
        self.dpl1 = number % 10
        self.dpl2 = number // 10
        self._warned_dpl1 = False
        self._warned_dpl2 = False

    def write_dpl_bcd(self, dpl1_bits, dpl2_bits):
        """Write *raw BCD* outputs from a 2-grade task.

        dpl1_bits: [TB26(1), TB27(2), TB28(4), TB29(8)]
        dpl2_bits: [TB30(10),TB31(20),TB32(40),TB33(80)]
        """
        self.dpl1 = decode_bcd(dpl1_bits)
        self.dpl2 = decode_bcd(dpl2_bits)
        self._warned_dpl1 = False
        self._warned_dpl2 = False

    def read_dpl_bits(self):
        """Return actual (DPL1, DPL2) four-bit outputs, LSB-first.

        Unlike the decimal encode_bcd helper, this preserves raw 10..15
        patterns so students can inspect the electrical-equivalent signal.
        """
        return _raw_bits_lsb(self.dpl1), _raw_bits_lsb(self.dpl2)

    def get_state(self):
        blank1 = self.dpl1 > 9
        blank2 = self.dpl2 > 9
        return {
            "dsw": self.dsw,
            "dsw_bits": list(self.read_dsw_bits()),
            # No meaningful two-digit decimal value if either digit is blank.
            "dpl": None if (blank1 or blank2) else self.dpl2 * 10 + self.dpl1,
            "dpl1_bcd": self.dpl1,
            "dpl2_bcd": self.dpl2,
            "dpl1_blank": blank1,
            "dpl2_blank": blank2,
            "dpl1_bits": list(_raw_bits_lsb(self.dpl1)),
            "dpl2_bits": list(_raw_bits_lsb(self.dpl2)),
        }

    # --- Student-facing names (aliases for existing API) ---
    def web_shori(self):
        """WebからのHTTP要求を最大1件処理する。要求がなければすぐ戻る。"""
        return self.poll()

    def dsw_yomu(self):
        """dsw_bits_yomu() の別名"""
        return self.dsw_bits_yomu()

    def dpl_hyouji(self, number):
        """WebのDPLへ十進数00～99を表示する（従来どおり）。"""
        self.set_dpl(number)

    # --- Student-facing BCD bits: MSB first, weights [8,4,2,1] ---
    def dsw_bits_yomu(self):
        """DSWのBCD入力をMSB先頭のリストで返す。3なら[0,0,1,1]。"""
        return [(self.dsw >> shift) & 1 for shift in (3, 2, 1, 0)]

    def _student_dpl_write(self, dpl_num, bits):
        """Write raw BCD nibble; decimal display blanks on 10..15.

        This emulates the KENTEI decimal display: an out-of-range 4-bit
        signal remains present on its terminal and only its digit blanks.
        Malformed lists aren't a four-bit signal; warn and keep the last
        output. Both cases are non-fatal to the control loop.
        """
        try:
            value = _read_nibble_msb(bits)
        except (ValueError, TypeError):
            # A malformed Python value is not a real 4-wire input.
            warned = self._warned_dpl1 if dpl_num == 1 else self._warned_dpl2
            if not warned:
                print('[KENTEI HMI] WARNING: DPL%d malformed BCD bits: %s' %
                      (dpl_num, repr(bits)[:80]))
                print('[KENTEI HMI] 4ビットの0/1を指定してください。前の出力を維持します。')
            if dpl_num == 1:
                self._warned_dpl1 = True
            else:
                self._warned_dpl2 = True
            return

        # Preserve 10..15 as actual 4-bit signals; don't clamp or hold them.
        if dpl_num == 1:
            was_warned = self._warned_dpl1
            self.dpl1 = value
            self._warned_dpl1 = value > 9
        else:
            was_warned = self._warned_dpl2
            self.dpl2 = value
            self._warned_dpl2 = value > 9
        if value > 9 and not was_warned:
            print('[KENTEI HMI] WARNING: DPL%d BCD=%s (%d) -> 10進表示範囲外のため消灯' %
                  (dpl_num, ''.join(str(b) for b in bits), value))

    def dpl1_hyouji(self, bits):
        """DPL1（一の位）へMSB先頭4ビット。10～15は消灯・警告。"""
        self._student_dpl_write(1, bits)

    def dpl2_hyouji(self, bits):
        """DPL2（十の位）へMSB先頭4ビット。10～15は消灯・警告。"""
        self._student_dpl_write(2, bits)

    # --- Network setup: join an existing classroom AP (STA) ---
    def start(self):
        """Join Wi-Fi, receive a DHCP address, then start the HTTP server."""
        import time
        if self.server is not None:
            return
        if not self.ssid or self.password is None:
            raise ValueError('Set Wi-Fi SSID and password in wifi_config.py')
        import network

        # MicroPython versions use STA_IF or WLAN.IF_STA.
        if hasattr(network, 'STA_IF'):
            sta_interface = network.STA_IF
        else:
            sta_interface = network.WLAN.IF_STA
        self.wlan = network.WLAN(sta_interface)
        self.wlan.active(True)
        print('[KENTEI HMI] mode: STA (classroom Wi-Fi)')
        print('[KENTEI HMI] connecting SSID:', self.ssid)
        # Never echo the classroom Wi-Fi password to Shell.

        try:
            if not self.wlan.isconnected():
                self.wlan.connect(self.ssid, self.password)
                start_ms = time.ticks_ms()
                while not self.wlan.isconnected():
                    if time.ticks_diff(time.ticks_ms(), start_ms) >= self.connect_timeout_ms:
                        raise RuntimeError('Wi-Fi connection timed out; check SSID / password / AP')
                    time.sleep_ms(100)

            addr = self.wlan.ifconfig()  # DHCP: (IP, netmask, gateway, DNS)
            self.ip = addr[0]
            if not self.ip or self.ip == '0.0.0.0':
                raise RuntimeError('Wi-Fi connected but DHCP IP is unavailable')

            self.server = socket.socket()
            self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server.bind(('0.0.0.0', self.port))
            self.server.listen(2)
            self.server.setblocking(False)
            self.poller = select.poll()
            self.poller.register(self.server, select.POLLIN)
        except Exception:
            if self.server:
                self.server.close()
                self.server = None
            if self.wlan:
                self.wlan.active(False)
                self.wlan = None
            self.poller = None
            self.ip = None
            raise

        print('[KENTEI HMI] DHCP IP:', self.ip)
        print('[KENTEI HMI] gateway:', addr[2])
        print('[KENTEI HMI] open: http://%s/' % self.ip)

    def stop(self):
        if self.poller is not None and self.server is not None:
            self.poller.unregister(self.server)
        if self.server is not None:
            self.server.close()
            self.server = None
        if self.wlan is not None:
            self.wlan.active(False)
            self.wlan = None
        self.poller = None
        self.ip = None

    # --- A small cooperative HTTP server ---
    def poll(self):
        """Handle at most one request. Call frequently; never use as safety I/O."""
        if self.server is None:
            return False
        if not self.poller.poll(0):
            return False
        try:
            client, _address = self.server.accept()
        except OSError:
            return False
        try:
            # A slow/nonresponsive browser must not block indefinitely.
            client.settimeout(0.8)
            self._handle(client)
        except OSError:
            pass
        finally:
            client.close()
        return True

    def _read_request(self, client):
        raw = b''
        header_end = -1
        content_length = 0
        while len(raw) < 4096:
            chunk = client.recv(1024)
            if not chunk:
                break
            raw += chunk
            if header_end < 0:
                header_end = raw.find(b'\r\n\r\n')
                if header_end >= 0:
                    headers = raw[:header_end].decode('utf-8')
                    for line in headers.split('\r\n')[1:]:
                        if line.lower().startswith('content-length:'):
                            content_length = int(line.split(':', 1)[1].strip())
                    if content_length > 256:
                        raise ValueError('Request too large')
            if header_end >= 0 and len(raw) >= header_end + 4 + content_length:
                break
        if header_end < 0:
            raise ValueError('Incomplete request')
        first_line = raw[:header_end].split(b'\r\n', 1)[0].decode('ascii')
        method, path, _ = first_line.split(' ', 2)
        path = path.split('?', 1)[0]
        body = raw[header_end + 4:header_end + 4 + content_length]
        if len(body) != content_length:
            raise ValueError('Incomplete body')
        return method, path, body

    def _write(self, client, data):
        # sendall() is defined for *blocking* MicroPython sockets.
        client.sendall(data)

    def _headers(self, client, status, content_type, length):
        head = ('HTTP/1.1 %s\r\n'
                'Content-Type: %s\r\n'
                'Content-Length: %d\r\n'
                'Cache-Control: no-store\r\n'
                'Connection: close\r\n'
                'X-Content-Type-Options: nosniff\r\n\r\n'
                % (status, content_type, length))
        self._write(client, head.encode('utf-8'))

    def _json(self, client, status, data):
        body = json.dumps(data).encode('utf-8')
        self._headers(client, status, 'application/json; charset=utf-8', len(body))
        self._write(client, body)

    def _handle(self, client):
        try:
            method, path, body = self._read_request(client)
        except (ValueError, IndexError, UnicodeError):
            self._json(client, '400 Bad Request', {'error': 'Malformed HTTP request'})
            return

        if method == 'GET' and path == '/api/state':
            self._json(client, '200 OK', self.get_state())
        elif method == 'POST' and path == '/api/dsw':
            try:
                value = json.loads(body.decode('utf-8'))['value']
                if type(value) is not int or value < 0 or value > 9:
                    raise ValueError('DSW must be 0..9')
                self.dsw = value
                self._json(client, '200 OK', self.get_state())
            except (ValueError, KeyError, TypeError, UnicodeError):
                self._json(client, '400 Bad Request', {'error': 'DSW must be integer 0..9'})
        elif method == 'GET' and path == '/':
            try:
                import os
                n = os.stat('index.html')[6]
                self._headers(client, '200 OK', 'text/html; charset=utf-8', n)
                with open('index.html', 'rb') as f:
                    while True:
                        block = f.read(768)
                        if not block:
                            break
                        self._write(client, block)
            except OSError:
                # On an ESP32 the file may not yet be uploaded.
                # If headers have already been sent, the browser reports a load error.
                pass
        else:
            self._json(client, '404 Not Found', {'error': 'Not found'})

    def wait_ms(self, ms):
        start = time.ticks_ms()

        while time.ticks_diff(time.ticks_ms(), start) < ms:
            self.web_shori()
            time.sleep_ms(10)
