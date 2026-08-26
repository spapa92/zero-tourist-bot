## Purpose

Persiste conversazioni, slot estratti ed esiti in PostgreSQL per l'analisi e la futura predizione.

## ADDED Requirements

### Requirement: Persistenza dello stato conversazionale
Il sistema DEVE persistere lo stato della conversazione per riprenderla in seguito, anche dopo riavvii.

#### Scenario: Ripresa conversazione
- **WHEN** il sistema viene riavviato durante una conversazione attiva
- **THEN** lo stato della conversazione viene ripristinato dal database

### Requirement: Log del lead e dell'esito
Il sistema DEVE registrare per ogni conversazione gli slot estratti, la decisione di routing e l'esito.

#### Scenario: Registrazione esito
- **WHEN** una conversazione termina
- **THEN** il sistema registra slot estratti, decisione (in/out target) ed esito nel lead log

### Requirement: Tracciamento dell'outcome calendario
Il sistema DEVE registrare l'esito dell'appuntamento (es. presentato, non presentato) come base per analisi future.

#### Scenario: No-show
- **WHEN** un lead in target non si presenta all'appuntamento
- **THEN** il sistema registra l'outcome come "non presentato" per le analisi future
