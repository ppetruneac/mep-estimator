"""Vector path extraction: colour, layer hints, scaled length."""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import pymupdf as fitz


@dataclass
class PathSeg:
    points: list[tuple[float, float]]  # displayed frame
    colour: tuple[float, ...] | None
    colour_hex: str | None
    width: float
    layer: str | None = None
    length_pt: float = 0.0
    length_m: float | None = None
    bbox: list[float] = field(default_factory=list)

    @property
    def cx(self) -> float:
        if not self.points:
            return 0.0
        return sum(p[0] for p in self.points) / len(self.points)

    @property
    def cy(self) -> float:
        if not self.points:
            return 0.0
        return sum(p[1] for p in self.points) / len(self.points)


def _rgb_to_hex(rgb: tuple[float, ...] | None) -> str | None:
    if not rgb or len(rgb) < 3:
        return None
    r, g, b = [max(0, min(255, int(round(c * 255)))) for c in rgb[:3]]
    return f"#{r:02x}{g:02x}{b:02x}"


def _polyline_length(pts: list[tuple[float, float]]) -> float:
    if len(pts) < 2:
        return 0.0
    total = 0.0
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        total += math.hypot(x1 - x0, y1 - y0)
    return total


def _items_to_points(items: list) -> list[tuple[float, float]]:
    pts: list[tuple[float, float]] = []
    for it in items:
        op = it[0]
        if op == "l":  # line: ("l", p1, p2) or similar depending on version
            # PyMuPDF drawing items: ("l", p1, p2) where p are Point
            if len(it) >= 3:
                p1, p2 = it[1], it[2]
                if not pts:
                    pts.append((float(p1.x), float(p1.y)))
                pts.append((float(p2.x), float(p2.y)))
        elif op == "c":  # curve — sample endpoints
            if len(it) >= 4:
                for p in it[1:4]:
                    pts.append((float(p.x), float(p.y)))
        elif op == "re":  # rectangle
            # ("re", rect) 
            if len(it) >= 2:
                r = it[1]
                pts.extend(
                    [
                        (float(r.x0), float(r.y0)),
                        (float(r.x1), float(r.y0)),
                        (float(r.x1), float(r.y1)),
                        (float(r.x0), float(r.y1)),
                        (float(r.x0), float(r.y0)),
                    ]
                )
        elif op == "qu":  # quad
            if len(it) >= 2:
                q = it[1]
                for p in (q.ul, q.ur, q.lr, q.ll, q.ul):
                    pts.append((float(p.x), float(p.y)))
    return pts


def extract_paths(page: fitz.Page, m_per_pt: float) -> list[PathSeg]:
    segs: list[PathSeg] = []
    try:
        drawings = page.get_drawings()
    except Exception:
        return segs

    for d in drawings:
        colour = d.get("color")
        # stroke colour may be under "color"; fill under "fill"
        if colour is None:
            colour = d.get("fill")
        width = float(d.get("width") or 0.0)
        items = d.get("items") or []
        pts = _items_to_points(items)
        if len(pts) < 2 and d.get("rect") is not None:
            r = d["rect"]
            pts = [
                (float(r.x0), float(r.y0)),
                (float(r.x1), float(r.y0)),
                (float(r.x1), float(r.y1)),
                (float(r.x0), float(r.y1)),
            ]
        if len(pts) < 2:
            continue
        length_pt = _polyline_length(pts)
        if length_pt < 1.0:
            continue
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        layer = None
        # Some drawings expose "layer" key when OCGs are mapped
        if d.get("layer"):
            layer = str(d["layer"])
        segs.append(
            PathSeg(
                points=pts,
                colour=tuple(colour) if colour else None,
                colour_hex=_rgb_to_hex(tuple(colour) if colour else None),
                width=width,
                layer=layer,
                length_pt=length_pt,
                length_m=length_pt * m_per_pt,
                bbox=[min(xs), min(ys), max(xs), max(ys)],
            )
        )
    return segs


def is_cyanish(colour: tuple[float, ...] | None) -> bool:
    if not colour or len(colour) < 3:
        return False
    r, g, b = colour[:3]
    return b > 0.45 and g > 0.35 and r < 0.55 and (b + g) > 1.2 * (r + 0.1)


def is_greenish(colour: tuple[float, ...] | None) -> bool:
    if not colour or len(colour) < 3:
        return False
    r, g, b = colour[:3]
    return g > 0.4 and g > r + 0.1 and g > b + 0.05


def is_reddish(colour: tuple[float, ...] | None) -> bool:
    if not colour or len(colour) < 3:
        return False
    r, g, b = colour[:3]
    return r > 0.5 and r > g + 0.15 and r > b + 0.15


def filter_by_colour(
    segs: list[PathSeg],
    *,
    cyan: bool = False,
    green: bool = False,
    red: bool = False,
) -> list[PathSeg]:
    out = []
    for s in segs:
        if cyan and is_cyanish(s.colour):
            out.append(s)
        elif green and is_greenish(s.colour):
            out.append(s)
        elif red and is_reddish(s.colour):
            out.append(s)
    return out


def total_length_m(segs: list[PathSeg]) -> float:
    return sum(s.length_m or 0.0 for s in segs)


def paths_near(
    segs: list[PathSeg], cx: float, cy: float, radius_pt: float = 100.0
) -> list[PathSeg]:
    r2 = radius_pt * radius_pt
    out = []
    for s in segs:
        dx = s.cx - cx
        dy = s.cy - cy
        if dx * dx + dy * dy <= r2:
            out.append(s)
            continue
        # Also check if any vertex is near
        for x, y in s.points:
            if (x - cx) ** 2 + (y - cy) ** 2 <= r2:
                out.append(s)
                break
    return out


def longest_cluster_length_m(segs: list[PathSeg], gap_pt: float = 40.0) -> float:
    """Greedy sum of near-connected cyan/tray strokes as a crude spine length."""
    if not segs:
        return 0.0
    remaining = sorted(segs, key=lambda s: s.length_pt, reverse=True)
    used = [False] * len(remaining)
    best = 0.0
    for i, seed in enumerate(remaining):
        if used[i]:
            continue
        cluster = [seed]
        used[i] = True
        changed = True
        while changed:
            changed = False
            for j, cand in enumerate(remaining):
                if used[j]:
                    continue
                for m in cluster:
                    if _segs_near(m, cand, gap_pt):
                        cluster.append(cand)
                        used[j] = True
                        changed = True
                        break
        best = max(best, total_length_m(cluster))
    return best


def _segs_near(a: PathSeg, b: PathSeg, gap_pt: float) -> bool:
    for x0, y0 in a.points[:: max(1, len(a.points) // 8)]:
        for x1, y1 in b.points[:: max(1, len(b.points) // 8)]:
            if math.hypot(x0 - x1, y0 - y1) <= gap_pt:
                return True
    return False
