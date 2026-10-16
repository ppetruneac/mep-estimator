"""Unit tests for Phase 4 length calculations."""

import pytest

from riser_extract.lengths import (
    DEFAULT_COORDINATION_FACTOR,
    DEFAULT_TAIL_M_PER_PIPE,
    DEFAULT_TRAY_WASTE_FACTOR,
    aggregate_by_item,
    apply_tender,
    tender_length_two_pipe,
    tray_length_with_waste,
)
from riser_extract.schema import MeasurementType, Occurrence, Scope


def test_tender_length_two_pipe_default():
    # plan 10 m → (10 * 2 * 1.15) + (1.5 * 2) = 23 + 3 = 26
    assert tender_length_two_pipe(10.0) == pytest.approx(26.0)


def test_tender_length_custom_factors():
    assert tender_length_two_pipe(5.0, coordination_factor=1.0, tail_m_per_pipe=0.0) == 10.0


def test_tender_length_negative_raises():
    with pytest.raises(ValueError):
        tender_length_two_pipe(-1.0)


def test_tray_waste_default():
    assert tray_length_with_waste(100.0) == pytest.approx(115.0)


def test_tray_waste_custom():
    assert tray_length_with_waste(100.0, waste_factor=0.10) == pytest.approx(110.0)


def test_apply_tender_pipe_default():
    occ = Occurrence(
        drawing_number="D1",
        floor_tab_name="Ground",
        scale="1:50",
        annotation="pipe run",
        item_id="MEC-CU-IN",
        unit="m",
        length_m=10.0,
        measurement_type=MeasurementType.SCALED,
        scope=Scope.IN,
    )
    updated = apply_tender(occ)
    assert getattr(updated, "tender_length_m") == pytest.approx(26.0)
    assert "tender conversion" in (updated.notes or "")


def test_apply_tender_pipe_custom():
    occ = Occurrence(
        drawing_number="D1",
        floor_tab_name="Ground",
        scale="1:50",
        annotation="pipe run",
        item_id="MEC-CU-IN",
        unit="m",
        length_m=10.0,
        measurement_type=MeasurementType.SCALED,
        scope=Scope.IN,
    )
    updated = apply_tender(occ, coordination_factor=1.0, tail_m_per_pipe=0.0)
    assert getattr(updated, "tender_length_m") == pytest.approx(20.0)


def test_apply_tender_tray():
    occ = Occurrence(
        drawing_number="D1",
        floor_tab_name="Ground",
        scale="1:50",
        annotation="tray",
        item_id="MEC-TRAY-400",
        unit="m",
        length_m=20.0,
        measurement_type=MeasurementType.SCALED,
        scope=Scope.IN,
    )
    updated = apply_tender(occ)
    assert getattr(updated, "tender_length_m") == pytest.approx(23.0)


def test_apply_tender_tray_custom():
    occ = Occurrence(
        drawing_number="D1",
        floor_tab_name="Ground",
        scale="1:50",
        annotation="tray",
        item_id="MEC-TRAY-400",
        unit="m",
        length_m=20.0,
        measurement_type=MeasurementType.SCALED,
        scope=Scope.IN,
    )
    updated = apply_tender(occ, tray_waste_factor=0.05)
    assert getattr(updated, "tender_length_m") == pytest.approx(21.0)


def test_aggregate_by_item():
    occs = [
        Occurrence(
            drawing_number="D1",
            floor_tab_name="Ground",
            scale="1:50",
            annotation="a",
            item_id="MEC-CU-IN",
            unit="m",
            length_m=10.0,
            count=1,
            measurement_type=MeasurementType.SCALED,
            scope=Scope.IN,
        ),
        Occurrence(
            drawing_number="D1",
            floor_tab_name="Ground",
            scale="1:50",
            annotation="b",
            item_id="MEC-CU-IN",
            unit="m",
            length_m=5.0,
            count=1,
            measurement_type=MeasurementType.GEOMETRY,
            scope=Scope.IN,
        ),
    ]
    processed = [apply_tender(o) for o in occs]
    groups = aggregate_by_item(processed)
    key = ("MEC-CU-IN", "Ground")
    assert key in groups
    g = groups[key]
    assert g["plan_m"] == pytest.approx(15.0)
    assert g["tender_m"] == pytest.approx(26.0 + 14.5)  # 10	o26, 5	o(5*2*1.15 + 3)=14.5
    assert "scaled" in g["measurement_types"]
    assert "geometry" in g["measurement_types"]
