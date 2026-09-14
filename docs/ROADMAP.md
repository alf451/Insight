# ROADMAP

Fasi come da spec sezione 51, con un aggiustamento: il secondo lavoro reale
disponibile (`sstprot_function_final_report.md` + `SSTProt V1.54.pdf`,
forniti dall'utente) documentava un'integrazione **SSTProt/TCP** verso un
GeniusOne reale, non MQTT. Piuttosto che aspettare dati MQTT che potrebbero
non esistere per questo dispositivo, il backend/frontend sono stati
costruiti sul protocollo per cui esisteva già documentazione ufficiale e
un esempio reale verificabile — vedi [SSTPROT.md](SSTPROT.md). La traccia
MQTT (Fase 1, Probe) resta valida e indipendente per qualunque dispositivo
che effettivamente parli MQTT.

| Fase | Contenuto | Stato |
|---|---|---|
| 1 | MQTT Discovery Probe + Simulator | ✅ **Completato e testato** |
| 2 (SSTProt) | Connector + comandi protocollo GeniusOne | ✅ **Completato**, verificato contro esempi ufficiali e report reale |
| 3 (SSTProt) | Device configuration (CRUD + test connessione) | ✅ **Completato** |
| 4 (SSTProt) | Acquisition/polling + WRITE (system time, sensitivity) | ✅ **Completato** |
| 7 (SSTProt) | Database history (SQLite di default, Postgres/SQL Server via `DATABASE_URL`) | ✅ **Completato** per readings + logbook |
| 8 (SSTProt) | Dashboard (Vue 3 + WebSocket real-time) | ✅ **Completato**, verificato in browser |
| 2 (MQTT) | MQTT adapter Insight (backend) | ⛔ Non iniziato — in attesa di conferma che un dispositivo reale parli MQTT |
| 5 | SQL Server Production Context (ordine/articolo/lotto) | ⛔ Non iniziato |
| 6 | Production Sessions | ⛔ Non iniziato |
| 9 | Sensitivity: storicizzazione strutturata, controllo configurazione attesa/attuale | 🟡 Parziale — la sensibilità è letta/scritta/archiviata, ma non ancora come `SensitivityConfiguration` versionato dedicato |
| 10 | OPC UA | ⛔ Non iniziato |
| 11 | REST/API generico per altri dispositivi | ⛔ Non iniziato |
| 12 | Security/hardening (RBAC, audit log, TLS ovunque) | ⛔ Non iniziato |
| — | Import `device_profile.json` del Probe nel backend | ⛔ Non iniziato (rilevante solo quando/se un device MQTT verrà confermato) |
| — | `IProtocolAdapter` come interfaccia reale (oggi il backend chiama SSTProt direttamente) | ⛔ Non ancora astratto — vedi [ARCHITECTURE.md](ARCHITECTURE.md) |

## Rischi noti

- **`LE` (logbook entry) — byte finali ambigui nel PDF**: vedi
  [SSTPROT.md](SSTPROT.md#what-was-deliberately-not-automated). Gestito in
  modo difensivo, non verificato contro hardware reale.
- **WRITE non verificate su hardware reale**: `set_system_time` e
  soprattutto `set_product_data` (sensibilità) sono documentate
  ufficialmente e testate solo contro il simulatore — vedi
  [SSTPROT.md](SSTPROT.md#write-commands--risk-notes). Verificare su uno
  slot prodotto non critico prima dell'uso in produzione.
- **TA (login per operazioni privilegiate) non automatizzato**: la
  generazione del codice di accesso richiede supporto Sesotec — vedi
  SSTPROT.md. `clear_logbook()` esiste ma non è esposto via API/frontend.
- **TLS MQTT reale non testato** (ereditato dalla Fase 1): il codice del
  Probe implementa TLS ma non è stato verificato contro un broker TLS
  reale.
- **Volume di traffico reale sconosciuto** per entrambi i protocolli — il
  polling SSTProt rispetta il gap minimo di 200ms tra comandi richiesto
  dallo spec, il che rende un ciclo di poll completo (~15-30 comandi)
  dell'ordine di alcuni secondi — vedi `backend/app/poller.py`.

## Prossimi passi immediati

1. Verificare `set_product_data`/`set_system_time` contro un GeniusOne
   reale (slot prodotto non critico) prima di qualunque uso in produzione.
2. Se/quando servirà un secondo dispositivo/protocollo reale, estrarre
   `IProtocolAdapter` davvero (oggi sarebbe astrazione prematura).
3. Production Context (Fase 5/6): richiede di conoscere le tabelle
   ERP/DWH reali del cliente — non ancora note.
4. La sessione di discovery MQTT presso il cliente (vedi
   [DISCOVERY_PROBE.md](DISCOVERY_PROBE.md)) resta utile per confermare
   se esiste *anche* un canale MQTT, indipendentemente da SSTProt.
