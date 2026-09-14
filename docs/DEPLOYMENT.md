# DEPLOYMENT — installazione, configurazione e test

Guida pratica per installare Insight, configurare un dispositivo e
verificare che connessione e acquisizione dati funzionino — sia contro il
simulatore (nessun hardware richiesto) sia contro un GeniusOne reale.

> Per il Discovery Probe (uso sul campo, discovery MQTT) vedi la sezione
> dedicata più sotto e [DISCOVERY_PROBE.md](DISCOVERY_PROBE.md) — è uno
> strumento standalone separato dal backend/frontend descritti qui.

## 1. Requisiti

- Windows 10/11
- Python 3.10+. **Su alcune macchine il comando `python` punta allo stub
  Microsoft Store e non funziona** — se capita, usa il launcher `py` al suo
  posto (`py -m venv .venv`, `py -m pip install ...`). Verifica con:
  ```bash
  py --version
  ```
- Node.js 18+ e npm (solo per il frontend):
  ```bash
  node --version
  npm --version
  ```
- Nessun database server richiesto per iniziare: il backend usa SQLite in
  locale di default. PostgreSQL/SQL Server sono supportati via
  `DATABASE_URL` (vedi sezione 8).

## 2. Installazione backend

```bash
cd backend
py -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Nessuna configurazione obbligatoria: senza `DATABASE_URL` impostata, il
backend crea `backend\insight.db` (SQLite) al primo avvio.

## 3. Installazione frontend

```bash
cd frontend
npm install
```

## 4. Avvio — senza hardware reale (simulatore)

Tre terminali:

```bash
# terminale 1 — dispositivo GeniusOne simulato (dati reali di esempio, vedi docs/SSTPROT.md)
cd simulator
py -c "from insight_simulator.sstprot_server import SstProtTestServer; SstProtTestServer('127.0.0.1', 19001).serve_forever()"
```

```bash
# terminale 2 — backend
cd backend
.venv\Scripts\activate
py -m uvicorn app.main:app --reload --port 8000
```

```bash
# terminale 3 — frontend
cd frontend
npm run dev
```

Apri **http://localhost:5173**.

## 5. Configurare un dispositivo (tab "Devices")

1. Clic su **+ Add device**.
2. Compila:
   - **Name**: nome libero, es. `MD01 - Linea 3`.
   - **Host / IP**: indirizzo del dispositivo.
     - Simulatore: `127.0.0.1`
     - Reale: l'IP del GeniusOne sulla rete industriale (es. `192.168.1.125`)
   - **Port**: `19001` per il simulatore, altrimenti **`10001`** (porta
     SSTProt standard su Ethernet — spec ufficiale, non modificabile sul
     dispositivo).
   - **Address (hex)**: indirizzo SSTProt del dispositivo, 2 cifre hex.
     `FF` è l'indirizzo di default legale su Ethernet (va bene quasi
     sempre); se il dispositivo risponde con errore "WRONG ADDRESS" prova
     l'indirizzo reale ottenuto separatamente (comando `DA`).
   - **Poll interval (s)**: ogni quanto interrogare il dispositivo. Un
     ciclo di poll completo emette ~15-25 comandi SSTProt con un minimo di
     200ms tra un comando e l'altro (richiesto dallo spec, vedi
     [SSTPROT.md](SSTPROT.md)) — con le impostazioni di default un ciclo
     dura qualche secondo. Non impostare un intervallo troppo aggressivo
     (`< 5s`) su hardware reale.
   - **Enabled**: lascia spuntato per far partire subito il polling.
3. **Save**.

## 6. Testare la connessione

Nella riga del dispositivo, clic su **Test**. Chiama una volta `DA`+`DT`
(indirizzo + tipo dispositivo) e mostra:

- **OK** + nome tipo dispositivo (es. `GeniusOne`) → la connessione TCP e
  il framing SSTProt funzionano.
- **ERROR** + messaggio → vedi la tabella troubleshooting (sezione 10).

Lo stesso controllo è disponibile via API:

```bash
curl -X POST http://127.0.0.1:8000/api/devices/1/test
```

## 7. Testare l'acquisizione dati

1. Vai sulla tab **Monitor**, seleziona il dispositivo dal menu a tendina.
2. Attendi un ciclo di poll (qualche secondo, vedi sezione 5): il badge
   passa da assente a **ONLINE**, e compaiono:
   - **System status**: stato principale (IDLE/WARNING/ERROR/...), segnale
     metallo, prodotto corrente, flag attivi.
   - **Product data**: sensibilità, angolo, gain, threshold, velocità nastro.
   - **Counters**: contatori globali metallo/errori, occupazione logbook.
   - **Logbook (archiviato)**: le voci del logbook via via sincronizzate.
   - **Storico letture (archiviate)**: ogni lettura salvata nel database.
3. Se dopo 2-3 cicli di poll non compare nulla e il badge resta assente,
   controlla i log del backend (terminale 2) — un errore di polling per un
   dispositivo non blocca gli altri dispositivi, ma viene comunque
   registrato lì.

Verifica via API (utile per script/automazione):

```bash
curl http://127.0.0.1:8000/api/devices/1/latest      # stato corrente in memoria
curl http://127.0.0.1:8000/api/devices/1/readings     # storico archiviato
curl http://127.0.0.1:8000/api/devices/1/logbook       # logbook archiviato
```

`latest.connected == true` e `latest.data` popolato = acquisizione
funzionante end-to-end (TCP → parsing SSTProt → archiviazione DB → API).

## 8. Verificare l'archiviazione nel database

Con SQLite (default), il file è `backend\insight.db`. Ispezione rapida:

```bash
py -c "
import sqlite3
con = sqlite3.connect('backend/insight.db')
print(con.execute('select count(*) from device_readings').fetchone())
print(con.execute('select count(*) from logbook_entries').fetchone())
"
```

Per usare PostgreSQL o SQL Server invece di SQLite, imposta `DATABASE_URL`
prima di avviare il backend (vedi `.env.example` alla radice del
repository per gli esempi di connection string) — nessun'altra modifica
richiesta, lo schema viene creato automaticamente al primo avvio.

```powershell
# PowerShell
$env:DATABASE_URL = "postgresql+psycopg://insight:changeme@localhost:5432/insight"
py -m uvicorn app.main:app --port 8000
```

```cmd
:: cmd.exe
set DATABASE_URL=postgresql+psycopg://insight:changeme@localhost:5432/insight
py -m uvicorn app.main:app --port 8000
```

## 9. Scritture di esempio — attenzione

Il pannello "Scrittura verso il dispositivo" nella tab Monitor offre due
comandi WRITE, entrambi documentati ufficialmente ma **mai verificati su
hardware reale** in questo progetto (vedi
[SSTPROT.md](SSTPROT.md#write-commands--risk-notes)):

- **Sync system time**: basso rischio.
- **Update sensitivity**: cambia cosa il metal detector rifiuta in
  produzione. Richiede una spunta di conferma esplicita nella UI. **La
  prima volta su un dispositivo reale, usa uno slot prodotto non critico**
  e verifica il readback prima di fidarti in produzione.

## 10. Troubleshooting

| Sintomo | Causa probabile | Azione |
|---|---|---|
| `Test` → ERROR "Connection refused" / timeout | Host/porta errati, o dispositivo non raggiungibile in rete | Verifica IP/porta (10001), ping al dispositivo, firewall |
| `Test` → NA "WRONG ADDRESS" | Address SSTProt configurato non corrisponde al dispositivo | Prova `FF`, oppure ottieni l'indirizzo reale col comando `DA` |
| `Test` → NA "ACCESS LEVEL" | Il comando richiede un livello di accesso non garantito da `FF`/default | Vedi [SSTPROT.md](SSTPROT.md) — il login `TA` non è automatizzato, serve un codice da Sesotec |
| `Test` OK ma Monitor resta senza dati per molti cicli | Poll interval troppo corto rispetto al tempo reale di un ciclo (~qualche secondo), o dispositivo disabilitato (`enabled=false`) | Aumenta `poll_interval_s`, verifica `enabled=true` nella lista Devices |
| Frontend non raggiunge il backend (`Failed to fetch`) | Backend non avviato, o porta diversa da 8000 | Verifica che `uvicorn` sia in ascolto su `:8000` — `vite.config.js` fa proxy di `/api` e `/ws` lì |
| `py` non trovato / `python` non funziona | Alias Microsoft Store attivo, Python non installato correttamente | Installa Python da python.org (non dallo Store) con "Add to PATH" attivo; usa sempre `py` su questa classe di problemi |

Codici di errore NA (`Not Acknowledged`) completi in
`backend/app/sstprot/frame.py::NA_ERROR_CODES`.

## 11. Discovery Probe (MQTT, uso sul campo)

Strumento separato, per dispositivi che parlano MQTT (non SSTProt) — vedi
[DISCOVERY_PROBE.md](DISCOVERY_PROBE.md) per il workflow completo.

```bash
cd probe
run_probe.bat
```

## 12. Test automatici (l'intero repository)

```bash
py -m pip install -r tests/requirements.txt -r probe/requirements.txt -r simulator/requirements.txt -r backend/requirements.txt
py -m pytest
```

## 13. Cosa manca per un deploy di produzione

Non ancora fatto (vedi [ROADMAP.md](ROADMAP.md)): pacchettizzazione
Docker di backend/frontend, avvio come servizio Windows,
autenticazione/RBAC, audit log, TLS sulla connessione al dispositivo. Fino
ad allora, questo resta un setup da "pilota": avvio manuale, zero
installazione di sistema, completamente reversibile.
