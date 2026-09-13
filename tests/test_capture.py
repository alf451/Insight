from pathlib import Path

from insight_probe.capture import append_capture, capture_filename, read_capture, write_capture
from insight_probe.models import MessageRecord


def sample_messages():
    return [
        MessageRecord(
            timestamp="2026-01-01T00:00:00+00:00",
            topic="md/01/status",
            qos=0,
            retain=False,
            payload='{"a": 1}',
        ),
        MessageRecord(
            timestamp="2026-01-01T00:00:01+00:00",
            topic="md/01/status",
            qos=1,
            retain=True,
            payload="not json",
        ),
    ]


def test_capture_filename_format():
    from datetime import datetime, timezone

    name = capture_filename(datetime(2026, 3, 4, 5, 6, 7, tzinfo=timezone.utc))
    assert name == "capture_20260304_050607.jsonl"


def test_write_and_read_capture_roundtrip(tmp_path: Path):
    path = tmp_path / "capture_test.jsonl"
    messages = sample_messages()
    write_capture(path, messages)

    read_back = list(read_capture(path))
    assert len(read_back) == 2
    assert read_back[0].topic == "md/01/status"
    assert read_back[0].payload == '{"a": 1}'
    assert read_back[1].retain is True
    assert read_back[1].payload == "not json"  # original payload never altered


def test_append_capture_adds_lines(tmp_path: Path):
    path = tmp_path / "capture_append.jsonl"
    msgs = sample_messages()
    append_capture(path, msgs[0])
    append_capture(path, msgs[1])

    read_back = list(read_capture(path))
    assert len(read_back) == 2
