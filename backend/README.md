# backend

FastAPI backend implementing the **SSTProt** protocol (Sesotec GeniusOne,
TCP port 10001) — device configuration, monitoring, historical archiving,
and two documented WRITE examples. See
[`../docs/SSTPROT.md`](../docs/SSTPROT.md) for the protocol details and
verification, and [`../docs/ROADMAP.md`](../docs/ROADMAP.md) for what's
still missing (OPC UA, production context, RBAC/audit).

## Quick start

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate      # Windows
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```

Defaults to a local SQLite file (`./insight.db`) — set `DATABASE_URL` to
point at PostgreSQL or SQL Server instead (see `.env.example` at the repo
root). No database server needs to be running for local development.

## Testing without real hardware

`../simulator/insight_simulator/sstprot_server.py` is a mock GeniusOne TCP
server seeded with real captured values from an actual device (see
docs/SSTPROT.md). Run it, then point a device at `127.0.0.1:<port>` via
the API or the frontend:

```bash
cd simulator
python -c "from insight_simulator.sstprot_server import SstProtTestServer; SstProtTestServer('127.0.0.1', 19001).serve_forever()"
```

## API

- `GET/POST/PUT/DELETE /api/devices` — device connection config
- `POST /api/devices/{id}/test` — one-shot connection test
- `GET /api/devices/{id}/latest` — current in-memory state (for the dashboard)
- `GET /api/devices/{id}/readings` — archived historical readings (SQLite/Postgres/SQL Server)
- `GET /api/devices/{id}/logbook` — archived historical logbook entries
- `WS /ws/devices/{id}` — live push of every poll
- `POST /api/devices/{id}/write/system-time` — safe write example
- `POST /api/devices/{id}/write/sensitivity` — write example for the domain's key variable, gated behind `confirm: true` — read docs/SSTPROT.md's risk notes first

## Tests

```bash
cd ..   # repo root
py -m pytest
```
