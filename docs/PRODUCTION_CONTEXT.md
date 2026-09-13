# PRODUCTION CONTEXT

> Stato: **design non ancora implementato** (Fase 5/6).

## Concetto (spec sezioni 14-18)

- **Production Context**: informazione su cosa si sta producendo in questo
  momento (ordine, articolo, lotto, impianto, linea, stazione, dispositivo).
- **Production Session**: entità che fissa un intervallo temporale specifico
  con quel contesto (`start_time`/`end_time`/`status`), a cui ogni
  acquisizione viene associata.

## Fonte dati

Prima fonte prevista: SQL Server Data Warehouse del cliente, tramite
un'interfaccia `IProductionContextProvider` — mai un accoppiamento diretto
alle tabelle applicative ERP (spec sezione 15).

Implementazioni previste:
- `SqlServerProductionContextProvider`
- `PostgreSqlProductionContextProvider`
- `RestProductionContextProvider`
- `MockProductionContextProvider` (per sviluppo/test, come nel Simulator)

## Fallback manuale (spec sezione 18)

Se il DWH non è disponibile, selezione manuale della Production Session,
esplicita, auditata, visibile, modificabile, con user e timestamp.

## Cosa NON è ancora deciso

- Nomi reali delle tabelle/colonne del DWH del cliente — **UNKNOWN**, da
  determinare in loco. Non verranno ipotizzati; la query di mapping sarà
  configurabile (spec sezione 17).
- Se la selezione manuale di fallback richiede conferma a doppio livello
  (operatore + supervisore) o basta un singolo utente autenticato — da
  chiarire con requisiti operativi del cliente.
