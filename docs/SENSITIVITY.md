# SENSITIVITY

> Stato: **design non ancora implementato** (Fase 9). Il Discovery Probe
> (Fase 1, implementato) aiuta a *individuare* il campo giusto, ma non
> implementa ancora un modello di dominio persistito.

## Perché è prioritaria

La sensibilità è la variabile più importante del metal detector (spec
sezione 22) e determina se un lotto è stato controllato correttamente.

## Cosa il Probe fa oggi

Individua **candidati possibili** (spec sezione 9) confrontando l'ultimo
segmento di ogni JSON path osservato con una lista di keyword plausibili
(`sensitivity`, `sensibility`, `threshold`, `fe`, `nonfe`, `stainless`,
`recipe`, `program`, ecc. — vedi `probe/insight_probe/json_analyzer.py`).
Questi candidati **non sono un mapping definitivo**: vanno confermati con
documentazione/cliente/test.

## Modello di dominio previsto (backend, non implementato)

```
SensitivityConfiguration
  device
  production_session
  parameter        # es. FE, NON_FE, STAINLESS — ma configurabile, non fisso
  value
  unit
  timestamp
  source
```

Ogni modifica va storicizzata (mai update in-place), per poter rispondere a
domande come "con quale sensibilità è stato controllato il lotto X?" (spec
sezione 30).

## Controllo configurazione (spec sezione 23, non prioritario per la prima release)

Confronto CONFIGURAZIONE ATTESA vs ATTUALE con stato OK/WARNING — feature
opzionale, da implementare solo dopo che il modello base è stabile.

## Cosa NON è ancora deciso

- Quanti e quali parametri di sensibilità esistono realmente sul dispositivo
  del cliente — **UNKNOWN**, dipende dalla discovery sul campo.
- Unità di misura reale (mm? valore adimensionale? scala 0-100?) —
  **UNKNOWN**.
