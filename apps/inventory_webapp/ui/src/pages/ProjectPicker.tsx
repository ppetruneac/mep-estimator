import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Card, Text, Title } from "@tremor/react";
import { api, Project } from "../api";

export function ProjectPicker() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [err, setErr] = useState<string | null>(null);
  const nav = useNavigate();

  useEffect(() => {
    api.projects().then(setProjects).catch((e) => setErr(String(e)));
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <Title>Projects</Title>
        <Text className="mt-1">Select a project to review inventory</Text>
      </div>
      {err && (
        <Card>
          <Text className="text-red-600">{err}</Text>
        </Card>
      )}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {projects.map((p) => {
          const tb = p.title_block;
          return (
            <Card
              key={p.uuid}
              className="cursor-pointer transition hover:border-sky-300 hover:shadow-md"
              onClick={() => nav(`/projects/${p.uuid}`)}
            >
              <Title className="text-base">
                {tb?.display_name || p.name}
              </Title>
              {tb?.location && (
                <Text className="mt-1">Location: {tb.location}</Text>
              )}
              <div className="mt-3 space-y-1 text-sm text-slate-700">
                <div>
                  <span className="text-xs font-semibold uppercase tracking-wide text-slate-400">
                    Client
                  </span>{" "}
                  {p.client || tb?.client || "—"}
                </div>
                <div>
                  <span className="text-xs font-semibold uppercase tracking-wide text-slate-400">
                    Architect
                  </span>{" "}
                  {p.architect || tb?.architect || "—"}
                </div>
                <div>
                  <span className="text-xs font-semibold uppercase tracking-wide text-slate-400">
                    Owner
                  </span>{" "}
                  {p.owner || tb?.mep || "Seneca Group Ltd"}
                </div>
              </div>
              <Text className="mt-3">Code: {p.name}</Text>
              {(tb?.job_series?.length || tb?.scale || tb?.stage) && (
                <Text className="mt-1">
                  {[tb?.job_series?.join(", "), tb?.scale, tb?.stage]
                    .filter(Boolean)
                    .join(" · ")}
                </Text>
              )}
              <div className="mt-4 flex flex-wrap gap-2">
                <span className="rounded-full bg-slate-100 px-2.5 py-0.5 text-xs font-medium text-slate-700">
                  {p.drawing_count} drawings
                </span>
                <span className="rounded-full bg-slate-100 px-2.5 py-0.5 text-xs font-medium text-slate-700">
                  {p.occurrence_count} lines
                </span>
                <span
                  className={[
                    "rounded-full px-2.5 py-0.5 text-xs font-medium",
                    p.pending_count
                      ? "bg-amber-100 text-amber-800"
                      : "bg-emerald-100 text-emerald-800",
                  ].join(" ")}
                >
                  {p.pending_count} pending
                </span>
              </div>
            </Card>
          );
        })}
      </div>
      {!err && projects.length === 0 && (
        <Text>
          No projects. Run <code>make seed-hubby</code>.
        </Text>
      )}
    </div>
  );
}
