from riser_extract.ids import CATALOGUE, spec_for


def test_legacy_mapping_covers_skill_ids():
    assert CATALOGUE["MEC-FCU-WALL"].legacy_item_id == "HC-FCU-WALL"
    assert CATALOGUE["ELEC-PNL"].legacy_item_id == "HC-ELEC-PNL"
    assert CATALOGUE["VENT-AHU"].legacy_item_id == "VT-AHU"
    assert CATALOGUE["PLUM-ASHP-DHW"].legacy_item_id == "PH-ASHP-DHW"
    assert CATALOGUE["VENT-AHU"].scope == "out"


def test_spec_for_unknown():
    assert spec_for(None) is None
    assert spec_for("NOPE") is None
