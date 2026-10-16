"""Phase 4: length calculations and tender conversion.

Consumes Phase 1/2 Occurrence records (length_m is the one-way plan route).
Applies the formulas from skills/drawings-reader/SKILL.md, with user-overridable
waste factors (defaults match the skill).

Does **not** create new SQLite tables. Tender results are written into the
notes field of the existing Phase 3 ``occurrences`` table. No CSV/JSON reports.
"""

from __future__ import annotations

import sqlite3
from collections import defaultdict
from typing import Iterable

from riser_extract.schema import ExtractionResult, MeasurementType, Occurrence

# Defaults from SKILL.md — override via function arguments or config
DEFAULT_COORDINATION_FACTOR = 1.15
DEFAULT_TAIL_M_PER_PIPE = 1.5
DEFAULT_TRAY_WASTE_FACTOR = 0.15


def tender_length_two_pipe(
    plan_route_m: float,
    coordination_factor: float = DEFAULT_COORDINATION_FACTOR,
    tail_m_per_pipe: float = DEFAULT_TAIL_M_PER_PIPE,
) -> float:
    """Default tender conversion for a two-pipe indoor run (water F+R or refrigerant pair).

    tender_m = (plan_route_m × 2 pipes × coordination_factor) + (tail_m_per_pipe × 2)

    Factors are user-overridable; defaults match SKILL.md.
    """
    if plan_route_m < 0:
        raise ValueError("plan_route_m must be >= 0")
    if coordination_factor < 0 or tail_m_per_pipe < 0:
        raise ValueError("factors must be >= 0")
    return (plan_route_m * 2 * coordination_factor) + (tail_m_per_pipe * 2)


def tray_length_with_waste(
    plan_length_m: float,
    waste_factor: float = DEFAULT_TRAY_WASTE_FACTOR,
) -> float:
    """One tray per printed size + waste.

    waste_factor is user-overridable (e.g. 0.10 = 10 %); default is 15 %.
    """
    if plan_length_m < 0:
        raise ValueError("plan_length_m must be >= 0")
    if waste_factor < 0:
        raise ValueError("waste_factor must be >= 0")
    return plan_length_m * (1 + waste_factor)


def apply_tender(
    occ: Occurrence,
    *,
    coordination_factor: float = DEFAULT_COORDINATION_FACTOR,
    tail_m_per_pipe: float = DEFAULT_TAIL_M_PER_PIPE,
    tray_waste_factor: float = DEFAULT_TRAY_WASTE_FACTOR,
) -> Occurrence:
    """Return a copy with tender conversion appended to notes.

    length_m remains the drawn/plan route. tender_length_m is stashed on the
    object for callers; it is not a schema field.
    Factors are user-overridable.
    """
    updated = occ.model_copy(deep=True)
    plan = occ.length_m or 0.0
    notes = list(filter(None, [occ.notes]))

    if occ.unit == "m" and plan > 0:
        if "tray" in (occ.item_id or "").lower() or "tray" in (occ.legacy_item_id or "").lower():
            tender = tray_length_with_waste(plan, waste_factor=tray_waste_factor)
            notes.append(f"tray waste {tray_waste_factor:.0%} applied → tender {tender:.2f} m")
        elif occ.measurement_type in {MeasurementType.SCALED, MeasurementType.GEOMETRY}:
            tender = tender_length_two_pipe(
                plan,
                coordination_factor=coordination_factor,
                tail_m_per_pipe=tail_m_per_pipe,
            )
            notes.append(
                f"tender conversion (2×{coordination_factor} + {tail_m_per_pipe*2:.1f} m tails) → {tender:.2f} m"
            )
        else:
            tender = plan
            notes.append("no tender conversion (printed/vertical/excluded)")
        updated.notes = "; ".join(notes)
        updated.__dict__["tender_length_m"] = round(tender, 2)
    return updated


def aggregate_by_item(
    occurrences: Iterable[Occurrence],
) -> dict[tuple[str, str], dict]:
    """Group by (item_id or legacy, floor_tab_name)."""
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


def update_existing_inventory(
    conn: sqlite3.Connection,
    *,
    project_id: int | None = None,
    document_id: int | None = None,
    coordination_factor: float = DEFAULT_COORDINATION_FACTOR,
    tail_m_per_pipe: float = DEFAULT_TAIL_M_PER_PIPE,
    tray_waste_factor: float = DEFAULT_TRAY_WASTE_FACTOR,
) -> int:
    """Apply tender conversion notes to existing Phase 3 occurrences.

    Updates the ``notes`` column of rows that have length_m > 0 and unit = 'm'.
    Does not create tables or columns. Returns the number of rows updated.

    Waste factors are user-overridable; defaults match SKILL.md.
    Caller must already have the Phase 3 schema (occurrences table).
    """
    where = ["unit = 'm'", "length_m IS NOT NULL", "length_m > 0"]
    params: list = []
    if project_id is not None:
        where.append("project_id = ?")
        params.append(project_id)
    if document_id is not None:
        where.append("document_id = ?")
        params.append(document_id)

    sql = f"""
        SELECT id, item_id, legacy_item_id, measurement_type, length_m, notes
        FROM occurrences
        WHERE {' AND '.join(where)}
    """
    rows = conn.execute(sql, params).fetchall()
    updated = 0
    for row in rows:
        from riser_extract.schema import Scope
        occ = Occurrence(
            drawing_number="",
            floor_tab_name="",
            scale="",
            annotation="",
            item_id=row["item_id"],
            legacy_item_id=row["legacy_item_id"],
            unit="m",
            length_m=row["length_m"],
            measurement_type=row["measurement_type"] or "scaled",
            scope=Scope.IN,
            notes=row["notes"],
        )
        processed = apply_tender(
            occ,
            coordination_factor=coordination_factor,
            tail_m_per_pipe=tail_m_per_pipe,
            tray_waste_factor=tray_waste_factor,
        )
        if processed.notes != row["notes"]:
            conn.execute(
                "UPDATE occurrences SET notes = ? WHERE id = ?",
                (processed.notes, row["id"]),
            )
            updated += 1
    conn.commit()
    return updated


def process_extraction(
    result: ExtractionResult,
    *,
    coordination_factor: float = DEFAULT_COORDINATION_FACTOR,
    tail_m_per_pipe: float = DEFAULT_TAIL_M_PER_PIPE,
    tray_waste_factor: float = DEFAULT_TRAY_WASTE_FACTOR,
) -> tuple[list[Occurrence], dict]:
    """Apply tender conversion to all occurrences in an ExtractionResult.

    Waste factors are user-overridable.
    """
    processed = [
        apply_tender(
            o,
            coordination_factor=coordination_factor,
            tail_m_per_pipe=tail_m_per_pipe,
            tray_waste_factor=tray_waste_factor,
        )
        for o in result.occurrences
    ]
    groups = aggregate_by_item(processed)
    return processed, groups
