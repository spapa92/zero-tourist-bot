import { Link } from "react-router-dom";
import type { LeadListItem } from "../api/client";

function formatDate(value: string | null): string {
  if (!value) return "—";
  return new Date(value).toLocaleString("it-IT");
}

export default function LeadsTable({ leads }: { leads: LeadListItem[] }) {
  if (leads.length === 0) {
    return <p className="empty-state">Nessun lead trovato.</p>;
  }

  return (
    <table className="leads-table">
      <thead>
        <tr>
          <th>Telefono</th>
          <th>Ultimo contatto</th>
          <th>Primo contatto</th>
          <th>Esito</th>
          <th>Appuntamento</th>
        </tr>
      </thead>
      <tbody>
        {leads.map((lead) => (
          <tr key={lead.phone}>
            <td>
              <Link to={`/leads/${encodeURIComponent(lead.phone)}`}>{lead.phone}</Link>
            </td>
            <td>{formatDate(lead.last_inbound_at)}</td>
            <td>{formatDate(lead.created_at)}</td>
            <td>
              {lead.latest_decision ? (
                <span className={`badge badge-${lead.latest_decision}`}>{lead.latest_decision}</span>
              ) : (
                "—"
              )}
            </td>
            <td>{lead.latest_appointment_status ?? "—"}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
