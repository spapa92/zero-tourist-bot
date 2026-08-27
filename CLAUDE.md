# CLAUDE.md

Guida per gli assistenti AI che lavorano su questo repository.

## Progetto

**zero-tourist-bot** (brand: **FluxAssist**) — un bot WhatsApp che prequalifica i lead
immobiliari, così che gli agenti smettano di perdere ore con i "turisti dell'immobile"
(contatti senza budget reale, senza mutuo pre-approvato o fuori zona).

Microservizio single-tenant: **un deploy per agenzia**, guidato da un unico file YAML di
configurazione. Il carico di riferimento è < 100 conversazioni/giorno, quindi tutto è
volutamente piccolo e senza fronzoli.

Flusso: inbound WhatsApp → slot-filling LangGraph (`intento, zona, tipologia, budget, mutuo`)
→ routing config-driven → **in target**: crea lo slot su Google Calendar / **fuori target**:
congedo educato + link al sito dell'agenzia. Ogni turno viene loggato su Postgres.

La motivazione di business e le decisioni architetturali già chiuse stanno in
`docs/assessment.md`. Leggilo prima di proporre cambi di architettura: quasi tutte le
alternative sono già state valutate e scartate lì (runtime Java/Node, API WhatsApp non
ufficiali, Cal.com, cloud gestito).

## Comandi

```bash
# Setup (nessun venv è versionato; creane uno se vuoi isolamento)
pip install -r requirements.txt
pip install pytest ruff langgraph-checkpoint-sqlite   # solo dev, vedi nota sotto

pytest                        # suite completa — 40 test, ~1s, non serve rete
pytest tests/test_graph.py -q # singolo file

ruff check .                  # gate di lint — deve restare pulito

alembic upgrade head          # applica le migrazioni (URL da DATABASE_URL, non da alembic.ini)
uvicorn app.main:app --reload # server locale su :8000

docker compose up -d          # app + Postgres + Caddy (serve un dominio reale nel Caddyfile)
```

**Dipendenza di sviluppo mancante:** `tests/test_checkpointer.py` importa
`langgraph.checkpoint.sqlite`, ma `langgraph-checkpoint-sqlite` non è dichiarato né in
`requirements.txt` né nell'extra `dev` di `pyproject.toml`. Installalo a mano, altrimenti quel
test fallisce con `ModuleNotFoundError`.

**Non lanciare `ruff format .` sull'intero repo.** Quattro file già versionati
(`alembic/versions/0001_initial.py`, `app/graph/builder.py`, `app/whatsapp/client.py`,
`tests/test_e2e.py`) divergono dall'output di ruff-format. Il gate applicato è `ruff check`;
una formattazione a tappeto seppellirebbe le modifiche vere sotto il rumore. Formatta solo le
righe che tocchi davvero.

## Architettura

```
POST /webhook  (app/whatsapp/webhook.py)
  ├─ verify_signature()          HMAC-SHA256 sul body grezzo, X-Hub-Signature-256 → 403 se fallisce
  ├─ repository.get_or_create_lead() + add_message("user", …)
  ├─ container.graph.invoke({phone, user_message}, thread_id=phone)
  │     app/graph/builder.py — 4 nodi, tutti terminali (un nodo per turno, poi END):
  │       classify → detect_exit()  ──────────────► exit      (STOP / UMANO / AIUTO)
  │                → llm.extract_slots() + merge ─► ask       (chiede il primo campo mancante)
  │                                              └► route     (tutti e 5 gli slot pieni)
  ├─ whatsapp.send_reply()        formato libero dentro la finestra 24h, altrimenti template re-opener
  └─ repository.add_message("bot", …) + save_outcome() quando si è arrivati a una decisione
```

