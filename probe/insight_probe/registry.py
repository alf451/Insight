"""In-memory aggregation of everything observed during a discovery session:
per-topic stats and per-field stats. Pure logic, no I/O, no MQTT, no Tkinter —
so it is directly unit-testable.
"""
from __future__ import annotations

from typing import Dict, List, Optional

from .json_analyzer import analyze_payload
from .models import EventAnnotation, FieldStat, MessageRecord, TopicStat, utcnow_iso


class DiscoveryRegistry:
    def __init__(self) -> None:
        self.messages: List[MessageRecord] = []
        self.topics: Dict[str, TopicStat] = {}
        self.fields: Dict[tuple, FieldStat] = {}
        self.events: List[EventAnnotation] = []

    def reset(self) -> None:
        self.messages.clear()
        self.topics.clear()
        self.fields.clear()
        self.events.clear()

    def ingest(self, msg: MessageRecord) -> dict:
        """Record one message and update all derived stats.

        Returns the JSON analysis result for this message (useful for live
        GUI display) — never raises, even on malformed payloads.
        """
        self.messages.append(msg)

        topic_stat = self.topics.setdefault(msg.topic, TopicStat(topic=msg.topic))
        topic_stat.record(msg)

        analysis = analyze_payload(msg.payload)
        if analysis["is_json"]:
            for f in analysis["fields"]:
                key = (msg.topic, f["json_path"])
                existing = self.fields.get(key)
                if existing is None:
                    self.fields[key] = FieldStat(
                        topic=msg.topic,
                        json_path=f["json_path"],
                        data_type=f["data_type"],
                        sample_value=f["sample_value"],
                        occurrence_count=1,
                        first_seen=msg.timestamp,
                        last_seen=msg.timestamp,
                        is_sensitivity_candidate=f["is_sensitivity_candidate"],
                    )
                else:
                    existing.occurrence_count += 1
                    existing.last_seen = msg.timestamp
                    existing.sample_value = f["sample_value"]
                    existing.data_type = f["data_type"]

        return analysis

    def mark_event(self, event_type: str, description: str = "") -> EventAnnotation:
        ev = EventAnnotation(timestamp=utcnow_iso(), event_type=event_type, description=description)
        self.events.append(ev)
        return ev

    def sensitivity_candidates(self) -> List[FieldStat]:
        return [f for f in self.fields.values() if f.is_sensitivity_candidate]

    def topic_list(self) -> List[TopicStat]:
        return sorted(self.topics.values(), key=lambda t: t.topic)

    def field_list(self) -> List[FieldStat]:
        return sorted(self.fields.values(), key=lambda f: (f.topic, f.json_path))
