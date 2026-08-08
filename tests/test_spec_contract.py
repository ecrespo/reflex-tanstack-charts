"""Snapshots of the ChartSpec v1 contract — the 14 MUST marks.

REQs covered: REQ-CH-002/REQ-CH-003 (each mark produces the exact MarkSpec the
bridge interprets). Any change here is a contract change → Data Model §5.
Specs: specs/data-model/chartspec-schema.md §2.2
"""

from reflex_tanstack_charts import (
    area_x,
    area_y,
    bar_x,
    bar_y,
    cell,
    dot,
    line_x,
    line_y,
    pie,
    rule_x,
    rule_y,
    text,
    tick_x,
    tick_y,
)

XY = [{"x": 1, "y": 2}, {"x": 3, "y": 4}]
CAT = [{"cat": "A", "val": 10}, {"cat": "B", "val": 20}]
GRID = [{"col": "a", "row": "b", "heat": 5}]


def test_req_ch_003_snapshot_line_y():
    assert line_y(XY, x="x", y="y", curve="monotone-x", points=True) == {
        "type": "lineY",
        "data": XY,
        "temporal_fields": [],
        "options": {"x": "x", "y": "y", "curve": "monotone-x", "points": True},
    }


def test_req_ch_003_snapshot_line_x():
    assert line_x(XY, x="x", y="y") == {
        "type": "lineX",
        "data": XY,
        "temporal_fields": [],
        "options": {"x": "x", "y": "y"},
    }


def test_req_ch_003_snapshot_area_y():
    assert area_y(XY, x="x", y="y", fill_opacity=0.2) == {
        "type": "areaY",
        "data": XY,
        "temporal_fields": [],
        "options": {"x": "x", "y": "y", "fillOpacity": 0.2},
    }


def test_req_ch_003_snapshot_area_x():
    assert area_x(XY, y="y", x="x") == {
        "type": "areaX",
        "data": XY,
        "temporal_fields": [],
        "options": {"x": "x", "y": "y"},
    }


def test_req_ch_003_snapshot_bar_y():
    assert bar_y(CAT, x="cat", y="val", fill="#4f46e5") == {
        "type": "barY",
        "data": CAT,
        "temporal_fields": [],
        "options": {"x": "cat", "y": "val", "fill": "#4f46e5"},
    }


def test_req_ch_003_snapshot_bar_x():
    assert bar_x(CAT, y="cat", x="val") == {
        "type": "barX",
        "data": CAT,
        "temporal_fields": [],
        "options": {"x": "val", "y": "cat"},
    }


def test_req_ch_003_snapshot_dot():
    assert dot(XY, x="x", y="y", r=4, id="scatter") == {
        "type": "dot",
        "data": XY,
        "temporal_fields": [],
        "options": {"x": "x", "y": "y", "r": 4, "id": "scatter"},
    }


def test_req_ch_003_snapshot_rule_x():
    assert rule_x([0], stroke_opacity=0.5) == {
        "type": "ruleX",
        "data": [0],
        "temporal_fields": [],
        "options": {"strokeOpacity": 0.5},
    }


def test_req_ch_003_snapshot_rule_y():
    assert rule_y([70, 80]) == {
        "type": "ruleY",
        "data": [70, 80],
        "temporal_fields": [],
        "options": {},
    }


def test_req_ch_003_snapshot_text():
    assert text(CAT, x="cat", y="val", text="cat", dy=-10, font_size=12) == {
        "type": "text",
        "data": CAT,
        "temporal_fields": [],
        "options": {"x": "cat", "y": "val", "text": "cat", "dy": -10, "fontSize": 12},
    }


def test_req_ch_003_snapshot_tick_x():
    assert tick_x(XY, x="x") == {
        "type": "tickX",
        "data": XY,
        "temporal_fields": [],
        "options": {"x": "x"},
    }


def test_req_ch_003_snapshot_tick_y():
    assert tick_y(XY, y="y", stroke="gray") == {
        "type": "tickY",
        "data": XY,
        "temporal_fields": [],
        "options": {"y": "y", "stroke": "gray"},
    }


def test_req_ch_003_snapshot_cell():
    assert cell(GRID, x="col", y="row", fill="heat", inset=1) == {
        "type": "cell",
        "data": GRID,
        "temporal_fields": [],
        "options": {"x": "col", "y": "row", "fill": "heat", "inset": 1},
    }


def test_req_ch_003_snapshot_pie():
    assert pie(CAT, value="val", label="cat", inner_radius=50) == {
        "type": "pie",
        "data": CAT,
        "temporal_fields": [],
        "options": {"value": "val", "label": "cat", "innerRadius": 50},
    }
