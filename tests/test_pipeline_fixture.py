from pathlib import Path

from riser_extract.pipeline import extract_drawing

FIXTURE = Path(__file__).parent / "fixtures" / "synthetic_hvac.pdf"


def test_synthetic_extract_title_and_tags():
    result = extract_drawing(FIXTURE)
    assert result.title_block.drawing_number == "25280-SEN-02-DR-M-5602"
    assert result.title_block.floor_tab_name == "Second Floor"
    assert result.title_block.scale and "1:50" in result.title_block.scale
    fcus = [o for o in result.occurrences if o.item_id == "MEC-FCU-WALL"]
    hbcs = [o for o in result.occurrences if o.item_id == "MEC-HBC"]
    assert len(fcus) == 2
    assert len(hbcs) == 1
    assert all(o.legacy_item_id for o in fcus)
