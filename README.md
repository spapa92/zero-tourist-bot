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
* **Messaging Provider:** Meta WhatsApp Business Cloud API (o 360dialog)
* **Database:** PostgreSQL (Persistenza dello stato conversazionale e lead log)
* **Calendario:** Google Calendar API (generazione slot)
* **Deployment:** VPS + Docker / Docker Compose + Caddy (auto-TLS)