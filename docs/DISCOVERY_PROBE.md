# INSIGHT MQTT DISCOVERY PROBE

Stato: **implementato e verificato** (Fase 1). Codice in `probe/`.

## Scopo

Strumento standalone, read-only, usabile presso il cliente per scoprire il
protocollo MQTT reale del metal detector Sesotec, PRIMA di implementare
qualsiasi mapping definitivo in Insight. Vedi [MQTT.md](MQTT.md) per il
principio "non inventare Sesotec".

## Interfaccia

- Connessione: broker, porta, versione MQTT (3.1.1/5), username/password,
  TLS (CA cert / client cert / client key), topic di subscription
  (default `#`).
- Tab **Messages**: elenco messaggi in tempo reale (timestamp, topic, QoS,
  retain, size, se JSON) con vista payload raw e JSON prettificato per il
  messaggio selezionato.
- Tab **Topics**: conteggio messaggi, first/last seen per topic.
- Tab **Fields / Sensitivity Candidates**: ogni JSON path osservato, con
  tipo, valore campione, conteggio occorrenze, e flag **POSSIBLE
  CANDIDATE** per i campi che matchano euristiche di naming legate alla
  sensibilità (spec sezione 9) — mai una mappatura definitiva.
- Tab **Events**: annotazioni manuali (`MARK EVENT`) per correlare azioni
  operatore al traffico MQTT (spec sezione 10).
- Pulsanti: `CLEAR`, `START CAPTURE` / `STOP CAPTURE` (streaming continuo su
  file), `SAVE CAPTURE` (snapshot on-demand), `EXPORT DEVICE PROFILE`.

## Workflow presso il cliente (spec sezione 13)

1. Collegare il PC alla rete industriale.
2. Ottenere broker hostname/IP, porta, credenziali; configurare TLS se
   necessario.
3. Avviare il Probe (`probe/run_probe.bat`).
4. Subscription `#`, CONNECT.
5. Verificare il traffico nella tab Messages; identificare i topic del
   metal detector nella tab Topics.
6. Eseguire azioni controllate sul dispositivo, marcando ogni azione con
   `MARK EVENT` (macchina ferma, in produzione, cambio articolo, cambio
   lotto, modifica sensibilità, test metal detection, test reject, test
   allarme — spec sezione 13, ultimo blocco).
7. `SAVE CAPTURE` per salvare la sessione in JSON Lines.
8. `EXPORT DEVICE PROFILE` per produrre `device_profile.json`, da importare
   successivamente in Insight (Fase 3+, non ancora implementato).

## Formato di capture (JSON Lines)

Un oggetto JSON per riga, payload originale mai alterato:

```json
{"timestamp": "...", "topic": "...", "qos": 0, "retain": false, "payload": "...", "connection_id": "...", "client_id": "...", "payload_encoding": "utf-8"}
```

## Device profile (`insight-device-profile/v1`)

Vedi [`docs/examples/device_profile.example.json`](examples/device_profile.example.json)
— generato da una sessione reale Probe + [Simulator](../simulator/README.md)
contro un broker MQTT locale (non da dati Sesotec reali). Ogni variabile
esportata ha `status: "DISCOVERED"` e `access: "READ"`: deve essere
confermata da un umano prima di essere trattata come VERIFIED/CONFIGURED
(spec sezione 43).

## Acceptance test (spec sezione 53)

Verificato il 2026-09-13 con: GUI smoke test (costruzione widget senza
eccezioni) + test end-to-end con broker MQTT reale locale (`amqtt`) e
[Simulator](../simulator/README.md).

- [x] Parte su Windows (Tkinter, stdlib — nessuna dipendenza da Node/browser)
- [x] Permette configurazione broker
- [x] Connette MQTT (verificato contro broker reale)
- [x] Permette MQTT 3.1.1
- [x] Permette MQTT 5 (selezione protocollo implementata; non testata contro
      un broker MQTT5 reale in questa sessione — solo unit-level)
- [x] Supporta username/password
- [x] Supporta TLS (implementato via `tls_set`; non testato contro un
      broker TLS reale in questa sessione — nessun broker TLS disponibile
      per il test)
- [x] Subscribe `#`
- [x] Mostra topic (tab Topics)
- [x] Mostra payload (raw + JSON prettificato)
- [x] Identifica JSON
- [x] Estrae JSON path
- [x] Identifica data type
- [x] Conta messaggi (per topic e per campo)
- [x] Mostra QoS
- [x] Mostra retain
- [x] Salva JSONL (verificato: round-trip write/read testato)
- [x] Marca eventi
- [x] Esporta `device_profile.json` (verificato con dati reali del test e2e)
- [x] NON effettua WRITE (nessun metodo `publish()` esiste nel codice)
- [x] Non perde il processo se arriva un payload malformato (verificato con
      unit test dedicato: `try_parse_json`/`analyze_payload`/`registry.ingest`
      non sollevano eccezioni su payload non-JSON)

**Non ancora verificato sul campo**: comportamento contro il broker MQTT
reale del cliente, con TLS reale e con volumi di traffico Sesotec reali.
Questo richiede la sessione di discovery vera e propria.
