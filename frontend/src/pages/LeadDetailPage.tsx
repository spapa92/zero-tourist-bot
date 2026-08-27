import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { fetchLeadDetail, type LeadDetailResponse } from "../api/client";
import ConversationTranscript from "../components/ConversationTranscript";
import OutcomeCard from "../components/OutcomeCard";

export default function LeadDetailPage() {
  const { phone } = useParams<{ phone: string }>();
  const [lead, setLead] = useState<LeadDetailResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!phone) return;
    let cancelled = false;
    fetchLeadDetail(phone)
      .then((response) => {
        if (!cancelled) setLead(response);
      })
      .catch((err) => {
        if (!cancelled) setError(String(err));
      });
    return () => {
      cancelled = true;
    };
  }, [phone]);

  return (
    <div>
      <Link to="/" className="back-link">
        ← Tutti i lead
      </Link>

      {error && <p className="error">{error}</p>}
      {!lead && !error && <p className="empty-state">Caricamento…</p>}

      {lead && (
        <>
          <h2>{lead.phone}</h2>
          <p className="lead-meta">
            Primo contatto: {new Date(lead.created_at).toLocaleString("it-IT")}
          </p>

          {lead.outcomes.length > 0 && (
            <section>
              <h3>Esiti qualifica</h3>
              {lead.outcomes.map((outcome, index) => (
                <OutcomeCard key={index} outcome={outcome} />
              ))}
            </section>
          )}

          <section>
            <h3>Conversazione</h3>
            <ConversationTranscript messages={lead.messages} />
          </section>
        </>
      )}
    </div>
  );
}
