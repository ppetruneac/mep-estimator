import { FormEvent, useEffect, useState } from "react";
import {
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
import { api, CatalogueItem, CatalogueResponse } from "../api";

export function CataloguePage() {
  const [data, setData] = useState<CatalogueResponse | null>(null);
  const [category, setCategory] = useState("");
  const [q, setQ] = useState("");
  const [qDraft, setQDraft] = useState("");
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    setErr(null);
    api
      .catalogue({
        category: category || undefined,
        q: q || undefined,
      })
      .then(setData)
      .catch((e) => setErr(String(e)));
  }, [category, q]);

  function onSearch(e: FormEvent) {
    e.preventDefault();
    setQ(qDraft.trim());
  }

  const items: CatalogueItem[] = data?.items ?? [];
  const categories = data?.categories ?? [];
  const totalCount = categories.reduce((n, c) => n + c.count, 0);

  return (
    <div className="space-y-6">
      <div>
        <Title>Catalogue</Title>
        <Text className="mt-1">
          All categories and items (SKU) used in inventory take-off
        </Text>
      </div>

      {err && (
        <Card>
          <Text className="text-red-600">{err}</Text>
        </Card>
      )}

      {data && (
        <Card className="space-y-4">
          <div>
            <div className="obs-label-upper mb-2">Category</div>
            <div className="flex flex-wrap gap-2">
              <Chip
                label="All"
                count={totalCount}
                selected={!category}
                onClick={() => setCategory("")}
              />
              {categories.map((c) => (
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

          <form
            className="flex flex-wrap items-center gap-2"
            onSubmit={onSearch}
          >
            <input
              type="search"
              value={qDraft}
              onChange={(e) => setQDraft(e.target.value)}
              placeholder="Item ID, SKU, label, category…"
              className="min-w-[16rem] flex-1 rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 shadow-sm outline-none ring-sky-500 focus:ring-2 dark:border-gray-700 dark:bg-gray-900 dark:text-gray-100"
            />
            <button
              type="submit"
              className="rounded-lg bg-slate-900 px-3 py-2 text-sm font-medium text-white hover:bg-slate-800 dark:bg-indigo-500 dark:hover:bg-indigo-400"
            >
              Search
            </button>
            {(category || q) && (
              <button
                type="button"
                className="rounded-lg px-3 py-2 text-sm font-medium text-slate-600 hover:bg-slate-100 dark:text-gray-300 dark:hover:bg-white/5"
                onClick={() => {
                  setCategory("");
                  setQ("");
                  setQDraft("");
                }}
              >
                Clear filters
              </button>
            )}
          </form>

          <Text>
            Showing {items.length}
            {category || q ? ` of ${totalCount}` : ""} catalogue item
            {items.length === 1 ? "" : "s"}
          </Text>
        </Card>
      )}

      <Card className="overflow-x-auto p-0">
        <Table>
          <TableHead>
            <TableRow>
              <TableHeaderCell>Category</TableHeaderCell>
              <TableHeaderCell>Item ID</TableHeaderCell>
              <TableHeaderCell>SKU</TableHeaderCell>
              <TableHeaderCell>Label</TableHeaderCell>
              <TableHeaderCell>Unit</TableHeaderCell>
              <TableHeaderCell>Scope</TableHeaderCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {items.length === 0 && (
              <TableRow>
                <TableCell colSpan={6}>
                  <Text className="py-4 text-slate-500 dark:text-gray-400">
                    {data ? "No catalogue items match these filters." : "Loading…"}
                  </Text>
                </TableCell>
              </TableRow>
            )}
            {items.map((it) => (
              <TableRow key={it.item_id}>
                <TableCell>
                  <span className="text-sm text-slate-800 dark:text-gray-200">
                    {it.category || "Unclassified"}
                  </span>
                </TableCell>
                <TableCell>
                  <code className="text-xs font-medium text-slate-900 dark:text-gray-100">
                    {it.item_id}
                  </code>
                  {it.legacy_item_id &&
                    it.legacy_item_id !== it.item_id &&
                    it.legacy_item_id !== it.category && (
                      <div className="mt-0.5 text-xs text-slate-500 dark:text-gray-400">
                        was {it.legacy_item_id}
                      </div>
                    )}
                </TableCell>
                <TableCell>
                  <code className="text-xs text-slate-700 dark:text-gray-300">
                    {it.catalog_sku || "—"}
                  </code>
                </TableCell>
                <TableCell>
                  <span className="text-sm text-slate-800 dark:text-gray-200">
                    {it.item_label || it.description || "—"}
                  </span>
                </TableCell>
                <TableCell>
                  <span className="text-sm tabular-nums text-slate-700 dark:text-gray-300">
                    {it.unit || "—"}
                  </span>
                </TableCell>
                <TableCell>
                  <span className="text-sm text-slate-700 dark:text-gray-300">
                    {it.scope_default || "—"}
                  </span>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Card>
    </div>
  );
}

function Chip({
  label,
  count,
  selected,
  onClick,
}: {
  label: string;
  count: number;
  selected: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      className={[
        "inline-flex items-center gap-2 rounded-full px-3 py-1.5 text-sm font-medium transition-colors",
        selected
          ? "bg-slate-900 text-white dark:bg-indigo-500"
          : "bg-white ring-1 ring-slate-200 text-slate-700 hover:bg-slate-50 dark:bg-gray-900 dark:ring-gray-700 dark:text-gray-300 dark:hover:bg-gray-800",
      ].join(" ")}
      onClick={onClick}
    >
      <span>{label}</span>
      <span
        className={[
          "rounded-full px-1.5 py-0.5 text-xs tabular-nums",
          selected
            ? "bg-white/20"
            : "bg-slate-100 text-slate-600 dark:bg-gray-800 dark:text-gray-300",
        ].join(" ")}
      >
        {count}
      </span>
    </button>
  );
}
