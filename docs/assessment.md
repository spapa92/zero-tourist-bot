# Assessment — Stack Tecnologico & Architettura

> Esito dell'analisi iniziale del progetto **zero-tourist-bot** (brand FluxAssist).
> Data: Agosto 2026 · Stato: **decisioni chiuse, pronti alla formalizzazione**.

---

## 1. Il problema

Nel settore immobiliare, l'acquisizione lead via WhatsApp soffre di:
- 10–15 ore/settimana perse dagli agenti in qualificazione manuale.
- Oltre il 60% dei contatti è "turista immobiliare": budget insufficiente, mutuo non pre-approvato, fuori zona.
- Risposta lenta = conversione persa; risposta H24 manuale = insostenibile.

## 2. La soluzione

Microservizio autonomo (brand **FluxAssist**) che si interpone tra i canali dell'agenzia e l'agenda degli agenti: accoglie H24, prequalifica in modo conversazionale, instrada i lead in-target verso lo slot calendario e congeda i fuori-target reindirizzandoli al sito.

---

## 3. Vincoli di partenza

| Vincolo | Valore |
|---|---|
| Volume | < 100 conversazioni/giorno (≈ 4–5 msg/ora di picco) |
| Team | sviluppatore singolo, nessuna preferenza di linguaggio |
| Produzione | da subito, ma **minimal** |
| Tenant | **single-tenant** (un deploy per agenzia) |
| Predizione | rimandata a **Fase 2** |

---

## 4. Decisione runtime

**Scelta: Python unico runtime (FastAPI + LangGraph).**

Il README originario indicava "Java Spring Boot / Next.js" ma l'orchestrazione scelta è LangGraph, che è Python-first. Un team singolo senza vincoli di linguaggio non ha motivo di spezzare il progetto in due runtime. Scartati: Java Spring Boot (verbosità, ecosistema AI debole), Node/TS (LangGraph.js meno maturo), polyglot (due runtime da mantenere da soli).

## 5. Decisione LLM

**Scelta: Gemini Flash 2.x di default, dietro un `LLMClient` swappabile.**

L'LLM serve solo per **estrazione dati** (NER/slot-filling con output strutturato), non per ragionare: la macchina a stati è deterministica.

| Candidato | Costo ~100 conv/g | GDPR/Data residency | Verdetto |
|---|---|---|---|
| Gemini Flash 2.x | ~5–15€/mese | EU residency opzionale | **scelto** |
| Claude Haiku 3.5 | ~20–40€/mese | US | valido, più caro |
| DeepSeek V3 | ~2–8€/mese | Cina (rischio GDPR) | scartato per dati sensibili |

Architetturalmente: provider dietro un'interfaccia sottile (`extract_slots(text) -> Schema`), quindi sostituibile via configurazione. **Fallback deterministico a regole/regex** per degradare senza morire se l'LLM è lento/down.

## 6. Decisione messaging WhatsApp

**Scelta: Meta WhatsApp Business Cloud API (o 360dialog).**

Problema noto: la **finestra di servizio 24h** — fuori finestra si possono inviare solo template approvati.

**Strategia: inbound-first + re-opener + 2 template.**

