# CLAUDE.md

Guidance for AI assistants working in this repository.

## Project

**zero-tourist-bot** (brand: **FluxAssist**) — a WhatsApp bot that pre-qualifies real-estate
leads so agents stop losing hours on "property tourists" (contacts with no real budget,
no mortgage pre-approval, or outside the served area).

Single-tenant microservice: **one deploy per agency**, driven by one YAML config file.
Target load is < 100 conversations/day, so everything is deliberately small and boring.

Flow: WhatsApp inbound → LangGraph slot-filling (`intento, zona, tipologia, budget, mutuo`)
→ config-driven routing → **in target**: book a Google Calendar slot / **out of target**:
polite dismissal + link to the agency website. Every turn is logged to Postgres.

Business rationale and closed architectural decisions live in `docs/assessment.md`.
Read it before proposing architectural changes — most alternatives were already evaluated
and rejected there (Java/Node runtimes, unofficial WhatsApp APIs, Cal.com, managed cloud).

## Commands

```bash
# Setup (no venv is committed; create one if you want isolation)
pip install -r requirements.txt
pip install pytest ruff langgraph-checkpoint-sqlite   # dev-only, see note below

pytest                        # full suite — 40 tests, ~1s, no network required
pytest tests/test_graph.py -q # single file
ruff check .                  # lint gate — must stay clean

alembic upgrade head          # apply migrations (URL comes from DATABASE_URL, not alembic.ini)
uvicorn app.main:app --reload # local server on :8000

docker compose up -d          # app + Postgres + Caddy (needs a real domain in Caddyfile)
```

**Dev-dependency gap:** `tests/test_checkpointer.py` imports `langgraph.checkpoint.sqlite`, but
`langgraph-checkpoint-sqlite` is declared in neither `requirements.txt` nor the `dev` extra in
`pyproject.toml`. Install it manually or that test fails with `ModuleNotFoundError`.

**Do not run `ruff format .` repo-wide.** Four committed files (`alembic/versions/0001_initial.py`,
`app/graph/builder.py`, `app/whatsapp/client.py`, `tests/test_e2e.py`) drift from ruff-format
output. `ruff check` is the enforced gate; a blanket format would bury real changes in noise.
Format only the lines you actually touch.

## Architecture

```
POST /webhook  (app/whatsapp/webhook.py)
  ├─ verify_signature()          HMAC-SHA256 over the raw body, X-Hub-Signature-256 → 403 on fail
  ├─ repository.get_or_create_lead() + add_message("user", …)
  ├─ container.graph.invoke({phone, user_message}, thread_id=phone)
  │     app/graph/builder.py — 4 nodes, all terminal (one node per turn, then END):
  │       classify → detect_exit()  ──────────────► exit      (STOP / UMANO / AIUTO)
  │                → llm.extract_slots() + merge ─► ask       (asks first missing field)
  │                                              └► route     (all 5 slots filled)
  ├─ whatsapp.send_reply()        free-form inside the 24h window, else the re-opener template
  └─ repository.add_message("bot", …) + save_outcome() when a decision was reached
```

| Path | Responsibility |
|---|---|
| `app/main.py` | FastAPI factory; stashes `settings` + `container` on `app.state` |
| `app/deps.py` | Wires the container — the only place that picks concrete implementations |
| `app/container.py` | Plain dataclass holding the wired singletons |
| `app/config/settings.py` | Env/`.env` settings (pydantic-settings, `@lru_cache`) |
| `app/config/agency_config.py` | Per-agency YAML rules → `AgencyConfig` |
| `app/domain/slots.py` | `Slots` model, `FIELD_ORDER`, `merge()`, `missing_fields()` |
| `app/graph/` | LangGraph builder, `ConversationState` TypedDict, checkpointer factory |
| `app/routing/engine.py` | `route(slots, config) -> RoutingResult` — pure, no I/O |
| `app/llm/` | `LLMClient` Protocol + `GeminiClient` + `RegexFallbackClient` |
| `app/whatsapp/` | Meta Cloud API client (24h window logic) + webhook router |
| `app/gcalendar/client.py` | `CalendarClient` Protocol + Google impl + `next_business_day_slot()` |
| `app/db/` | SQLAlchemy models (`lead`, `message`, `outcome`), repository fns, session factory |

External integrations sit behind `typing.Protocol` interfaces (`LLMClient`, `CalendarClient`),
so tests inject fakes and providers are swappable by config. Keep it that way.

## Conventions

- **Italian for anything a human reads inside the project**: docstrings, code comments, commit
  bodies, docs, and every user-facing bot string. Identifiers stay in the existing mixed style —
  domain terms are Italian (`intento`, `zona`, `mutuo`, `slots`), plumbing is English.
