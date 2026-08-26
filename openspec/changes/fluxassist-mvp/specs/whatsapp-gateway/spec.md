## Purpose

Riceve i messaggi WhatsApp in entrata dell'agenzia e invia le risposte del bot, gestendo correttamente la finestra di servizio di 24 ore.

## ADDED Requirements

### Requirement: Ricezione messaggi in entrata
Il sistema DEVE ricevere i messaggi WhatsApp in ingresso tramite il webhook della Meta WhatsApp Business Cloud API e verificarne l'autenticità.

#### Scenario: Messaggio in entrata valido
- **WHEN** un utente invia un messaggio al numero WhatsApp dell'agenzia
- **THEN** il sistema verifica la firma del webhook e passa il messaggio alla macchina di qualificazione

#### Scenario: Richiesta non autenticata
- **WHEN** arriva una richiesta webhook con firma non valida
- **THEN** il sistema la rifiuta senza elaborarla

### Requirement: Invio risposte dentro la finestra 24h
Il sistema DEVE inviare messaggi in formato libero in risposta a un messaggio dell'utente entro la finestra di servizio di 24 ore.

#### Scenario: Risposta dentro finestra
- **WHEN** l'utente ha inviato un messaggio nelle ultime 24 ore
- **THEN** il sistema invia la risposta in formato libero senza template

### Requirement: Riapertura della finestra con template re-opener
Quando la finestra di 24 ore è scaduta, il sistema DEVE riaprirla inviando un messaggio template approvato (re-opener) prima di riprendere i messaggi liberi.

#### Scenario: Riapertura finestra
- **WHEN** il sistema deve contattare un lead la cui finestra di 24 ore è scaduta
- **THEN** invia il template re-opener e attende la risposta dell'utente prima di proseguire in formato libero

### Requirement: Reminder visita via template
Il sistema DEVE poter inviare un promemoria di appuntamento tramite template approvato.

#### Scenario: Promemoria visita
- **WHEN** esiste un appuntamento imminente per il lead
- **THEN** il sistema invia il template di reminder con i dettagli della visita
