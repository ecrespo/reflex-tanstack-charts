"""Tests de helpers de marcas.

REQs cubiertos: REQ-CH-003 (marcas núcleo), REQ-CH-011 (serialización de fechas,
frontera JSON), REQ-CH-012 (fail-fast ante campo inexistente).
Specs: specs/prd/reflex-tanstack-charts.md · specs/api/component-api-v1.md §2.2
"""

from datetime import date, datetime, timezone

import pytest
import reflex as rx
from reflex_tanstack_charts import (
    area_y,
    bar_y,
    dot,
    line_y,
    pie,
    rule_y,
    text,
)

UTC = timezone.utc  # compat <3.11 (ver pyproject: ignore UP017)

DATA = [
    {"letter": "E", "frequency": 0.127},
    {"letter": "T", "frequency": 0.091},
]


def test_req_ch_003_bar_y_basic_shape():
    m = bar_y(DATA, x="letter", y="frequency")
    assert m == {
        "type": "barY",
        "data": DATA,
        "temporal_fields": [],
        "options": {"x": "letter", "y": "frequency"},
    }


def test_req_ch_003_snake_case_channels_become_camel():
    m = line_y(DATA, x="letter", y="frequency", stroke_width=2, stroke_dasharray="4 4")
    assert m["options"]["strokeWidth"] == 2
    assert m["options"]["strokeDasharray"] == "4 4"
    assert "stroke_width" not in m["options"]


def test_req_ch_003_none_channels_are_omitted():
    m = line_y(DATA, x="letter", y="frequency", stroke=None, z=None)
    assert "stroke" not in m["options"]
    assert "z" not in m["options"]


def test_req_ch_003_curve_catalog_accepts_known_names():
    m = line_y(DATA, x="letter", y="frequency", curve="monotone-x")
    assert m["options"]["curve"] == "monotone-x"


def test_req_ch_003_curve_catalog_rejects_unknown_names():
    with pytest.raises(ValueError, match="curve"):
        line_y(DATA, x="letter", y="frequency", curve="wiggly")


def test_req_ch_003_rule_y_accepts_reference_values():
    m = rule_y([70], stroke="red", stroke_dasharray="7 7")
    assert m["type"] == "ruleY"
    assert m["data"] == [70]
    assert m["options"]["stroke"] == "red"


def test_req_ch_003_area_y_requires_y_or_band():
    with pytest.raises(ValueError, match="y"):
        area_y(DATA, x="letter")
    band = [{"x": 1, "lo": 0.1, "hi": 0.9}]
    m = area_y(band, x="x", y1="lo", y2="hi")
    assert m["options"] == {"x": "x", "y1": "lo", "y2": "hi"}


def test_req_ch_003_text_requires_text_channel():
    with pytest.raises(ValueError, match="text"):
        text(DATA, x="letter", y="frequency")
    m = text(DATA, x="letter", y="frequency", text="letter")
    assert m["options"]["text"] == "letter"


def test_req_ch_003_pie_camel_cases_radii():
    m = pie(DATA, value="frequency", label="letter", inner_radius=60, pad_angle=0.02)
    assert m["type"] == "pie"
    assert m["options"]["innerRadius"] == 60
    assert m["options"]["padAngle"] == 0.02
    assert m["options"]["value"] == "frequency"


def test_req_ch_012_unknown_field_raises():
    with pytest.raises(ValueError, match="UNKNOWN_FIELD"):
        bar_y(DATA, x="letra", y="frequency")


def test_req_ch_012_unknown_optional_field_channel_raises():
    with pytest.raises(ValueError, match="UNKNOWN_FIELD"):
        dot(DATA, x="letter", y="frequency", z="segmento")


def test_req_ch_012_var_data_defers_validation():
    v = rx.Var.create([{"x": 1, "y": 2}])
    m = bar_y(v, x="whatever", y="anything")  # no debe lanzar (validación diferida)
    assert m["options"]["x"] == "whatever"


def test_req_ch_011_datetime_serialized_iso_and_marked_temporal():
    data = [
        {"day": datetime(2026, 3, 1, tzinfo=UTC), "v": 1.5},
        {"day": datetime(2026, 3, 2, tzinfo=UTC), "v": 2.5},
    ]
    m = line_y(data, x="day", y="v")
    assert m["temporal_fields"] == ["day"]
    assert m["data"][0]["day"] == "2026-03-01T00:00:00+00:00"
    assert isinstance(m["data"][1]["day"], str)


def test_req_ch_011_date_serialized_iso():
    data = [{"day": date(2026, 3, 1), "v": 1}]
    m = bar_y(data, x="day", y="v")
    assert m["data"][0]["day"] == "2026-03-01"
    assert m["temporal_fields"] == ["day"]


def test_req_ch_011_nan_and_inf_rejected():
    with pytest.raises(ValueError, match="serializable"):
        bar_y([{"x": "a", "y": float("nan")}], x="x", y="y")
    with pytest.raises(ValueError, match="serializable"):
        bar_y([{"x": "a", "y": float("inf")}], x="x", y="y")


def test_req_ch_011_original_data_not_mutated():
    data = [{"day": datetime(2026, 3, 1, tzinfo=UTC), "v": 1}]
    line_y(data, x="day", y="v")
    assert isinstance(data[0]["day"], datetime)
