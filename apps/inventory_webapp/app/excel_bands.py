"""Map extractor rows → Hubby gold Excel take-off categories.

Names match the source inventory workbook section bands.
"""

from __future__ import annotations

# Canonical categories (Excel language)
INDOOR_UNITS = "A — INDOOR UNITS AND CONTROLLERS"
FLOW_RETURN = "B — FLOW AND RETURN PIPEWORK"
REFRIGERANT = "C — REFRIGERANT"
TRAY_RISERS = "D — TRAY AND RISERS"
ELECTRIC_HEATING = "E — ELECTRIC HEATING"
ASSOCIATED_NOT_ANNOTATED = "F — ASSOCIATED PIPEWORK NOT ANNOTATED ON THE SHEET"
EXCLUSIONS = "G — EXCLUSIONS / INTERFACES"
PIPE_LAGGING = "PIPE LAGGING"
CONTAINMENT = "CONTAINMENT (TRAY / PIPE / SUPPORTS / CLIPS)"
CONSUMABLES = "CONSUMABLES"
ROOM_STATS = "ROOM THERMOSTATS / CONTROLLERS"
NAMED_PLANT = "A — NAMED PLANT"
DUCT_SIZES = "B — PRINTED DUCT SIZES"


def excel_category(
    *,
    floor_tab_name: str | None,
    item_id: str | None,
    annotation: str | None = None,
    symbol_class: str | None = None,
) -> str:
    floor = (floor_tab_name or "").strip()
    iid = (item_id or "").upper().strip()
    ann = (annotation or "").upper()
    sym = (symbol_class or "").lower()

    # --- item_id first (never let linked FCU symbol_class steal pipe rows) ---
    if iid in {"MEC-CU-IN", "MEC-CU-ROOF"}:
        if floor == "Roof Plant" or iid == "MEC-CU-ROOF":
            return REFRIGERANT
        if "REFRIGERANT" in ann and "F+R" not in ann and "PAIR" not in ann:
            return REFRIGERANT
        return FLOW_RETURN

    if iid == "MEC-CU-RISER":
        return TRAY_RISERS

    if iid in {"MEC-TRAY-300", "MEC-TRAY-400"}:
        return TRAY_RISERS

    if iid in {"MEC-FCU-WALL", "MEC-FCU-CASS", "MEC-HBC"}:
        return INDOOR_UNITS

    if iid in {"ELEC-PNL", "ELEC-CUR"}:
        return ELECTRIC_HEATING

    if iid in {"MEC-LAG-S", "MEC-LAG-L"}:
        return PIPE_LAGGING

    if iid == "ELEC-STAT":
        return ROOM_STATS

    if iid in {"VENT-AHU", "PLUM-ASHP-DHW", "MEC-ODU"}:
        if floor == "Roof Plant":
            return NAMED_PLANT
        return EXCLUSIONS

    # --- symbol_class only when item_id did not decide ---
    if sym in {"fcu_wall", "fcu_cass", "hbc"}:
        return INDOOR_UNITS
    if sym in {"panel_heater", "door_curtain"}:
        return ELECTRIC_HEATING
    if sym in {"ahu", "ashp"}:
        return NAMED_PLANT if floor == "Roof Plant" else EXCLUSIONS
    if sym == "tray_note":
        return TRAY_RISERS

    # --- annotation fallbacks ---
    if "F+R" in ann or "PAIR" in ann or "HOME-RUN" in ann or "HOME RUN" in ann:
        return FLOW_RETURN
    if "REFRIGERANT" in ann:
        return REFRIGERANT
    if "TRAY" in ann:
        return TRAY_RISERS
    if "RISER" in ann or "PASSING" in ann:
        return TRAY_RISERS
    if "DUCT" in ann:
        return DUCT_SIZES
    if "LAGGING" in ann or " LAG" in f" {ann}":
        return PIPE_LAGGING
    if "THERMOSTAT" in ann or "STAT" in ann:
        return ROOM_STATS
    if "CLIP" in ann or "HANGER" in ann or "COUPLER" in ann or "SUPPORT" in ann:
        return CONTAINMENT
    if "OFN" in ann or "NITROGEN" in ann or "CONSUMABLE" in ann:
        return CONSUMABLES
    if "EXCLUS" in ann:
        return EXCLUSIONS
    if "CONDENS" in ann:
        return ASSOCIATED_NOT_ANNOTATED

    # Labels / notes without a firm item_id
    return ASSOCIATED_NOT_ANNOTATED
