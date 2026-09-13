"""Capture file writer/reader — JSON Lines format (spec section 11).

One JSON object per line, one line per MQTT message. The original payload is
never altered.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator, List

from .models import MessageRecord


def capture_filename(now: datetime | None = None) -> str:
    now = now or datetime.now(timezone.utc)
    return f"capture_{now.strftime('%Y%m%d_%H%M%S')}.jsonl"


def write_capture(path: Path, messages: List[MessageRecord]) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        for msg in messages:
            fh.write(json.dumps(msg.to_json_dict(), ensure_ascii=False))
            fh.write("\n")


def append_capture(path: Path, msg: MessageRecord) -> None:
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(msg.to_json_dict(), ensure_ascii=False))
        fh.write("\n")


def read_capture(path: Path) -> Iterator[MessageRecord]:
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            data = json.loads(line)
            yield MessageRecord(
                timestamp=data["timestamp"],
                topic=data["topic"],
                qos=data["qos"],
                retain=data["retain"],
                payload=data["payload"],
                connection_id=data.get("connection_id"),
                client_id=data.get("client_id"),
                payload_encoding=data.get("payload_encoding", "utf-8"),
            )
