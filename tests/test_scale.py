from riser_extract.page import PageInfo
from riser_extract.scale import m_per_pt_from_ratio, parse_drawing_number, parse_floor_tab, resolve_scale


def test_m_per_pt_1_50():
    assert abs(m_per_pt_from_ratio(50) - 0.01764) < 1e-6


def test_resolve_scale_from_title():
    info = PageInfo(
        path=__import__("pathlib").Path("x.pdf"),
        page_index=0,
        width_pt=1684,
        height_pt=2384,
        rotation=270,
        display_width=2384,
        display_height=1684,
        measure_m_per_cm=0.49949,
    )
    scale = resolve_scale(info, "Heating and Cooling Layout 1:50 @ A1 DO NOT SCALE")
    assert scale.ratio == 50
    assert "1:50" in scale.scale_str
    assert abs(scale.m_per_pt - (0.49949 / (72 / 2.54))) < 1e-9


def test_parse_drawing_and_floor_from_filename():
    fn = "25280-SEN-02-DR-M-5602 - Second Floor - Heating and Cooling Layout.pdf"
    assert parse_drawing_number("", fn) == "25280-SEN-02-DR-M-5602"
    assert parse_floor_tab("", fn) == "Second Floor"
