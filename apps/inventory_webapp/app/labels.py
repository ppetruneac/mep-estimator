"""Human-readable labels for item IDs and measurement types.

Trade IDs (MEC-*) are the stable catalog keys. The Hubby gold Excel uses
annotation text (FCU.B.01) + category bands — we show both.
"""

from __future__ import annotations

ITEM_LABELS: dict[str, str] = {
    "MEC-FCU-WALL": "Wall-mounted VRF / FCU",
    "MEC-FCU-CASS": "Ceiling cassette FCU",
    "MEC-HBC": "Heat / branch controller (HBC)",
    "MEC-ODU": "Outdoor VRV / heat-pump module",
    "MEC-CU-IN": "Indoor refrigerant pair (FCU → HBC home-run)",
    "MEC-CU-RISER": "This-storey riser / passing refrigerant pair",
    "MEC-CU-ROOF": "Roof plant refrigerant lateral",
    "MEC-TRAY-400": "400 mm services tray",
    "MEC-TRAY-300": "300 mm services tray",
    "PLUM-COND": "FCU condensate drain",
    "MEC-LAG-S": "Lagging — small diameter",
    "MEC-LAG-L": "Lagging — large diameter",
    "ELEC-STAT": "Room thermostat / controller",
    "ELEC-PNL": "Electric panel heater",
    "ELEC-CUR": "Electric over-door curtain",
    "VENT-AHU": "Air handling unit (ventilation — exclusion)",
    "PLUM-ASHP-DHW": "ASHP / DHW plant (exclusion)",
}

MEASUREMENT_TYPE_HELP: dict[str, str] = {
    "printed": "Count or size printed on the drawing (tag, note, schedule).",
    "scaled": "Length measured from vector geometry at the sheet scale.",
    "geometry": "Estimated from tag-to-core / crow-flies geometry (not a traced spine).",
    "vertical": "Vertical rise from storey height or section (not plan length).",
    "specified-not-drawn": "Required by spec/notes but not drawn on this sheet.",
    "excluded": "Seen on the sheet but outside this take-off premise.",
}


def item_label(item_id: str | None) -> str | None:
    if not item_id:
        return None
    return ITEM_LABELS.get(item_id)
