"""PC-side tests: BCD, STA startup simulation, HTTP, student API.

Tests do not connect to real Wi-Fi, ESP32, or KENTEI hardware.
"""
import contextlib
import io
import os
import sys
import time
import threading
import types
import unittest
import urllib.request
import urllib.error
from unittest import mock

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, ROOT)
from hmi import WebHMI, encode_bcd, decode_bcd


class BCDTests(unittest.TestCase):
    def test_all_digits_roundtrip(self):
        for n in range(10):
            self.assertEqual(decode_bcd(encode_bcd(n)), n)

    def test_example_7_and_42(self):
        self.assertEqual(encode_bcd(7), (1, 1, 1, 0))
        h = WebHMI()
        h.dpl_hyouji(42)
        self.assertEqual(h.read_dpl_bits(), ((0, 1, 0, 0), (0, 0, 1, 0)))
        h.write_dpl_bcd((0, 1, 0, 0), (0, 0, 1, 0))
        self.assertEqual(h.get_state()['dpl'], 42)

    def test_invalid_bcd_rejected(self):
        for n in (10, 11, 15, -1, True, 1.5, '3'):
            with self.assertRaises(ValueError):
                encode_bcd(n)
        for bits in ((1, 1, 1, 1), (1, 0, 1, 1), (1, 1), (0, 0, 0, 2)):
            with self.assertRaises(ValueError):
                decode_bcd(bits)

    def test_out_of_range_dpl_rejected(self):
        h = WebHMI()
        for n in (-1, 100, True, '30'):
            with self.assertRaises(ValueError):
                h.dpl_hyouji(n)

    def test_friendly_aliases(self):
        h = WebHMI()
        h.dsw = 9
        self.assertEqual(h.dsw_yomu(), h.dsw_bits_yomu())
        h.dpl_hyouji(27)
        self.assertEqual(h.get_state()['dpl'], 27)


class StudentBitsTests(unittest.TestCase):
    """v0.5: student-visible bit order is MSB-first [8,4,2,1]."""

    def test_dsw_msb_first_all_digits(self):
        h = WebHMI()
        for n in range(10):
            h.dsw = n
            expected = [(n >> bit) & 1 for bit in (3,2,1,0)]
            self.assertEqual(h.dsw_bits_yomu(), expected)
        h.dsw = 3
        self.assertEqual(h.dsw_bits_yomu(), [0,0,1,1])
        h.dsw = 9
        self.assertEqual(h.dsw_bits_yomu(), [1,0,0,1])
        self.assertIsInstance(h.dsw_bits_yomu(), list)

    def test_dpl1_dpl2_msb_first_separate(self):
        h = WebHMI()
        h.dpl1_hyouji([0,0,1,0])  # ones = 2
        self.assertEqual(h.get_state()['dpl'], 2)
        h.dpl2_hyouji([0,1,0,0])  # tens = 4
        self.assertEqual(h.get_state()['dpl'], 42)
        h.dpl1_hyouji([1,0,0,1])  # ones = 9
        self.assertEqual(h.get_state()['dpl'], 49)
        h.dpl2_hyouji([0,0,0,0])  # tens = 0
        self.assertEqual(h.get_state()['dpl'], 9)

    def test_invalid_4bit_bcd_blanks_only_affected_digit(self):
        h = WebHMI()
        h.dpl_hyouji(42)
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            h.dpl1_hyouji([1, 1, 0, 0])  # 12 on units (actual KENTEI test)
        state = h.get_state()
        self.assertIsNone(state['dpl'])
        self.assertTrue(state['dpl1_blank'])
        self.assertFalse(state['dpl2_blank'])
        self.assertEqual(state['dpl1_bcd'], 12)
        self.assertEqual(state['dpl1_bits'], [0, 0, 1, 1])  # TB26..29 LSB first
        self.assertEqual(state['dpl2_bcd'], 4)  # the other digit stays lit
        self.assertIn('消灯', out.getvalue())
        h.dpl1_hyouji([0, 1, 0, 0])  # 4 -> recover
        self.assertEqual(h.get_state()['dpl'], 44)
        self.assertFalse(h.get_state()['dpl1_blank'])

    def test_all_10_through_15_hold_raw_nibble_and_blank(self):
        h = WebHMI()
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            for n in range(10, 16):
                bits = [(n >> i) & 1 for i in (3, 2, 1, 0)]
                h.dpl1_hyouji(bits)
                self.assertEqual(h.get_state()['dpl1_bcd'], n)
                self.assertIsNone(h.get_state()['dpl'])
                self.assertEqual(h.read_dpl_bits()[0], tuple((n >> i) & 1 for i in range(4)))
                h.dpl2_hyouji(bits)
                self.assertEqual(h.get_state()['dpl2_bcd'], n)
                self.assertTrue(h.get_state()['dpl1_blank'])
                self.assertTrue(h.get_state()['dpl2_blank'])
        # A continuous invalid run warns once for each digit.
        self.assertEqual(out.getvalue().count('WARNING:'), 2)

    def test_malformed_input_warns_keeps_previous_4wire_signal(self):
        h = WebHMI()
        h.dpl_hyouji(42)
        bad = ([0,0,1], [0,0,0,0,1], [0,1,0,2],
               [0,1,0,True], '0101', None, (1.0,0,0,0))
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            for bits in bad:
                with self.subTest(bits=bits):
                    h.dpl1_hyouji(bits)
                    h.dpl2_hyouji(bits)
                    self.assertEqual(h.get_state()['dpl'], 42)
        self.assertIn('malformed BCD bits', out.getvalue())
        self.assertIn('前の出力', out.getvalue())
        self.assertEqual(out.getvalue().count('WARNING:'), 2)

    def test_valid_write_rearms_warning(self):
        h = WebHMI()
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            for _ in range(10):
                h.dpl2_hyouji([1, 0, 1, 0])  # 10 -> blank
            h.dpl2_hyouji([0, 1, 0, 0])      # valid 4 -> lit
            h.dpl2_hyouji([1, 1, 1, 1])      # 15 -> blank and warn again
        self.assertEqual(h.dpl2, 15)
        self.assertEqual(out.getvalue().count('WARNING: DPL2'), 2)
        self.assertTrue(h.get_state()['dpl2_blank'])

    def test_valid_8_to_invalid_12_to_valid_4(self):
        h = WebHMI()
        with contextlib.redirect_stdout(io.StringIO()):
            h.dpl1_hyouji([1,0,0,0])
            self.assertEqual(h.get_state()['dpl1_bcd'], 8)
            h.dpl1_hyouji([1,1,0,0])
            self.assertIsNone(h.get_state()['dpl'])
            self.assertEqual(h.get_state()['dpl1_bcd'], 12)
            h.dpl1_hyouji([0,1,0,0])
            self.assertEqual(h.get_state()['dpl'], 4)

    def test_legacy_decimal_and_terminal_order_unchanged(self):
        h = WebHMI()
        h.dsw = 3
        self.assertEqual(h.read_dsw(), 3)
        self.assertEqual(h.read_dsw_bits(), (1, 1, 0, 0))  # TB13..16
        h.dpl_hyouji(42)
        self.assertEqual(h.get_state()['dpl'], 42)
        h.write_dpl_bcd((0,1,0,0), (0,0,1,0))  # old terminal order
        self.assertEqual(h.get_state()['dpl'], 42)
        self.assertEqual(h.read_dpl_bits(), ((0,1,0,0), (0,0,1,0)))


