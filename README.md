# INSIGHT

Piattaforma industriale per l'integrazione, acquisizione, supervisione e
storicizzazione dei dati provenienti da metal detector industriali Sesotec
(e, in futuro, altri dispositivi). Vedi lo spec completo di progetto per
l'elenco integrale dei requisiti.

## Stato del progetto (aggiornato: Fase 1)

| Componente | Stato |
|---|---|
| `probe/` — Insight MQTT Discovery Probe | ✅ Funzionante, testato con broker reale |
| `simulator/` — Mock Metal Detector | ✅ Funzionante, testato end-to-end col Probe |
| `tests/` | ✅ 27 unit test + 1 test end-to-end manuale |
| `backend/` — FastAPI + adapter MQTT/OPC UA | ⛔ Non ancora iniziato (Fase 2+) |
| `frontend/` — Vue 3 dashboard | ⛔ Non ancora iniziato (Fase 8) |
| `database/` — schema Postgres/SQL Server | ⛔ Non ancora iniziato (Fase 5/7) |

**Non dichiarare nulla di quanto sopra "completo" oltre quanto indicato: le
cartelle `backend/`, `frontend/`, `database/` esistono come placeholder di
struttura ma non contengono ancora codice funzionante.**

Vedi [`docs/ROADMAP.md`](docs/ROADMAP.md) per le 12 fasi di sviluppo e il
relativo stato.

## Perché si comincia dal Probe

L'obiettivo operativo immediato (spec sezione 57) non è controllare il metal
detector, ma:

> Domani devo potermi collegare al sistema del cliente, vedere e registrare
> cosa pubblica il metal detector, capire come viene espressa la
> sensibilità, identificare le variabili, correlare i messaggi agli eventi
> di produzione e portare queste informazioni nello sviluppo di Insight.

Per questo **nessun dettaglio del protocollo Sesotec è stato inventato** in
nessuna parte di questo repository — vedi
[`docs/MQTT.md`](docs/MQTT.md) sezione "Cosa NON sappiamo ancora".

## Quick start — Probe (uso sul campo, oggi)

```bash
cd probe
run_probe.bat
```

Vedi [`probe/README.md`](probe/README.md) per l'uso dettagliato e
[`docs/DISCOVERY_PROBE.md`](docs/DISCOVERY_PROBE.md) per il workflow di
commissioning completo.

## Quick start — sviluppo/test senza hardware reale

```bash
# 1. Avvia un broker MQTT di test
docker compose up mqtt-broker

# 2. In un altro terminale: avvia il simulatore
cd simulator
python -m venv .venv && .venv\Scripts\activate
pip install -r requirements.txt
python -m insight_simulator --broker localhost --port 1883

# 3. In un altro terminale: avvia il Probe e connettiti a localhost:1883
cd probe
run_probe.bat
```

## Test automatici

```bash
py -m pip install -r tests/requirements.txt -r probe/requirements.txt -r simulator/requirements.txt
py -m pytest
```

27 test coprono: parsing/flatten JSON, riconoscimento candidati sensibilità,
aggregazione topic/campi, capture JSONL (round-trip), export/import device
profile, e la state machine del mock metal detector. Un test end-to-end
manuale (broker reale + simulator + vero client MQTT del Probe) è descritto
in [`docs/DISCOVERY_PROBE.md`](docs/DISCOVERY_PROBE.md).

## Struttura del progetto

```
Insight/
  backend/        # FastAPI — non ancora implementato (Fase 2+)
  frontend/        # Vue 3 — non ancora implementato (Fase 8)
  probe/            # Insight MQTT Discovery Probe (Tkinter) — FASE 1, completo
  simulator/        # Mock metal detector MQTT — FASE 1, completo
  database/         # schema SQL — non ancora implementato (Fase 5/7)
  docker/           # config di supporto (mosquitto di test)
  docs/             # documentazione architetturale e operativa
  tests/            # unit test (pytest)
  docker-compose.yml
  .env.example
```

## Documentazione

- [ARCHITECTURE.md](docs/ARCHITECTURE.md) — modello Device/Connection/Protocol Adapter
- [MQTT.md](docs/MQTT.md) — configurazione MQTT e principio "non inventare Sesotec"
- [DISCOVERY_PROBE.md](docs/DISCOVERY_PROBE.md) — workflow e acceptance test del Probe
- [COMMISSIONING.md](docs/COMMISSIONING.md) — procedura tecnico sul campo
- [DEPLOYMENT.md](docs/DEPLOYMENT.md) — istruzioni di avvio Windows/Docker
- [ROADMAP.md](docs/ROADMAP.md) — le 12 fasi di sviluppo
- [SECURITY.md](docs/SECURITY.md), [DATABASE.md](docs/DATABASE.md), [PRODUCTION_CONTEXT.md](docs/PRODUCTION_CONTEXT.md), [SENSITIVITY.md](docs/SENSITIVITY.md), [OPCUA.md](docs/OPCUA.md), [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) — design/placeholder per le fasi successive
