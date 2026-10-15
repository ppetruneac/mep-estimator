"""Propose leader associations: annotation text → nearby path/symbol."""

from __future__ import annotations

import math
from dataclasses import dataclass

from riser_extract.paths import PathSeg, is_cyanish, is_greenish, is_reddish
from riser_extract.tags import TagHit


@dataclass
class LeaderLink:
    tag: TagHit
    path: PathSeg | None
    target_desc: str
    distance_pt: float


def _endpoint_near_text(seg: PathSeg, tag: TagHit, pad: float = 30.0) -> bool:
    for x, y in (seg.points[0], seg.points[-1]):
        if tag.x0 - pad <= x <= tag.x1 + pad and tag.y0 - pad <= y <= tag.y1 + pad:
            return True
    return False


def _min_dist(seg: PathSeg, tag: TagHit) -> float:
    best = 1e18
    for x, y in (seg.points[0], seg.points[-1], (seg.cx, seg.cy)):
        best = min(best, math.hypot(x - tag.cx, y - tag.cy))
    return best


def propose_leaders(
    tags: list[TagHit],
    paths: list[PathSeg],
    *,
    max_dist_pt: float = 220.0,
) -> list[LeaderLink]:
    """For each equipment tag, find a plausible leader / nearby coloured path."""
    # Candidate leader strokes: thin, relatively long, often black
    thin = [p for p in paths if p.width <= 1.5 and p.length_pt >= 20]
    links: list[LeaderLink] = []
    for tag in tags:
        if tag.kind in {"label"}:
            continue
        best: LeaderLink | None = None
        # Prefer a thin stroke that starts near the text
        for seg in thin:
            if not _endpoint_near_text(seg, tag, pad=36.0):
                continue
            dist = _min_dist(seg, tag)
            if dist > max_dist_pt:
                continue
            # Far end of the leader = the endpoint farther from the tag centroid
            p0, p1 = seg.points[0], seg.points[-1]
            d0 = math.hypot(p0[0] - tag.cx, p0[1] - tag.cy)
            d1 = math.hypot(p1[0] - tag.cx, p1[1] - tag.cy)
            other = p1 if d1 >= d0 else p0
            target = _describe_target(paths, other[0], other[1], tag)
            cand = LeaderLink(tag=tag, path=seg, target_desc=target, distance_pt=dist)
            if best is None or cand.distance_pt < best.distance_pt:
                best = cand
        if best is None:
            # Fallback: nearest coloured blob
            target = _describe_target(paths, tag.cx, tag.cy, tag)
            best = LeaderLink(tag=tag, path=None, target_desc=target, distance_pt=0.0)
        links.append(best)
    return links


def _describe_target(paths: list[PathSeg], x: float, y: float, tag: TagHit) -> str:
    near = []
    for p in paths:
        if math.hypot(p.cx - x, p.cy - y) > 80:
            continue
        if is_cyanish(p.colour):
            near.append("cyan spine/pipe")
        elif is_greenish(p.colour):
            near.append("green riser/tray box")
        elif is_reddish(p.colour):
            near.append("red electric bar")
        elif p.layer:
            near.append(f"layer:{p.layer}")
    if tag.kind == "fcu":
        near.append("FCU symbol")
    if tag.kind == "hbc":
        near.append("HBC controller")
    if not near:
        return "unresolved symbol"
    # unique preserve order
    seen = set()
    out = []
    for n in near:
        if n not in seen:
            seen.add(n)
            out.append(n)
    return ", ".join(out[:3])