class FakeSTA:
    def __init__(self, connect_succeeds=True):
        self.active_state = False
        self.connected = False
        self.connect_succeeds = connect_succeeds
        self.credentials = None

    def active(self, value):
        self.active_state = value

    def connect(self, ssid, password):
        self.credentials = (ssid, password)
        if self.connect_succeeds:
            self.connected = True

    def isconnected(self):
        return self.connected

    def ifconfig(self):
        return ('127.0.0.1', '255.0.0.0', '127.0.0.1', '127.0.0.1')


class HTTPTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sta = FakeSTA()
        cls.network_patch = mock.patch.dict(sys.modules, {
            'network': types.SimpleNamespace(STA_IF=0, WLAN=lambda _: cls.sta)
        })
        cls.network_patch.start()
        cls.time_patch = mock.patch.multiple(time,
            ticks_ms=mock.DEFAULT, ticks_diff=mock.DEFAULT, sleep_ms=mock.DEFAULT,
            create=True)
        cls.clock = cls.time_patch.start()
        cls.clock['ticks_ms'].side_effect = lambda: int(time.monotonic() * 1000)
        cls.clock['ticks_diff'].side_effect = lambda a, b: a - b
        cls.clock['sleep_ms'].side_effect = lambda ms: time.sleep(ms / 1000)
        cls.hmi = WebHMI(ssid='TRAINING-AP', password='private-test', port=0)
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            cls.hmi.start()
        cls.boot_log = output.getvalue()
        cls.port = cls.hmi.server.getsockname()[1]
        cls.running = True
        cls.worker = threading.Thread(target=cls.loop, daemon=True)
        cls.worker.start()

    @classmethod
    def loop(cls):
        while cls.running:
            cls.hmi.web_shori()
            time.sleep(0.01)

    @classmethod
    def tearDownClass(cls):
        cls.running = False
        cls.worker.join(timeout=2)
        cls.hmi.stop()
        cls.time_patch.stop()
        cls.network_patch.stop()

    def url(self, path):
        return 'http://127.0.0.1:%d%s' % (self.port, path)

    def test_sta_connect_and_dhcp_log(self):
        self.assertEqual(self.sta.credentials, ('TRAINING-AP', 'private-test'))
        self.assertIn('STA', self.boot_log)
        self.assertIn('TRAINING-AP', self.boot_log)
        self.assertIn('DHCP IP: 127.0.0.1', self.boot_log)
        self.assertIn('open: http://127.0.0.1/', self.boot_log)
        self.assertNotIn('private-test', self.boot_log)

    def test_get_page(self):
        with urllib.request.urlopen(self.url('/'), timeout=3) as r:
            html = r.read().decode('utf-8')
        self.assertIn('KENTEI', html)
        self.assertIn('DPL', html)
        self.assertIn('DSW', html)

    def test_dsw_post_and_read(self):
        req = urllib.request.Request(self.url('/api/dsw'),
            data=b'{"value":7}', headers={'Content-Type': 'application/json'}, method='POST')
        with urllib.request.urlopen(req, timeout=3) as r:
            self.assertEqual(r.status, 200)
            self.assertIn(b'"dsw":7', r.read())
        self.assertEqual(self.hmi.read_dsw(), 7)
        self.assertEqual(self.hmi.read_dsw_bits(), (1, 1, 1, 0))

    def test_web_dsw_and_bit_dpl_via_http(self):
        import json
        req = urllib.request.Request(self.url('/api/dsw'),
            data=b'{"value":3}', headers={'Content-Type': 'application/json'}, method='POST')
        with urllib.request.urlopen(req, timeout=3) as response:
            self.assertEqual(response.status, 200)
        self.assertEqual(self.hmi.dsw_bits_yomu(), [0,0,1,1])
        self.hmi.dpl1_hyouji([0,0,1,0])
        self.hmi.dpl2_hyouji([0,1,0,0])
        with urllib.request.urlopen(self.url('/api/state'), timeout=3) as response:
            state = json.loads(response.read().decode())
        self.assertEqual(state['dpl'], 42)
        self.assertEqual(state['dpl1_bcd'], 2)
        self.assertEqual(state['dpl2_bcd'], 4)

    def test_http_raw_bcd_blank_and_recovery(self):
        import json
        with contextlib.redirect_stdout(io.StringIO()):
            self.hmi.dpl_hyouji(42)
            self.hmi.dpl2_hyouji([1,1,0,0])  # 12 -> blank tens
        with urllib.request.urlopen(self.url('/api/state'), timeout=3) as resp:
            state = json.loads(resp.read().decode())
        self.assertIsNone(state['dpl'])
        self.assertTrue(state['dpl2_blank'])
        self.assertFalse(state['dpl1_blank'])
        self.assertEqual(state['dpl2_bcd'], 12)
        self.assertEqual(state['dpl2_bits'], [0,0,1,1])
        self.hmi.dpl2_hyouji([0,1,0,0])
        with urllib.request.urlopen(self.url('/api/state'), timeout=3) as resp:
            state = json.loads(resp.read().decode())
        self.assertEqual(state['dpl'], 42)
        self.assertFalse(state['dpl2_blank'])

    def test_invalid_post_no_change(self):
        old = self.hmi.read_dsw()
        for body in (b'{"value":12}', b'{"value":true}', b'{"value":-1}', b'{"wrong":3}'):
            req = urllib.request.Request(self.url('/api/dsw'), data=body, method='POST')
            with self.assertRaises(urllib.error.HTTPError) as err:
                urllib.request.urlopen(req, timeout=3)
            self.assertEqual(err.exception.code, 400)
            self.assertEqual(self.hmi.read_dsw(), old)

    def test_dpl_state(self):
        self.hmi.dpl_hyouji(42)
        with urllib.request.urlopen(self.url('/api/state'), timeout=3) as r:
            import json
            state = json.loads(r.read().decode())
        self.assertEqual(state['dpl'], 42)
        self.assertEqual(state['dpl1_bits'], [0, 1, 0, 0])
        self.assertEqual(state['dpl2_bits'], [0, 0, 1, 0])


class ConnectionFailureTests(unittest.TestCase):
    def test_no_credentials(self):
        with self.assertRaises(ValueError):
            WebHMI().start()

    def test_connection_timeout(self):
        sta = FakeSTA(connect_succeeds=False)
        count = [0]
        def clock():
            count[0] += 200
            return count[0]
        with mock.patch.dict(sys.modules, {'network': types.SimpleNamespace(STA_IF=0, WLAN=lambda _: sta)}), \
             mock.patch.object(time, 'ticks_ms', clock, create=True), \
             mock.patch.object(time, 'ticks_diff', lambda a, b: a-b, create=True), \
             mock.patch.object(time, 'sleep_ms', lambda ms: None, create=True), \
             contextlib.redirect_stdout(io.StringIO()):
            h = WebHMI(ssid='FAIL-AP', password='bad', connect_timeout_ms=300)
            with self.assertRaisesRegex(RuntimeError, 'timed out'):
                h.start()
            self.assertIsNone(h.server)
            self.assertFalse(sta.active_state)


if __name__ == '__main__':
    unittest.main(verbosity=2)
