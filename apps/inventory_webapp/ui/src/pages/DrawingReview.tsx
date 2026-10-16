import { FormEvent, useEffect, useState } from "react";
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
import { api, Drawing, Item } from "../api";

export function DrawingReview() {
  const { projectId, drawingId } = useParams();
  const did = Number(drawingId);
  const projectUuid = String(projectId);
  const [drawing, setDrawing] = useState<Drawing | null>(null);
  const [items, setItems] = useState<Item[]>([]);
  const [statusFilter, setStatusFilter] = useState("");
  const [err, setErr] = useState<string | null>(null);
  const [amend, setAmend] = useState<Item | null>(null);

  async function load() {
    const [d, its] = await Promise.all([
      api.drawings(projectUuid).then((ds) => ds.find((x) => x.id === did) || null),
      api.items(did, statusFilter ? `?status=${statusFilter}` : ""),
    ]);
    setDrawing(d);
    setItems(its);
  }

  useEffect(() => {
    load().catch((e) => setErr(String(e)));
  }, [did, projectUuid, statusFilter]);

  async function setStatus(id: number, status: string) {
    await api.patchItem(id, { status });
    await load();
  }

  async function bulk(action: "approve" | "exclude") {
    await api.bulk(did, action);
    await load();
  }

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
            {drawing?.drawing_number} · {drawing?.scale} · {items.length} rows
          </Text>
        </div>
        <div className="flex flex-wrap gap-2">
          <a
            href={api.pdfUrl(did)}
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center gap-1.5 rounded-lg bg-slate-900 px-3 py-1.5 text-sm font-medium text-white hover:bg-slate-800"
          >
            <ArrowTopRightOnSquareIcon className="h-4 w-4" />
            Open drawing in new tab
          </a>
          <a
            href={api.overlayUrl(did)}
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

      <div className="flex flex-wrap items-center gap-2">
        <select
          className="obs-select"
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
        >
          <option value="">All statuses</option>
          <option value="pending">Pending</option>
          <option value="approved">Approved</option>
          <option value="excluded">Excluded</option>
          <option value="amended">Amended</option>
        </select>
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
                <TableHeaderCell>Item</TableHeaderCell>
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
                    <div className="font-medium text-slate-900">
                      {it.item_id || "—"}
                    </div>
                    <div className="text-xs text-slate-500">{it.category}</div>
                  </TableCell>
                  <TableCell>{it.annotation}</TableCell>
                  <TableCell>{it.effective_qty}</TableCell>
                  <TableCell>{it.unit}</TableCell>
                  <TableCell>{it.measurement_type}</TableCell>
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
                        onClick={() => setStatus(it.id, "approved")}
                      >
                        Approve
                      </Button>
                      <Button
                        size="xs"
                        variant="secondary"
                        color="red"
                        onClick={() => setStatus(it.id, "excluded")}
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
