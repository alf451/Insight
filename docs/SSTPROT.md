# SSTProt (Sesotec SST-Protocol) — GeniusOne integration

Status: **implemented and verified** (backend + simulator). This is the
first real, working protocol integration in Insight — built entirely from
official documentation, not MQTT (see "Relationship to the MQTT/Probe work"
below).

## Sources

1. `SSTProt V1.54.pdf` — official Sesotec protocol specification, provided
   by the user from `OneDrive/Omikron/Industria 4.0/90 Progetti Collegati/Metaldetector/`.
   82 pages, covers Genius/Genius+/GeniusOne/INTUITY/Raycon command sets.
2. `sstprot_function_final_report.md` — a report of a prior, real, working
   integration (`sstprot_function_final.py`) run against an actual
   GeniusOne device at `192.168.1.125` on 2026-05-19, provided by the user.
   The Python source file itself was not available in this session — only
   its documented behaviour and real captured output — but that output is
   what `backend/app/sstprot/` was cross-checked against (see "Verification"
   below).

Every field name, command code, and table value in `backend/app/sstprot/`
traces back to one of these two documents. Nothing was invented.

## Protocol basics (page 3-9 of the PDF)

Frame: `STX(0x02) ADR(2 ascii-hex) LEN(2 ascii-hex) CMD(2 ascii) [params] CS(2 ascii-hex) ETX(0x03)`.
LEN = ASCII length of `CMD+params`. CS = 8-bit sum of the ASCII bytes of
`ADR+LEN+CMD+params`, mod 256, hex-encoded (with a documented edge case:
if the raw sum equals `0x0D`, it's bit-inverted).

Transport: TCP, port **10001** (page 9, "Ethernet Interface"). Device
address `FF` is legal as a default for Ethernet (page 9). Spec recommends
>=200ms between commands (page 9, "Scan Cycle") — `connector.py` enforces
this.

**Verified byte-for-byte** against the two worked examples in the PDF
(`tests/test_sstprot_frame.py::test_encode_clear_logbook_matches_official_example`
and `test_encode_get_logbook_count_matches_official_example`):

```
Set "Clear logbook":  STX 11 02 LC 53 ETX  ->  STX 11 04 LC 00 B5 ETX
Get "Logbook count":  STX 11 02 LN 5E ETX  ->  STX 11 06 LN 0012 25 ETX
```

## Commands implemented (`backend/app/sstprot/commands.py`)

| Command | Direction | Purpose | PDF page |
|---|---|---|---|
| DA | GET | device address | 10 |
| DT | GET | device type | 10 |
| DN | GET | device name | 10 |
| DL | GET | line name | 10 |
| DM | GET | MAC address | 10 |
| TT | GET/**SET** | system time | 11 |
| SQ | GET | system status (state, metal signal, error status, flags) | 12 |
| PJ | GET | current product number | 32 |
| PD | GET/**SET** | product data — **sensitivity**, angle, frequency index, blanking, options, conveyor speed, gain, threshold | 33 |
| SL | GET | global/product/batch/user counters (u32) | 12 |
| LI | GET | logbook max capacity | 42 |
| LN | GET | logbook entry count | 42 |
| LE | GET | one logbook entry by absolute position | 44 |
| LC | **SET, destructive** | clear logbook | 44 |
| TA | **SET** | set access level (raw wrapper — see "What was deliberately NOT automated" below) | 13 |

`read_device_data(conn)` composes DA/DT/DN/DL/DM/TT/SQ/PJ/PD/SL/LI/LN into
one dict — same shape as the report's `read_device_data()`.
`read_logbook(conn, max_entries)` walks LE backwards from the latest entry,
same behaviour as the report's `read_logbook()`.

## Verification against the real report

`simulator/insight_simulator/sstprot_server.py` is a fake SSTProt TCP
server seeded with the **exact values** from the report's real captured
example (product 16: sensitivity=85, angle=1382, gain=184, threshold=20;
global counters error=284/metal=247910; the 30 real logbook entries with
their real timestamps and codes).

`tests/test_sstprot_commands.py` and `tests/test_sstprot_frame.py` (17
tests) run the connector and commands against this simulator and assert
the output matches the report's real numbers **exactly**, field by field —
this is a real cross-check against actual device behaviour, not just
internal self-consistency.

### Backend end-to-end verification (manual, reproducible)

Beyond pytest, the full stack (poller → SQLite archiving → REST API →
WebSocket → write-with-readback) was verified against a real running
`uvicorn` process and real HTTP requests (not FastAPI's TestClient, to
rule out test-harness artifacts):

```bash
# terminal 1
cd simulator && python -c "from insight_simulator.sstprot_server import SstProtTestServer; SstProtTestServer('127.0.0.1', 19001).serve_forever()"
# terminal 2
cd backend && DATABASE_URL=sqlite:///./dev_insight.db python -m uvicorn app.main:app --port 8000
# terminal 3: create a device pointing at 127.0.0.1:19001, then poll /api/devices/1/latest,
# /api/devices/1/readings, /api/devices/1/logbook, and POST .../write/sensitivity with confirm=true
```

Confirmed: device created → polled every cycle → readings archived to
SQLite → logbook entries archived (deduplicated by absolute number) →
`write/sensitivity` changes the mock device's state and the *next* poll
picks up the new value → the frontend's WebSocket subscriber receives it
live. The frontend itself was exercised in a real browser against this
same stack (see `frontend/README.md`).

## What was deliberately NOT automated

- **TA (set access level) login code generation**: page 18 of the PDF
  describes an algorithm ("Code = ((hhmm) x (0xFF-DevAdr)) & 0xFFFF") for
  service-level login codes, but that page's text extraction is degraded
  and mixed with an unrelated hardware pinout table — it isn't reliable
  enough to automate blindly. `clear_logbook()` will raise
  `SstProtNotAcknowledged` with `error_name == "ACCESS LEVEL"` if the
  device demands a login first; `set_access_level()` exists as a thin
  wrapper for a code obtained through Sesotec support, but nothing in this
  codebase computes one.
- **LE (get logbook entry) trailing bytes**: the PDF's declared response
  length (`0x2A` = 42 ASCII chars) doesn't cleanly close over its own
  documented field list (entry code + timestamp + 4×u16 params = 30 chars
  accounted for, 10 chars of "Parameter _1*"/"absolut number" left
  ambiguous by what looks like an OCR/table-merge artifact in the source
  PDF). `get_logbook_entry()` parses the unambiguous 30-char prefix, then
  treats the first 8 remaining chars as the u32 absolute number and keeps
  anything past that as unparsed `raw_tail_hex` rather than guessing its
  meaning. This degrades gracefully and matched the real report's data in
  every field that report exposed — but treat `absolute_number` in
  particular as "implemented per best reading of the spec, not
  hardware-confirmed" until validated against a real device.
- **DS/DV (serial number / firmware version)**: not implemented — the
  report's real `device_info` example doesn't include them, and their PDF
  table rows were visually merged with DA/DT during text extraction in a
  way that made the exact field layout uncertain. Add them once actually
  needed, reading that part of the PDF (or the device) directly rather
  than reusing this note's guess.

## WRITE commands — risk notes

- `set_system_time()`: low risk, documented, exercised only against the
  simulator.
- `set_product_data()` (used for the sensitivity write example): changes
  what the metal detector actually rejects. Documented per spec, exercised
  only against the simulator in this project — **verify on a non-critical
  product slot on the real device before trusting it in production**, per
  the original brief's "never invent WRITE commands" principle now
  extended to "never trust an unverified WRITE against production either."
- `clear_logbook()`: destructive by design (spec: "clears logbook
  definitely!"). Exposed in `commands.py` but **not wired to any API
  endpoint or frontend button** — deliberately, until there's a reason to
  need it operationally.

## Relationship to the MQTT/Probe work (Fase 1)

The original brief assumed MQTT as the first protocol (spec section 1).
The real prior integration the user provided works over raw TCP (SSTProt),
not MQTT — there is no evidence this client's GeniusOne publishes to an
MQTT broker at all. The [Discovery Probe](DISCOVERY_PROBE.md) and
[MQTT.md](MQTT.md) work from the first session remain valid and useful —
if this or a future device *does* speak MQTT (directly, or via a gateway),
the Probe is exactly the right tool to confirm that before mapping it —
but for *this* GeniusOne, SSTProt-over-TCP is the confirmed, working,
documented channel, and it's what the backend now implements.

## What's NOT built yet

- OPC UA, REST adapter for other device types (unchanged from before, see
  [ROADMAP.md](ROADMAP.md)).
- Production Context / DWH linking (article, lot, order) — the backend
  currently archives *device* readings, not production-correlated ones.
- RBAC, audit log, multi-site — see [ROADMAP.md](ROADMAP.md).
- Alembic migrations — schema is created via `Base.metadata.create_all()`
  at startup; fine for a pilot, not for schema evolution in production.