| Percorso | Responsabilità |
|---|---|
| `app/main.py` | Factory FastAPI; mette `settings` e `container` su `app.state` |
| `app/deps.py` | Costruisce il container — unico punto che sceglie le implementazioni concrete |
| `app/container.py` | Dataclass che tiene insieme i singleton già cablati |
| `app/config/settings.py` | Impostazioni da env/`.env` (pydantic-settings, `@lru_cache`) |
| `app/config/agency_config.py` | Regole YAML per agenzia → `AgencyConfig` |
| `app/domain/slots.py` | Modello `Slots`, `FIELD_ORDER`, `merge()`, `missing_fields()` |
| `app/graph/` | Builder LangGraph, TypedDict `ConversationState`, factory del checkpointer |
| `app/routing/engine.py` | `route(slots, config) -> RoutingResult` — puro, nessun I/O |
| `app/llm/` | Protocol `LLMClient` + `GeminiClient` + `RegexFallbackClient` |
| `app/whatsapp/` | Client Meta Cloud API (logica finestra 24h) + router del webhook |
| `app/gcalendar/client.py` | Protocol `CalendarClient` + implementazione Google + `next_business_day_slot()` |
| `app/db/` | Modelli SQLAlchemy (`lead`, `message`, `outcome`), funzioni repository, session factory |

Le integrazioni esterne stanno dietro interfacce `typing.Protocol` (`LLMClient`,
`CalendarClient`): i test iniettano dei fake e i provider restano sostituibili via
configurazione. Mantieni questa impostazione.

## Convenzioni

- **Italiano per tutto ciò che legge una persona dentro il progetto**: docstring, commenti,
  corpo dei commit, documentazione e ogni stringa del bot rivolta all'utente. Gli identificatori
  restano nello stile misto già presente: i termini di dominio sono in italiano (`intento`,
  `zona`, `mutuo`, `slots`), l'infrastruttura in inglese.
- **Conventional commits** (`feat:`, `fix:`, `docs:`, …), con l'oggetto in inglese.
- **Le regole di routing sono dati, mai codice.** Zone, soglie di budget, intenti/tipologie
  ammessi e stati del mutuo vivono nello YAML dell'agenzia (`config/agency.example.yaml`), non
  in rami `if`. `app/routing/engine.py` è un motore generico che applica ciò che dice la config.
- **La macchina a stati è deterministica; l'LLM si limita a estrarre.** `GeminiClient` fa
  estrazione strutturata degli slot (JSON schema) e nient'altro. Non lasciare mai al modello la
  decisione in/out target, la formulazione delle risposte o il controllo di flusso: è questa la
  garanzia anti-allucinazione.
- `from __future__ import annotations` in cima a ogni modulo; type hint moderni (`str | None`).
- Lunghezza riga 100, regole ruff `E, F, I, W`, Python ≥ 3.11.
- I segreti non finiscono mai in git: `.gitignore` copre già `.env`, `*credentials*.json`, `*.db`.

## Modello dati

`lead` (telefono, `last_inbound_at` — governa la finestra 24h) → `message` (ruolo `user`/`bot`,
contenuto) → `outcome` (decisione `in_target`/`out_target`/`exit`, slot estratti come JSON,
`appointment_status`).

`outcome.appointment_status` è volutamente inutilizzato in Fase 1: come spiega
`docs/assessment.md`, la ground truth del "turista" è il **no-show** a calendario, ed è
l'etichetta futura per lo scoring predittivo di Fase 2. Ora si loggano i dati, si predice dopo:
non aggiungere scoring alla Fase 1.

Le migrazioni sono scritte a mano in `alembic/versions/`. `alembic/env.py` sovrascrive l'URL di
`alembic.ini` con `Settings.database_url`: imposta `DATABASE_URL` invece di modificare l'ini.

## Test

- I test sono offline per scelta. Usa `tests/helpers.py` (`FakeLLM`, `FakeCalendar`) e la fixture
  `agency_config` da `conftest.py`; non aggiungere mai test che chiamano Gemini, Meta o Google.
