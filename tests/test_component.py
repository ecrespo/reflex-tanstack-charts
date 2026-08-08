"""Tests for the TanStackChart component and the root ChartSpec.

REQs covered: REQ-CH-001 (component compiles), REQ-CH-005 (spec accepts Vars),
REQ-CH-006/007 (tooltip/animate), REQ-CH-008/009 (triggers), REQ-CH-016 (sizing),
REQ-CH-017 (aria warning), REQ-CH-018 (theme), REQ-CH-020 (npm pins),
REQ-CH-023 (ordinal color).
Specs: specs/api/component-api-v1.md §2.1, §4 · specs/technical/architecture.md
"""

import warnings

import pytest
import reflex as rx
from reflex_tanstack_charts import (
    axis,
    bar_y,
    build_chart_spec,
    scale,
    tanstack_chart,
)

DATA = [{"letter": "E", "frequency": 0.127}]
MARKS = [bar_y(DATA, x="letter", y="frequency")]


class _S(rx.State):
    picked: str = ""

    @rx.event
    def on_pick(self, point: dict | None):
        self.picked = str(point)


# --- REQ-CH-001 -------------------------------------------------------------


def test_req_ch_001_component_compiles():
    comp = tanstack_chart(marks=MARKS, aria_label="test chart")
    assert isinstance(comp, rx.Component)
    rendered = str(comp.render())
    assert "TanStackChartBridge" in rendered


def test_req_ch_001_library_is_local_public_asset():
    comp = tanstack_chart(marks=MARKS, aria_label="t")
    assert "$/public" in str(comp.library)
    assert "TanStackChartBridge" in str(comp.library)


def test_req_ch_001_invalid_marks_raises():
    with pytest.raises(ValueError, match="INVALID_MARKS"):
        tanstack_chart(marks=[], aria_label="t")
    with pytest.raises(ValueError, match="INVALID_MARKS"):
        tanstack_chart(marks=["not-a-mark"], aria_label="t")


# --- Root ChartSpec (REQ-CH-006/007/023, version) ---------------------------


def test_spec_version_is_1():
    spec = build_chart_spec(marks=MARKS)
    assert spec["version"] == 1


def test_req_ch_006_tooltip_flag():
    assert build_chart_spec(marks=MARKS, tooltip=True)["tooltip"] is True
    assert build_chart_spec(marks=MARKS)["tooltip"] is False


def test_req_ch_007_animate_flag():
    assert build_chart_spec(marks=MARKS, animate=True)["animate"] is True


def test_req_ch_023_color_ordinal_scale():
    spec = build_chart_spec(
        marks=MARKS,
        color={"scale": scale("ordinal", domain=["A", "B"], range=["#111", "#222"])},
    )
    assert spec["color"]["scale"]["type"] == "ordinal"
    assert spec["color"]["scale"]["range"] == ["#111", "#222"]


def test_axes_embedded_in_spec():
    spec = build_chart_spec(
        marks=MARKS,
        x=axis(scale=scale("band", padding=0.18)),
        y=axis(grid=True, label="Frequency"),
    )
    assert spec["x"]["scale"] == {"type": "band", "padding": 0.18}
    assert spec["y"]["grid"] is True


# --- REQ-CH-016: sizing ------------------------------------------------------


def test_req_ch_016_default_height():
    comp = tanstack_chart(marks=MARKS, aria_label="t")
    assert "320" in str(comp.render())


def test_req_ch_016_sizing_validation():
    with pytest.raises(ValueError, match="height"):
        tanstack_chart(marks=MARKS, aria_label="t", height=-10)
    with pytest.raises(ValueError, match="aspect_ratio"):
        tanstack_chart(marks=MARKS, aria_label="t", height=400, aspect_ratio=1.5)


def test_req_ch_016_aspect_ratio_mode():
    comp = tanstack_chart(marks=MARKS, aria_label="t", aspect_ratio=16 / 9, initial_width=720)
    rendered = str(comp.render())
    assert "aspectRatio" in rendered
    assert "initialWidth" in rendered


# --- REQ-CH-017: aria --------------------------------------------------------


def test_req_ch_017_missing_aria_label_warns():
    with pytest.warns(UserWarning, match="aria_label"):
        tanstack_chart(marks=MARKS)


def test_req_ch_017_aria_label_no_warning():
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        tanstack_chart(marks=MARKS, aria_label="ok")


# --- REQ-CH-018: theme -------------------------------------------------------


def test_req_ch_018_theme_vars_prop():
    comp = tanstack_chart(marks=MARKS, aria_label="t", theme={"--ts-chart-accent": "#f00"})
    assert "themeVars" in str(comp.render())


# --- REQ-CH-008/009: triggers -----------------------------------------------


def test_req_ch_008_focus_trigger_declared():
    comp = tanstack_chart(marks=MARKS, aria_label="t", on_focus_change=_S.on_pick)
    assert "onFocusChange" in str(comp.render())


def test_req_ch_009_select_trigger_declared():
    comp = tanstack_chart(marks=MARKS, aria_label="t", on_select=_S.on_pick)
    assert "onSelect" in str(comp.render())


# --- REQ-CH-005: spec accepts Vars ------------------------------------------


def test_req_ch_005_spec_is_var_compatible():
    var_data = rx.Var.create([{"x": 1, "y": 2}])
    comp = tanstack_chart(marks=[bar_y(var_data, x="x", y="y")], aria_label="t")
    assert isinstance(comp, rx.Component)


# --- REQ-CH-020: npm pins ----------------------------------------------------


def test_req_ch_020_pinned_lib_dependencies():
    # Amendment 2026-08-07 (Delta bridge-dom-host): the bridge mounts with the
    # vanilla DOM host of @tanstack/charts; the React adapter
    # (@tanstack/react-charts) is no longer a dependency (this avoids the double
    # React problem in vite dev).
    comp = tanstack_chart(marks=MARKS, aria_label="t")
    deps = set(comp.lib_dependencies)
    assert deps == {
        "@tanstack/charts@0.7.2",
        "@tanstack/charts-scales@0.7.2",
        "d3-scale@4.0.2",
        "d3-shape@3.2.0",
    }
