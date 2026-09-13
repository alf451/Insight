"""Device profile export/import (spec section 12).

Everything exported from the Probe is DISCOVERED data, never VERIFIED
(spec section 43) — access is always forced to READ and status is always
"discovered". Insight's importer is responsible for promoting fields to
VERIFIED/CONFIGURED after human confirmation.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, List, Optional

from .models import EventAnnotation, FieldStat, TopicStat, utcnow_iso

PROFILE_FORMAT = "insight-device-profile/v1"


def build_device_profile(
    *,
    device_name: Optional[str],
    model: Optional[str],
    firmware: Optional[str],
    broker: Optional[str],
    port: Optional[int],
    protocol: Optional[str],
    subscription: Optional[str],
    topics: List[TopicStat],
    fields: List[FieldStat],
    events: List[EventAnnotation],
    capture_file: Optional[str],
) -> dict:
    return {
        "format": PROFILE_FORMAT,
        "device": {
            "name": device_name,
            "manufacturer": "Sesotec",
            "model": model,
            "firmware": firmware,
        },
        "mqtt": {
            "broker": broker,
            "port": port,
            "protocol": protocol,
            "subscription": subscription,
        },
        "topics": [
            {
                "topic": t.topic,
                "count": t.count,
                "first_seen": t.first_seen,
                "last_seen": t.last_seen,
            }
            for t in topics
        ],
        "variables": [
            {
                "topic": f.topic,
                "json_path": f.json_path,
                "data_type": f.data_type,
                "sample_value": _json_safe(f.sample_value),
                "occurrence_count": f.occurrence_count,
                "first_seen": f.first_seen,
                "last_seen": f.last_seen,
                "sensitivity_candidate": f.is_sensitivity_candidate,
                "status": "DISCOVERED",
                "access": "READ",
            }
            for f in fields
        ],
        "events": [e.to_json_dict() for e in events],
        "discovery": {
            "created_at": utcnow_iso(),
            "capture_file": capture_file,
        },
    }


def _json_safe(value: Any) -> Any:
    try:
        json.dumps(value)
        return value
    except TypeError:
        return str(value)


def save_device_profile(path: Path, profile: dict) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(profile, fh, indent=2, ensure_ascii=False)


def load_device_profile(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)
