import pytest

from insight_simulator.mock_metal_detector import MockMetalDetector


def test_initial_state_is_stopped_and_unknown():
    md = MockMetalDetector()
    assert md.running is False
    assert md.article == "UNKNOWN"
    assert md.lot == "UNKNOWN"


def test_start_stop():
    md = MockMetalDetector()
    md.start()
    assert md.running is True
    md.stop()
    assert md.running is False


def test_set_article_and_lot():
    md = MockMetalDetector()
    md.set_article("ABC123")
    md.set_lot("L001")
    assert md.article == "ABC123"
    assert md.lot == "L001"


def test_set_sensitivity_valid_parameters():
    md = MockMetalDetector()
    md.set_sensitivity("fe", 1.4)
    md.set_sensitivity("nonfe", 1.6)
    md.set_sensitivity("stainless", 2.2)
    assert md.sensitivity_fe == 1.4
    assert md.sensitivity_nonfe == 1.6
    assert md.sensitivity_stainless == 2.2


def test_set_sensitivity_invalid_parameter_raises():
    md = MockMetalDetector()
    with pytest.raises(ValueError):
        md.set_sensitivity("bogus", 1.0)


def test_trigger_detection_increments_counters():
    md = MockMetalDetector()
    payload = md.trigger_detection(rejected=False)
    assert md.detections == 1
    assert md.rejects == 0
    assert payload["event"] == "DETECTION"

    payload = md.trigger_detection(rejected=True)
    assert md.detections == 2
    assert md.rejects == 1
    assert payload["event"] == "REJECT"


def test_trigger_alarm_increments_counter_and_includes_reason():
    md = MockMetalDetector()
    payload = md.trigger_alarm("METAL_TEST")
    assert md.alarms == 1
    assert payload["event"] == "ALARM"
    assert payload["details"]["reason"] == "METAL_TEST"


def test_build_status_payload_shape():
    md = MockMetalDetector(device_id="MD-X")
    md.set_article("A1")
    md.set_lot("L1")
    payload = md.build_status_payload()
    assert payload["device_id"] == "MD-X"
    assert payload["status"]["running"] is False
    assert payload["product"]["article"] == "A1"
    assert payload["product"]["lot"] == "L1"
    assert "fe" in payload["sensitivity"]
