"""Insight Mock Metal Detector Simulator.

Publishes MQTT traffic that LOOKS like a metal detector so Insight and the
Discovery Probe can be developed/tested without real hardware (spec section
41).

IMPORTANT: the topic names and payload shape used here are entirely
made up for testing purposes. They are NOT derived from Sesotec
documentation and must never be treated as the real protocol (spec
section 2). Real mapping only comes from documentation, device
configuration, captured traffic, or on-site tests.
"""

__version__ = "0.1.0"
