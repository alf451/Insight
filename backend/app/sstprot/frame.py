"""SSTProt frame encoding/decoding — checksum verified byte-for-byte against
the two worked examples in the official "SSTProt V1.54.pdf" (section
"Telegramm and Protocol Structure"):

    Set command "Clear logbook":
        request  = STX "11" "02" "LC"        CS="53" ETX   -> b'\\x02' + b'1102LC53' + b'\\x03'
        response = STX "11" "04" "LC" "00"   CS="B5" ETX

    Get command "Get number of logbook entries":
        request  = STX "11" "02" "LN"        CS="5E" ETX
        response = STX "11" "06" "LN" "0012" CS="25" ETX   (0x0012 = 18 entries)

Both checksums are reproduced exactly by `checksum()` below — see
tests/test_sstprot_frame.py.

Frame layout: STX(0x02) ADR(2 ascii-hex) LEN(2 ascii-hex) CMD(2 ascii)
[params ascii] CS(2 ascii-hex) ETX(0x03). LEN counts the ASCII length of
CMD+params. CS is the 8-bit sum of the ASCII bytes of ADR+LEN+CMD+params,
mod 256, hex-encoded — with one documented special case (see `checksum`).

KNOWN GAP (see docs/SSTPROT.md): the exact trailing byte layout of the "LE"
(get logbook entry) response could not be pinned down with certainty from
the PDF's text extraction (the arithmetic doesn't cleanly close over the
documented field list). `commands.py` decodes it defensively rather than
guessing silently — see its docstring.
"""
from __future__ import annotations

from dataclasses import dataclass

STX = 0x02
ETX = 0x03

# Case of error (spec section "Case of Error", page 8)
NA_ERROR_CODES = {
    0x01: "WRONG ADDRESS",
    0x02: "WRONG LENGTH",
    0x03: "CMD NOT FOUND",
    0x04: "CS ERROR",
    0x05: "STX MISSING",
    0x06: "ETX MISSING",
    0x07: "INTERNAL ERROR",
    0x08: "GENIUS+ TOUCH: ALREADY CONNECTED",
    0x09: "ACCESS LEVEL",
}


class SstProtError(Exception):
    """Base class for all SSTProt errors."""


class SstProtFrameError(SstProtError):
    """Malformed frame (missing STX/ETX, bad checksum, ...)."""


class SstProtNotAcknowledged(SstProtError):
    """Device responded with 'NA' + an error code."""

    def __init__(self, error_code: int):
        self.error_code = error_code
        self.error_name = NA_ERROR_CODES.get(error_code, f"UNKNOWN (0x{error_code:02X})")
        super().__init__(f"NA: {self.error_name}")


def checksum(payload: bytes) -> int:
    """payload = ASCII bytes of ADR+LEN+CMD+params (i.e. everything between
    STX and CS, exclusive). Returns the raw checksum byte value (0-255).

    Per spec: 8-bit addition of all bytes, then if the result equals 0x0D
    (<CR>) it is inverted bit-by-bit — this is a documented edge case, not
    a guess.
    """
    total = sum(payload) & 0xFF
    if total == 0x0D:
        total = (~total) & 0xFF
    return total


def encode_frame(adr: str, cmd: str, params: str = "") -> bytes:
    """Build a full request frame ready to send over the TCP socket.

    adr: 2-char ASCII hex device address (e.g. "FF" for broadcast/Ethernet default).
    cmd: 2 uppercase ASCII letters (e.g. "LN").
    params: already hex/ASCII-encoded parameter string (e.g. "0001" for a u16).
    """
    if len(adr) != 2:
        raise ValueError(f"adr must be 2 ASCII hex chars, got {adr!r}")
    if len(cmd) != 2 or not cmd.isupper():
        raise ValueError(f"cmd must be 2 uppercase ASCII letters, got {cmd!r}")

    body = cmd + params
    length = len(body)
    if length > 0x80:
        raise ValueError(f"frame body too long ({length} > 128 bytes): {cmd}")
    len_hex = f"{length:02X}"

    payload = (adr + len_hex + body).encode("ascii")
    cs = checksum(payload)
    cs_hex = f"{cs:02X}"

    return bytes([STX]) + payload + cs_hex.encode("ascii") + bytes([ETX])


@dataclass
class ParsedFrame:
    adr: str
    cmd: str
    """Echoed command code, or 'NA' on error."""
    data: str
    """Everything after CMD and before CS, as an ASCII string (hex-encoded
    binary fields, or raw text for string fields)."""


def decode_frame(raw: bytes) -> ParsedFrame:
    """Parse and checksum-verify one complete response frame (STX..ETX
    inclusive). Raises SstProtFrameError on structural problems,
    SstProtNotAcknowledged if the device returned 'NA'.
    """
    if len(raw) < 8:
        raise SstProtFrameError(f"frame too short: {raw!r}")
    if raw[0] != STX:
        raise SstProtFrameError(f"missing STX: {raw!r}")
    if raw[-1] != ETX:
        raise SstProtFrameError(f"missing ETX: {raw!r}")

    body = raw[1:-1]
    payload, cs_hex = body[:-2], body[-2:]
    try:
        received_cs = int(cs_hex.decode("ascii"), 16)
    except ValueError as exc:
        raise SstProtFrameError(f"bad checksum field: {cs_hex!r}") from exc

    computed_cs = checksum(payload)
    if computed_cs != received_cs:
        raise SstProtFrameError(
            f"checksum mismatch: computed 0x{computed_cs:02X}, received 0x{received_cs:02X} in {raw!r}"
        )

    text = payload.decode("ascii")
    adr, len_hex, rest = text[0:2], text[2:4], text[4:]
    declared_len = int(len_hex, 16)
    if declared_len != len(rest):
        raise SstProtFrameError(f"LEN mismatch: declared {declared_len}, actual {len(rest)} in {raw!r}")

    cmd, data = rest[0:2], rest[2:]
    if cmd == "NA":
        error_code = int(data[0:2], 16) if len(data) >= 2 else 0xFF
        raise SstProtNotAcknowledged(error_code)

    return ParsedFrame(adr=adr, cmd=cmd, data=data)


# ---------------------------------------------------------------------------
# Fixed-width ASCII-hex integer encode/decode helpers
# ---------------------------------------------------------------------------

def enc_u8(v: int) -> str:
    return f"{v & 0xFF:02X}"


def enc_u16(v: int) -> str:
    return f"{v & 0xFFFF:04X}"


def enc_u32(v: int) -> str:
    return f"{v & 0xFFFFFFFF:08X}"


def dec_u8(s: str) -> int:
    return int(s, 16)


def dec_u16(s: str) -> int:
    return int(s, 16)


def dec_u32(s: str) -> int:
    return int(s, 16)


def dec_i8(s: str) -> int:
    v = int(s, 16)
    return v - 0x100 if v > 0x7F else v
