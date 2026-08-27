# Canali WhatsApp — Meta Cloud API o Twilio

FluxAssist parla WhatsApp attraverso **due canali intercambiabili**, attivi **uno alla volta**.
Si sceglie con una sola variabile d'ambiente:

```bash
WHATSAPP_PROVIDER=meta     # Meta WhatsApp Business Cloud API (default)
WHATSAPP_PROVIDER=twilio   # Twilio Programmable Messaging
```

Il resto dell'applicazione (grafo di qualificazione, routing, calendario, lead log) non sa
quale canale sia attivo: dipende solo dall'interfaccia `WhatsAppClient`.

---

## 1. Cosa cambia tra i due

| | `meta` | `twilio` |
|---|---|---|
| Onboarding | verifica Business Manager + numero + template (lento) | account Twilio + sender WhatsApp; sandbox usabile in minuti |
| Costo | messaggi a tariffa Meta | tariffa Meta + markup Twilio |
| Autenticità webhook | HMAC-SHA256 `X-Hub-Signature-256` sul body | HMAC-SHA1 `X-Twilio-Signature` su URL + parametri |
| Challenge di verifica | `GET /webhook` con `hub.challenge` | non previsto |
| Formato in entrata | JSON | form `application/x-www-form-urlencoded` |
| Template | per nome (es. `reopener`) + lingua | per `ContentSid` (`HX...`) della Content API |
| Formato numero lead | `393331234567` | `+393331234567` |

**L'endpoint pubblico è lo stesso in entrambi i casi: `POST /webhook`.** Cambiare provider non
richiede di toccare Caddy né il DNS: viene montato solo il webhook del canale attivo, quindi
l'endpoint dell'altro provider non esiste finché non lo si attiva.

`GET /health` dice sempre quale canale è attivo e se ha credenziali sufficienti:

```json
{"status": "ok", "whatsapp_provider": "twilio", "whatsapp_configured": true}
```

---

## 2. Configurare il canale Meta

```bash
WHATSAPP_PROVIDER=meta
WHATSAPP_TOKEN=EAAG...              # API Setup → token (permanente via System User)
WHATSAPP_PHONE_NUMBER_ID=1234567890 # API Setup → "Phone number ID"
WHATSAPP_APP_SECRET=...             # Impostazioni app → Base → App secret
WHATSAPP_VERIFY_TOKEN=una-stringa-che-scegli-tu
```

Nel pannello Meta, come callback URL del webhook: `https://tuo-dominio/webhook`, con lo stesso
`WHATSAPP_VERIFY_TOKEN`. Meta chiama prima `GET /webhook` per il challenge: quella verifica ha
bisogno solo di `WHATSAPP_VERIFY_TOKEN`, quindi si può completare **prima** di avere il token di
invio — l'app parte anche con le credenziali incomplete e fallisce (con un errore esplicito) solo
al primo invio.

I template si dichiarano per nome nel Business Manager: servono `reopener` e `reminder_visita`
in lingua `it`.

---

## 3. Configurare il canale Twilio

```bash
WHATSAPP_PROVIDER=twilio
TWILIO_ACCOUNT_SID=AC...
TWILIO_AUTH_TOKEN=...
TWILIO_WHATSAPP_NUMBER=+14155238886        # sandbox o numero WhatsApp approvato
# oppure, in alternativa al numero:
TWILIO_MESSAGING_SERVICE_SID=MG...
```

In Twilio Console → **Messaging → Senders → WhatsApp senders** (o *Sandbox settings* per la
sandbox), imposta *When a message comes in* su `https://tuo-dominio/webhook`, metodo **POST**.

### Template (Content API)

Twilio non usa i nomi dei template ma un `ContentSid`. Crea i due contenuti approvati in
**Messaging → Content Template Builder** e mappali:

```bash
TWILIO_CONTENT_SID_REOPENER=HX...   # template re-opener
TWILIO_CONTENT_SID_REMINDER=HX...   # template reminder visita
```

Le variabili sono posizionali (`{{1}}`, `{{2}}`) in entrambi i canali: il codice passa
`{"1": "...", "2": "..."}` e ogni provider le traduce (componenti per Meta,
`ContentVariables` per Twilio). Se manca il `ContentSid` di un template usato, l'invio fallisce
con `TemplateNotConfigured` e un messaggio che nomina la variabile mancante — non con un errore
generico di Twilio.

Nota: dentro la finestra 24h il bot non usa mai i template, quindi si può partire senza i
`ContentSid` e aggiungerli quando serve il re-opener.

### Verifica della firma

Il webhook rifiuta con `403` ogni richiesta la cui `X-Twilio-Signature` non corrisponde. La firma
si calcola su **URL pubblico + parametri POST**, quindi dietro un reverse proxy l'URL va ricostruito
correttamente:

- Caddy propaga `X-Forwarded-Proto` / `X-Forwarded-Host` e la ricostruzione è automatica;
- se la catena di proxy altera gli header (o non li invia), imposta l'URL esatto configurato in
  Twilio:

```bash
TWILIO_WEBHOOK_URL=https://tuo-dominio/webhook
```

`TWILIO_VALIDATE_SIGNATURE=false` disattiva il controllo: utile solo per test manuali in locale,
**mai in produzione** (l'endpoint diventa pubblicamente scrivibile).

---

## 4. Passare da un canale all'altro

1. Configura le variabili del nuovo canale.
2. Cambia `WHATSAPP_PROVIDER` e riavvia (`docker compose up -d --build`).
3. Verifica `GET /health` (`whatsapp_provider` e `whatsapp_configured`).
4. Imposta il webhook `https://tuo-dominio/webhook` nella console del nuovo provider.

⚠️ **I lead sono identificati dal numero nel formato del provider**: Meta consegna
`393331234567`, Twilio `+393331234567`. Se si cambia canale su un deploy con storico, gli stessi
contatti ripartono come lead nuovi (le conversazioni precedenti restano nel DB ma non vengono
riagganciate). In un deploy nuovo la cosa è irrilevante; su uno esistente, se serve continuità,
va normalizzata la colonna `lead.phone` con una migrazione dedicata.
