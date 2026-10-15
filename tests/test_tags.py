from riser_extract.tags import TagHit, dedupe_tags, find_tags
from riser_extract.text import Word


def test_dedupe_nearby_identical_tags():
    hits = [
        TagHit("fcu", "FCU.02.01", "FCU.02.01", 10, 10, 20, 20),
        TagHit("fcu", "FCU.02.01", "FCU.02.01", 12, 11, 22, 21),
        TagHit("fcu", "FCU.02.02", "FCU.02.02", 200, 200, 210, 210),
    ]
    out = dedupe_tags(hits, radius_pt=42)
    assert len(out) == 2
    assert {h.normalised for h in out} == {"FCU.02.01", "FCU.02.02"}


def test_find_fcu_and_hb_tags():
    words = [
        Word("FCU.02.01", 0, 0, 40, 10),
        Word("HB:02:01", 100, 0, 140, 10),
        Word("HB:02:02", 200, 0, 240, 10),
    ]
    tags = find_tags(words)
    kinds = {t.kind for t in tags}
    assert "fcu" in kinds and "hbc" in kinds
    norms = {t.normalised for t in tags}
    assert "FCU.02.01" in norms
    assert "HB:02:01" in norms
