## 1. Astrazione del provider

- [x] 1.1 Definire l'interfaccia `WhatsAppClient` (invio libero, invio template, `send_reply` con
  finestra 24h, `is_configured`) e verificare con un client fittizio che la logica di finestra sia
  condivisa da tutti i provider
- [x] 1.2 Definire la forma neutra dei parametri di template (`{"1": ..., "2": ...}`) e verificare
  che l'ordinamento posizionale sia rispettato

## 2. Provider Meta

- [x] 2.1 Portare il client Meta esistente sulla nuova interfaccia e verificare i payload di
  `send_text` e `send_template` (componenti del body generate dai parametri posizionali)
- [x] 2.2 Verificare che l'invio senza `WHATSAPP_TOKEN`/`WHATSAPP_PHONE_NUMBER_ID` fallisca con un
  errore esplicito e senza chiamate HTTP

## 3. Provider Twilio

- [x] 3.1 Implementare il client Twilio (Messages API, auth di base, mittente da numero o
  Messaging Service) e verificare il payload di `send_text`
- [x] 3.2 Implementare la normalizzazione degli indirizzi (`whatsapp:+39...`) e verificare i casi
  con e senza prefisso/`+`
- [x] 3.3 Implementare l'invio template via `ContentSid`/`ContentVariables` e verificare che un
  template non mappato fallisca con un errore che nomina la configurazione mancante

## 4. Webhook per canale

- [x] 4.1 Estrarre la gestione del messaggio in entrata (lead log → grafo → risposta → outcome) in
  un handler condiviso e verificare che entrambi i webhook producano lo stesso effetto
- [x] 4.2 Implementare il webhook Twilio (parsing form urlencoded, firma HMAC-SHA1 su URL +
  parametri) e verificare che una firma errata o assente venga rifiutata con `403`
- [x] 4.3 Ricostruire l'URL pubblico dietro reverse proxy (`X-Forwarded-*` o `TWILIO_WEBHOOK_URL`)
  e verificare che la firma sia validata sull'URL pubblico
- [x] 4.4 Montare solo il webhook del provider attivo e verificare che l'endpoint dell'altro
  provider non sia esposto

## 5. Configurazione e documentazione

- [x] 5.1 Aggiungere `WHATSAPP_PROVIDER` e le variabili `TWILIO_*` alle impostazioni, con
  validazione dei valori ammessi, e verificare che un provider sconosciuto venga rigettato
- [x] 5.2 Esporre provider attivo e stato di configurazione su `GET /health`
- [x] 5.3 Documentare i due canali, il passaggio dall'uno all'altro e l'impatto sul formato del
  numero dei lead (`docs/whatsapp-providers.md`, `.env.example`, README)

## 6. Verifiche con credenziali reali

- [ ] 6.1 Verificare il flusso completo sulla sandbox WhatsApp di Twilio (messaggio in entrata,
  qualifica, risposta) con firma attiva
- [ ] 6.2 Verificare l'invio di un template Twilio approvato (re-opener) fuori dalla finestra 24h

---

### Note sui task rimanenti

- **6.1 / 6.2** — richiedono un account Twilio con sandbox attiva (o numero approvato) e un
  endpoint pubblico raggiungibile; il codice è coperto da test con provider e HTTP mockati.
