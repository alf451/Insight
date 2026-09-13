from pathlib import Path

from insight_probe.device_profile import build_device_profile, load_device_profile, save_device_profile
from insight_probe.models import EventAnnotation, FieldStat, TopicStat


def test_build_device_profile_marks_everything_discovered_read_only():
    topics = [TopicStat(topic="md/01/status", count=5, first_seen="t0", last_seen="t1")]
    fields = [
        FieldStat(
            topic="md/01/status",
            json_path="$.sensitivity.fe",
            data_type="number",
            sample_value=1.2,
            occurrence_count=5,
            first_seen="t0",
            last_seen="t1",
            is_sensitivity_candidate=True,
        )
    ]
    events = [EventAnnotation(timestamp="t0", event_type="SENSITIVITY_CHANGED", description="")]

    profile = build_device_profile(
        device_name=None,
        model=None,
        firmware=None,
        broker="localhost",
        port=1883,
        protocol="3.1.1",
        subscription="#",
        topics=topics,
        fields=fields,
        events=events,
        capture_file="capture_x.jsonl",
    )

    assert profile["format"] == "insight-device-profile/v1"
    assert profile["device"]["manufacturer"] == "Sesotec"
    assert profile["device"]["model"] is None
    assert len(profile["variables"]) == 1
    var = profile["variables"][0]
    assert var["status"] == "DISCOVERED"
    assert var["access"] == "READ"
    assert var["sensitivity_candidate"] is True
    assert len(profile["events"]) == 1
    assert len(profile["topics"]) == 1


def test_save_and_load_device_profile_roundtrip(tmp_path: Path):
    profile = build_device_profile(
        device_name="MD01",
        model=None,
        firmware=None,
        broker="localhost",
        port=1883,
        protocol="5",
        subscription="#",
        topics=[],
        fields=[],
        events=[],
        capture_file=None,
    )
    path = tmp_path / "device_profile.json"
    save_device_profile(path, profile)
    loaded = load_device_profile(path)
    assert loaded == profile
