# OPC UA

> Stato: **non implementato** (Fase 10). Nessun codice OPC UA esiste ancora.

## Design previsto (spec sezione 28)

Adapter `OpcUaAdapter` che implementa la stessa interfaccia
`IProtocolAdapter` usata da `MqttAdapter` (vedi [ARCHITECTURE.md](ARCHITECTURE.md)),
basato su `asyncua`.

Funzioni previste: `connect`, `disconnect`, `browse`, `read`, `write`,
`subscribe`, `monitor`.

Configurazione prevista: endpoint, security policy, certificato,
username/password, namespace, node ID, sampling interval, publishing
interval.

## Principio fondamentale

Esattamente come per MQTT (vedi [MQTT.md](MQTT.md)): **nessun namespace o
node ID Sesotec-specifico verrà implementato senza dati reali** (spec
sezioni 2, 28). Se in futuro il metal detector espone anche un server OPC
UA, servirà una sessione di discovery equivalente a quella MQTT (browse
dell'address space reale) prima di scrivere qualunque mapping.
