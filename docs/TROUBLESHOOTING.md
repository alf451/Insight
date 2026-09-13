# TROUBLESHOOTING

## Probe

**"Connection failed" / stato ERROR nella barra di stato**
Controllare il messaggio dettagliato accanto a `ERROR:` — viene tradotto
dal CONNACK MQTT (es. "bad username or password", "not authorised", "server
unavailable"). Vedi `probe/insight_probe/mqtt_client.py::_CONNACK_MESSAGES`.

**Il Probe non parte / errore "No module named tkinter"**
La distribuzione Python in uso non include Tkinter. Usare l'installer
ufficiale python.org (Windows) che lo include di default, non una
distribuzione minimale.

**Nessun messaggio arriva dopo CONNECT**
- Verificare che il topic di subscription sia corretto (default `#` per
  vedere tutto).
- Verificare che il broker non richieda ACL che blocchino la subscription
  wildcard per l'utente usato.
- Verificare che il dispositivo stia effettivamente pubblicando (chiedere
  conferma al cliente, o testare prima col [Simulator](../simulator/README.md)
  contro un broker locale per escludere problemi lato Probe).

**Un payload non-JSON appare come "non valido JSON" nella tab Messages**
Comportamento atteso — non tutti i topic devono per forza pubblicare JSON.
Il payload raw resta comunque visibile e catturato integralmente.

## Simulator

**"Connection refused" all'avvio**
Nessun broker in ascolto sull'host/porta indicati. Avviare prima
`docker compose up mqtt-broker` o un Mosquitto locale.

## Test automatici

**`ModuleNotFoundError: No module named 'insight_probe'` durante `pytest`**
Eseguire `pytest` dalla root del progetto (dove si trova `pytest.ini`), non
da dentro `tests/` — `tests/conftest.py` aggiunge `probe/` e `simulator/` a
`sys.path` automaticamente in quel caso.

---

> Questa pagina crescerà con i problemi reali incontrati durante la
> discovery sul campo e lo sviluppo del backend (Fase 2+). Non contiene
> ancora troubleshooting per componenti non implementati.
