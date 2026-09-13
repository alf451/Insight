# SECURITY

> Stato: **hardening non ancora implementato** (Fase 12). Questo documento
> elenca i requisiti target, non lo stato attuale del backend (che non
> esiste ancora).

## Applicato già oggi (Probe/Simulator, Fase 1)

- La password MQTT non viene mai loggata in chiaro: il Probe non ha logging
  di configurazione, e il campo password nella GUI usa mascheramento
  (`show="*"`).
- Il Probe è strutturalmente read-only: nessun metodo `publish()` esiste nel
  codice, quindi non può scrivere sul dispositivo per costruzione, non solo
  per configurazione.
- Nessuna credenziale è hardcoded: tutta la configurazione connessione viene
  inserita a runtime dall'utente nella GUI.

## Requisiti target per il backend (spec sezione 37, non ancora implementati)

- TLS per MQTT/OPC UA/DB dove supportato dal broker/server.
- Credential management: nessuna credenziale in repository; uso di
  variabili d'ambiente (`.env`, mai committato — vedi `.gitignore`).
- RBAC per le operazioni di scrittura/configurazione.
- Audit di ogni modifica di configurazione (spec sezione 31).
- Session management per l'autenticazione utenti frontend.
- Assunzioni di segmentazione di rete e least privilege da validare con
  l'IT del cliente caso per caso — non sono qualcosa che il software da
  solo può garantire.

## Logging (spec sezione 35)

Livelli DEBUG/INFO/WARNING/ERROR/CRITICAL previsti per il backend. Non
loggare mai password, token, chiavi private — principio già rispettato nel
Probe e da mantenere in ogni componente futuro.
