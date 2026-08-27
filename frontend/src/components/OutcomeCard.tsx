import type { OutcomeOut } from "../api/client";

export default function OutcomeCard({ outcome }: { outcome: OutcomeOut }) {
  const slotEntries = Object.entries(outcome.slots).filter(([, value]) => value !== null);

  return (
    <div className="outcome-card">
      <div className="outcome-header">
        <span className={`badge badge-${outcome.decision}`}>{outcome.decision}</span>
        <span className="outcome-date">
          {new Date(outcome.created_at).toLocaleString("it-IT")}
        </span>
      </div>
      {outcome.appointment_status && (
        <p className="outcome-appointment">Appuntamento: {outcome.appointment_status}</p>
      )}
      {slotEntries.length > 0 && (
        <dl className="outcome-slots">
          {slotEntries.map(([key, value]) => (
            <div key={key} className="outcome-slot">
              <dt>{key}</dt>
              <dd>{String(value)}</dd>
            </div>
          ))}
        </dl>
      )}
    </div>
  );
}
