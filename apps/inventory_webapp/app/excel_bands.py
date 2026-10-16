"""Map extractor rows → Hubby gold Excel take-off categories.

These names match the source inventory workbook section bands
(without per-floor letter prefixes), so the review table reads like
the Excel file.
"""

from __future__ import annotations

# Canonical categories (same language as the gold Excel)
INDOOR_UNITS = "INDOOR UNITS AND CONTROLLERS"
FLOW_RETURN = "FLOW AND RETURN PIPEWORK"
REFRIGERANT = "REFRIGERANT"
TRAY_RISERS = "TRAY AND RISERS"
ELECTRIC_HEATING = "ELECTRIC HEATING"
PIPE_LAGGING = "PIPE LAGGING"
CONTAINMENT = "CONTAINMENT (TRAY / PIPE / SUPPORTS / CLIPS)"
CONSUMABLES = "CONSUMABLES"
ROOM_STATS = "ROOM THERMOSTATS / CONTROLLERS"
EXCLUSIONS = "EXCLUSIONS / INTERFACES"
ASSOCIATED_NOT_DRAWN = "ASSOCIATED PIPE NOT DRAWN"
NAMED_PLANT = "NAMED PLANT"
DUCT_SIZES = "PRINTED DUCT SIZES"


def excel_category(
    *,
    floor_tab_name: str | None,
    item_id: str | None,
    annotation: str | None = None,
    symbol_class: str | None = None,
) -> str:
    floor = (floor_tab_name or "").strip()
    iid = (item_id or "").upper()
    ann = (annotation or "").upper()
    sym = (symbol_class or "").lower()

    # --- item_id first (stable) ---
    if iid in {"MEC-FCU-WALL", "MEC-FCU-CASS", "MEC-HBC"} or sym in {
        "fcu_wall",
        "fcu_cass",
        "hbc",
    }:
        return INDOOR_UNITS

    if iid in {"ELEC-PNL", "ELEC-CUR"} or sym in {"panel_heater", "door_curtain"}:
        # Ground-floor annotated electrics sit with hotel terminals in Excel,
        # but the shared estimator language is electric heating.
        return ELECTRIC_HEATING

    if iid in {"MEC-TRAY-300", "MEC-TRAY-400"} or "TRAY" in ann:
        return TRAY_RISERS

    if iid == "MEC-CU-RISER" or "RISER" in ann or "PASSING" in ann:
        return TRAY_RISERS

    if iid in {"MEC-CU-IN", "MEC-CU-ROOF"}:
        # Basement F+R home-runs are "flow and return"; roof laterals are refrigerant.
        if floor == "Roof Plant" or iid == "MEC-CU-ROOF":
            return REFRIGERANT
        if "REFRIGERANT" in ann and "F+R" not in ann and "PAIR" not in ann:
            return REFRIGERANT
        return FLOW_RETURN

    if iid in {"MEC-LAG-S", "MEC-LAG-L"} or "LAGGING" in ann or "LAG" in ann:
        return PIPE_LAGGING

    if iid == "ELEC-STAT" or "THERMOSTAT" in ann or "STAT" in ann:
        return ROOM_STATS

    if iid in {"VENT-AHU", "PLUM-ASHP-DHW", "MEC-ODU"} or sym in {"ahu", "ashp"}:
        if floor == "Roof Plant":
            return NAMED_PLANT
        return EXCLUSIONS

    # --- annotation fallbacks ---
    if "F+R" in ann or "PAIR" in ann or "HOME-RUN" in ann or "HOME RUN" in ann:
        return FLOW_RETURN
    if "REFRIGERANT" in ann:
        return REFRIGERANT
    if "DUCT" in ann:
        return DUCT_SIZES
    if "CLIP" in ann or "HANGER" in ann or "COUPLER" in ann or "SUPPORT" in ann:
        return CONTAINMENT
    if "OFN" in ann or "NITROGEN" in ann or "CONSUMABLE" in ann:
        return CONSUMABLES
    if "CONDENS" in ann:
        return ASSOCIATED_NOT_DRAWN

    return ASSOCIATED_NOT_DRAWN
