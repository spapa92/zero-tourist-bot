## 1. Setup del progetto

- [x] 1.1 Inizializzare il progetto Python (pyproject/requirements, venv, struttura moduli `app/`) e verificare che l'app FastAPI risponda su `/health` con `200`
- [x] 1.2 Aggiungere le dipendenze (fastapi, uvicorn, langgraph, sqlalchemy, alembic, httpx, pydantic) e verificare che `pip install` completi senza errori
- [x] 1.3 Configurare lint/formattazione (ruff) e verificare che `ruff check` passi pulito

## 2. Config e modello di dominio

- [x] 2.1 Definire il modello di configurazione agenzia (zone servite, soglie budget, regole mutuo, intenzioni ammesse) e il caricatore da file YAML; verificare con un test che una config valida venga caricata
- [x] 2.2 Definire lo schema degli slot `{intento, zona, tipologia, budget, mutuo}` (pydantic) e verificare che la validazione rigetti campi mancanti/tipati male
- [x] 2.3 Definire una config di esempio per un'agenzia fittizia e verificare che sia parsabile

## 3. Persistenza (PostgreSQL + SQLAlchemy + Alembic)

- [x] 3.1 Creare i modelli `lead`, `message`, `outcome` e verificare che `alembic upgrade head` crei le tabelle
- [x] 3.2 Configurare il checkpointer LangGraph su Postgres e verificare che uno stato venga salvato e ripristinato dopo un riavvio simulato
- [x] 3.3 Implementare il salvataggio del lead log (slot, decisione, esito) e verificare con un test di lettura/scrittura

## 4. LLMClient e fallback deterministico

- [x] 4.1 Implementare l'interfaccia `LLMClient.extract_slots(text) -> Slots` e verificare che un fake client iniettato venga usato dal motore
- [ ] 4.2 Implementare l'adattatore Gemini Flash con output strutturato e verificare con una chiamata reale su un messaggio di esempio
- [x] 4.3 Implementare il fallback deterministico a regole/regex e verificare che venga usato quando l'LLM va in errore o timeout

## 5. Motore conversazionale (LangGraph)

- [x] 5.1 Implementare il grafo di slot-filling (accoglienza → estrazione → richiesta campo mancante) e verificare con un test end-to-end su conversazione simulata
- [x] 5.2 Implementare le uscite globali (`STOP`, `UMANO`, `AIUTO`) e verificare che vengano intercettate in ogni stato
- [x] 5.3 Implementare l'ordine di fallback (intenzione → zona → tipologia → budget → mutuo) e verificare che il campo giusto venga richiesto

## 6. Routing config-driven

- [x] 6.1 Implementare il motore di routing che applica la config agli slot e verificare che produca in/out target su casi limite (zona fuori, budget sotto soglia, mutuo non approvato)
- [x] 6.2 Implementare il messaggio di congedo con link al sito e verificare che venga inviato al lead fuori target

## 7. Gateway WhatsApp (webhook + finestra 24h)

- [x] 7.1 Implementare il webhook Meta con verifica firma e challenge di verifica; verificare che una richiesta non autenticata venga rifiutata
- [x] 7.2 Implementare l'invio risposte in formato libero dentro la finestra 24h e verificare con un mock del provider
- [x] 7.3 Implementare il re-opener e il template reminder; verificare che fuori finestra venga inviato il template e non un messaggio libero

## 8. Calendar booking

- [ ] 8.1 Implementare la creazione dello slot su Google Calendar per i lead in target e verificare con un evento creato su un calendario di test
- [x] 8.2 Implementare la conferma all'utente e la gestione dell'errore di prenotazione; verificare che un errore venga segnalato per intervento umano

## 9. Deploy (Docker Compose + Caddy)

- [ ] 9.1 Scrivere `Dockerfile` e `docker-compose.yml` (app + Postgres + Caddy) e verificare che `docker compose up` avvii tutti i servizi
- [ ] 9.2 Configurare Caddy con auto-TLS per il webhook e verificare che l'endpoint risponda su HTTPS

## 10. Integrazione e test

- [x] 10.1 Scrivere un test end-to-end che simula una conversazione completa (inbound → qualifica → routing → esito) e verificare che passi
- [ ] 10.2 Verificare l'intero flusso contro un numero WhatsApp di test e confermare accoglienza, qualifica, slot e congedo

---

### Note sui task rimanenti (richiedono credenziali/infrastruttura esterne)

Il codice per questi task è già implementato e coperto da test con mock; manca solo la verifica con credenziali reali:

- **4.2** — `GEMINI_API_KEY` reale per una chiamata live.
- **8.1** — credenziali service account Google Calendar (`GOOGLE_CALENDAR_CREDENTIALS`).
- **9.1** — `docker compose config -q` valida, ma `docker compose up` richiede dominio/credenziali per build + avvio completo.
- **9.2** — richiede un dominio reale per l'emissione TLS di Caddy.
- **10.2** — richiede un numero WhatsApp business verificato e i token Meta.
