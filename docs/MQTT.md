# MQTT

> **Nota**: il backend oggi (`backend/`) implementa il protocollo
> **SSTProt** (TCP, non MQTT) contro un GeniusOne reale — vedi
> [SSTPROT.md](SSTPROT.md). Questo documento resta valido per la
> discovery MQTT (Fase 1, Probe) e per qualunque dispositivo che
> effettivamente parli MQTT, confermato o meno per questo cliente.

## Principio fondamentale: non inventare Sesotec

Nessun topic, struttura payload, nome campo, unità di misura o comando WRITE
specifico Sesotec è ipotizzato in questo repository. Ogni informazione del
genere deve provenire da una delle fonti seguenti, e va documentata indicando
la fonte:

1. documentazione ufficiale fornita dal cliente;
2. configurazione reale del dispositivo;
3. messaggi MQTT catturati con il [Discovery Probe](DISCOVERY_PROBE.md);
4. test effettuati presso il cliente.

**Stato attuale: UNKNOWN per tutti i seguenti punti Sesotec-specifici** —
verranno riempiti solo dopo la sessione di discovery sul campo:

| Elemento | Valore | Fonte |
|---|---|---|
| Topic prefix reale | UNKNOWN | — |
| Struttura payload | UNKNOWN | — |
| Nome campo sensibilità | UNKNOWN (candidati possibili individuati dal Probe, non confermati) | — |
| Namespace/comandi WRITE | UNKNOWN | — |
| Unità di misura sensibilità | UNKNOWN | — |

## Cosa è invece implementato oggi (Fase 1, generico, non Sesotec-specifico)

Il [Probe](DISCOVERY_PROBE.md) e il futuro `MqttAdapter` del backend
condividono lo stesso modello di configurazione connessione (spec sezione 5):

```
broker_host
broker_port
protocol            # "3.1.1" o "5"
username
password            # mai loggata in chiaro
tls_enabled
ca_certificate
client_certificate
client_key
keepalive
reconnect_enabled
reconnect_interval  # con backoff esponenziale
qos
subscription_topic  # supporta wildcard, es. "#"
```

Implementato e testato in `probe/insight_probe/mqtt_client.py`:
- MQTT 3.1.1 e MQTT 5 (selezione protocollo);
- username/password;
- TLS (CA cert, client cert, client key);
- QoS, retain;
- keepalive, reconnect con backoff esponenziale (`reconnect_delay_set`);
- subscription con wildcard;
- stato di connessione diagnostico (CONNECTING/CONNECTED/DISCONNECTED/ERROR
  con messaggio leggibile).

**Non implementato per design nel Probe**: nessun metodo `publish()` esiste
nel codice — il Probe è strutturalmente incapace di scrivere sul broker
(spec sezioni 6, 27).

## MqttAdapter (backend, non ancora implementato)

Riuserà lo stesso `MqttProbeConfig`/logica di connessione del Probe (stessa
libreria, stesso comportamento di reconnect), esposto dietro l'interfaccia
`IProtocolAdapter` (vedi [ARCHITECTURE.md](ARCHITECTURE.md)). La differenza
principale è che l'adapter del backend alimenta l'Acquisition Engine invece
di una GUI di discovery, e — solo dopo verifica documentata — potrà
esporre `write_variable()` per i comandi WRITE confermati (spec sezione 27).

## Modalità di acquisizione e MQTT

MQTT è per natura message/subscription-oriented, non a polling. Per questo:
- **CHANGE** e **SYSTEMATIC** (spec sezione 20) si applicano naturalmente ad
  ogni messaggio ricevuto;
- **EVENT** è predisposto architetturalmente ma non ha ancora una
  implementazione concreta;
- l'`interval_ms` di una `VariableDefinition` non traduce in polling MQTT —
  è usato solo dove tecnicamente applicabile (es. un futuro adapter REST).
