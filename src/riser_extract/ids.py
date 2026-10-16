"""Trade item IDs + legacy skill ID mapping.

Live IDs: MEC / ELEC / PLUM / VENT
Legacy skill IDs (drawings-reader inventory-model.md): HC / VT / PH
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ItemSpec:
    item_id: str
    legacy_item_id: str
    category: str
    unit: str
    scope: str = "in"


# Canonical catalogue for Phase 1 classification.
CATALOGUE: dict[str, ItemSpec] = {
    "MEC-FCU-WALL": ItemSpec("MEC-FCU-WALL", "HC-FCU-WALL", "Indoor terminals", "no."),
    "MEC-FCU-CASS": ItemSpec("MEC-FCU-CASS", "HC-FCU-CASS", "Indoor terminals", "no."),
    "MEC-HBC": ItemSpec("MEC-HBC", "HC-HBC", "Controllers", "no."),
    "MEC-ODU": ItemSpec("MEC-ODU", "HC-ODU", "Outdoor / plant", "no."),
    "MEC-CU-IN": ItemSpec("MEC-CU-IN", "HC-CU-IN", "Refrigerant / F+R pipe", "m"),
    "MEC-CU-RISER": ItemSpec("MEC-CU-RISER", "HC-CU-RISER", "Refrigerant / F+R pipe", "m"),
    "MEC-CU-ROOF": ItemSpec("MEC-CU-ROOF", "HC-CU-ROOF", "Refrigerant / F+R pipe", "m"),
    "MEC-TRAY-400": ItemSpec("MEC-TRAY-400", "HC-TRAY-400", "Tray / containment", "m"),
    "MEC-TRAY-300": ItemSpec("MEC-TRAY-300", "HC-TRAY-300", "Tray / containment", "m"),
    "PLUM-COND": ItemSpec("PLUM-COND", "HC-COND", "Condensate", "m"),
    "MEC-LAG-S": ItemSpec("MEC-LAG-S", "HC-LAG-S", "Lagging", "m"),
    "MEC-LAG-L": ItemSpec("MEC-LAG-L", "HC-LAG-L", "Lagging", "m"),
    "ELEC-STAT": ItemSpec("ELEC-STAT", "HC-STAT", "Controls / stats", "no."),
    "ELEC-PNL": ItemSpec("ELEC-PNL", "HC-ELEC-PNL", "Electric heat", "no."),
    "ELEC-CUR": ItemSpec("ELEC-CUR", "HC-ELEC-CUR", "Electric heat", "no."),
    "VENT-AHU": ItemSpec("VENT-AHU", "VT-AHU", "Exclusions / interfaces", "no.", scope="out"),
    "PLUM-ASHP-DHW": ItemSpec(
        "PLUM-ASHP-DHW", "PH-ASHP-DHW", "Exclusions / interfaces", "no.", scope="out"
    ),
}


def spec_for(item_id: str | None) -> ItemSpec | None:
    if not item_id:
        return None
    return CATALOGUE.get(item_id)
