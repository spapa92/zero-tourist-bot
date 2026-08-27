## Why

L'onboarding sulla Meta WhatsApp Business Cloud API è bloccante: verifica del Business Manager,
verifica del numero e approvazione dei template richiedono giorni e passaggi fuori dal controllo
dello sviluppatore. Twilio espone lo stesso canale WhatsApp con un onboarding molto più rapido
(sandbox utilizzabile in minuti) al costo di un markup sui messaggi.

Legare il gateway a un solo provider significa che un blocco amministrativo blocca l'intero
prodotto. Serve poter scegliere il canale senza toccare il codice.

## What Changes

- Introduce un'interfaccia `WhatsAppClient` (invio libero, invio template, finestra 24h) con due
  implementazioni: **Meta Cloud API** e **Twilio**.
- Il canale attivo si sceglie con `WHATSAPP_PROVIDER` (`meta` | `twilio`): **uno alla volta**.
  Viene montato solo il webhook del provider attivo, sempre su `POST /webhook`, così cambiare
  canale non richiede modifiche a reverse proxy, DNS o URL pubblico.
- Aggiunge il webhook Twilio: parsing del form `application/x-www-form-urlencoded` e validazione
  della firma `X-Twilio-Signature` (HMAC-SHA1 su URL pubblico + parametri ordinati), con l'URL
  pubblico ricostruito dagli header `X-Forwarded-*` o forzato da `TWILIO_WEBHOOK_URL`.
- Uniforma i parametri dei template in una forma neutra (`{"1": ..., "2": ...}`), tradotta in
  componenti per Meta e in `ContentVariables`/`ContentSid` per Twilio.
- La gestione del messaggio in entrata (lead log → grafo → risposta → outcome) diventa condivisa:
  i webhook si limitano ad autenticare la richiesta e normalizzarne il payload.
- `GET /health` espone il canale attivo e se ha credenziali sufficienti per inviare.

## Capabilities

### New Capabilities

### Modified Capabilities
- `whatsapp-gateway`: la ricezione e l'invio non sono più legati alla Meta Cloud API ma a un
  provider selezionabile a configurazione (Meta o Twilio), con verifica di autenticità e
  gestione template specifiche per canale.

## Impact

- **Codice**: `app/whatsapp/` riorganizzato in interfaccia (`client.py`), provider
  (`providers/meta.py`, `providers/twilio.py`), webhook per canale (`webhooks/`), gestione
  condivisa del messaggio (`handler.py`) e selezione (`factory.py`). `app/main.py` monta il
  webhook del canale attivo.
- **Configurazione**: nuove variabili `WHATSAPP_PROVIDER` e `TWILIO_*`. Le variabili Meta
  esistenti restano invariate e `meta` resta il default: i deploy attuali non cambiano
  comportamento.
- **Dati**: il numero del lead è nel formato del provider (`393331234567` per Meta,
  `+393331234567` per Twilio). Cambiare canale su un deploy con storico ricrea i lead; su un
  deploy nuovo è irrilevante.
- **Nessuna nuova dipendenza**: il client Twilio usa `httpx` e la firma è verificata con `hmac`
  della standard library.
