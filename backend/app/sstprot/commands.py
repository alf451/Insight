"""High-level SSTProt commands, matching the shape of `read_device_data()` /
`read_logbook()` described in `sstprot_function_final_report.md` (a prior,
real, working integration against a GeniusOne device at 192.168.1.125).

Every field name and byte layout below is taken from SSTProt V1.54.pdf
(official Sesotec documentation) and cross-checked against the report's
real captured example output — see docs/SSTPROT.md for the page-by-page
mapping and the one place a field layout could not be pinned down with
full certainty (the "LE" logbook entry trailing bytes).

WRITE commands (`set_system_time`, `set_product_data`) are implemented
because the byte layout IS documented officially — but neither has been
exercised against a real device in this session (no hardware available).
Treat them as "implemented per spec, field-unverified" until tried
against a real GeniusOne, ideally on a non-critical product slot first.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from .connector import SstProtConnector
from .frame import (
    SstProtNotAcknowledged,
    dec_u16,
    dec_u32,
    dec_u8,
    enc_u16,
    enc_u32,
    enc_u8,
)
from .tables import (
    DEVICE_TYPE_NAMES,
    LOGBOOK_ENTRY_CODES,
    MAIN_STATE_NAMES,
    decode_error_status,
    decode_flags,
    describe_entry_code,
)


def _chunks(s: str, width: int) -> list[str]:
    return [s[i : i + width] for i in range(0, len(s), width)]


def _decode_fixed_string(s: str) -> str:
    """Device name/line name fields are fixed-width ASCII, padded with
    trailing NUL or spaces — strip both."""
    return s.split("\x00", 1)[0].strip()


# ---------------------------------------------------------------------------
# Device information
# ---------------------------------------------------------------------------


def get_device_address(conn: SstProtConnector) -> int:
    resp = conn.send_command("DA")
    return dec_u8(resp.data)


def get_device_type(conn: SstProtConnector) -> tuple[int, str]:
    resp = conn.send_command("DT")
    code = dec_u8(resp.data)
    return code, DEVICE_TYPE_NAMES.get(code, f"UNKNOWN (0x{code:02X})")


def get_device_name(conn: SstProtConnector) -> str:
    resp = conn.send_command("DN")
    return _decode_fixed_string(resp.data)


def get_line_name(conn: SstProtConnector) -> str:
    resp = conn.send_command("DL")
    return _decode_fixed_string(resp.data)


def get_mac_address(conn: SstProtConnector) -> str:
    resp = conn.send_command("DM")
    return resp.data.strip()


def get_device_info(conn: SstProtConnector) -> dict:
    address = get_device_address(conn)
    device_type, device_type_name = get_device_type(conn)
    return {
        "address": address,
        "device_type": device_type,
        "device_type_name": device_type_name,
        "device_name": get_device_name(conn),
        "line_name": get_line_name(conn),
        "mac_address": get_mac_address(conn),
    }


# ---------------------------------------------------------------------------
# System time
# ---------------------------------------------------------------------------


def get_system_time(conn: SstProtConnector) -> dict:
    resp = conn.send_command("TT")
    y, mo, d, h, mi, s = (dec_u8(c) for c in _chunks(resp.data, 2))
    return {"year": 2000 + y, "month": mo, "day": d, "hour": h, "minute": mi, "second": s}


def set_system_time(conn: SstProtConnector, dt: Optional[datetime] = None) -> bool:
    """WRITE. Sets the device's system clock. Documented per SSTProt "TT"
    set command (page 11). Low risk relative to product/sensitivity writes,
    but not exercised against real hardware in this session."""
    dt = dt or datetime.now()
    params = "".join(
        enc_u8(v) for v in (dt.year % 100, dt.month, dt.day, dt.hour, dt.minute, dt.second)
    )
    resp = conn.send_command("TT", params)
    return dec_u8(resp.data) == 0x00


# ---------------------------------------------------------------------------
# System status
# ---------------------------------------------------------------------------


def get_system_status(conn: SstProtConnector) -> dict:
    resp = conn.send_command("SQ")
    parts = resp.data
    main_state = dec_u8(parts[0:2])
    sub_state = dec_u8(parts[2:4])
    metal_signal = dec_u16(parts[4:8])
    error_status = dec_u32(parts[8:16])
    flags = dec_u8(parts[16:18])
    counter = dec_u16(parts[18:22])
    product_par_changed = dec_u8(parts[22:24]) if len(parts) >= 24 else None
    system_par_changed = dec_u8(parts[24:26]) if len(parts) >= 26 else None
    return {
        "main_state": main_state,
        "main_state_name": MAIN_STATE_NAMES.get(main_state, f"UNKNOWN (0x{main_state:02X})"),
        "sub_state": sub_state,
        "metal_signal": metal_signal,
        "error_status": error_status,
        "flags": flags,
        "counter": counter,
        "active_errors": decode_error_status(error_status),
        "active_flags": decode_flags(flags),
        "product_par_changed": product_par_changed,
        "system_par_changed": system_par_changed,
    }


# ---------------------------------------------------------------------------
# Product data
# ---------------------------------------------------------------------------


def get_current_product_number(conn: SstProtConnector) -> int:
    resp = conn.send_command("PJ")
    return dec_u16(resp.data)


def get_product_data(conn: SstProtConnector, product_number: int) -> dict:
    resp = conn.send_command("PD", enc_u16(product_number))
    parts = resp.data
    sensitivity = dec_u16(parts[0:4])
    product_angle = dec_u16(parts[4:8])
    frequency_index = dec_u8(parts[8:10])
    blanking = dec_u8(parts[10:12])
    options = dec_u8(parts[12:14])
    conveyor_speed = dec_u16(parts[14:18])
    gain = dec_u8(parts[18:20])
    threshold = dec_u8(parts[20:22])
    return {
        "product_number": product_number,
        "sensitivity": sensitivity,
        "product_angle": product_angle,
        "frequency_index": frequency_index,
        "blanking": blanking,
        "options": options,
        "conveyor_speed": conveyor_speed,
        "gain": gain,
        "threshold": threshold,
    }


def set_product_data(
    conn: SstProtConnector,
    product_number: int,
    sensitivity: int,
    product_angle: int,
    frequency_index: int,
    blanking: int,
    options: int,
    conveyor_speed: int,
    gain: int,
    threshold: int,
) -> bool:
    """WRITE. Sets sensitivity and the other product parameters for one
    product slot. Documented per SSTProt "PD" set command (page 33).

    sensitivity: 1-100 [%]. product_angle: 0-1800 [1/10 deg] (1801=no angle).
    conveyor_speed: 10-30000 [mm/s]. gain: 1-8. threshold: 20-120.

    NOT exercised against real hardware in this session — verify against a
    non-critical product slot before relying on this in production. See
    docs/SSTPROT.md.
    """
    params = (
        enc_u16(product_number)
        + enc_u16(sensitivity)
        + enc_u16(product_angle)
        + enc_u8(frequency_index)
        + enc_u8(blanking)
        + enc_u8(options)
        + enc_u16(conveyor_speed)
        + enc_u8(gain)
        + enc_u8(threshold)
    )
    resp = conn.send_command("PD", params)
    return dec_u8(resp.data) == 0x00


# ---------------------------------------------------------------------------
# Counters
# ---------------------------------------------------------------------------

COUNTER_GLOBAL = 0x00
COUNTER_PRODUCT = 0x01
COUNTER_BATCH = 0x02
COUNTER_USER = 0x03


def get_counters(conn: SstProtConnector, which: int = COUNTER_GLOBAL) -> dict:
    resp = conn.send_command("SL", enc_u8(which))
    parts = resp.data
    return {
        "counter_type": {0: "global", 1: "product", 2: "batch", 3: "user"}.get(which, str(which)),
        "error_counter": dec_u32(parts[0:8]),
        "metal_counter": dec_u32(parts[8:16]),
        "product_counter": dec_u32(parts[16:24]),
    }


# ---------------------------------------------------------------------------
# Logbook
# ---------------------------------------------------------------------------


def get_logbook_max(conn: SstProtConnector) -> int:
    resp = conn.send_command("LI")
    return dec_u16(resp.data)


def get_logbook_count(conn: SstProtConnector) -> int:
    resp = conn.send_command("LN")
    return dec_u16(resp.data)


def clear_logbook(conn: SstProtConnector) -> bool:
    """WRITE, DESTRUCTIVE. Permanently clears the logbook. If the device
    requires a higher access level it raises SstProtNotAcknowledged with
    error_name == "ACCESS LEVEL" — this function does NOT attempt to guess
    a login code (see docs/SSTPROT.md on the TA command's code-generation
    scheme, which requires a code from Sesotec support)."""
    resp = conn.send_command("LC")
    return dec_u8(resp.data) == 0x00


def set_access_level(conn: SstProtConnector, code: int, level: int) -> bool:
    """WRITE. Direct wrapper of the "TA" command — pass an already-known
    login code (see docs/SSTPROT.md; this module does not compute one)."""
    params = enc_u16(code) + enc_u8(level)
    resp = conn.send_command("TA", params)
    return dec_u8(resp.data) == 0x00


@dataclass
class LogbookEntry:
    absolute_number: Optional[int]
    timestamp: str
    entry_code: int
    entry_code_description: str
    decoded: dict = field(default_factory=dict)
    raw_tail_hex: str = ""


def get_logbook_entry(conn: SstProtConnector, position: int = 0xFFFFFFFF) -> LogbookEntry:
    """Read one logbook entry via "LE" (position 0xFFFFFFFF = latest).

    KNOWN AMBIGUITY: the PDF's documented response length (0x2A = 42 ASCII
    chars of data) doesn't cleanly match summing its own field list — see
    docs/SSTPROT.md. This parses the unambiguous prefix (entry code +
    timestamp + 4 x u16 params, all arithmetic-verified) and then treats
    the first 8 remaining chars as the u32 "absolute number" (if present),
    keeping anything past that as unparsed `raw_tail_hex` rather than
    guessing its meaning.
    """
    resp = conn.send_command("LE", enc_u32(position))
    data = resp.data
    entry_code = dec_u8(data[0:2])
    y, mo, d, h, mi, s = (dec_u8(c) for c in _chunks(data[2:14], 2))
    timestamp = f"{2000+y:04d}-{mo:02d}-{d:02d} {h:02d}:{mi:02d}:{s:02d}"

    param_hex = data[14:30]
    params = {i + 1: dec_u16(c) for i, c in enumerate(_chunks(param_hex, 4)) if c}

    tail = data[30:]
    absolute_number = dec_u32(tail[0:8]) if len(tail) >= 8 else None
    raw_tail_hex = tail[8:]

    label, meanings = LOGBOOK_ENTRY_CODES.get(entry_code, (describe_entry_code(entry_code), {}))
    decoded = {meanings[i]: params[i] for i in meanings if i in params}

    return LogbookEntry(
        absolute_number=absolute_number,
        timestamp=timestamp,
        entry_code=entry_code,
        entry_code_description=label,
        decoded=decoded,
        raw_tail_hex=raw_tail_hex,
    )


def read_logbook(conn: SstProtConnector, max_entries: int = 0) -> list[dict]:
    """Read the logbook backwards (latest first), matching the report's
    `read_logbook()` behaviour. Entries that fail to parse are skipped
    (matching the report's "entries with 'error' are discarded" note)
    rather than aborting the whole read.
    """
    count_available = get_logbook_count(conn)
    limit = count_available if max_entries in (0, None) else min(max_entries, count_available)

    results: list[dict] = []
    position = 0xFFFFFFFF
    for _ in range(limit):
        try:
            entry = get_logbook_entry(conn, position)
        except SstProtNotAcknowledged:
            break
        results.append(
            {
                "absolute_number": entry.absolute_number,
                "timestamp": entry.timestamp,
                "entry_code": entry.entry_code,
                "entry_code_description": entry.entry_code_description,
                "decoded": entry.decoded,
            }
        )
        if entry.absolute_number is None or entry.absolute_number <= 1:
            break
        position = entry.absolute_number - 1
    return results


# ---------------------------------------------------------------------------
# Aggregate read matching sstprot_function_final_report.md's read_device_data()
# ---------------------------------------------------------------------------


def read_device_data(conn: SstProtConnector) -> dict:
    current_product_number = get_current_product_number(conn)
    return {
        "device_info": get_device_info(conn),
        "system_time": get_system_time(conn),
        "system_status": get_system_status(conn),
        "current_product_number": current_product_number,
        "product_data": get_product_data(conn, current_product_number),
        "global_counters": get_counters(conn, COUNTER_GLOBAL),
        "logbook_max": get_logbook_max(conn),
        "logbook_count": get_logbook_count(conn),
    }
