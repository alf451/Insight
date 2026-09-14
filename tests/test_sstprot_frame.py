"""Verified byte-for-byte against the two worked examples in the official
SSTProt V1.54.pdf (section "Telegramm and Protocol Structure")."""
import pytest

from app.sstprot.frame import (
    STX,
    ETX,
    SstProtFrameError,
    SstProtNotAcknowledged,
    checksum,
    decode_frame,
    dec_u16,
    dec_u32,
    dec_u8,
    enc_u16,
    enc_u32,
    enc_u8,
    encode_frame,
)


def test_encode_clear_logbook_matches_official_example():
    frame = encode_frame("11", "LC")
    assert frame == bytes([STX]) + b"1102LC53" + bytes([ETX])


def test_encode_get_logbook_count_matches_official_example():
    frame = encode_frame("11", "LN")
    assert frame == bytes([STX]) + b"1102LN5E" + bytes([ETX])


def test_decode_clear_logbook_response():
    raw = bytes([STX]) + b"1104LC00B5" + bytes([ETX])
    parsed = decode_frame(raw)
    assert parsed.adr == "11"
    assert parsed.cmd == "LC"
    assert parsed.data == "00"


def test_decode_get_logbook_count_response():
    raw = bytes([STX]) + b"1106LN001225" + bytes([ETX])
    parsed = decode_frame(raw)
    assert parsed.cmd == "LN"
    assert dec_u16(parsed.data) == 0x0012 == 18


def test_checksum_special_case_cr_is_inverted():
    # contrived payload whose plain 8-bit sum is exactly 0x0D
    payload = bytes([0x0D])
    assert checksum(payload) == (~0x0D) & 0xFF


def test_decode_frame_rejects_bad_checksum():
    raw = bytes([STX]) + b"1104LC00FF" + bytes([ETX])
    with pytest.raises(SstProtFrameError):
        decode_frame(raw)


def test_decode_frame_rejects_missing_stx_or_etx():
    with pytest.raises(SstProtFrameError):
        decode_frame(b"1104LC00B5" + bytes([ETX]))
    with pytest.raises(SstProtFrameError):
        decode_frame(bytes([STX]) + b"1104LC00B5")


def test_decode_frame_raises_not_acknowledged():
    # NA + error code 0x09 (ACCESS LEVEL), checksum computed for real
    from app.sstprot.frame import checksum as cs

    payload = b"1104NA09"
    c = cs(payload)
    raw = bytes([STX]) + payload + f"{c:02X}".encode() + bytes([ETX])
    with pytest.raises(SstProtNotAcknowledged) as exc_info:
        decode_frame(raw)
    assert exc_info.value.error_code == 0x09
    assert exc_info.value.error_name == "ACCESS LEVEL"


@pytest.mark.parametrize(
    "enc,dec,value",
    [
        (enc_u8, dec_u8, 0x00),
        (enc_u8, dec_u8, 0xFF),
        (enc_u16, dec_u16, 0x1234),
        (enc_u32, dec_u32, 0xDEADBEEF),
    ],
)
def test_integer_roundtrip(enc, dec, value):
    assert dec(enc(value)) == value


def test_encode_frame_rejects_oversized_body():
    with pytest.raises(ValueError):
        encode_frame("11", "PD", "0" * 200)
