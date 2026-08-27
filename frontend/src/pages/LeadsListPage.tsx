import { useEffect, useState } from "react";
import { fetchLeads, type LeadListItem } from "../api/client";
import LeadsTable from "../components/LeadsTable";

const PAGE_SIZE = 25;

export default function LeadsListPage() {
  const [leads, setLeads] = useState<LeadListItem[]>([]);
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    fetchLeads({ q: query || undefined, limit: PAGE_SIZE, offset })
      .then((response) => {
        if (cancelled) return;
        setLeads(response.items);
        setTotal(response.total);
        setError(null);
      })
      .catch((err) => {
        if (!cancelled) setError(String(err));
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [query, offset]);

  return (
    <div>
      <div className="toolbar">
        <input
          type="search"
          placeholder="Cerca per numero di telefono…"
          value={query}
          onChange={(event) => {
            setOffset(0);
            setQuery(event.target.value);
          }}
        />
      </div>

      {error && <p className="error">{error}</p>}
      {loading ? (
        <p className="empty-state">Caricamento…</p>
      ) : (
        <>
          <LeadsTable leads={leads} />
          <div className="pagination">
            <button disabled={offset === 0} onClick={() => setOffset(Math.max(0, offset - PAGE_SIZE))}>
              ← Precedenti
            </button>
            <span>
              {total === 0 ? 0 : offset + 1}–{Math.min(offset + PAGE_SIZE, total)} di {total}
            </span>
            <button
              disabled={offset + PAGE_SIZE >= total}
              onClick={() => setOffset(offset + PAGE_SIZE)}
            >
              Successivi →
            </button>
          </div>
        </>
      )}
    </div>
  );
}
