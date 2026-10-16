import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import {
  Badge,
  Card,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeaderCell,
  TableRow,
  Text,
  Title,
} from "@tremor/react";
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
    <div className="space-y-6">
      <div>
        <Title>{tb?.display_name || project?.name || "…"}</Title>
        <Text className="mt-1">
          {tb?.location ? `${tb.location} · ` : ""}
          {project?.pending_count ?? 0} pending · {project?.drawing_count ?? 0}{" "}
          drawings
        </Text>
      </div>

      {tb && (
        <Card>
          <Text className="text-xs font-semibold uppercase tracking-wide text-slate-400">
            Title block (from drawings)
          </Text>
          <div className="mt-3 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <Meta label="Project" value={tb.display_name} />
            <Meta label="Location" value={tb.location} />
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
          </div>
        </Card>
      )}

      {err && (
        <Card>
          <Text className="text-red-600">{err}</Text>
        </Card>
      )}

      <div className="flex flex-wrap gap-2">
        {(
          [
            ["drawings", "Drawings"],
            ["floor", "Summary by floor"],
            ["category", "Summary by category"],
          ] as const
        ).map(([key, label]) => (
          <button
            key={key}
            type="button"
            className={tab === key ? "obs-tab obs-tab-active" : "obs-tab"}
            onClick={() => setTab(key)}
          >
            {label}
          </button>
        ))}
      </div>

      {tab === "drawings" && (
        <Card className="p-0 overflow-hidden">
          <div className="obs-table-scroll">
            <Table>
              <TableHead>
                <TableRow>
                  <TableHeaderCell>Floor</TableHeaderCell>
                  <TableHeaderCell>Drawing</TableHeaderCell>
                  <TableHeaderCell>Scale</TableHeaderCell>
                  <TableHeaderCell>Items</TableHeaderCell>
                  <TableHeaderCell>Pending</TableHeaderCell>
                  <TableHeaderCell>Approved</TableHeaderCell>
                  <TableHeaderCell>Excluded</TableHeaderCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {drawings.map((d) => (
                  <TableRow
                    key={d.id}
                    className="click-row"
                    onClick={() => nav(`/projects/${uuid}/drawings/${d.id}`)}
                  >
                    <TableCell>{d.floor_tab_name}</TableCell>
                    <TableCell>{d.drawing_number}</TableCell>
                    <TableCell>{d.scale}</TableCell>
                    <TableCell>{d.item_count}</TableCell>
                    <TableCell>
                      <Badge color={d.pending_count ? "amber" : "emerald"}>
                        {d.pending_count}
                      </Badge>
                    </TableCell>
                    <TableCell>{d.approved_count}</TableCell>
                    <TableCell>{d.excluded_count}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </Card>
      )}

      {tab === "floor" && (
        <SummaryCard
          rows={byFloor}
          onExport={() => exportCsv(byFloor, "summary-by-floor.csv")}
        />
      )}
      {tab === "category" && (
        <SummaryCard
          rows={byCat}
          onExport={() => exportCsv(byCat, "summary-by-category.csv")}
        />
      )}
    </div>
  );
}

function Meta({ label, value }: { label: string; value?: string | null }) {
  if (!value) return null;
  return (
    <div>
      <div className="text-xs font-semibold uppercase tracking-wide text-slate-400">
        {label}
      </div>
      <div className="mt-0.5 text-sm font-medium text-slate-900">{value}</div>
    </div>
  );
}

function SummaryCard({
  rows,
  onExport,
}: {
  rows: SummaryRow[];
  onExport: () => void;
}) {
  return (
    <Card>
      <div className="mb-3 flex items-center gap-3">
        <button type="button" className="obs-tab" onClick={onExport}>
          Export CSV
        </button>
        <Text>Approved / amended qty only</Text>
      </div>
      <div className="obs-table-scroll">
        <Table>
          <TableHead>
            <TableRow>
              <TableHeaderCell>Label</TableHeaderCell>
              <TableHeaderCell>Qty</TableHeaderCell>
              <TableHeaderCell>Unit</TableHeaderCell>
              <TableHeaderCell>Approved lines</TableHeaderCell>
              <TableHeaderCell>Excluded</TableHeaderCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {rows.map((r) => (
              <TableRow key={r.key}>
                <TableCell>{r.label}</TableCell>
                <TableCell>{r.qty}</TableCell>
                <TableCell>{r.unit}</TableCell>
                <TableCell>{r.item_count}</TableCell>
                <TableCell>{r.excluded_count}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </Card>
  );
}
