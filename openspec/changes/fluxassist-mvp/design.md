## Context

Repository greenfield (nessun codice applicativo esistente). Vincoli: sviluppatore singolo, traffico < 100 conversazioni/giorno, single-tenant, produzione da subito ma minimal. Motivazione e scope in `proposal.md`.

## Goals / Non-Goals

**Goals:**
- Un singolo runtime Python che implementa la Fase 1 (qualifica + routing + slot + congedo + logging).
- Routing configurabile per agenzia senza redeploy del codice.
- Degrado resiliente quando l'LLM non risponde.

**Non-Goals:**
- Predizione/scoring del "turista" (Fase 2).
- Multi-tenancy (tenant isolation, auth multi-agenzia).
- Interfaccia admin o dashboard.
- Broadcast marketing WhatsApp.

## Decisions

### 1. Runtime unico: Python + FastAPI + LangGraph
*Alternative:* Java Spring Boot, Node/TS + LangGraph.js, architettura polyglot.
*Scelta:* un solo runtime Python. LangGraph è Python-first; un team singolo senza vincoli evita il costo di due codebase e di un boundary HTTP interno.

### 2. Flusso: slot-filling flessibile con ordine di fallback
*Alternative:* macchina a stati rigida a sequenza fissa.
*Scelta:* l'LLM estrae da ogni messaggio tutti i campi riconoscibili; lo stato è `{intento, zona, tipologia, budget, mutuo}`. Quando mancano campi, il bot chiede quello a priorità più alta secondo un ordine di fallback predefinito (`intenzione → zona → tipologia → budget → mutuo`). Uscite globali (`STOP`, `UMANO`, `AIUTO`) intercettate ovunque.

### 3. Routing config-driven
*Alternative:* soglie hardcoded nel codice.
*Scelta:* le regole (zone servite, soglie budget, requisiti mutuo, intenzioni ammesse) vivono in un file di configurazione per agenzia (YAML/env), caricato all'avvio o aggiornabile via reload. Il codice è un motore generico che applica la config agli slot estratti. Single-tenant → nessuna colonna tenant, nessuna isolazione.

### 4. LLM dietro `LLMClient` con fallback deterministico
*Alternative:* chiamata diretta al provider dentro il grafo.
*Scelta:* interfaccia sottile `extract_slots(text) -> Schema`, implementazione Gemini Flash di default, sostituibile via configurazione. Fallback deterministico a regole/regex quando la chiamata fallisce o va in timeout, così il bot degrada ma non muore (H24).

### 5. WhatsApp: inbound-first + re-opener + 2 template
*Alternative:* API non ufficiale (Baileys/whatsapp-web.js).
*Scelta:* Meta WhatsApp Business Cloud API ufficiale. Il bot è inbound-first, quindi il grosso della conversazione vive dentro la finestra 24h. Fuori finestra si usano solo 2 template utility: re-opener (riapre la finestra) e reminder visita. L'API non ufficiale è scartata per rischio di ban del numero dell'agenzia.

### 6. Persistenza: checkpointer LangGraph + tabelle lead/outcome
*Scelta:* PostgreSQL su due livelli. Memoria breve = checkpointer LangGraph (stato conversazionale). Memoria lunga = tabelle `lead`, `message`, `outcome` (slot estratti, decisione routing, esito calendario). SQLAlchemy + Alembic per schema e migrazioni.

### 7. Deploy: VPS + Docker Compose + Caddy
*Alternative:* cloud gestito (AWS/GCP), ibrido VPS + DB gestito.
*Scelta:* a < 100 conv/giorno il cloud gestito è sovradimensionato. Compose per app + Postgres, Caddy come reverse proxy con auto-TLS. Opzione futura: spostare solo il DB su Neon/Supabase free tier se si vuole zero manutenzione.

### 8. Calendario: Google Calendar API
*Alternative:* Cal.com.
*Scelta:* Google Calendar API gratuito e maturo; l'agenzia ha già quasi certamente un account Google.

## Risks / Trade-offs

- **Errori di estrazione LLM** (fraintende budget/zona) → fallback deterministico + uscita "UMANO" + log dell'estrazione per controllo.
- **Latenza/approvazione template WhatsApp** → soli 2 template, pattern re-opener, approvazione una tantum.
- **Data residency Gemini** → configurare la regione UE dove disponibile.
- **Outcome no-show non disponibile in Fase 1** → tracciare lo stato dell'appuntamento come campo, sincronizzare lo stato del calendario in Fase 2.
- **Complessità LangGraph per un flusso semplice** → tenere il grafo minimo (un loop di estrazione + routing), evitare sotto-grafi prematuri.

## Migration Plan

- Nessuna migrazione: repo greenfield.
- Deploy iniziale: `docker compose up` su VPS, Caddy fronta il webhook Meta su HTTPS. Rollback = redeploy dell'immagine precedente.

## Open Questions

- Soglie di business esatte per agenzia (zone, budget, mutuo) → da raccogliere dal primo cliente; sono config, non codice.
- Provider WhatsApp definitivo (Meta Cloud API diretta vs 360dialog) → da decidere all'integrazione in base al numero business disponibile.
