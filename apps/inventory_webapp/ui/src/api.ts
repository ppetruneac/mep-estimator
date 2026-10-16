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

export type ProjectTitleBlock = {
  display_name?: string | null;
  location?: string | null;
  client?: string | null;
  architect?: string | null;
  mep?: string | null;
  mep_address?: string | null;
  mep_web?: string | null;
  stage?: string | null;
  scale?: string | null;
  paper?: string | null;
  disclaimer?: string | null;
  revision?: string | null;
  latest_date?: string | null;
  job_series?: string[];
  floors?: string[];
};

export type Project = {
  id: number;
  uuid: string;
  name: string;
  premise?: string;
  owner?: string | null;
  client?: string | null;
  architect?: string | null;
  drawing_count: number;
  occurrence_count: number;
  pending_count: number;
  title_block?: ProjectTitleBlock | null;
};

export type Drawing = {
  id: number;
  project_id: number;
  project_uuid?: string;
  drawing_number: string;
  key: string;
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
  item_label?: string;
  annotation?: string;
  qty: number;
  unit: string;
  length_m?: number;
  size?: string;
  measurement_type?: string;
  measurement_type_help?: string;
  scope?: string;
  status: string;
  amended_qty?: number;
  amended_notes?: string;
  effective_qty: number;
  category?: string;
  excel_category?: string;
  catalog_category?: string;
  amber_flag: boolean;
  notes?: string;
  linked_to?: string;
};

export type SummaryRow = {
  key: string;
  label: string;
  qty: number;
  unit?: string;
  item_count: number;
  excluded_count: number;
};

export type CatalogueItem = {
  item_id: string;
  legacy_item_id?: string | null;
  category: string;
  description?: string | null;
  item_label?: string | null;
  unit?: string | null;
  scope_default?: string | null;
  catalog_sku?: string | null;
  source?: string | null;
};

export type CatalogueResponse = {
  items: CatalogueItem[];
  categories: { category: string; count: number }[];
};

export type DrawingFacets = {
  categories: { category: string; count: number }[];
  statuses: { key: string; count: number; help?: string | null }[];
  measurement_types: { key: string; count: number; help?: string | null }[];
};

function qs(params: Record<string, string | undefined | null>) {
  const sp = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v != null && v !== "") sp.set(k, v);
  }
  const s = sp.toString();
  return s ? `?${s}` : "";
}

export const api = {
  projects: () => req<Project[]>("/api/projects"),
  project: (uuid: string) => req<Project>(`/api/projects/${uuid}`),
  drawings: (projectUuid: string) =>
    req<Drawing[]>(`/api/projects/${projectUuid}/drawings`),
  drawing: (projectUuid: string, drawingKey: string) =>
    req<Drawing>(
      `/api/projects/${projectUuid}/drawings/${encodeURIComponent(drawingKey)}`
    ),
  items: (
    projectUuid: string,
    drawingKey: string,
    filters: {
      status?: string;
      measurement_type?: string;
      category?: string;
      q?: string;
    } = {}
  ) =>
    req<Item[]>(
      `/api/projects/${projectUuid}/drawings/${encodeURIComponent(drawingKey)}/items${qs(filters)}`
    ),
  facets: (projectUuid: string, drawingKey: string) =>
    req<DrawingFacets>(
      `/api/projects/${projectUuid}/drawings/${encodeURIComponent(drawingKey)}/facets`
    ),
  patchItem: (id: number, body: Record<string, unknown>) =>
    req<Item>(`/api/items/${id}`, { method: "PATCH", body: JSON.stringify(body) }),
  bulk: (
    projectUuid: string,
    drawingKey: string,
    action: "approve" | "exclude",
    filters: {
      status?: string;
      category?: string;
      measurement_type?: string;
      q?: string;
    } = {}
  ) =>
    req<{ updated: number }>(
      `/api/projects/${projectUuid}/drawings/${encodeURIComponent(drawingKey)}/items/bulk`,
      {
        method: "POST",
        body: JSON.stringify({
          action,
          only_pending: false,
          status: filters.status || null,
          category: filters.category || null,
          measurement_type: filters.measurement_type || null,
          q: filters.q || null,
        }),
      }
    ),
  summaryByFloor: (projectUuid: string) =>
    req<SummaryRow[]>(`/api/projects/${projectUuid}/summary/by-floor`),
  summaryByCategory: (projectUuid: string) =>
    req<SummaryRow[]>(`/api/projects/${projectUuid}/summary/by-category`),
  catalogue: (filters: { category?: string; q?: string } = {}) =>
    req<CatalogueResponse>(`/api/catalogue${qs(filters)}`),
  pdfUrl: (projectUuid: string, drawingKey: string) =>
    `${API_BASE}/api/projects/${projectUuid}/drawings/${encodeURIComponent(drawingKey)}/pdf`,
  overlayUrl: (projectUuid: string, drawingKey: string) =>
    `${API_BASE}/api/projects/${projectUuid}/drawings/${encodeURIComponent(drawingKey)}/overlay`,
};
