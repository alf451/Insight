# Insight Mock Metal Detector Simulator

Publishes MQTT traffic that looks like a metal detector, so the Discovery
Probe and (later) Insight's MQTT adapter can be developed and tested without
real hardware (spec section 41).

**The topic names and JSON payload shape here are entirely made up for
testing.** They are not derived from Sesotec documentation and must never be
treated as ground truth. Real mapping only comes from documentation, actual
device configuration, captured traffic, or on-site tests — see
[`../docs/MQTT.md`](../docs/MQTT.md).

## Requirements

A running MQTT broker (e.g. local Mosquitto). See
[`../docker-compose.yml`](../docker-compose.yml) for a ready-to-use test
broker, or install Mosquitto directly.

## Run

Windows:

```bash
cd simulator
run_simulator.bat --broker localhost --port 1883
```

Manual / other platforms:

```bash
cd simulator
python -m venv .venv
.venv\Scripts\activate      # Windows
pip install -r requirements.txt
python -m insight_simulator --broker localhost --port 1883
```

## What it publishes

- `insight/sim/<device_id>/status` every `--interval` seconds: running
  state, current article/lot, sensitivity (fe/nonFe/stainless), and
  detection/reject/alarm counters.
- `insight/sim/<device_id>/event` on demand: `DETECTION`, `REJECT` (a
  detection with `rejected=true`... see payload), or `ALARM`.

## Interactive commands (typed at the running console)

```
start                     set running=true
stop                      set running=false
article <name>            change current article
lot <name>                change current lot
sensitivity fe <value>
sensitivity nonfe <value>
sensitivity stainless <value>
detect                    publish a DETECTION event
reject                    publish a DETECTION event with rejected=true
alarm [reason]            publish an ALARM event
quit
```

Use these while the Discovery Probe is connected and subscribed to `#` to
verify end-to-end that messages, JSON field discovery, and event
correlation all work before going to the client site.
