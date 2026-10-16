"""Phase 4: length calculations, tender conversion, aggregation.

Consumes Phase 1 ExtractionResult / Occurrence records (length_m is the one-way
plan route). Applies the exact formulas from skills/drawings-reader/SKILL.md.
Stores results in SQLite (no CSV/JSON reports).

Deferred to later phases:
- Catalog-driven engineering formulas (Hazen-Williams etc.) — need Phase 3 catalog.
- Full Master/Summary Excel book assembly.
- Drive ground-truth validation harness (data not in repo).
"""

from __future__ import annotations

import sqlite3
from collections import defaultdict
from pathlib import Path
from typing import Iterable

from riser_extract.schema import ExtractionResult, MeasurementType, Occurrence, Scope

# Defaults from SKILL.md
COORDINATION_FACTOR = 1.15
TAIL_M_PER_PIPE = 1.5
TRAY_WASTE_FACTOR = 0.15


def tender_length_two_pipe(
    plan_route_m: float,
    coordination_factor: float = COORDINATION_FACTOR,
    tail_m_per_pipe: float = TAIL_M_PER_PIPE,
) -> float:
    """Default tender conversion for a two-pipe indoor run (water F+R or refrigerant pair).

    tender_m = (plan_route_m × 2 pipes × coordination) + (tail × 2)
    """
    if plan_route_m < 0:
        raise ValueError("plan_route_m must be >= 0")
    return (plan_route_m * 2 * coordination_factor) + (tail_m_per_pipe * 2)


def tray_length_with_waste(
    plan_length_m: float,
    waste_factor: float = TRAY_WASTE_FACTOR,
) -> float:
    """One tray per printed size + waste."""
    if plan_length_m < 0:
        raise ValueError("plan_length_m must be >= 0")
    return plan_length_m * (1 + waste_factor)


def apply_tender(occ: Occurrence) -> Occurrence:
    """Return a copy with tender_length_m computed and notes updated.

    length_m remains the drawn/plan route. tender is attached as a note field
    for now (schema extension deferred).
    """
    # Shallow copy via model_copy if pydantic v2
    updated = occ.model_copy(deep=True)
    plan = occ.length_m or 0.0
    notes = list(filter(None, [occ.notes]))

    if occ.unit == "m" and plan > 0:
        if "tray" in (occ.item_id or "").lower() or "tray" in (occ.legacy_item_id or "").lower():
            tender = tray_length_with_waste(plan)
            notes.append(f"tray waste {TRAY_WASTE_FACTOR:.0%} applied → tender {tender:.2f} m")
        elif occ.measurement_type in {MeasurementType.SCALED, MeasurementType.GEOMETRY}:
            # Two-pipe indoor run default
            tender = tender_length_two_pipe(plan)
            notes.append(
                f"tender conversion (2×{COORDINATION_FACTOR} + {TAIL_M_PER_PIPE*2:.1f} m tails) → {tender:.2f} m"
            )
        else:
            tender = plan
            notes.append("no tender conversion (printed/vertical/excluded)")
        # Store tender in notes for now; a future schema field can hold it explicitly
        updated.notes = "; ".join(notes)
        # Also stash on the object for downstream (not in schema yet)
        updated.__dict__["tender_length_m"] = round(tender, 2)
    return updated


def aggregate_by_item(
    occurrences: Iterable[Occurrence],
) -> dict[tuple[str, str], dict]:
    """Group by (item_id or legacy, floor_tab_name).

    Returns dict of key → {
        "plan_m": sum of length_m,
        "tender_m": sum of tender,
        "count": sum of counts,
        "measurement_types": set,
        "scopes": set,
        "notes": list,
    }
    Unique vs interface is recorded but full building aggregation is left to the caller
    (or Phase 3 Master tab).
    """
    groups: dict[tuple[str, str], dict] = defaultdict(
        lambda: {
            "plan_m": 0.0,
            "tender_m": 0.0,
            "count": 0.0,
            "measurement_types": set(),
            "scopes": set(),
            "notes": [],
            "where_found": set(),
        }
    )
    for occ in occurrences:
        key_id = occ.item_id or occ.legacy_item_id or occ.annotation or "unknown"
        key = (key_id, occ.floor_tab_name)
        g = groups[key]
        plan = occ.length_m or 0.0
        tender = getattr(occ, "tender_length_m", plan)
        if occ.unit == "m":
            g["plan_m"] += plan
            g["tender_m"] += tender
        g["count"] += occ.count
        g["measurement_types"].add(occ.measurement_type.value)
        g["scopes"].add(occ.scope.value)
        if occ.notes:
            g["notes"].append(occ.notes)
        g["where_found"].add(f"{occ.floor_tab_name} ({occ.drawing_number})")
    return dict(groups)


class LengthStore:
    """SQLite store for Phase 4 length results."""

    def __init__(self, db_path: str | Path = "lengths.sqlite"):
        self.db_path = Path(db_path)
        self.conn = sqlite3.connect(self.db_path)
        self._init_schema()

    def _init_schema(self) -> None:
        self.conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS segments (
                id INTEGER PRIMARY KEY,
                drawing_number TEXT,
                floor_tab_name TEXT,
                item_id TEXT,
                legacy_item_id TEXT,
                annotation TEXT,
                layer TEXT,
                colour TEXT,
                plan_length_m REAL,
                tender_length_m REAL,
                measurement_type TEXT,
                scope TEXT,
                notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS aggregates (
                id INTEGER PRIMARY KEY,
                item_id TEXT,
                floor_tab_name TEXT,
                plan_m REAL,
                tender_m REAL,
                count REAL,
                measurement_types TEXT,
                scopes TEXT,
                where_found TEXT,
                notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        self.conn.commit()

    def insert_occurrences(self, occurrences: Iterable[Occurrence]) -> None:
        rows = []
        for occ in occurrences:
            tender = getattr(occ, "tender_length_m", occ.length_m or 0.0)
            rows.append(
                (
                    occ.drawing_number,
                    occ.floor_tab_name,
                    occ.item_id,
                    occ.legacy_item_id,
                    occ.annotation,
                    occ.layer,
                    occ.colour,
                    occ.length_m,
                    tender,
                    occ.measurement_type.value,
                    occ.scope.value,
                    occ.notes,
                )
            )
        self.conn.executemany(
            """
            INSERT INTO segments (
                drawing_number, floor_tab_name, item_id, legacy_item_id,
                annotation, layer, colour, plan_length_m, tender_length_m,
                measurement_type, scope, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            rows,
        )
        self.conn.commit()

    def insert_aggregates(self, groups: dict) -> None:
        rows = []
        for (item_id, floor), g in groups.items():
            rows.append(
                (
                    item_id,
                    floor,
                    g["plan_m"],
                    g["tender_m"],
                    g["count"],
                    ",".join(sorted(g["measurement_types"])),
                    ",".join(sorted(g["scopes"])),
                    "; ".join(sorted(g["where_found"])),
                    " | ".join(g["notes"][:3]),
                )
            )
        self.conn.executemany(
            """
            INSERT INTO aggregates (
                item_id, floor_tab_name, plan_m, tender_m, count,
                measurement_types, scopes, where_found, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            rows,
        )
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()


def process_extraction(
    result: ExtractionResult,
    store: LengthStore | None = None,
) -> tuple[list[Occurrence], dict]:
    """Apply tender conversion to all occurrences and optionally persist."""
    processed = [apply_tender(o) for o in result.occurrences]
    groups = aggregate_by_item(processed)
    if store:
        store.insert_occurrences(processed)
        store.insert_aggregates(groups)
    return processed, groups
