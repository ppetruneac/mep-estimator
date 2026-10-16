"""Extract words with coordinates in the displayed page frame."""

from __future__ import annotations

from dataclasses import dataclass

import pymupdf as fitz


@dataclass
class Word:
    text: str
    x0: float
    y0: float
    x1: float
    y1: float

    @property
    def cx(self) -> float:
        return 0.5 * (self.x0 + self.x1)

    @property
    def cy(self) -> float:
        return 0.5 * (self.y0 + self.y1)

    @property
    def bbox(self) -> list[float]:
        return [self.x0, self.y0, self.x1, self.y1]


def extract_words(page: fitz.Page) -> list[Word]:
    """Return words in displayed-page coordinates (rotation applied)."""
    words: list[Word] = []
    # get_text("words") → tuples (x0, y0, x1, y1, word, block, line, wordno)
    for w in page.get_text("words"):
        text = (w[4] or "").strip()
        if not text:
            continue
        words.append(Word(text=text, x0=float(w[0]), y0=float(w[1]), x1=float(w[2]), y1=float(w[3])))
    return words


def full_text(words: list[Word]) -> str:
    return " ".join(w.text for w in words)


def words_near(words: list[Word], cx: float, cy: float, radius_pt: float = 80.0) -> list[Word]:
    out = []
    r2 = radius_pt * radius_pt
    for w in words:
        dx = w.cx - cx
        dy = w.cy - cy
        if dx * dx + dy * dy <= r2:
            out.append(w)
    return out


def join_nearby_words(words: list[Word], max_gap_pt: float = 12.0) -> list[Word]:
    """Merge adjacent word fragments into phrases.

    Handles both normal horizontal text and AutoCAD-rotated labels whose
    glyphs stack vertically (narrow x-span, progressive y).
    """
    if not words:
        return []
    # Horizontal pass (same line)
    ordered = sorted(words, key=lambda w: (round(w.cy, 1), w.x0))
    horiz: list[Word] = []
    cur = ordered[0]
    for w in ordered[1:]:
        same_line = abs(w.cy - cur.cy) < 4.0
        gap = w.x0 - cur.x1
        if same_line and 0 <= gap <= max_gap_pt:
            cur = Word(
                text=f"{cur.text} {w.text}",
                x0=cur.x0,
                y0=min(cur.y0, w.y0),
                x1=w.x1,
                y1=max(cur.y1, w.y1),
            )
        else:
            horiz.append(cur)
            cur = w
    horiz.append(cur)

    # Vertical pass (rotated stacks share nearly the same x)
    ordered_v = sorted(horiz, key=lambda w: (round(w.cx, 0), w.y0))
    merged: list[Word] = []
    cur = ordered_v[0]
    for w in ordered_v[1:]:
        same_col = abs(w.cx - cur.cx) < 14.0
        gap = w.y0 - cur.y1
        # Also allow slight overlap from glyph boxes
        if same_col and -4.0 <= gap <= max_gap_pt:
            cur = Word(
                text=f"{cur.text} {w.text}",
                x0=min(cur.x0, w.x0),
                y0=min(cur.y0, w.y0),
                x1=max(cur.x1, w.x1),
                y1=max(cur.y1, w.y1),
            )
        else:
            merged.append(cur)
            cur = w
    merged.append(cur)
    return merged
