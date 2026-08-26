## Why

Le agenzie immobiliari perdono 10–15 ore/settimana a qualificare manualmente lead WhatsApp, di cui oltre il 60% sono "turisti dell'immobile" (budget insufficiente, mutuo non pre-approvato, fuori zona). Serve un agente virtuale che qualifichi i contatti H24 prima che occupino l'agenda degli agenti.

## What Changes

- Introduce un microservizio **FluxAssist** che accoglie i contatti WhatsApp dell'agenzia e li prequalifica conversazionalmente.
- Implementa una macchina a stati con **slot-filling flessibile** che raccoglie: intenzione, zona, tipologia, budget, stato del mutuo.
- Introduce un **motore di routing config-driven**: le regole in/out target (zone servite, soglie budget, regole mutuo, intent ammessi) sono configurabili per agenzia senza modificare il codice.
- Per i lead **in target**, genera automaticamente lo slot di visita/chiamata su **Google Calendar**.
- Per i lead **fuori target**, congeda educatamente e reindirizza al sito dell'agenzia.
- Persiste conversazioni, slot estratti ed esiti in **PostgreSQL** (lead log + outcome per analisi future).
- Gestisce la **finestra 24h di WhatsApp** con strategia inbound-first, un template re-opener e un template reminder visita.

## Capabilities

### New Capabilities
- `whatsapp-gateway`: ricezione messaggi WhatsApp in entrata (webhook Meta Cloud API), invio risposte, gestione della finestra 24h (re-opener e template).
- `lead-qualification`: la conversazione di prequalifica con slot-filling flessibile (intenzione, zona, tipologia, budget, stato mutuo) e uscite globali (stop, umano, aiuto).
- `lead-routing`: decisione config-driven in/out target applicando le regole dell'agenzia agli slot estratti.
- `calendar-booking`: creazione dello slot di visita/chiamata su Google Calendar per i lead in target.
- `lead-memory`: persistenza di conversazioni, slot ed esiti (outcome) in PostgreSQL per analisi e futura predizione.

### Modified Capabilities

## Impact

- **Nuova codebase**: servizio Python (FastAPI + LangGraph) — repository greenfield.
- **Dipendenze esterne**: Meta WhatsApp Business Cloud API, Google Calendar API, LLM Gemini Flash (dietro `LLMClient` swappabile), PostgreSQL.
- **Infrastruttura**: deploy su VPS con Docker Compose + Caddy (auto-TLS).
- **Nessuna modifica a codice esistente**: il repository non contiene ancora codice applicativo.