- **Conventional commits** (`feat:`, `fix:`, `docs:`, …), subject line in English.
- **Routing rules are data, never code.** Zones, budget thresholds, allowed intents/types and
  mortgage states belong in the agency YAML (`config/agency.example.yaml`), not in `if` branches.
  `app/routing/engine.py` is a generic engine that applies whatever the config says.
- **The state machine is deterministic; the LLM only extracts.** `GeminiClient` does structured
  slot extraction (JSON schema) and nothing else. Never let the model decide in/out target,
  phrase replies, or drive control flow — that is the anti-hallucination guarantee.
- `from __future__ import annotations` at the top of every module; modern type hints (`str | None`).
- Line length 100, ruff lint rules `E, F, I, W`, Python ≥ 3.11.
- Secrets never land in git — `.gitignore` already covers `.env`, `*credentials*.json`, `*.db`.

## Data model

`lead` (phone, `last_inbound_at` — drives the 24h window) → `message` (role `user`/`bot`, content)
→ `outcome` (decision `in_target`/`out_target`/`exit`, extracted slots as JSON, `appointment_status`).

`outcome.appointment_status` is intentionally unused in Phase 1: per `docs/assessment.md`,
the ground truth for "tourist" is the calendar **no-show**, and it is the future label for the
Phase 2 predictive scoring. Log data now, predict later — do not add scoring to Phase 1.

Migrations are hand-written in `alembic/versions/`. `alembic/env.py` overrides the URL in
`alembic.ini` with `Settings.database_url`, so set `DATABASE_URL` rather than editing the ini.

## Testing

- Tests are offline by design. Use `tests/helpers.py` (`FakeLLM`, `FakeCalendar`) and the
  `agency_config` fixture from `conftest.py`; never add a test that calls Gemini, Meta or Google.
- `FakeLLM` is a dict lookup keyed by the **exact** message text — an unlisted message returns
  empty `Slots()`. When you add a conversation turn to a test, add its mapping too.
- SQLAlchemy tests build their own in-memory engine (`create_engine("sqlite://")` +
  `Base.metadata.create_all`) instead of running Alembic.
- New behaviour needs a test in the matching `tests/test_*.py` before the task counts as done.

## Gotchas

- **`budget_by_zone` lookup is exact-key**, while zone matching in `_matches()` is
  case-insensitive substring. `RegexFallbackClient` lowercases zones, so a fallback-extracted
  `"milano"` misses the `"Milano"` key and silently falls back to `min_budget`. Normalize on both
  sides if you touch either.
- **The regex fallback is selection-time, not runtime.** `build_container` picks
  `RegexFallbackClient` when `LLM_PROVIDER=fallback` or `GEMINI_API_KEY` is empty, but a Gemini
  call that fails at runtime propagates out of the `classify` node and 500s the webhook — the
  degradation promised in `docs/assessment.md` §5 is not implemented yet. Wrap `extract_slots`
  before relying on it.
- **`_handle_message` is synchronous inside an `async` endpoint**, so blocking HTTP calls run on
  the event loop. Fine at this traffic level; revisit before raising volume.
- **The Postgres checkpointer degrades silently.** `build_checkpointer` swallows connection errors
  and returns `MemorySaver()`, so a misconfigured DB looks healthy while losing conversation state
  on restart.
- **`thread_id` is the phone number**, so LangGraph state and lead identity are the same key.
- Meta's 24h service window: outside it only approved templates send (`reopener`,
  `reminder_visita`). `send_reply()` already routes this — don't call `send_text` directly.
- `next_business_day_slot()` uses naive local time while Google events are pinned to
  `Europe/Rome`; the container's timezone matters.

## OpenSpec workflow

This repo uses spec-driven development (`openspec/`, plus skills in `.claude/skills/` and slash
commands in `.claude/commands/opsx/`). The `openspec` CLI is **not installed** in this container —
read and edit the markdown artifacts directly.

`openspec/changes/fluxassist-mvp/` holds the active change: `proposal.md` (why/what),
`design.md` (decisions + alternatives), `tasks.md` (checklist), and per-capability specs under
`specs/<capability>/spec.md` using `Requirement:` / `#### Scenario:` with WHEN/THEN.

When you implement something covered by a task, tick it in `tasks.md`. The five open items
(4.2, 8.1, 9.1, 9.2, 10.2) are all coded and mock-tested — they only await real credentials
(Gemini key, Google service account, a domain, a verified WhatsApp number), as `tasks.md` notes
at the bottom. Do not "implement" them again.

## Configuration

Copy `.env.example` → `.env`. Key variables: `AGENCY_CONFIG_PATH`, `DATABASE_URL` (SQLite locally,
Postgres in Docker), the four `WHATSAPP_*` values, `GEMINI_API_KEY` / `LLM_PROVIDER`
(`gemini` | `fallback`), and `GOOGLE_CALENDAR_CREDENTIALS`. Every field has a sane default in
`Settings`, so the app boots with no `.env` — it just runs with the regex fallback and no calendar.
