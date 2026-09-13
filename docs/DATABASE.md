# DATABASE

> Stato: **design non ancora implementato** (Fase 5/7). Nessuno schema SQL
> esiste ancora in `database/`.

## Requisiti (spec sezione 29)

Tabelle minime previste: `devices`, `device_connections`,
`variable_definitions`, `variable_values`, `production_orders`, `articles`,
`lots`, `plants`, `lines`, `stations`, `production_sessions`,
`sensitivity_configurations`, `alarms`, `device_events`, `audit_logs`,
`users`.

Indici previsti su: `timestamp`, `device_id`, `variable_id`,
`production_session_id`, `article_id`, `lot_id` — per sostenere query
storiche ad alto volume (spec sezione 29-30).

## Decisioni di design proposte

- Supporto sia PostgreSQL sia SQL Server via SQLAlchemy (spec sezioni 3, 16,
  24).
- Pattern versionato per configurazioni che cambiano nel tempo (es.
  sensibilità, tolleranze) — mai update in-place, nuova riga versione, per
  mantenere corrette le analisi storiche dopo un cambio limiti/parametri.

## Cosa NON è ancora deciso

- Schema esatto delle colonne per tabella — dipende in parte dai campi
  reali scoperti via Discovery Probe (es. quanti parametri di sensibilità
  esistono davvero: FE/NON_FE/STAINLESS o altro).
- Strategia di partizionamento per `variable_values` ad alto volume (spec
  sezione 29: "progettare per elevati volumi") — da dimensionare quando
  sarà nota la frequenza reale di pubblicazione del dispositivo.
- Se buffering locale (spec sezione 36, DB temporaneamente indisponibile)
  usa SQLite locale o una coda in-process — da decidere in Fase 7.
