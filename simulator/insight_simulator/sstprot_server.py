"""Fake SSTProt TCP server — a mock GeniusOne metal detector, used to test
the backend's SSTProt connector/commands without real hardware.

Seeded with the EXACT values from a real captured session
(`sstprot_function_final_report.md`, GeniusOne @ 192.168.1.125,
2026-05-19) so a successful test against this simulator is a genuine
cross-check against real device behaviour, not just internal consistency.
"""
from __future__ import annotations

import socket
import socketserver
import sys
import threading
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))

from app.sstprot.frame import STX, ETX, checksum, dec_u16, dec_u32, dec_u8, enc_u16, enc_u32, enc_u8

DEFAULT_PORT = 10001

# Real product 16 data, verbatim from the report's product_data example.
SEED_PRODUCT_16 = {
    "sensitivity": 85,
    "product_angle": 1382,
    "frequency_index": 0,
    "blanking": 0,
    "options": 0,
    "conveyor_speed": 11,
    "gain": 184,
    "threshold": 20,
}

# Real global counters, verbatim from the report.
SEED_COUNTERS = {"error_counter": 284, "metal_counter": 247910, "product_counter": 0}

# Real logbook, verbatim from the report (30 entries, newest first).
# (timestamp, entry_code, {param_index: value})
SEED_LOGBOOK = [
    ("2026-05-18 15:28:11", 0x90, {1: 0x0200}),
    ("2026-05-18 15:13:34", 0x90, {1: 0x0200}),
    ("2026-05-18 14:48:29", 0x90, {1: 0x0200}),
    ("2026-05-18 14:45:28", 0x90, {1: 0x0200}),
    ("2026-05-18 14:35:46", 0x93, {1: 1}),
    ("2026-05-18 06:34:39", 0x41, {}),
    ("2026-05-18 06:34:39", 0x80, {}),
    ("2026-05-16 05:13:43", 0x81, {}),
    ("2026-05-15 05:30:31", 0x01, {1: 16, 2: 159, 3: 51302, 4: 0}),
    ("2026-05-15 05:29:37", 0x01, {1: 16, 2: 100, 3: 51301, 4: 0}),
    ("2026-05-15 05:28:32", 0x01, {1: 16, 2: 100, 3: 51300, 4: 0}),
    ("2026-05-15 05:28:25", 0x01, {1: 16, 2: 277, 3: 51299, 4: 0}),
    ("2026-05-15 04:07:40", 0x01, {1: 16, 2: 103, 3: 51298, 4: 0}),
    ("2026-05-15 04:07:40", 0x01, {1: 16, 2: 255, 3: 51297, 4: 0}),
    ("2026-05-15 04:07:32", 0x01, {1: 16, 2: 126, 3: 51296, 4: 0}),
    ("2026-05-15 04:07:10", 0x01, {1: 16, 2: 251, 3: 51295, 4: 0}),
    ("2026-05-15 04:07:02", 0x01, {1: 16, 2: 122, 3: 51294, 4: 0}),
    ("2026-05-15 04:06:41", 0x01, {1: 16, 2: 295, 3: 51293, 4: 0}),
    ("2026-05-15 04:06:33", 0x01, {1: 16, 2: 119, 3: 51292, 4: 0}),
    ("2026-05-15 04:06:11", 0x01, {1: 16, 2: 284, 3: 51291, 4: 0}),
    ("2026-05-15 04:06:03", 0x01, {1: 16, 2: 126, 3: 51290, 4: 0}),
    ("2026-05-15 04:05:41", 0x01, {1: 16, 2: 245, 3: 51289, 4: 0}),
    ("2026-05-15 04:05:33", 0x01, {1: 16, 2: 126, 3: 51288, 4: 0}),
    ("2026-05-15 04:05:11", 0x01, {1: 16, 2: 236, 3: 51287, 4: 0}),
    ("2026-05-15 04:05:03", 0x01, {1: 16, 2: 149, 3: 51286, 4: 0}),
    ("2026-05-15 04:04:41", 0x01, {1: 16, 2: 210, 3: 51285, 4: 0}),
    ("2026-05-15 04:01:27", 0x01, {1: 16, 2: 275, 3: 51284, 4: 0}),
    ("2026-05-15 04:01:18", 0x01, {1: 16, 2: 159, 3: 51283, 4: 0}),
    ("2026-05-15 04:00:57", 0x01, {1: 16, 2: 239, 3: 51282, 4: 0}),
    ("2026-05-15 04:00:49", 0x01, {1: 16, 2: 149, 3: 51281, 4: 0}),
]
LOGBOOK_MAX = 1500
LOGBOOK_COUNT = 1500
# newest entry gets the highest absolute number (logbook is full: 1500/1500)
_NEWEST_ABS = LOGBOOK_COUNT


class MockGeniusOne:
    def __init__(self, address: int = 1) -> None:
        self.address = address
        self.device_type = 0x50  # GeniusOne
        self.device_name = ""
        self.line_name = ""
        self.mac_address = ""
        self.main_state = 0x05  # WARNING, matches the report's example
        self.sub_state = 0x00
        self.metal_signal = 1
        self.error_status = 0
        self.flags = 0x91  # Operation ON + New Logbook Entry + Service user logged in
        self.status_counter = 0
        self.current_product_number = 16
        self.products = {16: dict(SEED_PRODUCT_16)}
        self.counters = dict(SEED_COUNTERS)
        self.logbook = list(SEED_LOGBOOK)


