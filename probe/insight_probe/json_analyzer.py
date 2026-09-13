"""Recursive JSON payload analysis (spec sections 8 and 9).

Pure functions, no I/O — this is what the unit tests in tests/test_json_analyzer.py
exercise directly.

IMPORTANT: this module NEVER assumes a field named "sensitivity" (or any other
Sesotec-specific name) is authoritative. It only flags SEMANTICALLY PLAUSIBLE
candidates for the human to confirm. See spec section 9.
"""
from __future__ import annotations

import json
from typing import Any, Iterator, Optional

# Keywords used to flag a field as a POSSIBLE sensitivity candidate.
# This list is intentionally broad and language-mixed (EN/IT) because we do
# not know the real Sesotec naming yet. Matching is substring, case-insensitive,
# against the last path segment.
SENSITIVITY_KEYWORDS = [
    "sensitivity",
    "sensibility",
    "sensibilita",
    "threshold",
    "detection",
    "fe",
    "nonfe",
    "non_fe",
    "stainless",
    "inox",
    "metal",
    "parameter",
    "recipe",
    "program",
]


def infer_type(value: Any) -> str:
    """Map a Python JSON-decoded value to a simple type label."""
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"
    return "unknown"


def try_parse_json(payload: str) -> Optional[Any]:
    """Return the decoded JSON value, or None if payload is not valid JSON.

    Never raises — a malformed payload must not crash the Probe
    (spec section 53: "non perde il processo se arriva un payload malformato").
    """
    try:
        return json.loads(payload)
    except (json.JSONDecodeError, TypeError, ValueError):
        return None


def flatten_json(value: Any, prefix: str = "$") -> Iterator[tuple[str, Any]]:
    """Recursively walk a decoded JSON value, yielding (json_path, leaf_value)
    for every scalar leaf. Objects and arrays are recursed into; empty
    objects/arrays are yielded as-is (no scalar leaves inside them).

    JSON path syntax: $.a.b, $.a[0].b — matches the examples in spec section 8.
    """
    if isinstance(value, dict):
        if not value:
            yield prefix, value
            return
        for k, v in value.items():
            yield from flatten_json(v, f"{prefix}.{k}")
    elif isinstance(value, list):
        if not value:
            yield prefix, value
            return
        for i, v in enumerate(value):
            yield from flatten_json(v, f"{prefix}[{i}]")
    else:
        yield prefix, value


def is_sensitivity_candidate(json_path: str) -> bool:
    """Check the last path segment (ignoring array indices) against the
    keyword list. Returns True only for a POSSIBLE CANDIDATE — never a
    confirmed mapping (spec section 9)."""
    last_segment = json_path.rsplit(".", 1)[-1]
    # strip a trailing [n] if present
    if "[" in last_segment:
        last_segment = last_segment.split("[", 1)[0]
    last_segment_lower = last_segment.lower()
    return any(keyword in last_segment_lower for keyword in SENSITIVITY_KEYWORDS)


def analyze_payload(payload: str) -> dict:
    """Top-level analysis entry point for one message payload.

    Returns a dict:
        {
            "is_json": bool,
            "fields": [ {json_path, data_type, sample_value, is_sensitivity_candidate}, ... ]
        }
    If the payload is not JSON, fields is empty and is_json is False —
    the raw payload is still captured elsewhere untouched.
    """
    decoded = try_parse_json(payload)
    if decoded is None:
        return {"is_json": False, "fields": []}

    fields = []
    for json_path, leaf in flatten_json(decoded):
        fields.append(
            {
                "json_path": json_path,
                "data_type": infer_type(leaf),
                "sample_value": leaf,
                "is_sensitivity_candidate": is_sensitivity_candidate(json_path),
            }
        )
    return {"is_json": True, "fields": fields}
