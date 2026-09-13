"""Data models used by the Discovery Probe.

Kept dependency-free (stdlib dataclasses only) so they can be unit tested
without a Tkinter or MQTT runtime.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Optional


def utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class MessageRecord:
    """One captured MQTT message, per spec section 11 (CAPTURE).

    payload is stored as originally received (str, decoded utf-8 with
    'replace' on error) — never mutated.
    """

    timestamp: str
    topic: str
    qos: int
    retain: bool
    payload: str
    connection_id: Optional[str] = None
    client_id: Optional[str] = None
    payload_encoding: str = "utf-8"

    def to_json_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "topic": self.topic,
            "qos": self.qos,
            "retain": self.retain,
            "payload": self.payload,
            "connection_id": self.connection_id,
            "client_id": self.client_id,
            "payload_encoding": self.payload_encoding,
        }


@dataclass
class TopicStat:
    topic: str
    count: int = 0
    first_seen: Optional[str] = None
    last_seen: Optional[str] = None
    last_qos: Optional[int] = None
    last_retain: Optional[bool] = None
    last_payload_size: int = 0

    def record(self, msg: MessageRecord) -> None:
        self.count += 1
        if self.first_seen is None:
            self.first_seen = msg.timestamp
        self.last_seen = msg.timestamp
        self.last_qos = msg.qos
        self.last_retain = msg.retain
        self.last_payload_size = len(msg.payload.encode("utf-8", errors="replace"))


@dataclass
class FieldStat:
    """One JSON field discovered under a given topic (spec section 8)."""

    topic: str
    json_path: str
    data_type: str
    sample_value: Any
    occurrence_count: int = 1
    first_seen: Optional[str] = None
    last_seen: Optional[str] = None
    is_sensitivity_candidate: bool = False

    def key(self) -> tuple:
        return (self.topic, self.json_path)


@dataclass
class EventAnnotation:
    """Manual event marker correlating operator action to MQTT traffic
    (spec section 10)."""

    timestamp: str
    event_type: str
    description: str = ""

    def to_json_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "event_type": self.event_type,
            "description": self.description,
        }


EVENT_TYPES = [
    "START_PRODUCTION",
    "ARTICLE_CHANGED",
    "LOT_CHANGED",
    "SENSITIVITY_CHANGED",
    "METAL_TEST",
    "REJECT_TEST",
    "ALARM_TEST",
    "STOP_PRODUCTION",
    "OTHER",
]
