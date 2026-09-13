import json

from insight_probe.models import MessageRecord
from insight_probe.registry import DiscoveryRegistry


def make_message(topic, payload_dict, timestamp="2026-01-01T00:00:00+00:00"):
    return MessageRecord(
        timestamp=timestamp,
        topic=topic,
        qos=0,
        retain=False,
        payload=json.dumps(payload_dict),
    )


def test_ingest_updates_topic_and_field_stats():
    registry = DiscoveryRegistry()
    registry.ingest(make_message("md/01/status", {"sensitivity": {"fe": 1.2}}))
    registry.ingest(
        make_message("md/01/status", {"sensitivity": {"fe": 1.3}}, timestamp="2026-01-01T00:00:05+00:00")
    )

    topics = registry.topic_list()
    assert len(topics) == 1
    assert topics[0].count == 2
    assert topics[0].first_seen == "2026-01-01T00:00:00+00:00"
    assert topics[0].last_seen == "2026-01-01T00:00:05+00:00"

    fields = registry.field_list()
    fe_field = next(f for f in fields if f.json_path == "$.sensitivity.fe")
    assert fe_field.occurrence_count == 2
    assert fe_field.sample_value == 1.3  # updated to latest
    assert fe_field.is_sensitivity_candidate is True


def test_ingest_malformed_payload_does_not_raise_and_still_counts_topic():
    registry = DiscoveryRegistry()
    from insight_probe.models import MessageRecord as MR

    msg = MR(timestamp="2026-01-01T00:00:00+00:00", topic="md/01/raw", qos=0, retain=False, payload="{{bad")
    analysis = registry.ingest(msg)
    assert analysis["is_json"] is False
    assert registry.topic_list()[0].count == 1
    assert registry.field_list() == []


def test_sensitivity_candidates_filters_correctly():
    registry = DiscoveryRegistry()
    registry.ingest(make_message("md/01/status", {"sensitivity": {"fe": 1.2}, "product": "ABC"}))
    candidates = registry.sensitivity_candidates()
    assert len(candidates) == 1
    assert candidates[0].json_path == "$.sensitivity.fe"


def test_mark_event_appends_to_events():
    registry = DiscoveryRegistry()
    ev = registry.mark_event("SENSITIVITY_CHANGED", "fe set to 1.3")
    assert registry.events == [ev]
    assert ev.event_type == "SENSITIVITY_CHANGED"


def test_reset_clears_everything():
    registry = DiscoveryRegistry()
    registry.ingest(make_message("md/01/status", {"a": 1}))
    registry.mark_event("OTHER")
    registry.reset()
    assert registry.messages == []
    assert registry.topics == {}
    assert registry.fields == {}
    assert registry.events == []
