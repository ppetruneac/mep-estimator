import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { api, Drawing, Project, SummaryRow } from "../api";

export function ProjectView() {
  const { projectId } = useParams();
  const uuid = String(projectId);
  const nav = useNavigate();
  const [project, setProject] = useState<Project | null>(null);
  const [drawings, setDrawings] = useState<Drawing[]>([]);
  const [tab, setTab] = useState<"drawings" | "floor" | "category">("drawings");
  const [byFloor, setByFloor] = useState<SummaryRow[]>([]);
  const [byCat, setByCat] = useState<SummaryRow[]>([]);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([
      api.project(uuid),
      api.drawings(uuid),
      api.summaryByFloor(uuid),
      api.summaryByCategory(uuid),
    ])
      .then(([p, d, f, c]) => {
        setProject(p);
        setDrawings(d);
        setByFloor(f);
        setByCat(c);
      })
      .catch((e) => setErr(String(e)));
  }, [uuid]);

  function exportCsv(rows: SummaryRow[], name: string) {
    const lines = ["label,qty,unit,item_count,excluded_count"];
    for (const r of rows) {
      lines.push(
        [r.label, r.qty, r.unit ?? "", r.item_count, r.excluded_count]
          .map((x) => `"${String(x).replaceAll('"', '""')}"`)
          .join(",")
      );
    }
    const blob = new Blob([lines.join("\n")], { type: "text/csv" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = name;
    a.click();
  }

  const tb = project?.title_block;

  return (
    <div className="wrap">
      <div className="header">
        <div>
          <h1>{tb?.display_name || project?.name || "…"}</h1>
          <div className="muted">
            {tb?.location ? `${tb.location} · ` : ""}
            {project?.pending_count ?? 0} pending · {project?.drawing_count ?? 0}{" "}
            drawings
          </div>
        </div>
      </div>

      <div className="party-banner">
        <div>
          <div className="party-label">Client</div>
          <div className="party-value">{project?.client || tb?.client || "—"}</div>
        </div>
        <div>
          <div className="party-label">Architect</div>
          <div className="party-value">{project?.architect || tb?.architect || "—"}</div>
        </div>
        <div>
          <div className="party-label">Owner</div>
          <div className="party-value">{project?.owner || tb?.mep || "Seneca Group Ltd"}</div>
        </div>
      </div>

      {tb && (
        <div className="titleblock-card">
          <div className="titleblock-kicker">Title block (from drawings)</div>
          <div className="titleblock-grid">
            <Meta label="Project" value={tb.display_name} />
            <Meta label="Location" value={tb.location} />
            <Meta label="Client" value={tb.client || project?.client} />
            <Meta label="Architect" value={tb.architect || project?.architect} />
            <Meta label="Owner / MEP" value={project?.owner || tb.mep} />
            <Meta label="MEP address" value={tb.mep_address} />
            <Meta label="MEP web" value={tb.mep_web} />
            <Meta label="Job series" value={tb.job_series?.join(", ")} />
            <Meta label="Stage" value={tb.stage} />
            <Meta label="Scale" value={tb.scale} />
            <Meta label="Paper" value={tb.paper} />
            <Meta label="Revision" value={tb.revision} />
            <Meta label="Date" value={tb.latest_date} />
            <Meta label="Disclaimer" value={tb.disclaimer} />
            <Meta label="Project code" value={project?.name} />
            <Meta label="Premise" value={project?.premise} />
          </div>
        </div>
      )}

      {err && <div className="err">{err}</div>}
      <div className="tabs">
        <button
          className={`tab ${tab === "drawings" ? "active" : ""}`}
          onClick={() => setTab("drawings")}
        >
          Drawings
        </button>
        <button
          className={`tab ${tab === "floor" ? "active" : ""}`}
          onClick={() => setTab("floor")}
        >
          Summary by floor
        </button>
        <button
          className={`tab ${tab === "category" ? "active" : ""}`}
          onClick={() => setTab("category")}
        >
          Summary by category
        </button>
      </div>

      {tab === "drawings" && (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Floor</th>
                <th>Drawing</th>
                <th>Scale</th>
                <th>Items</th>
                <th>Pending</th>
                <th>Approved</th>
                <th>Excluded</th>
              </tr>
            </thead>
            <tbody>
              {drawings.map((d) => (
                <tr
                  key={d.id}
                  className="click-row"
                  onClick={() => nav(`/projects/${uuid}/drawings/${d.id}`)}
                >
                  <td>{d.floor_tab_name}</td>
                  <td>{d.drawing_number}</td>
                  <td>{d.scale}</td>
                  <td>{d.item_count}</td>
                  <td>
                    <span className={`badge ${d.pending_count ? "warn" : "ok"}`}>
                      {d.pending_count}
                    </span>
                  </td>
                  <td>{d.approved_count}</td>
                  <td>{d.excluded_count}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {tab === "floor" && (
        <>
          <div className="toolbar">
            <button
              className="btn"
              onClick={() => exportCsv(byFloor, "summary-by-floor.csv")}
            >
              Export CSV
            </button>
            <span className="muted">Approved / amended qty only</span>
          </div>
          <SummaryTable rows={byFloor} />
        </>
      )}
      {tab === "category" && (
        <>
          <div className="toolbar">
            <button
              className="btn"
              onClick={() => exportCsv(byCat, "summary-by-category.csv")}
            >
              Export CSV
            </button>
          </div>
          <SummaryTable rows={byCat} />
        </>
      )}
    </div>
  );
}

function Meta({ label, value }: { label: string; value?: string | null }) {
  if (!value) return null;
  return (
    <div className="meta-cell">
      <div className="meta-label">{label}</div>
      <div className="meta-value">{value}</div>
    </div>
  );
}

function SummaryTable({ rows }: { rows: SummaryRow[] }) {
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Label</th>
            <th>Qty</th>
            <th>Unit</th>
            <th>Approved lines</th>
            <th>Excluded</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r.key}>
              <td>{r.label}</td>
              <td>{r.qty}</td>
              <td>{r.unit}</td>
              <td>{r.item_count}</td>
              <td>{r.excluded_count}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