- `FakeLLM` è una lookup su dizionario con chiave il testo **esatto** del messaggio: un messaggio
  non mappato restituisce `Slots()` vuoto. Se aggiungi un turno di conversazione a un test,
  aggiungi anche la sua mappatura.
- I test SQLAlchemy costruiscono un engine in memoria
  (`create_engine("sqlite://")` + `Base.metadata.create_all`) invece di lanciare Alembic.
- Un comportamento nuovo richiede un test nel corrispondente `tests/test_*.py` prima che il task
  possa dirsi concluso.

## Insidie note

- **La lookup su `budget_by_zone` è a chiave esatta**, mentre il match della zona in `_matches()`
  è case-insensitive su sottostringa. `RegexFallbackClient` restituisce le zone in minuscolo,
  quindi un `"milano"` estratto dal fallback manca la chiave `"Milano"` e ricade silenziosamente
  su `min_budget`. Se tocchi uno dei due lati, normalizza entrambi.
- **Il fallback a regex è a tempo di selezione, non a runtime.** `build_container` sceglie
  `RegexFallbackClient` quando `LLM_PROVIDER=fallback` o `GEMINI_API_KEY` è vuota, ma una
  chiamata a Gemini che fallisce *durante* la conversazione risale dal nodo `classify` e manda il
  webhook in 500: la degradazione promessa in `docs/assessment.md` §5 non è ancora implementata.
  Incapsula `extract_slots` prima di farci affidamento.
- **`_handle_message` è sincrona dentro un endpoint `async`**, quindi le chiamate HTTP bloccanti
  girano sull'event loop. Accettabile a questo traffico; da rivedere prima di alzare i volumi.
- **Il checkpointer Postgres degrada in silenzio.** `build_checkpointer` inghiotte gli errori di
  connessione e restituisce `MemorySaver()`: un DB mal configurato sembra sano mentre perde lo
  stato conversazionale a ogni riavvio.
- **`thread_id` è il numero di telefono**, quindi lo stato LangGraph e l'identità del lead
  condividono la stessa chiave.
- Finestra di servizio 24h di Meta: fuori da essa si inviano solo template approvati (`reopener`,
  `reminder_visita`). `send_reply()` gestisce già questo instradamento: non chiamare `send_text`
  direttamente.
- `next_business_day_slot()` usa orario locale naive mentre gli eventi Google sono fissati su
  `Europe/Rome`: il fuso orario del container conta.

## Workflow OpenSpec

Il repository adotta lo sviluppo spec-driven (`openspec/`, più le skill in `.claude/skills/` e i
comandi slash in `.claude/commands/opsx/`). La CLI `openspec` **non è installata** in questo
container: leggi e modifica direttamente i file markdown.

`openspec/changes/fluxassist-mvp/` contiene il change attivo: `proposal.md` (perché/cosa),
`design.md` (decisioni e alternative), `tasks.md` (checklist) e le spec per capability sotto
`specs/<capability>/spec.md`, con `Requirement:` / `#### Scenario:` in forma WHEN/THEN.

Quando implementi qualcosa coperto da un task, spuntalo in `tasks.md`. I cinque punti aperti
(4.2, 8.1, 9.1, 9.2, 10.2) sono già scritti e coperti da test con mock: attendono solo credenziali
reali (chiave Gemini, service account Google, un dominio, un numero WhatsApp verificato), come
annota `tasks.md` in fondo. Non "implementarli" di nuovo.

## Configurazione

Copia `.env.example` in `.env`. Variabili principali: `AGENCY_CONFIG_PATH`, `DATABASE_URL`
(SQLite in locale, Postgres in Docker), i quattro valori `WHATSAPP_*`, `GEMINI_API_KEY` /
`LLM_PROVIDER` (`gemini` | `fallback`) e `GOOGLE_CALENDAR_CREDENTIALS`. Ogni campo ha un default
sensato in `Settings`, quindi l'app parte anche senza `.env`: semplicemente gira con il fallback
a regex e senza calendario.
