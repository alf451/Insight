# frontend

Vue 3 + Vite app with two views, backed by the SSTProt `backend/`:

- **Devices** — connection config/mapping (host, port, device address, poll
  interval), a "Test" button per device, enable/disable, edit, delete.
- **Monitor** — live dashboard for one device: system status, product data
  (sensitivity, angle, gain, threshold), global counters, the archived
  logbook and reading history, and the two WRITE examples (sync system
  time; update sensitivity, gated behind an explicit confirmation
  checkbox).

Live updates arrive over a WebSocket (`/ws/devices/{id}`), proxied by Vite
in dev (see `vite.config.js`) — no polling from the browser.

## Quick start

```bash
cd frontend
npm install
npm run dev
```

Requires the backend running on `http://127.0.0.1:8000` (see
`../backend/README.md`) — `vite.config.js` proxies `/api` and `/ws` there.

Verified in a real browser against the backend + the SSTProt simulator:
device list, connection test, live monitoring over WebSocket, and a
sensitivity write with visible readback in the UI.

## Build

```bash
npm run build
```
