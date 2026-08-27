# zero-tourist-bot 🤖🏠

> **Filtro autonomo su WhatsApp per qualificare i contatti immobiliari ed eliminare i "turisti dell'immobile" prima che occupino l'agenda degli agenti.**

---

### 🛑 Il Problema di Business
Nel settore immobiliare, l'acquisizione dei lead via WhatsApp soffre di un'enorme inefficienza operativa:
* **Tempo perso in qualificazione:** Gli agenti immobiliari spendono dalle 10 alle 15 ore a settimana a rispondere manualmente a messaggi generici ("È ancora disponibile?", "Quanto costa?").
* **Alto tasso di "Turismo Immobiliare":** Oltre il 60% dei contatti che richiedono informazioni o visite non ha la reale capacità finanziaria (budget insufficiente o mutuo non pre-approvato) o si trova fuori target per la zona.
* **Lentezza nella risposta:** Rispondere dopo diverse ore a un lead caldo riduce drasticamente le probabilità di conversione, mentre rispondere H24 manualmente è insostenibile per piccole e medie agenzie.

---

### 💡 La Soluzione
Un microservizio autonomo sviluppato sotto il brand **FluxAssist** che si interpone tra i canali di contatto dell'agenzia e l'agenda degli agenti.

L'agente virtuale gestisce la conversazione su WhatsApp attraverso una macchina a stati rigida:
1. **Risposta Istantanea:** Accoglie l'utente H24 sul numero dell'agenzia.
2. **Prequalificazione Stringente:** Raccoglie in modo conversazionale i dati chiave (*Intenzione, Zona, Tipologia, Budget reale e Stato del Mutuo*).
3. **Instradamento Intelligente:**
   * **In Target:** Genera automaticamente lo slot sul calendario (via API) per la visita o la chiamata conoscitiva.
   * **Fuori Target:** Congeda educatamente il contatto e lo reindirizza al sito web dell'agenzia, risparmiando tempo al team di vendita.

---

### 🛠 Stack Tecnologico
* **Backend:** Python + FastAPI (Webhook handler & API)
* **AI Orchestration:** LangGraph (Stateful graph routing anti-allucinazione)
* **LLM:** Gemini Flash dietro un `LLMClient` swappabile (fallback deterministico a regole)
* **Messaging Provider:** Meta WhatsApp Cloud API **o** Twilio, dietro un `WhatsAppClient` swappabile — un canale attivo alla volta via `WHATSAPP_PROVIDER` ([guida](docs/whatsapp-providers.md))
* **Database:** PostgreSQL (Persistenza dello stato conversazionale e lead log)
* **Calendario:** Google Calendar API (generazione slot)
* **Deployment:** VPS + Docker / Docker Compose + Caddy (auto-TLS)

---

### 🚀 Installazione

#### Requisiti
* Python 3.11+ (per lo sviluppo locale) oppure Docker + Docker Compose (per un deploy simil-produzione)
* Un numero WhatsApp Business collegato a **Meta Cloud API** o a **Twilio** — vedi [`docs/whatsapp-providers.md`](docs/whatsapp-providers.md) per attivare l'uno o l'altro
* (Opzionale) una `GEMINI_API_KEY` da [aistudio.google.com/apikey](https://aistudio.google.com/apikey) — senza, il bot usa un fallback deterministico a regole/regex
* (Opzionale) un service account Google Calendar, per la creazione automatica degli slot di visita

#### 1. Sviluppo locale (SQLite, senza Docker)

```bash
git clone https://github.com/spapa92/zero-tourist-bot.git
cd zero-tourist-bot

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# Compila almeno WHATSAPP_PROVIDER e le credenziali del canale scelto
```

Configura l'agenzia in `config/agency.example.yaml` (zone servite, soglie budget, regole mutuo)
oppure copialo e punta `AGENCY_CONFIG_PATH` alla tua copia.

Avvia l'app:

```bash
uvicorn app.main:app --reload
```

Verifica che risponda:

```bash
curl http://localhost:8000/health
# {"status":"ok","whatsapp_provider":"meta","whatsapp_configured":false}
```

`whatsapp_configured: false` è normale finché non compili le credenziali del provider scelto:
l'app parte comunque, per poter completare la verifica del webhook lato Meta/Twilio prima ancora
di avere il token di invio.

#### 2. Deploy con Docker Compose (Postgres + Caddy)

```bash
cp .env.example .env
# Compila .env con le credenziali reali
```

Modifica `Caddyfile` con il tuo dominio, poi:

```bash
docker compose up -d --build
```

Il servizio `app` esegue automaticamente `alembic upgrade head` all'avvio (vedi `Dockerfile`) e
si mette in ascolto dietro Caddy, che gestisce il TLS automatico. Verifica:

```bash
curl https://tuo-dominio.example.com/health
```

#### 3. Collegare il webhook WhatsApp

Imposta come callback URL, nella console del provider scelto, `https://tuo-dominio/webhook`
(su Meta serve anche `WHATSAPP_VERIFY_TOKEN` per il challenge di verifica). La procedura completa,
comprese le variabili `TWILIO_*` e come passare da un canale all'altro senza ricreare l'infrastruttura,
è in [`docs/whatsapp-providers.md`](docs/whatsapp-providers.md).

#### 4. Migrazioni database (sviluppo locale)

Con Postgres esterno o SQLite, le migrazioni si eseguono manualmente:

```bash
alembic upgrade head
```

#### Test e lint

```bash
pip install -e ".[dev]"
pytest
ruff check .
```