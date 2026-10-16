import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, Project } from "../api";

export function ProjectPicker() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [err, setErr] = useState<string | null>(null);
  const nav = useNavigate();

  useEffect(() => {
    api.projects().then(setProjects).catch((e) => setErr(String(e)));
  }, []);

  return (
    <div className="wrap">
      <div className="header">
        <div>
          <h1>Projects</h1>
          <div className="muted">Select a project to review inventory</div>
        </div>
      </div>
      {err && <div className="err">{err}</div>}
      <div className="cards">
        {projects.map((p) => {
          const tb = p.title_block;
          return (
            <div
              key={p.uuid}
              className="card"
              onClick={() => nav(`/projects/${p.uuid}`)}
            >
              <h2>{tb?.display_name || p.name}</h2>
              {tb?.location && (
                <div className="muted">Location: {tb.location}</div>
              )}
              <div className="party-lines">
                <div><span className="party-label">Client</span> {p.client || tb?.client || "—"}</div>
                <div><span className="party-label">Architect</span> {p.architect || tb?.architect || "—"}</div>
                <div><span className="party-label">Owner</span> {p.owner || tb?.mep || "Seneca Group Ltd"}</div>
              </div>
              <div className="muted">Code: {p.name}</div>
              {(tb?.job_series?.length || tb?.scale || tb?.stage) && (
                <div className="muted" style={{ marginTop: "0.25rem" }}>
                  {[tb?.job_series?.join(", "), tb?.scale, tb?.stage]
                    .filter(Boolean)
                    .join(" · ")}
                </div>
              )}
              <div
                style={{
                  marginTop: "0.6rem",
                  display: "flex",
                  gap: "0.4rem",
                  flexWrap: "wrap",
                }}
              >
                <span className="badge">{p.drawing_count} drawings</span>
                <span className="badge">{p.occurrence_count} lines</span>
                <span className={`badge ${p.pending_count ? "warn" : "ok"}`}>
                  {p.pending_count} pending
                </span>
              </div>
            </div>
          );
        })}
        {!err && projects.length === 0 && (
          <div className="muted">
            No projects. Run <code>make seed-hubby</code>.
          </div>
        )}
      </div>
    </div>
  );
}
