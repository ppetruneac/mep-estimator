const API_BASE = import.meta.env.VITE_API_URL ?? "";

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
    ...init,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`${res.status} ${text}`);
  }
  return res.json() as Promise<T>;
}

export type Project = {
  id: number;
  name: string;
  premise?: string;
  drawing_count: number;
  occurrence_count: number;
  pending_count: number;
};

export type Drawing = {
  id: number;
  project_id: number;
  drawing_number: string;
  floor_tab_name?: string;
  scale?: string;
  item_count: number;
  pending_count: number;
  approved_count: number;
  excluded_count: number;
};

export type Item = {
  id: number;
  document_id: number;
  item_id?: string;
  annotation?: string;
  qty: number;
  unit: string;
  length_m?: number;
  size?: string;
  measurement_type?: string;
  scope?: string;
  status: string;
  amended_qty?: number;
  amended_notes?: string;
  effective_qty: number;
  category?: string;
  amber_flag: boolean;
  notes?: string;
};

export type SummaryRow = {
  key: string;
  label: string;
  qty: number;
  unit?: string;
  item_count: number;
  excluded_count: number;
};

export const api = {
  projects: () => req<Project[]>("/api/projects"),
  project: (id: number) => req<Project>(`/api/projects/${id}`),
  drawings: (projectId: number) =>
    req<Drawing[]>(`/api/projects/${projectId}/drawings`),
  items: (drawingId: number, qs = "") =>
    req<Item[]>(`/api/drawings/${drawingId}/items${qs}`),
  patchItem: (id: number, body: Record<string, unknown>) =>
    req<Item>(`/api/items/${id}`, { method: "PATCH", body: JSON.stringify(body) }),
  bulk: (drawingId: number, action: "approve" | "exclude") =>
    req<{ updated: number }>(`/api/drawings/${drawingId}/items/bulk`, {
      method: "POST",
      body: JSON.stringify({ action, only_pending: true }),
    }),
  summaryByFloor: (projectId: number) =>
    req<SummaryRow[]>(`/api/projects/${projectId}/summary/by-floor`),
  summaryByCategory: (projectId: number) =>
    req<SummaryRow[]>(`/api/projects/${projectId}/summary/by-category`),
  pdfUrl: (drawingId: number) => `${API_BASE}/api/drawings/${drawingId}/pdf`,
  overlayUrl: (drawingId: number) =>
    `${API_BASE}/api/drawings/${drawingId}/overlay`,
};
