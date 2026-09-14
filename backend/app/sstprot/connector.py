"""TCP connector for SSTProt (Genius/GeniusOne/Genius+ over Ethernet, port
10001 per spec section "Implementation Hints" / "Ethernet Interface").

Usage (matches the report's described usage of `SestotecConnector`):

    with SstProtConnector("192.168.1.125") as conn:
        data = read_device_data(conn)
"""
from __future__ import annotations

import socket
import time

from .frame import STX, ETX, ParsedFrame, decode_frame, encode_frame

DEFAULT_PORT = 10001  # spec: "Ethernet Interface" section
DEFAULT_ADDRESS = "FF"  # spec: legal broadcast/default address for Ethernet/RS232
# Spec: "Between two commands (requests) there should be a gap of at least
# 200 ms to reduce processor load and to avoid communication errors."
MIN_COMMAND_INTERVAL_S = 0.2


class SstProtConnector:
    def __init__(
        self,
        host: str,
        port: int = DEFAULT_PORT,
        address: str = DEFAULT_ADDRESS,
        timeout: float = 3.0,
        inter_command_delay: float = MIN_COMMAND_INTERVAL_S,
    ) -> None:
        self.host = host
        self.port = port
        self.address = address
        self.timeout = timeout
        self.inter_command_delay = inter_command_delay
        self._sock: socket.socket | None = None
        self._last_command_at = 0.0

    def connect(self) -> None:
        self._sock = socket.create_connection((self.host, self.port), timeout=self.timeout)

    def close(self) -> None:
        if self._sock is not None:
            try:
                self._sock.close()
            finally:
                self._sock = None

    def __enter__(self) -> "SstProtConnector":
        self.connect()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def _respect_scan_cycle(self) -> None:
        elapsed = time.monotonic() - self._last_command_at
        remaining = self.inter_command_delay - elapsed
        if remaining > 0:
            time.sleep(remaining)

    def _read_frame(self) -> bytes:
        assert self._sock is not None, "not connected"
        buf = bytearray()
        started = False
        while True:
            chunk = self._sock.recv(256)
            if not chunk:
                raise ConnectionError("connection closed by device while reading response")
            buf += chunk
            if not started:
                idx = buf.find(STX)
                if idx == -1:
                    buf.clear()
                    continue
                del buf[:idx]
                started = True
            if ETX in buf:
                etx_idx = buf.index(ETX)
                return bytes(buf[: etx_idx + 1])

    def send_command(self, cmd: str, params: str = "") -> ParsedFrame:
        """Send one command and return the decoded response. Raises
        SstProtNotAcknowledged on an 'NA' response, SstProtFrameError on a
        malformed/checksum-invalid response.
        """
        assert self._sock is not None, "not connected — use as a context manager or call connect()"
        self._respect_scan_cycle()
        request = encode_frame(self.address, cmd, params)
        self._sock.sendall(request)
        raw = self._read_frame()
        self._last_command_at = time.monotonic()
        return decode_frame(raw)
