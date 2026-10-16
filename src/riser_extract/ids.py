"""Trade item IDs + catalogue mapping.

Catalogue = category (Excel take-off band) + item_id / SKU.

Live IDs: MEC / ELEC / PLUM / VENT
Legacy skill IDs (drawings-reader inventory-model.md): HC / VT / PH
"""

from __future__ import annotations

from dataclasses import dataclass

# Excel-band category names (same as apps/inventory_webapp/app/excel_bands.py)
CAT_INDOOR = "A — INDOOR UNITS AND CONTROLLERS"
CAT_FLOW_RETURN = "B — FLOW AND RETURN PIPEWORK"
CAT_REFRIGERANT = "C — REFRIGERANT"
CAT_TRAY_RISERS = "D — TRAY AND RISERS"
CAT_ELECTRIC = "E — ELECTRIC HEATING"
CAT_ASSOCIATED = "F — ASSOCIATED PIPEWORK NOT ANNOTATED ON THE SHEET"
CAT_EXCLUSIONS = "G — EXCLUSIONS / INTERFACES"
CAT_LAGGING = "PIPE LAGGING"
CAT_CONTAINMENT = "CONTAINMENT (TRAY / PIPE / SUPPORTS / CLIPS)"
CAT_CONSUMABLES = "CONSUMABLES"
CAT_STATS = "ROOM THERMOSTATS / CONTROLLERS"
CAT_NAMED_PLANT = "A — NAMED PLANT"


@dataclass(frozen=True)
class ItemSpec:
    item_id: str
    legacy_item_id: str
    category: str  # Excel-band catalogue category
    unit: str
    scope: str = "in"


# Catalogue: each row is category + item (SKU key = item_id)
CATALOGUE: dict[str, ItemSpec] = {
    "MEC-FCU-WALL": ItemSpec("MEC-FCU-WALL", "HC-FCU-WALL", CAT_INDOOR, "no."),
    "MEC-FCU-CASS": ItemSpec("MEC-FCU-CASS", "HC-FCU-CASS", CAT_INDOOR, "no."),
    "MEC-HBC": ItemSpec("MEC-HBC", "HC-HBC", CAT_INDOOR, "no."),
    "MEC-ODU": ItemSpec("MEC-ODU", "HC-ODU", CAT_NAMED_PLANT, "no."),
    "MEC-CU-IN": ItemSpec("MEC-CU-IN", "HC-CU-IN", CAT_FLOW_RETURN, "m"),
    "MEC-CU-RISER": ItemSpec("MEC-CU-RISER", "HC-CU-RISER", CAT_TRAY_RISERS, "m"),
    "MEC-CU-ROOF": ItemSpec("MEC-CU-ROOF", "HC-CU-ROOF", CAT_REFRIGERANT, "m"),
    "MEC-TRAY-400": ItemSpec("MEC-TRAY-400", "HC-TRAY-400", CAT_TRAY_RISERS, "m"),
    "MEC-TRAY-300": ItemSpec("MEC-TRAY-300", "HC-TRAY-300", CAT_TRAY_RISERS, "m"),
    "PLUM-COND": ItemSpec("PLUM-COND", "HC-COND", CAT_ASSOCIATED, "m"),
    "MEC-LAG-S": ItemSpec("MEC-LAG-S", "HC-LAG-S", CAT_LAGGING, "m"),
    "MEC-LAG-L": ItemSpec("MEC-LAG-L", "HC-LAG-L", CAT_LAGGING, "m"),
    "ELEC-STAT": ItemSpec("ELEC-STAT", "HC-STAT", CAT_STATS, "no."),
    "ELEC-PNL": ItemSpec("ELEC-PNL", "HC-ELEC-PNL", CAT_ELECTRIC, "no."),
    "ELEC-CUR": ItemSpec("ELEC-CUR", "HC-ELEC-CUR", CAT_ELECTRIC, "no."),
    "VENT-AHU": ItemSpec("VENT-AHU", "VT-AHU", CAT_EXCLUSIONS, "no.", scope="out"),
    "PLUM-ASHP-DHW": ItemSpec(
        "PLUM-ASHP-DHW", "PH-ASHP-DHW", CAT_EXCLUSIONS, "no.", scope="out"
    ),
}


def spec_for(item_id: str | None) -> ItemSpec | None:
    if not item_id:
        return None
    return CATALOGUE.get(item_id)
