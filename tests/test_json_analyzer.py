import json

from insight_probe.json_analyzer import (
    analyze_payload,
    flatten_json,
    infer_type,
    is_sensitivity_candidate,
    try_parse_json,
)


def test_infer_type_basic():
    assert infer_type(True) == "boolean"
    assert infer_type(1) == "integer"
    assert infer_type(1.5) == "number"
    assert infer_type("x") == "string"
    assert infer_type(None) == "null"
    assert infer_type([1, 2]) == "array"
    assert infer_type({"a": 1}) == "object"


def test_try_parse_json_malformed_does_not_raise():
    assert try_parse_json("{not valid json") is None
    assert try_parse_json("") is None
    assert try_parse_json("plain text payload") is None


def test_try_parse_json_valid():
    assert try_parse_json('{"a": 1}') == {"a": 1}


def test_flatten_json_nested_example_from_spec():
    payload = {
        "status": {"running": True},
        "product": "ABC123",
        "sensitivity": {"fe": 1.2, "nonFe": 1.5},
    }
    flattened = dict(flatten_json(payload))
    assert flattened["$.status.running"] is True
    assert flattened["$.product"] == "ABC123"
    assert flattened["$.sensitivity.fe"] == 1.2
    assert flattened["$.sensitivity.nonFe"] == 1.5


def test_flatten_json_arrays():
    payload = {"items": [{"id": 1}, {"id": 2}]}
    flattened = dict(flatten_json(payload))
    assert flattened["$.items[0].id"] == 1
    assert flattened["$.items[1].id"] == 2


def test_flatten_json_empty_containers():
    payload = {"empty_obj": {}, "empty_list": []}
    flattened = dict(flatten_json(payload))
    assert flattened["$.empty_obj"] == {}
    assert flattened["$.empty_list"] == []


def test_sensitivity_candidate_keywords():
    assert is_sensitivity_candidate("$.sensitivity.fe")
    assert is_sensitivity_candidate("$.params.threshold")
    assert is_sensitivity_candidate("$.recipe")
    assert not is_sensitivity_candidate("$.status.running")
    assert not is_sensitivity_candidate("$.product")


def test_analyze_payload_json():
    payload = json.dumps({"status": {"running": True}, "sensitivity": {"fe": 1.2}})
    result = analyze_payload(payload)
    assert result["is_json"] is True
    paths = {f["json_path"] for f in result["fields"]}
    assert "$.status.running" in paths
    assert "$.sensitivity.fe" in paths
    fe_field = next(f for f in result["fields"] if f["json_path"] == "$.sensitivity.fe")
    assert fe_field["is_sensitivity_candidate"] is True


def test_analyze_payload_non_json_does_not_raise():
    result = analyze_payload("not json at all {{{")
    assert result["is_json"] is False
    assert result["fields"] == []
