# INSIGHT

Piattaforma industriale per l'integrazione, acquisizione, supervisione e
storicizzazione dei dati provenienti da metal detector industriali Sesotec
(e, in futuro, altri dispositivi). Vedi lo spec completo di progetto per
l'elenco integrale dei requisiti.

## Stato del progetto

| Componente | Stato |
|---|---|
| `probe/` — Insight MQTT Discovery Probe | ✅ Funzionante, testato con broker reale |
| `simulator/` — Mock Metal Detector (MQTT) + Mock GeniusOne (SSTProt) | ✅ Funzionante, testato end-to-end |
| `backend/` — FastAPI + SSTProt (GeniusOne via TCP) | ✅ Funzionante: config dispositivi, monitoring, storico, 2 scritture di esempio |
| `frontend/` — Vue 3 (Devices + Monitor) | ✅ Funzionante, verificato in browser reale |
| `database/` — persistenza letture/logbook | ✅ SQLite di default (Postgres/SQL Server via `DATABASE_URL`) |
| `tests/` | ✅ 48 unit/integration test, tutti verdi |
| OPC UA, Production Context/DWH, RBAC/audit | ⛔ Non ancora iniziato |

**Non dichiarare nulla di quanto sopra "completo" oltre quanto indicato.**
Il backend implementa **SSTProt** (protocollo TCP proprietario Sesotec, non
MQTT) perché è quello che una precedente integrazione reale dell'utente usa
contro un GeniusOne vero — vedi [`docs/SSTPROT.md`](docs/SSTPROT.md) per le
fonti e la verifica. Il lavoro MQTT/Probe della Fase 1 resta valido per
qualunque dispositivo che effettivamente parli MQTT (vedi
[`docs/MQTT.md`](docs/MQTT.md)).

Vedi [`docs/ROADMAP.md`](docs/ROADMAP.md) per le fasi di sviluppo e il
relativo stato.

## Quick start — backend + frontend (SSTProt / GeniusOne)

```bash
# terminale 1: dispositivo simulato (nessun hardware reale necessario)
cd simulator
python -c "from insight_simulator.sstprot_server import SstProtTestServer; SstProtTestServer('127.0.0.1', 19001).serve_forever()"

# terminale 2: backend
cd backend
python -m venv .venv && .venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000

# terminale 3: frontend
cd frontend
npm install
npm run dev    # http://localhost:5173
```

Poi da "Devices" aggiungi un dispositivo con host `127.0.0.1`, porta
`19001`, address `01` — vedi [`backend/README.md`](backend/README.md) e
[`frontend/README.md`](frontend/README.md).

## Quick start — Probe (uso sul campo, discovery MQTT)

```bash
cd probe
run_probe.bat
```

Vedi [`probe/README.md`](probe/README.md) e
[`docs/DISCOVERY_PROBE.md`](docs/DISCOVERY_PROBE.md).

## Test automatici

```bash
py -m pip install -r tests/requirements.txt -r probe/requirements.txt -r simulator/requirements.txt -r backend/requirements.txt
py -m pytest
```

48 test coprono: framing/checksum SSTProt (verificato byte-per-byte contro
gli esempi ufficiali del PDF Sesotec), comandi SSTProt contro un GeniusOne
simulato seminato con dati reali, API backend (CRUD dispositivi, test
connessione, scritture), parsing/flatten JSON MQTT, capture JSONL,
export/import device profile, e la state machine del mock metal detector.
Verifiche end-to-end manuali aggiuntive (backend reale via `uvicorn` +
HTTP reale, frontend in browser reale) sono descritte in
[`docs/SSTPROT.md`](docs/SSTPROT.md).

## Struttura del progetto

```
Insight/
  backend/          # FastAPI + SSTProt (GeniusOne) — FASE 2-7 parziale, funzionante
  frontend/         # Vue 3 (Devices + Monitor) — funzionante
  probe/            # Insight MQTT Discovery Probe (Tkinter) — FASE 1, completo
  simulator/        # Mock metal detector: MQTT + SSTProt/GeniusOne — completo
  database/         # note di design (schema completo non ancora tutto implementato)
  docker/           # config di supporto (mosquitto di test)
  docs/             # documentazione architetturale e operativa
  tests/            # unit/integration test (pytest)
  docker-compose.yml
  .env.example
```

## Documentazione

- [ARCHITECTURE.md](docs/ARCHITECTURE.md) — modello Device/Connection/Protocol Adapter
- [SSTPROT.md](docs/SSTPROT.md) — protocollo Sesotec GeniusOne (TCP), fonti, verifica, rischi
- [MQTT.md](docs/MQTT.md) — configurazione MQTT e principio "non inventare Sesotec"
- [DISCOVERY_PROBE.md](docs/DISCOVERY_PROBE.md) — workflow e acceptance test del Probe
- [COMMISSIONING.md](docs/COMMISSIONING.md) — procedura tecnico sul campo
- [DEPLOYMENT.md](docs/DEPLOYMENT.md) — istruzioni di avvio Windows/Docker
- [ROADMAP.md](docs/ROADMAP.md) — fasi di sviluppo
- [SECURITY.md](docs/SECURITY.md), [DATABASE.md](docs/DATABASE.md), [PRODUCTION_CONTEXT.md](docs/PRODUCTION_CONTEXT.md), [SENSITIVITY.md](docs/SENSITIVITY.md), [OPCUA.md](docs/OPCUA.md), [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) — design/placeholder per le fasi successive