Il bot è *inbound-first* (l'utente scrive per primo), quindi il 90% della conversazione vive dentro la finestra e non tocca i template. I template servono solo per:

1. **Re-opener** (utility): riapre conversazioni fredde e copre anche l'handoff —
   *"Ciao {{1}}, vuoi ancora procedere con la ricerca dell'immobile?"*
2. **Reminder visita** (utility): l'unico caso out-of-window frequente —
   *"Promemoria: appuntamento per la visita di {{1}} alle {{2}}. Rispondi per confermare."*

Regola operativa: ogni contatto fuori finestra passa SEMPRE dal re-opener, poi si torna a messaggi liberi.

**Scartata l'API non ufficiale (Baileys/whatsapp-web.js)**: elimina i template ma viola i ToS e rischia il ban del numero dell'agenzia — inaccettabile per un tool di produzione.

## 7. Decisione calendario

**Scelta: Google Calendar API.** Gratuito, API matura e stabile, l'agenzia ha quasi certamente già un account Google. Cal.com scartato (dipendenza esterna non necessaria ora).

## 8. Decisione flusso di prequalifica

**Scelta: slot-filling flessibile.**

Lo stato è un dizionario di slot `{intento, zona, tipologia, budget, mutuo}`. L'LLM estrae da ogni messaggio tutti i campi riconoscibili; se mancano campi, il bot chiede il prossimo (quello a priorità più alta, con ordine di fallback). Uscite globali sempre intercettate: `STOP`, `VOGLIO UN UMANO`, `AIUTO`.

## 9. Decisione routing

**Scelta: config-driven, regole come dati.**

Le regole (zone servite, soglie budget, regole mutuo, intent ammessi) sono **config**, non codice: un file versionato per agenzia, modificabile senza redeploy. Il codice è un motore generico che applica la config agli slot estratti. Single-tenant → config in file/env, niente tenant isolation, un Postgres per deploy.

I criteri esatti di in/out target non sono ancora definiti (dipendono dall'agenzia) — per questo sono configurabili.

## 10. Memoria & predizione (Fase 1 / Fase 2)

- **Fase 1 (MVP):** le regole configurabili fanno il routing. La memoria *logga* tutto: conversazioni, slot estratti, esito routing, **outcome calendario** (slot preso, visita fatta, no-show).
- **Fase 2:** scoring predittivo del "turista" sopra le regole.

Insight chiave: la **ground truth** del turista non sta nella conversazione ma nel calendario (il no-show). Il collegamento bot ↔ Google Calendar fornisce l'etichetta per la futura predizione.

In termini LangGraph:
- **Memoria breve**: stato conversazionale → *checkpointer* (Postgres).
- **Memoria lunga**: lead log + outcome + statistiche → tabelle Postgres dedicate.

---

## 11. Deploy: cloud vs VPS

**Scelta: VPS (Docker Compose + Caddy auto-TLS).**

| | VPS | Cloud gestito |
|---|---|---|
| Costo | ~5–10€/mese fisso | ~30–80€/mese variabile |
| Fit per 1 microservizio a basso traffico | perfetto | sovradimensionato |
| Postgres | self-hosted | gestito |
| Uptime | buono (Caddy + healthcheck) | SLA 99.9% |
| Scalabilità | verticale, basta | orizzontale, non serve |

A <100 conversazioni/giorno il cloud gestito non ha argomenti a favore. Il costo dominante è l'**LLM** (~10–30€/mese), non l'infrastruttura. Opzione ibrida (app su VPS + Postgres Neon free tier) non necessaria ma disponibile se si vuole zero manutenzione DB.

---

## 12. Stack finale cristallizzato

```
┌───────────────────────────────────────────────────────────────┐
│  VPS — Docker Compose + Caddy (auto-TLS)                      │
│                                                               │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │ FastAPI (webhook) → LangGraph (slot-filling flessibile)  │  │
│  │   stato: {intento,zona,tipologia,budget,mutuo}            │  │
│  │   + uscite globali: STOP · UMANO · AIUTO                  │  │
│  └───────────────┬─────────────────────────────────────────┘  │
│                  │                                            │
│       ┌──────────┼───────────────┐                            │
│       ▼          ▼               ▼                            │
│  ┌─────────┐ ┌─────────┐  ┌──────────────┐                    │
│  │LLMClient│ │ RULES   │  │ CONFIG file  │                    │
│  │Gemini   │ │ engine  │  │ (per agenzia:│                    │
│  │Flash    │ │ (hard   │  │ zone, soglie,│                    │
│  │(swap)   │ │ gates)  │  │ regole mutuo)│                    │
│  └─────────┘ └────┬────┘  └──────────────┘                    │
│                   ▼                                           │
│            in/out target                                      │
│            ├─ in → Google Calendar (slot)                     │
│            └─ out → congedo + sito                            │
│                                                               │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │ PostgreSQL: checkpointer (memoria breve) + lead log      │  │
│  │            + outcome (slot preso / no-show)  ← FASE 2    │  │
│  └─────────────────────────────────────────────────────────┘  │
└───────────────────────────────────────────────────────────────┘
```

| Tema | Scelta |
|---|---|
| Runtime | Python + FastAPI + LangGraph (singolo runtime) |
| LLM | Gemini Flash, dietro `LLMClient` swappabile + fallback deterministico |
| Messaging | Meta WhatsApp Cloud API, inbound-first + re-opener + 2 template |
| Flusso | slot-filling flessibile con ordine di fallback |
| Routing | config-driven, regole come dati (file per agenzia) |
| Tenant | single-tenant |
| Memoria | log + outcome in Fase 1, predizione in Fase 2 (cold-start) |
| Deploy | VPS + Docker Compose + Caddy |

---

## 13. Confine Fase 1 / Fase 2

**Fase 1 (MVP):** slot-filling + regole configurabili + slot calendario + congedo. La memoria logga tutto ma non predice.

**Fase 2:** con i dati accumulati, scoring predittivo del "turista" sopra le regole.
