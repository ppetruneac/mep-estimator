import { FormEvent, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api, Drawing, Item } from "../api";

export function DrawingReview() {
  const { projectId, drawingId } = useParams();
  const did = Number(drawingId);
  const pid = Number(projectId);
  const [drawing, setDrawing] = useState<Drawing | null>(null);
  const [items, setItems] = useState<Item[]>([]);
  const [statusFilter, setStatusFilter] = useState("");
  const [showOverlay, setShowOverlay] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [amend, setAmend] = useState<Item | null>(null);

  async function load() {
    const [d, its] = await Promise.all([
      api.drawings(pid).then((ds) => ds.find((x) => x.id === did) || null),
      api.items(did, statusFilter ? `?status=${statusFilter}` : ""),
    ]);
    setDrawing(d);
    setItems(its);
  }

  useEffect(() => {
    load().catch((e) => setErr(String(e)));
  }, [did, pid, statusFilter]);

  async function setStatus(id: number, status: string) {
    await api.patchItem(id, { status });
    await load();
  }

  async function bulk(action: "approve" | "exclude") {
    await api.bulk(did, action);
    await load();
  }

  const pdfSrc = showOverlay ? api.overlayUrl(did) : api.pdfUrl(did);

  return (
    <div className="wrap">
      <div className="header">
        <div>
          <Link to={`/projects/${pid}`}>← {drawing?.floor_tab_name || "Project"}</Link>
          <h1>{drawing?.floor_tab_name}</h1>
          <div className="muted">
            {drawing?.drawing_number} · {drawing?.scale} · {items.length} rows
          </div>
        </div>
      </div>
      {err && <div className="err">{err}</div>}

      <div className="toolbar">
        <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
          <option value="">All statuses</option>
          <option value="pending">Pending</option>
          <option value="approved">Approved</option>
          <option value="excluded">Excluded</option>
          <option value="amended">Amended</option>
        </select>
        <button className="btn primary" onClick={() => bulk("approve")}>
          Approve all pending
        </button>
        <button className="btn danger" onClick={() => bulk("exclude")}>
          Exclude all pending
        </button>
        <button className="btn" onClick={() => setShowOverlay((v) => !v)}>
          {showOverlay ? "Show source PDF" : "Show overlay (if any)"}
        </button>
      </div>

      <div className="split">
        <div className="table-wrap" style={{ maxHeight: "75vh" }}>
          <table>
            <thead>
              <tr>
                <th>Item</th>
                <th>Annotation</th>
                <th>Qty</th>
                <th>Unit</th>
                <th>Type</th>
                <th>Status</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {items.map((it) => (
                <tr key={it.id} className={it.amber_flag || (it.measurement_type && it.measurement_type !== "printed") ? "amber" : ""}>
                  <td>
                    <div>{it.item_id || "—"}</div>
                    <div className="muted">{it.category}</div>
                  </td>
                  <td>{it.annotation}</td>
                  <td>{it.effective_qty}</td>
                  <td>{it.unit}</td>
                  <td>{it.measurement_type}</td>
                  <td>
                    <span className={`badge ${it.status === "approved" || it.status === "amended" ? "ok" : it.status === "excluded" ? "bad" : "warn"}`}>
                      {it.status}
                    </span>
                  </td>
                  <td>
                    <div className="row-actions">
                      <button className="btn" onClick={() => setStatus(it.id, "approved")}>Approve</button>
                      <button className="btn danger" onClick={() => setStatus(it.id, "excluded")}>Exclude</button>
                      <button className="btn" onClick={() => setAmend(it)}>Amend</button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div>
          <iframe className="pdf-frame" title="drawing-pdf" src={pdfSrc} />
          <div className="muted" style={{ marginTop: "0.35rem" }}>
            PDF from API. Overlay toggle 404s if no overlay file is present.
          </div>
        </div>
      </div>

      {amend && (
        <AmendModal
          item={amend}
          onClose={() => setAmend(null)}
          onSave={async (qty, notes) => {
            await api.patchItem(amend.id, {
              status: "amended",
              amended_qty: qty,
              amended_notes: notes,
            });
            setAmend(null);
            await load();
          }}
        />
      )}
    </div>
  );
}

function AmendModal({
  item,
  onClose,
  onSave,
}: {
  item: Item;
  onClose: () => void;
  onSave: (qty: number, notes: string) => Promise<void>;
}) {
  const [qty, setQty] = useState(String(item.amended_qty ?? item.effective_qty));
  const [notes, setNotes] = useState(item.amended_notes ?? "");
  const [busy, setBusy] = useState(false);

  async function submit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    try {
      await onSave(Number(qty), notes);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <form className="modal" onClick={(e) => e.stopPropagation()} onSubmit={submit}>
        <h3 style={{ margin: 0 }}>Amend {item.item_id || item.annotation}</h3>
        <label>
          Quantity
          <input value={qty} onChange={(e) => setQty(e.target.value)} required />
        </label>
        <label>
          Notes
          <input value={notes} onChange={(e) => setNotes(e.target.value)} />
        </label>
        <div className="row-actions">
          <button className="btn primary" disabled={busy} type="submit">Save</button>
          <button className="btn" type="button" onClick={onClose}>Cancel</button>
        </div>
      </form>
    </div>
  );
}
