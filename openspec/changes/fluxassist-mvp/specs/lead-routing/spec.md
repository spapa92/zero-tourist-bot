## Purpose

Decide se un lead è in target o fuori target applicando le regole configurabili dell'agenzia agli slot raccolti.

## ADDED Requirements

### Requirement: Decisione in/out target
Il sistema DEVE decidere, una volta raccolti tutti i campi, se il lead è in target o fuori target applicando le regole configurate.

#### Scenario: Lead in target
- **WHEN** gli slot raccolti soddisfano tutte le regole configurate (zona, budget, mutuo, intenzione)
- **THEN** il sistema classifica il lead come in target e procede alla prenotazione dello slot

#### Scenario: Lead fuori target
- **WHEN** almeno una regola configurata non è soddisfatta
- **THEN** il sistema classifica il lead come fuori target e lo congeda reindirizzandolo al sito

### Requirement: Regole configurabili per agenzia
Le regole di routing (zone servite, soglie di budget, requisiti mutuo, intenzioni ammesse) DEBBONO essere configurabili per agenzia senza modificare il codice.

#### Scenario: Cambio configurazione
- **WHEN** l'agenzia aggiorna una soglia di budget nella configurazione
- **THEN** il routing usa la nuova soglia senza alcuna modifica al codice

### Requirement: Congedo fuori target
Il sistema DEVE congedare educatamente il lead fuori target e fornire il collegamento al sito dell'agenzia.

#### Scenario: Congedo
- **WHEN** un lead è classificato fuori target
- **THEN** il sistema invia un messaggio di congedo educato con il link al sito
