"""Map extractor rows → Hubby gold Excel section bands.

The gold workbook uses lettered sections per floor tab, e.g.
``A — INDOOR UNITS AND CONTROLLERS``. Those are what estimators expect
to see as "category" in the review table.
"""

from __future__ import annotations

# Normalised section titles (single em-dash form)
BEDROOM = {
    "fcu_hbc": "A — INDOOR UNITS AND CONTROLLERS",
    "cu_in": "B — REFRIGERANT / F+R PIPEWORK",
    "tray_riser": "C — TRAY AND RISERS",
    "associated": "D — ASSOCIATED PIPE NOT DRAWN",
    "exclusions": "E — EXCLUSIONS",
}

BASEMENT = {
    "fcu_hbc": "A — INDOOR UNITS AND CONTROLLERS",
    "cu_in": "B — FLOW AND RETURN PIPEWORK (FCU TO HBC / RISER)",
    "refrigerant": "C — REFRIGERANT (BASEMENT ONLY)",
    "tray_riser": "D — TRAY AND RISERS",
    "electric": "E — ELECTRIC HEATING",
    "associated": "F — ASSOCIATED PIPEWORK NOT ANNOTATED ON THE SHEET",
    "exclusions": "G — EXCLUSIONS / INTERFACES",
}

GROUND = {
    "context": "A — DRAWING CONTEXT (ROOMS ON THIS SHEET)",
    "terminals": "B — HOTEL TERMINALS (ANNOTATED EQUIPMENT)",
    "riser": "C — RISERS AND REFRIGERANT PIPEWORK",
    "no_pipe": "D — PIPEWORK NOT PRESENT ON THIS SHEET",
    "exclusions": "E — EXCLUSIONS",
}

ROOF = {
    "plant": "A — NAMED PLANT (ON THE SHEET)",
    "duct": "B — PRINTED DUCT SIZES (ROOF CONNECTIONS)",
    "refrigerant": "C — REFRIGERANT AND WATER FROM THE ROOF",
    "exclusions": "D — EXCLUSIONS / INTERFACES",
}


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

    if floor == "Basement":
        return _basement(iid, ann, sym)
    if floor == "Ground Floor":
        return _ground(iid, ann, sym)
    if floor == "Roof Plant":
        return _roof(iid, ann, sym)
    # Bedroom floors (and First Floor if ever present)
    return _bedroom(iid, ann, sym)


def _basement(iid: str, ann: str, sym: str) -> str:
    # item_id wins over annotation keywords (F+R rows mention FCU tags)
    if iid.startswith("MEC-CU-IN") or iid == "MEC-CU-IN":
        return BASEMENT["cu_in"]
    if iid == "MEC-CU-RISER":
        return BASEMENT["tray_riser"]
    if iid in {"MEC-TRAY-300", "MEC-TRAY-400"}:
        return BASEMENT["tray_riser"]
    if iid in {"MEC-FCU-WALL", "MEC-FCU-CASS", "MEC-HBC"} or sym in {
        "fcu_wall",
        "fcu_cass",
        "hbc",
    }:
        return BASEMENT["fcu_hbc"]
    if iid in {"ELEC-PNL", "ELEC-CUR"} or sym in {"panel_heater", "door_curtain"}:
        return BASEMENT["electric"]
    if "TRAY" in ann:
        return BASEMENT["tray_riser"]
    if "RISER" in ann or "PASSING" in ann:
        return BASEMENT["tray_riser"]
    if "F+R" in ann or "PAIR" in ann:
        return BASEMENT["cu_in"]
    if iid in {"VENT-AHU", "PLUM-ASHP-DHW"} or "EXCLUS" in ann:
        return BASEMENT["exclusions"]
    if "REFRIGERANT" in ann and "HBC" not in ann:
        return BASEMENT["refrigerant"]
    return BASEMENT["associated"]


def _ground(iid: str, ann: str, sym: str) -> str:
    if iid in {"ELEC-PNL", "ELEC-CUR", "MEC-FCU-WALL", "MEC-FCU-CASS", "MEC-HBC"} or sym in {
        "panel_heater",
        "door_curtain",
        "fcu_wall",
        "fcu_cass",
        "hbc",
    }:
        return GROUND["terminals"]
    if iid in {"MEC-CU-RISER", "MEC-CU-IN"} or "RISER" in ann or "REFRIGERANT" in ann:
        return GROUND["riser"]
    if iid in {"VENT-AHU", "PLUM-ASHP-DHW"}:
        return GROUND["exclusions"]
    return GROUND["context"]


def _roof(iid: str, ann: str, sym: str) -> str:
    if iid in {"VENT-AHU", "PLUM-ASHP-DHW", "MEC-ODU"} or sym in {"ahu", "ashp"}:
        return ROOF["plant"]
    if iid in {"MEC-CU-ROOF", "MEC-CU-IN", "MEC-CU-RISER"} or "REFRIGERANT" in ann:
        return ROOF["refrigerant"]
    if "DUCT" in ann:
        return ROOF["duct"]
    return ROOF["exclusions"]


def _bedroom(iid: str, ann: str, sym: str) -> str:
    if iid in {"MEC-CU-IN", "MEC-CU-ROOF"}:
        return BEDROOM["cu_in"]
    if iid == "MEC-CU-RISER":
        return BEDROOM["tray_riser"]
    if iid in {"MEC-TRAY-300", "MEC-TRAY-400"}:
        return BEDROOM["tray_riser"]
    if iid in {"MEC-FCU-WALL", "MEC-FCU-CASS", "MEC-HBC"} or sym in {
        "fcu_wall",
        "fcu_cass",
        "hbc",
    }:
        return BEDROOM["fcu_hbc"]
    if "TRAY" in ann:
        return BEDROOM["tray_riser"]
    if "RISER" in ann or "PASSING" in ann:
        return BEDROOM["tray_riser"]
    if "F+R" in ann or "REFRIGERANT" in ann or "PAIR" in ann:
        return BEDROOM["cu_in"]
    if iid in {"VENT-AHU", "PLUM-ASHP-DHW"}:
        return BEDROOM["exclusions"]
    return BEDROOM["associated"]
