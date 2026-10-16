import { FormEvent, useEffect, useMemo, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { Link, useParams } from "react-router-dom";
import {
  ArrowTopRightOnSquareIcon,
  InformationCircleIcon,
} from "@heroicons/react/24/outline";
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
    await api.bulk(projectUuid, key, action, {
      status: status || undefined,
      category: category || undefined,
      measurement_type: measurementType || undefined,
      q: q || undefined,
    });
    // After bulk approve/exclude, clear status chip so the updated rows stay visible
    if (status && status !== (action === "approve" ? "approved" : "excluded")) {
      setStatus("");
    }
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

      {/* Category + status chips with counts */}
      {facets && (
        <div className="space-y-3">
          <div>
            <div className="mb-1.5 text-xs font-semibold uppercase tracking-wide text-slate-400">
              Category
            </div>
            <div className="flex flex-wrap gap-2">
              <Chip
                label="All"
                count={facets.categories.reduce((n, c) => n + c.count, 0)}
                selected={!category}
                onClick={() => setCategory("")}
              />
              {facets.categories.map((c) => (
                <Chip
                  key={c.category}
                  label={c.category}
                  count={c.count}
                  selected={category === c.category}
                  onClick={() =>
                    setCategory(category === c.category ? "" : c.category)
                  }
                />
              ))}
            </div>
          </div>
          <div>
            <div className="mb-1.5 text-xs font-semibold uppercase tracking-wide text-slate-400">
              Status
            </div>
            <div className="flex flex-wrap gap-2">
              <Chip
                label="All"
                count={facets.statuses.reduce((n, s) => n + s.count, 0)}
                selected={!status}
                onClick={() => setStatus("")}
              />
              {facets.statuses.map((s) => (
                <Chip
                  key={s.key}
                  label={s.key}
                  count={s.count}
                  selected={status === s.key}
                  tone={
                    s.key === "approved" || s.key === "amended"
                      ? "ok"
                      : s.key === "excluded"
                        ? "bad"
                        : s.key === "pending"
                          ? "warn"
                          : "default"
                  }
                  onClick={() => setStatus(status === s.key ? "" : s.key)}
                />
              ))}
            </div>
          </div>
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
      </Card>

      <div className="flex flex-wrap items-center gap-2">
        <Button onClick={() => bulk("approve")}>
          {category || measurementType || q
            ? "Approve all shown"
            : "Approve all"}
        </Button>
        <Button variant="secondary" color="red" onClick={() => bulk("exclude")}>
          {category || measurementType || q
            ? "Exclude all shown"
            : "Exclude all"}
        </Button>
      </div>

      <Card className="overflow-hidden p-0">
        <div className="obs-table-scroll">
          <Table className="min-w-[72rem]">
            <TableHead>
              <TableRow>
                <TableHeaderCell>Category</TableHeaderCell>
                <TableHeaderCell>Item ID</TableHeaderCell>
                <TableHeaderCell>Annotation</TableHeaderCell>
                <TableHeaderCell>Qty</TableHeaderCell>
                <TableHeaderCell>Unit</TableHeaderCell>
                <TableHeaderCell>
                  <span className="inline-flex items-center gap-1.5">
                    Type
                    <TypeInfoTip types={facets?.measurement_types || []} />
                  </span>
                </TableHeaderCell>
                <TableHeaderCell>Status</TableHeaderCell>
                <TableHeaderCell className="actions-col">Actions</TableHeaderCell>
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
                  <TableCell className="text-slate-700">
                    {it.category || "Unclassified"}
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
                  <TableCell>{it.measurement_type || "—"}</TableCell>
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
                  <TableCell className="actions-col">
                    <div className="flex flex-nowrap items-center gap-1">
                      <button
                        type="button"
                        className="rounded-md px-2 py-1 text-xs font-medium text-emerald-700 hover:bg-emerald-50"
                        onClick={() => setItemStatus(it.id, "approved")}
                      >
                        Approve
                      </button>
                      <button
                        type="button"
                        className="rounded-md px-2 py-1 text-xs font-medium text-red-700 hover:bg-red-50"
                        onClick={() => setItemStatus(it.id, "excluded")}
                      >
                        Exclude
                      </button>
                      <button
                        type="button"
                        className="rounded-md px-2 py-1 text-xs font-medium text-slate-700 hover:bg-slate-100"
                        onClick={() => setAmend(it)}
                      >
                        Amend
                      </button>
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

function Chip({
  label,
  count,
  selected,
  onClick,
  tone = "default",
}: {
  label: string;
  count: number;
  selected: boolean;
  onClick: () => void;
  tone?: "default" | "ok" | "warn" | "bad";
}) {
  const toneRing =
    !selected && tone === "ok"
      ? "ring-emerald-200 text-emerald-800"
      : !selected && tone === "warn"
        ? "ring-amber-200 text-amber-900"
        : !selected && tone === "bad"
          ? "ring-red-200 text-red-800"
          : "ring-slate-200 text-slate-700";
  return (
    <button
      type="button"
      className={[
        "inline-flex items-center gap-2 rounded-full px-3 py-1.5 text-sm font-medium transition-colors",
        selected
          ? "bg-slate-900 text-white"
          : `bg-white hover:bg-slate-50 ring-1 ${toneRing}`,
      ].join(" ")}
      onClick={onClick}
    >
      <span className="capitalize">{label}</span>
      <span
        className={[
          "rounded-full px-1.5 py-0.5 text-xs tabular-nums",
          selected ? "bg-white/20" : "bg-slate-100 text-slate-600",
        ].join(" ")}
      >
        {count}
      </span>
    </button>
  );
}

function TypeInfoTip({
  types,
}: {
  types: { key: string; count: number; help?: string | null }[];
}) {
  const [open, setOpen] = useState(false);
  const [pos, setPos] = useState<{ top: number; left: number } | null>(null);
  const btnRef = useRef<HTMLButtonElement>(null);
  const hideTimer = useRef<number | null>(null);

  function clearHide() {
    if (hideTimer.current != null) {
      window.clearTimeout(hideTimer.current);
      hideTimer.current = null;
    }
  }

  function show() {
    clearHide();
    const rect = btnRef.current?.getBoundingClientRect();
    if (rect) {
      const width = 320;
      const left = Math.min(
        Math.max(8, rect.left),
        window.innerWidth - width - 8
      );
      const below = rect.bottom + 8;
      const approxHeight = 220;
      const top =
        below + approxHeight > window.innerHeight
          ? Math.max(8, rect.top - approxHeight - 8)
          : below;
      setPos({ top, left });
    }
    setOpen(true);
  }

  function hideSoon() {
    clearHide();
    hideTimer.current = window.setTimeout(() => setOpen(false), 120);
  }

  useEffect(() => {
    if (!open) return;
    function onScroll() {
      setOpen(false);
    }
    window.addEventListener("scroll", onScroll, true);
    window.addEventListener("resize", onScroll);
    return () => {
      window.removeEventListener("scroll", onScroll, true);
      window.removeEventListener("resize", onScroll);
    };
  }, [open]);

  useEffect(
    () => () => {
      clearHide();
    },
    []
  );

  const entries =
    types.length > 0
      ? types
      : [
          { key: "printed", help: "Count or size printed on the drawing." },
          { key: "scaled", help: "Length from vector geometry at sheet scale." },
          {
            key: "geometry",
            help: "Estimated from tag-to-core geometry (not a traced spine).",
          },
        ];

  return (
    <span className="inline-flex" onMouseEnter={show} onMouseLeave={hideSoon}>
      <button
        ref={btnRef}
        type="button"
        className="inline-flex text-slate-400 hover:text-slate-700"
        aria-label="Measurement type descriptions"
        aria-expanded={open}
      >
        <InformationCircleIcon className="h-4 w-4" />
      </button>
      {open &&
        pos &&
        createPortal(
          <div
            className="fixed z-[100] w-80 rounded-xl border border-slate-200 bg-white p-3 text-left shadow-xl"
            style={{ top: pos.top, left: pos.left }}
            onMouseEnter={show}
            onMouseLeave={hideSoon}
          >
            <div className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-400">
              Measurement types
            </div>
            <ul className="space-y-2 text-xs text-slate-700">
              {entries.map((t) => (
                <li key={t.key}>
                  <span className="font-semibold text-slate-900">{t.key}</span>
                  {t.help ? ` — ${t.help}` : ""}
                </li>
              ))}
            </ul>
          </div>,
          document.body
        )}
    </span>
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
