from riser_extract.paths import PathSeg
from riser_extract.symbols import CLASS_FCU_WALL, CLASS_HBC, identify_symbols_rules
from riser_extract.tags import TagHit


def test_identify_fcu_and_hbc_with_compact_geom():
    tags = [
        TagHit("fcu", "FCU.02.01", "FCU.02.01", 100, 100, 140, 120),
        TagHit("hbc", "HB:02:01", "HB:02:01", 400, 100, 440, 120),
    ]
    paths = [
        PathSeg(
            points=[(80, 95), (95, 95), (95, 110), (80, 110)],
            colour=(1.0, 1.0, 0.0),
            colour_hex="#ffff00",
            width=1.0,
            layer="00AC Units",
            length_pt=60,
            length_m=1.0,
            bbox=[80, 95, 95, 110],
        ),
        PathSeg(
            points=[(380, 90), (410, 90), (410, 130), (380, 130)],
            colour=(1.0, 1.0, 1.0),
            colour_hex="#ffffff",
            width=1.0,
            layer="0",
            length_pt=80,
            length_m=1.2,
            bbox=[380, 90, 410, 130],
        ),
    ]
    syms = identify_symbols_rules(
        tags,
        paths,
        floor_tab_name="Second Floor",
        m_per_pt=0.01764,
        page_width=2000,
        page_height=1400,
    )
    classes = {s.symbol_class for s in syms}
    assert CLASS_FCU_WALL in classes
    assert CLASS_HBC in classes
    assert all(s.source == "rule" for s in syms)
    assert all(s.confidence > 0.5 for s in syms if s.linked_tag)
