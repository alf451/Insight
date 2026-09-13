# COMMISSIONING

Procedura per il tecnico sul campo (spec sezione 45).

| # | Step | Stato |
|---|---|---|
| 1 | Add Device | ⛔ richiede backend (Fase 3) |
| 2 | Configure MQTT | ⛔ richiede backend (Fase 3) — oggi: configurare la connessione nel Probe |
| 3 | Test Connection | ✅ possibile oggi col Probe (`CONNECT`) |
| 4 | Run Discovery | ✅ possibile oggi col Probe (subscription `#`) |
| 5 | Capture traffic | ✅ possibile oggi col Probe (`START CAPTURE`/`SAVE CAPTURE`) |
| 6 | Analyze variables | ✅ possibile oggi col Probe (tab Fields / Sensitivity Candidates) |
| 7 | Verify mappings | 🟡 manuale: confermare con cliente/documentazione i candidati marcati dal Probe |
| 8 | Import profile | ⛔ richiede backend (Fase 3) — oggi: `device_profile.json` esportato e conservato |
| 9 | Configure production context | ⛔ richiede backend + provider (Fase 5/6) |
| 10 | Start Production Session | ⛔ richiede backend (Fase 6) |
| 11 | Verify acquisition | ⛔ richiede backend (Fase 4) |
| 12 | Verify database | ⛔ richiede backend + database (Fase 7) |
| 13 | Verify dashboard | ⛔ richiede frontend (Fase 8) |
| 14 | Test alarms | ⛔ richiede backend (Fase 4/9) |
| 15 | Close commissioning | ⛔ richiede backend (audit log, Fase 7) |

**Oggi (Fase 1) il commissioning si ferma allo step 8**: il deliverable
della visita cliente è un `device_profile.json` verificato/annotato più i
file di capture, da usare come input per implementare il `MqttAdapter`
Sesotec-specifico nel backend (Fase 2-3).

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
