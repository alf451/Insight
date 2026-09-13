# ROADMAP

Fasi come da spec sezione 51. Non si sviluppa tutto contemporaneamente.

| Fase | Contenuto | Stato |
|---|---|---|
| 1 | MQTT Discovery Probe + Simulator | ✅ **Completato e testato** |
| 2 | MQTT adapter Insight (backend) | ⛔ Non iniziato |
| 3 | Device configuration (CRUD + import device_profile.json) | ⛔ Non iniziato |
| 4 | Variable acquisition (CHANGE/SYSTEMATIC, data quality) | ⛔ Non iniziato |
| 5 | SQL Server Production Context | ⛔ Non iniziato |
| 6 | Production Sessions | ⛔ Non iniziato |
| 7 | Database history (Postgres + SQL Server) | ⛔ Non iniziato |
| 8 | Dashboard (Vue 3 + real-time) | ⛔ Non iniziato |
| 9 | Sensitivity management + storicizzazione | ⛔ Non iniziato |
| 10 | OPC UA | ⛔ Non iniziato |
| 11 | REST/API generico | ⛔ Non iniziato |
| 12 | Security/hardening | ⛔ Non iniziato |

## Perché fermarsi qui per ora

L'obiettivo operativo immediato è la sessione di discovery presso il
cliente (spec sezione 57). Il Probe e il Simulator sono sufficienti per
quello. Implementare il backend prima di avere dati MQTT reali significherebbe
inventare il mapping Sesotec — esplicitamente vietato (spec sezione 2).

## Rischi noti

- **TLS reale non testato**: il codice implementa TLS (`tls_set`) ma non è
  stato verificato contro un broker TLS reale in questa sessione di lavoro
  (nessun broker TLS disponibile localmente). Da validare presso il cliente
  o con un broker Mosquitto configurato con certificati prima di fare
  affidamento su questa modalità sul campo.
- **MQTT 5 non testato contro un broker reale MQTT5**: il broker di test
  usato (`amqtt`) è MQTT 3.1.1. La select del protocollo è implementata ma
  non e2e-verificata in v5.
- **Splitter RS232/parallelismo con MeasurLink**: non applicabile a Insight
  (quel vincolo riguardava il progetto separato leank-spc) — non è un
  rischio di questo progetto, ma se il cliente Sesotec ha un vincolo di
  connessione simile (es. un solo consumer MQTT autorizzato) va verificato
  sul campo.
- **Volume di traffico reale sconosciuto**: la frequenza di pubblicazione
  reale del metal detector non è nota; il design del capture (in memoria +
  file) non è stato stress-testato per volumi alti.

## Prossimi passi immediati

1. Eseguire la sessione di discovery presso il cliente con il Probe.
2. Analizzare i `device_profile.json` e le capture raccolte.
3. Documentare in [MQTT.md](MQTT.md) i valori reali (sostituendo gli
   `UNKNOWN`), con fonte per ciascuno.
4. Solo a quel punto iniziare la Fase 2 (`MqttAdapter` backend).