class SstProtRequestHandler(socketserver.BaseRequestHandler):
    server: "SstProtTestServer"

    def handle(self) -> None:
        buf = bytearray()
        self.request.settimeout(30)
        while True:
            try:
                chunk = self.request.recv(256)
            except (socket.timeout, ConnectionError):
                return
            if not chunk:
                return
            buf += chunk
            while True:
                start = buf.find(STX)
                if start == -1:
                    buf.clear()
                    break
                end = buf.find(ETX, start)
                if end == -1:
                    break
                frame = bytes(buf[start : end + 1])
                del buf[: end + 1]
                response = self._handle_frame(frame)
                if response:
                    self.request.sendall(response)

    def _handle_frame(self, raw: bytes) -> bytes:
        body = raw[1:-1]
        payload, _cs = body[:-2], body[-2:]
        text = payload.decode("ascii")
        adr, _len_hex, rest = text[0:2], text[2:4], text[4:]
        cmd, params = rest[0:2], rest[2:]

        device = self.server.device
        try:
            data = self._dispatch(device, cmd, params)
        except LookupError:
            return self._build(adr, "NA", enc_u8(0x03))  # CMD NOT FOUND
        return self._build(adr, cmd, data)

    @staticmethod
    def _build(adr: str, cmd: str, data: str) -> bytes:
        body = cmd + data
        length = f"{len(body):02X}"
        payload = (adr + length + body).encode("ascii")
        cs = checksum(payload)
        return bytes([STX]) + payload + f"{cs:02X}".encode("ascii") + bytes([ETX])

    def _dispatch(self, d: MockGeniusOne, cmd: str, params: str) -> str:
        if cmd == "DA":
            return enc_u8(d.address)
        if cmd == "DT":
            return enc_u8(d.device_type)
        if cmd == "DN":
            return d.device_name.ljust(10)[:10]
        if cmd == "DL":
            return d.line_name.ljust(10)[:10]
        if cmd == "DM":
            return d.mac_address.ljust(12)[:12]
        if cmd == "TT":
            if params:  # set
                return enc_u8(0x00)
            now = datetime.now(timezone.utc)
            return "".join(enc_u8(v) for v in (now.year % 100, now.month, now.day, now.hour, now.minute, now.second))
        if cmd == "SQ":
            return (
                enc_u8(d.main_state)
                + enc_u8(d.sub_state)
                + enc_u16(d.metal_signal)
                + enc_u32(d.error_status)
                + enc_u8(d.flags)
                + enc_u16(d.status_counter)
                + enc_u8(0)
                + enc_u8(0)
            )
        if cmd == "PJ":
            return enc_u16(d.current_product_number)
        if cmd == "PD":
            if len(params) > 4:  # set: product_number(4) + 8 fields(22) = 26 chars; get: product_number(4) only
                product_number = dec_u16(params[0:4])
                d.products[product_number] = {
                    "sensitivity": dec_u16(params[4:8]),
                    "product_angle": dec_u16(params[8:12]),
                    "frequency_index": dec_u8(params[12:14]),
                    "blanking": dec_u8(params[14:16]),
                    "options": dec_u8(params[16:18]),
                    "conveyor_speed": dec_u16(params[18:22]),
                    "gain": dec_u8(params[22:24]),
                    "threshold": dec_u8(params[24:26]),
                }
                return enc_u8(0x00)
            product_number = dec_u16(params[0:4])
            p = d.products.get(product_number, dict(SEED_PRODUCT_16))
            return (
                enc_u16(p["sensitivity"])
                + enc_u16(p["product_angle"])
                + enc_u8(p["frequency_index"])
                + enc_u8(p["blanking"])
                + enc_u8(p["options"])
                + enc_u16(p["conveyor_speed"])
                + enc_u8(p["gain"])
                + enc_u8(p["threshold"])
            )
        if cmd == "SL":
            which = dec_u8(params[0:2])
            c = d.counters if which == 0 else {"error_counter": 0, "metal_counter": 0, "product_counter": 0}
            return enc_u32(c["error_counter"]) + enc_u32(c["metal_counter"]) + enc_u32(c["product_counter"])
        if cmd == "LI":
            return enc_u16(LOGBOOK_MAX)
        if cmd == "LN":
            return enc_u16(LOGBOOK_COUNT)
        if cmd == "LE":
            position = dec_u32(params[0:8])
            return self._encode_logbook_entry(d, position)
        if cmd == "LC":
            return enc_u8(0x00)
        raise LookupError(cmd)

    @staticmethod
    def _encode_logbook_entry(d: MockGeniusOne, position: int) -> str:
        if position == 0xFFFFFFFF:
            idx = 0
        else:
            idx = _NEWEST_ABS - position
            if idx < 0 or idx >= len(d.logbook):
                raise LookupError("LE")
        ts_str, entry_code, params = d.logbook[idx]
        dt = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
        time_field = "".join(enc_u8(v) for v in (dt.year % 100, dt.month, dt.day, dt.hour, dt.minute, dt.second))
        param_field = "".join(enc_u16(params.get(i, 0)) for i in range(1, 5))
        absolute_number = _NEWEST_ABS - idx
        return enc_u8(entry_code) + time_field + param_field + enc_u32(absolute_number)


class SstProtTestServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True

    def __init__(self, host: str, port: int, device: MockGeniusOne | None = None):
        self.device = device or MockGeniusOne()
        super().__init__((host, port), SstProtRequestHandler)


def run(host: str = "0.0.0.0", port: int = DEFAULT_PORT) -> SstProtTestServer:
    server = SstProtTestServer(host, port)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server


if __name__ == "__main__":
    srv = SstProtTestServer("0.0.0.0", DEFAULT_PORT)
    print(f"Mock GeniusOne (SSTProt) listening on 0.0.0.0:{DEFAULT_PORT}")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
