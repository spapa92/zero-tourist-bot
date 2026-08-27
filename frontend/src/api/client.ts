export interface LeadListItem {
  phone: string;
  created_at: string;
  last_inbound_at: string | null;
  latest_decision: string | null;
  latest_appointment_status: string | null;
}

export interface LeadListResponse {
  items: LeadListItem[];
  total: number;
  limit: number;
  offset: number;
}

export interface MessageOut {
  role: string;
  content: string;
  created_at: string;
}

export interface OutcomeOut {
  decision: string;
  slots: Record<string, unknown>;
  appointment_status: string | null;
  created_at: string;
}

export interface LeadDetailResponse {
  phone: string;
  created_at: string;
  last_inbound_at: string | null;
  messages: MessageOut[];
  outcomes: OutcomeOut[];
}

async function apiFetch<T>(path: string): Promise<T> {
  const response = await fetch(path);
  if (!response.ok) {
    throw new Error(`Richiesta a ${path} fallita: ${response.status}`);
  }
  return (await response.json()) as T;
}

export function fetchLeads(params: {
  q?: string;
  limit?: number;
  offset?: number;
}): Promise<LeadListResponse> {
  const search = new URLSearchParams();
  if (params.q) search.set("q", params.q);
  search.set("limit", String(params.limit ?? 50));
  search.set("offset", String(params.offset ?? 0));
  return apiFetch(`/api/leads?${search.toString()}`);
}

export function fetchLeadDetail(phone: string): Promise<LeadDetailResponse> {
  return apiFetch(`/api/leads/${encodeURIComponent(phone)}`);
}
