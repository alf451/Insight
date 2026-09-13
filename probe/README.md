# Insight MQTT Discovery Probe

Standalone, **read-only** Windows tool used at the client site to discover the
real MQTT protocol spoken by a Sesotec metal detector — before any mapping is
hardcoded into Insight. See [`../docs/DISCOVERY_PROBE.md`](../docs/DISCOVERY_PROBE.md)
for the full commissioning workflow.

**This tool never publishes/writes to the broker.** There is no publish
method anywhere in the code (see `insight_probe/mqtt_client.py`).

## Requirements

- Windows 10/11
- Python 3.10+ on PATH (Tkinter ships with the standard CPython Windows installer)
- Network access to the client's MQTT broker

## Quick start (Windows)

Double-click `run_probe.bat`, or from a terminal:

```bash
cd probe
run_probe.bat
```

The script creates a local virtual environment, installs dependencies
(`paho-mqtt` only), and launches the GUI.

## Manual start

```bash
cd probe
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m insight_probe
```

## Using the Probe

1. Fill in **Broker**, **Port**, **MQTT Version** (3.1.1 or 5), and
   credentials/TLS if required.
2. Leave **Subscription Topic** as `#` to see everything, or narrow it once
   you know the device's topic prefix.
3. Click **CONNECT**.
4. Watch the **Messages** tab for traffic; click a row to see the raw payload
   and, if it is JSON, a pretty-printed view.
5. The **Topics** tab summarizes message counts/timing per topic.
6. The **Fields / Sensitivity Candidates** tab lists every JSON field seen
   across all messages, with fields matching known sensitivity-related
   keywords highlighted as **POSSIBLE CANDIDATE** — never a confirmed
   mapping. Confirm the real field with the customer/documentation before
   using it anywhere else.
7. Use **MARK EVENT** while performing controlled actions on the metal
   detector (article change, sensitivity change, test reject, etc.) so the
   traffic can later be correlated to what actually happened.
8. **START CAPTURE** begins streaming every message to a timestamped
   `.jsonl` file under `probe/captures/` as it arrives (safe against a crash
   mid-session). **STOP CAPTURE** stops the stream (the file is kept).
   **SAVE CAPTURE** lets you save a snapshot of everything seen so far to a
   file of your choosing, independent of the streaming capture.
9. **EXPORT DEVICE PROFILE** writes a `device_profile.json` (spec
   `insight-device-profile/v1`) that Insight can later import. Every
   variable in it is marked `status: DISCOVERED, access: READ` — it must be
   confirmed by a human before Insight treats it as VERIFIED/CONFIGURED.

## Testing without a real metal detector

Use the `simulator/` project (see `../simulator/README.md`) together with a
local Mosquitto broker to generate MQTT traffic and exercise the Probe
end-to-end before going to the client site. **The simulator's payload shape
is entirely made up for testing purposes — it is not derived from any real
Sesotec documentation.**
