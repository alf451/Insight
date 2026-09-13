# DEPLOYMENT

> Stato: solo Probe/Simulator sono deployabili oggi. Le istruzioni per
> backend/frontend/database verranno aggiunte quando quelle fasi saranno
> implementate (vedi [ROADMAP.md](ROADMAP.md)).

## Probe (Windows, uso sul campo)

Requisiti: Windows 10/11, Python 3.10+ con Tkinter (incluso
nell'installer standard python.org; verificare se si usa una distribuzione
minimale).

```bash
cd probe
run_probe.bat
```

Lo script crea un virtualenv locale (`probe\.venv`), installa `paho-mqtt`
e avvia la GUI. Nessuna installazione di sistema, nessun diritto
amministratore richiesto.

## Simulator + broker di test (sviluppo)

```bash
docker compose up mqtt-broker
```

oppure, senza Docker, un Mosquitto locale con `allow_anonymous true` sulla
porta 1883 (solo per test, mai in produzione — vedi
`docker/mosquitto/mosquitto.conf`).

```bash
cd simulator
python -m venv .venv && .venv\Scripts\activate
pip install -r requirements.txt
python -m insight_simulator --broker localhost --port 1883
```

## Test automatici

```bash
py -m pip install -r tests/requirements.txt -r probe/requirements.txt -r simulator/requirements.txt
py -m pytest
```
