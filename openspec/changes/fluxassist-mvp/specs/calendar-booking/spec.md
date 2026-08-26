## Purpose

Crea automaticamente lo slot di visita o chiamata su Google Calendar per i lead qualificati in target.

## ADDED Requirements

### Requirement: Creazione slot per lead in target
Il sistema DEVE creare uno slot sul calendario dell'agenzia per i lead classificati in target.

#### Scenario: Prenotazione riuscita
- **WHEN** un lead è in target e richiede una visita o chiamata
- **THEN** il sistema crea lo slot su Google Calendar e conferma all'utente data e ora

#### Scenario: Errore di prenotazione
- **WHEN** la creazione dello slot fallisce
- **THEN** il sistema informa l'utente e segnala l'errore per intervento umano
