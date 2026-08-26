## Purpose

Gestisce la conversazione di prequalifica, raccogliendo i dati chiave del contatto tramite slot-filling flessibile.

## ADDED Requirements

### Requirement: Accoglienza H24
Il sistema DEVE accogliere ogni nuovo contatto con un messaggio di benvenuto, in qualunque momento.

#### Scenario: Primo contatto
- **WHEN** un utente scrive per la prima volta al numero dell'agenzia
- **THEN** il sistema risponde immediatamente con un messaggio di benvenuto

### Requirement: Raccolta flessibile dei dati
Il sistema DEVE estrarre da ogni messaggio tutti i campi riconoscibili tra: intenzione, zona, tipologia, budget, stato del mutuo.

#### Scenario: Estrazione multipla
- **WHEN** l'utente scrive un messaggio che contiene più informazioni (es. "cerco un trilocale in centro con budget 200k")
- **THEN** il sistema estrae tutti i campi riconoscibili e li memorizza nello stato

### Requirement: Richiesta del campo mancante
Il sistema DEVE chiedere il campo mancante a priorità più alta quando non tutti i campi sono stati raccolti.

#### Scenario: Campo mancante
- **WHEN** alcuni campi dello stato sono ancora vuoti
- **THEN** il sistema chiede il campo mancante con priorità più alta, secondo un ordine di fallback predefinito (intenzione, zona, tipologia, budget, mutuo)

### Requirement: Uscite globali
Il sistema DEVE riconoscere in ogni punto della conversazione le richieste di interrompere, di parlare con un umano, o di aiuto.

#### Scenario: Richiesta di un umano
- **WHEN** l'utente chiede di parlare con una persona
- **THEN** il sistema interrompe la qualifica e segnala la richiesta di intervento umano

### Requirement: Fallback deterministico
Il sistema DEVE degradare a un'estrazione deterministica a regole quando l'LLM non è disponibile.

#### Scenario: LLM non disponibile
- **WHEN** la chiamata all'LLM fallisce o supera il timeout
- **THEN** il sistema usa il fallback deterministico per continuare la conversazione
