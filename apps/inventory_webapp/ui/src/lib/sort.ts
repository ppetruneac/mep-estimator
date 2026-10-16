export type SortDir = "asc" | "desc";

function sortComparable(
  value: unknown
): { kind: "null" } | { kind: "num"; n: number } | { kind: "str"; s: string } {
  if (value == null) return { kind: "null" };
  if (typeof value === "number") {
    return Number.isFinite(value) ? { kind: "num", n: value } : { kind: "null" };
  }
  if (typeof value === "boolean") return { kind: "num", n: value ? 1 : 0 };
  if (typeof value === "string") {
    const trimmed = value.trim();
    if (trimmed === "") return { kind: "null" };
    const asNum = Number(trimmed);
    if (trimmed !== "" && Number.isFinite(asNum) && /^-?\d+(\.\d+)?$/.test(trimmed)) {
      return { kind: "num", n: asNum };
    }
    return { kind: "str", s: trimmed };
  }
  return { kind: "str", s: String(value) };
}

export function sortRows<T>(
  rows: T[],
  key: keyof T | string,
  dir: SortDir
): T[] {
  const mul = dir === "asc" ? 1 : -1;
  return [...rows].sort((a, b) => {
    const av = sortComparable((a as Record<string, unknown>)[key as string]);
    const bv = sortComparable((b as Record<string, unknown>)[key as string]);
    if (av.kind === "null" && bv.kind === "null") return 0;
    if (av.kind === "null") return 1;
    if (bv.kind === "null") return -1;
    if (av.kind === "num" && bv.kind === "num") {
      return (av.n - bv.n) * mul;
    }
    const as = av.kind === "str" ? av.s : String(av.n);
    const bs = bv.kind === "str" ? bv.s : String(bv.n);
    return (
      as.localeCompare(bs, undefined, {
        numeric: true,
        sensitivity: "base",
      }) * mul
    );
  });
}

export function nextSort(
  currentKey: string,
  currentDir: SortDir,
  nextKey: string
): { key: string; dir: SortDir } {
  if (currentKey === nextKey) {
    return { key: nextKey, dir: currentDir === "asc" ? "desc" : "asc" };
  }
  return { key: nextKey, dir: "asc" };
}
