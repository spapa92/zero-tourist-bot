## Purpose

Riceve i messaggi WhatsApp in entrata dell'agenzia e invia le risposte del bot, gestendo
correttamente la finestra di servizio di 24 ore, attraverso un provider di messaggistica
selezionabile a configurazione.

## ADDED Requirements

### Requirement: Selezione del canale di messaggistica
Il sistema DEVE supportare più provider WhatsApp (Meta Cloud API e Twilio) e permettere di
attivarne **uno alla volta** tramite configurazione, senza modifiche al codice e senza cambiare
l'URL pubblico del webhook.

#### Scenario: Canale attivo configurato
- **WHEN** l'applicazione viene avviata con un provider valido configurato
- **THEN** espone il webhook di quel solo provider su `POST /webhook` e instrada tutti gli invii
  attraverso di esso

#### Scenario: Canale non supportato
- **WHEN** viene configurato un provider non supportato
- **THEN** l'avvio fallisce con un errore che elenca i provider ammessi

#### Scenario: Diagnostica del canale attivo
- **WHEN** viene interrogato l'endpoint di health
- **THEN** la risposta indica il provider attivo e se dispone delle credenziali necessarie
  all'invio

### Requirement: Credenziali mancanti segnalate esplicitamente
Il sistema DEVE avviarsi anche con le credenziali di invio incomplete — così da poter completare
la verifica del webhook presso il provider — e DEVE fallire con un errore esplicito, che nomina la
configurazione mancante, al primo tentativo di invio.

#### Scenario: Invio senza credenziali
- **WHEN** il bot tenta di inviare un messaggio con il provider attivo non configurato
- **THEN** l'invio fallisce con un errore che indica quali variabili mancano

#### Scenario: Template non mappato
- **WHEN** il bot tenta di inviare un template che il provider attivo non ha mappato
- **THEN** l'invio fallisce con un errore che indica il template e la configurazione mancante

## MODIFIED Requirements

### Requirement: Ricezione messaggi in entrata
Il sistema DEVE ricevere i messaggi WhatsApp in ingresso tramite il webhook del provider attivo e
verificarne l'autenticità con il meccanismo previsto da quel provider (firma HMAC-SHA256 del body
per Meta, firma HMAC-SHA1 su URL e parametri per Twilio).

#### Scenario: Messaggio in entrata valido
- **WHEN** un utente invia un messaggio al numero WhatsApp dell'agenzia
- **THEN** il sistema verifica la firma del webhook e passa il messaggio alla macchina di
  qualificazione, indipendentemente dal provider attivo

#### Scenario: Richiesta non autenticata
- **WHEN** arriva una richiesta webhook con firma non valida o assente
- **THEN** il sistema la rifiuta senza elaborarla

#### Scenario: Messaggio senza testo
- **WHEN** arriva un messaggio non testuale (per esempio solo media)
- **THEN** il sistema risponde correttamente al provider senza attivare la qualificazione

#### Scenario: Verifica del webhook Meta
- **WHEN** Meta invia la richiesta di verifica del callback con il token atteso
- **THEN** il sistema restituisce il challenge, anche se le credenziali di invio non sono ancora
  complete

### Requirement: Riapertura della finestra con template re-opener
Quando la finestra di 24 ore è scaduta, il sistema DEVE riaprirla inviando un messaggio template
approvato (re-opener) tramite il provider attivo, prima di riprendere i messaggi liberi.

#### Scenario: Riapertura finestra
- **WHEN** il sistema deve contattare un lead la cui finestra di 24 ore è scaduta
- **THEN** invia il template re-opener e attende la risposta dell'utente prima di proseguire in
  formato libero

#### Scenario: Template indipendente dal provider
- **WHEN** il bot invia un template con parametri
- **THEN** i parametri posizionali vengono tradotti nel formato del provider attivo (componenti
  per Meta, ContentSid e ContentVariables per Twilio) senza che il chiamante debba conoscerlo
