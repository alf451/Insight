"""Pure state/payload logic for the mock metal detector — no MQTT, no I/O,
so it is directly unit-testable. Networking lives in main.py.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class MockMetalDetector:
    device_id: str = "MD-SIM-01"
    running: bool = False
    article: str = "UNKNOWN"
    lot: str = "UNKNOWN"
    sensitivity_fe: float = 1.2
    sensitivity_nonfe: float = 1.5
    sensitivity_stainless: float = 2.0
    detections: int = 0
    rejects: int = 0
    alarms: int = 0

    def start(self) -> None:
        self.running = True

    def stop(self) -> None:
        self.running = False

    def set_article(self, article: str) -> None:
        self.article = article

    def set_lot(self, lot: str) -> None:
        self.lot = lot

    def set_sensitivity(self, parameter: str, value: float) -> None:
        parameter = parameter.lower()
        if parameter == "fe":
            self.sensitivity_fe = value
        elif parameter in ("nonfe", "non_fe"):
            self.sensitivity_nonfe = value
        elif parameter == "stainless":
            self.sensitivity_stainless = value
        else:
            raise ValueError(f"Unknown sensitivity parameter: {parameter}")

    def trigger_detection(self, rejected: bool = False) -> dict:
        self.detections += 1
        if rejected:
            self.rejects += 1
        return self.build_event_payload("REJECT" if rejected else "DETECTION")

    def trigger_alarm(self, reason: str = "TEST") -> dict:
        self.alarms += 1
        return self.build_event_payload("ALARM", details={"reason": reason})

    def build_status_payload(self) -> dict:
        return {
            "device_id": self.device_id,
            "timestamp": _now_iso(),
            "status": {"running": self.running},
            "product": {"article": self.article, "lot": self.lot},
            "sensitivity": {
                "fe": self.sensitivity_fe,
                "nonFe": self.sensitivity_nonfe,
                "stainless": self.sensitivity_stainless,
            },
            "counters": {
                "detections": self.detections,
                "rejects": self.rejects,
                "alarms": self.alarms,
            },
        }

    def build_event_payload(self, event: str, details: Optional[dict] = None) -> dict:
        return {
            "device_id": self.device_id,
            "timestamp": _now_iso(),
            "event": event,
            "details": details or {},
        }
