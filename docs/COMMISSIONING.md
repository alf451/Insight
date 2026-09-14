# COMMISSIONING

Procedura per il tecnico sul campo (spec sezione 45). Copre due tracce
indipendenti — vedi [ROADMAP.md](ROADMAP.md) per perché esistono entrambe:

- **SSTProt** (GeniusOne via TCP, backend+frontend funzionanti) — per
  l'installazione/configurazione/test passo-passo vedi
  [DEPLOYMENT.md](DEPLOYMENT.md), è la guida più dettagliata.
- **MQTT** (Discovery Probe, per un dispositivo che effettivamente parli
  MQTT) — vedi [DISCOVERY_PROBE.md](DISCOVERY_PROBE.md).

| # | Step | Stato |
|---|---|---|
| 1 | Add Device | ✅ **SSTProt**: tab Devices del frontend (vedi DEPLOYMENT.md §5) |
| 2 | Configure MQTT | 🟡 **MQTT**: nel Probe, per ora — non applicabile a SSTProt (nessun broker coinvolto) |
| 3 | Test Connection | ✅ **SSTProt**: bottone "Test" (DEPLOYMENT.md §6) — ✅ **MQTT**: `CONNECT` nel Probe |
| 4 | Run Discovery | ✅ **MQTT**: subscription `#` nel Probe — non applicabile a SSTProt (protocollo già noto, vedi SSTPROT.md) |
| 5 | Capture traffic | ✅ **MQTT**: `START CAPTURE`/`SAVE CAPTURE` nel Probe — su SSTProt equivalente: archiviazione automatica in database (DEPLOYMENT.md §7-8) |
| 6 | Analyze variables | ✅ **MQTT**: tab Fields / Sensitivity Candidates nel Probe — su SSTProt: variabili già note da SSTPROT.md |
| 7 | Verify mappings | 🟡 **MQTT**: manuale, da confermare con cliente/documentazione — su SSTProt: mapping già verificato contro un report reale (SSTPROT.md) |
| 8 | Import profile | ⛔ **MQTT**: `device_profile.json` → Insight, non ancora implementato |
| 9 | Configure production context | ⛔ non ancora implementato (Fase 5/6, nessuna delle due tracce) |
| 10 | Start Production Session | ⛔ non ancora implementato (Fase 6) |
| 11 | Verify acquisition | ✅ **SSTProt**: tab Monitor (DEPLOYMENT.md §7) — ⛔ MQTT (nessun adapter backend) |
| 12 | Verify database | ✅ **SSTProt**: `/api/devices/{id}/readings` e `/logbook`, o ispezione diretta (DEPLOYMENT.md §8) — ⛔ MQTT |
| 13 | Verify dashboard | ✅ **SSTProt**: frontend, tab Monitor — ⛔ MQTT |
| 14 | Test alarms | ⛔ non ancora implementato per nessuna traccia (oggi solo stato/flag grezzi, non un concetto di allarme dedicato) |
| 15 | Close commissioning | ⛔ non ancora implementato (audit log, Fase 12) |

## Checklist scenari da eseguire durante la discovery (spec sezione 13)

- [ ] macchina ferma
- [ ] macchina in produzione
- [ ] cambio articolo
- [ ] cambio lotto
- [ ] modifica sensibilità
- [ ] prodotto normale
- [ ] test metal detection
- [ ] test reject
- [ ] test allarme

Per ciascuno: eseguire l'azione sul metal detector, premere `MARK EVENT` nel
Probe con il tipo evento corrispondente, osservare quali topic/campi
cambiano nella tab Fields.
