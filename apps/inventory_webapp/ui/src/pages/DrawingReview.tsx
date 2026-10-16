import { FormEvent, useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { ArrowTopRightOnSquareIcon } from "@heroicons/react/24/outline";
import {
  Badge,
  Button,
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
import { api, Drawing, DrawingFacets, Item } from "../api";

export function DrawingReview() {
  const { projectId, drawingKey } = useParams();
  const projectUuid = String(projectId);
  const key = decodeURIComponent(String(drawingKey));
  const [drawing, setDrawing] = useState<Drawing | null>(null);
  const [items, setItems] = useState<Item[]>([]);
  const [facets, setFacets] = useState<DrawingFacets | null>(null);
  const [category, setCategory] = useState("");
  const [status, setStatus] = useState("");
  const [measurementType, setMeasurementType] = useState("");
  const [q, setQ] = useState("");
  const [qDraft, setQDraft] = useState("");
  const [err, setErr] = useState<string | null>(null);
  const [amend, setAmend] = useState<Item | null>(null);

  async function load() {
    const [d, its, f] = await Promise.all([
      api.drawing(projectUuid, key),
      api.items(projectUuid, key, {
        status: status || undefined,
        measurement_type: measurementType || undefined,
        category: category || undefined,
        q: q || undefined,
      }),
      api.facets(projectUuid, key),
    ]);
    setDrawing(d);
    setItems(its);
    setFacets(f);
  }

  useEffect(() => {
    load().catch((e) => setErr(String(e)));
  }, [projectUuid, key, status, measurementType, category, q]);

  async function setItemStatus(id: number, next: string) {
    await api.patchItem(id, { status: next });
    await load();
  }

  async function bulk(action: "approve" | "exclude") {
    await api.bulk(projectUuid, key, action);
    await load();
  }

  const typeHelp = useMemo(() => {
    if (!measurementType || !facets) return null;
    return facets.measurement_types.find((t) => t.key === measurementType)?.help;
  }, [measurementType, facets]);

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <Link
            to={`/projects/${projectUuid}`}
            className="text-sm text-slate-500 hover:text-slate-800"
          >
            ← Back to project
          </Link>
          <Title className="mt-1">{drawing?.floor_tab_name}</Title>
          <Text className="mt-1">
            {drawing?.drawing_number} · {drawing?.scale} · {items.length} shown
          </Text>
        </div>
        <div className="flex flex-wrap gap-2">
          <a
            href={api.pdfUrl(projectUuid, key)}
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center gap-1.5 rounded-lg bg-slate-900 px-3 py-1.5 text-sm font-medium text-white hover:bg-slate-800"
          >
            <ArrowTopRightOnSquareIcon className="h-4 w-4" />
            Open drawing in new tab
          </a>
          <a
            href={api.overlayUrl(projectUuid, key)}
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center gap-1.5 rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-50"
          >
            <ArrowTopRightOnSquareIcon className="h-4 w-4" />
            Open overlay in new tab
          </a>
        </div>
      </div>

      {err && (
        <Card>
          <Text className="text-red-600">{err}</Text>
        </Card>
      )}

      {/* Category chips with counts */}
      {facets && (
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            className={[
              "inline-flex items-center gap-2 rounded-full px-3 py-1.5 text-sm font-medium transition-colors",
              !category
                ? "bg-slate-900 text-white"
                : "bg-white text-slate-700 ring-1 ring-slate-200 hover:bg-slate-50",
            ].join(" ")}
            onClick={() => setCategory("")}
          >
            All
            <span
              className={[
                "rounded-full px-1.5 py-0.5 text-xs tabular-nums",
                !category ? "bg-white/20" : "bg-slate-100 text-slate-600",
              ].join(" ")}
            >
              {facets.categories.reduce((n, c) => n + c.count, 0)}
            </span>
          </button>
          {facets.categories.map((c) => {
            const selected = category === c.category;
            return (
              <button
                key={c.category}
                type="button"
                className={[
                  "inline-flex items-center gap-2 rounded-full px-3 py-1.5 text-sm font-medium transition-colors",
                  selected
                    ? "bg-slate-900 text-white"
                    : "bg-white text-slate-700 ring-1 ring-slate-200 hover:bg-slate-50",
                ].join(" ")}
                onClick={() =>
                  setCategory(selected ? "" : c.category)
                }
              >
                {c.category}
                <span
                  className={[
                    "rounded-full px-1.5 py-0.5 text-xs tabular-nums",
                    selected ? "bg-white/20" : "bg-slate-100 text-slate-600",
                  ].join(" ")}
                >
                  {c.count}
                </span>
              </button>
            );
          })}
        </div>
      )}

      <Card>
        <div className="flex flex-wrap items-end gap-3">
          <label className="flex min-w-[14rem] flex-1 flex-col gap-1 text-sm">
            <span className="font-medium text-slate-700">Search</span>
            <input
              className="obs-select"
              style={{ backgroundImage: "none", paddingRight: "0.75rem" }}
              value={qDraft}
              placeholder="Annotation, item ID, category, notes…"
              onChange={(e) => setQDraft(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") setQ(qDraft.trim());
              }}
              onBlur={() => setQ(qDraft.trim())}
            />
          </label>
          <label className="flex min-w-[10rem] flex-col gap-1 text-sm">
            <span className="font-medium text-slate-700">Status</span>
            <select
              className="obs-select"
              value={status}
              onChange={(e) => setStatus(e.target.value)}
            >
              <option value="">All</option>
              {(facets?.statuses || []).map((s) => (
                <option key={s.key} value={s.key}>
                  {s.key} ({s.count})
                </option>
              ))}
            </select>
          </label>
          <label className="flex min-w-[12rem] flex-col gap-1 text-sm">
            <span className="font-medium text-slate-700">Type</span>
            <select
              className="obs-select"
              value={measurementType}
              onChange={(e) => setMeasurementType(e.target.value)}
            >
              <option value="">All</option>
              {(facets?.measurement_types || []).map((t) => (
                <option key={t.key} value={t.key}>
                  {t.key} ({t.count})
                </option>
              ))}
            </select>
          </label>
          <Button
            variant="secondary"
            onClick={() => {
              setCategory("");
              setStatus("");
              setMeasurementType("");
              setQ("");
              setQDraft("");
            }}
          >
            Clear filters
          </Button>
        </div>
        {typeHelp && (
          <div className="obs-info mt-3 mb-0">
            <span className="obs-info-label">Type</span>
            <div>
              <strong>{measurementType}</strong> — {typeHelp}
            </div>
          </div>
        )}
        <Text className="mt-3 text-slate-500">
          Item ID is the stable catalog key (e.g. <code>MEC-CU-IN</code> = indoor
          refrigerant pair / FCU→HBC home-run). Annotation is the printed tag
          from the sheet (e.g. FCU.B.01), matching the Hubby inventory book.
        </Text>
      </Card>

      <div className="flex flex-wrap items-center gap-2">
        <Button onClick={() => bulk("approve")}>Approve all pending</Button>
        <Button variant="secondary" color="red" onClick={() => bulk("exclude")}>
          Exclude all pending
        </Button>
      </div>

      <Card className="overflow-hidden p-0">
        <div className="obs-table-scroll">
          <Table>
            <TableHead>
              <TableRow>
                <TableHeaderCell>Category</TableHeaderCell>
                <TableHeaderCell>Item ID</TableHeaderCell>
                <TableHeaderCell>Annotation</TableHeaderCell>
                <TableHeaderCell>Qty</TableHeaderCell>
                <TableHeaderCell>Unit</TableHeaderCell>
                <TableHeaderCell>Type</TableHeaderCell>
                <TableHeaderCell>Status</TableHeaderCell>
                <TableHeaderCell>Actions</TableHeaderCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {items.map((it) => (
                <TableRow
                  key={it.id}
                  className={
                    it.amber_flag ||
                    (it.measurement_type && it.measurement_type !== "printed")
                      ? "amber"
                      : undefined
                  }
                >
                  <TableCell>
                    <Badge color="slate">{it.category || "Unclassified"}</Badge>
                  </TableCell>
                  <TableCell>
                    <div className="font-medium text-slate-900">
                      {it.item_id || "—"}
                    </div>
                    {it.item_label && (
                      <div className="text-xs text-slate-500">{it.item_label}</div>
                    )}
                  </TableCell>
                  <TableCell>
                    <div>{it.annotation}</div>
                    {it.linked_to && (
                      <div className="text-xs text-slate-500">{it.linked_to}</div>
                    )}
                  </TableCell>
                  <TableCell>{it.effective_qty}</TableCell>
                  <TableCell>{it.unit}</TableCell>
                  <TableCell>
                    <div>{it.measurement_type}</div>
                    {it.measurement_type_help && (
                      <div className="max-w-[14rem] text-xs text-slate-500">
                        {it.measurement_type_help}
                      </div>
                    )}
                  </TableCell>
                  <TableCell>
                    <Badge
                      color={
                        it.status === "approved" || it.status === "amended"
                          ? "emerald"
                          : it.status === "excluded"
                            ? "red"
                            : "amber"
                      }
                    >
                      {it.status}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <div className="flex flex-wrap gap-1.5">
                      <Button
                        size="xs"
                        variant="secondary"
                        onClick={() => setItemStatus(it.id, "approved")}
                      >
                        Approve
                      </Button>
                      <Button
                        size="xs"
                        variant="secondary"
                        color="red"
                        onClick={() => setItemStatus(it.id, "excluded")}
                      >
                        Exclude
                      </Button>
                      <Button size="xs" variant="light" onClick={() => setAmend(it)}>
                        Amend
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      </Card>

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
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 p-4"
      onClick={onClose}
    >
      <form
        className="w-full max-w-md space-y-3 rounded-xl border border-slate-200 bg-white p-5 shadow-xl"
        onClick={(e) => e.stopPropagation()}
        onSubmit={submit}
      >
        <Title className="text-base">
          Amend {item.item_id || item.annotation}
        </Title>
        <label className="block text-sm">
          <span className="text-slate-600">Quantity</span>
          <input
            className="obs-select mt-1 w-full"
            style={{ backgroundImage: "none" }}
            value={qty}
            onChange={(e) => setQty(e.target.value)}
            required
          />
        </label>
        <label className="block text-sm">
          <span className="text-slate-600">Notes</span>
          <input
            className="obs-select mt-1 w-full"
            style={{ backgroundImage: "none" }}
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
          />
        </label>
        <div className="flex gap-2 pt-1">
          <Button type="submit" loading={busy}>
            Save
          </Button>
          <Button type="button" variant="secondary" onClick={onClose}>
            Cancel
          </Button>
        </div>
      </form>
    </div>
  );
}
