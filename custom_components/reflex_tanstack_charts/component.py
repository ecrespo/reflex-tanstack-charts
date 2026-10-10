"""Reflex component `TanStackChart` + `tanstack_chart` factory.

REQs: REQ-CH-001 (component via local asset), REQ-CH-005 (Var-compatible spec),
REQ-CH-006/007 (tooltip/animate), REQ-CH-008/009/010 (events), REQ-CH-016 (sizing),
REQ-CH-017 (aria warning), REQ-CH-018 (theme), REQ-CH-020 (npm pins), REQ-CH-023 (color).
Specs: specs/api/component-api-v1.md §2.1, §4 · specs/technical/architecture.md §3.2, DD-001/002/005
"""

from __future__ import annotations

import warnings
from typing import Any

import reflex as rx

_TAG = "[reflex-tanstack-charts]"

#: REQ-CH-020 / Constitution Art. 4 — exact versions verified against npm
#: on 2026-10-10 (see Tech Design §10). Since 1.0 the compact scales ship inside
#: `@tanstack/charts` (`@tanstack/charts/scales/*`), so `charts-scales` is gone.
LIB_DEPENDENCIES = [
    "@tanstack/charts@1.1.0",
    "d3-scale@4.0.2",
    "d3-shape@3.2.0",
]

SPEC_VERSION = 1

try:  # pragma: no cover - depends on the compilation context
    _BRIDGE_PATH = rx.asset("TanStackChartBridge.jsx", shared=True)
except Exception:  # outside an app (e.g. isolated tests)
    _BRIDGE_PATH = "/external/reflex_tanstack_charts/TanStackChartBridge.jsx"


class TanStackChart(rx.Component):
    """Wrapper around the local bridge that interprets ChartSpec → defineChart (DD-001)."""

    library = f"$/public{_BRIDGE_PATH}"
    tag = "TanStackChartBridge"

    lib_dependencies: list[str] = LIB_DEPENDENCIES

    #: Full ChartSpec v1 (Data Model §2.1).
    spec: rx.Var[dict[str, Any]]
    #: Fixed height in px (REQ-CH-016).
    height: rx.Var[int]
    #: Responsive alternative to height.
    aspect_ratio: rx.Var[float]
    #: Initial width for SSR when using aspect_ratio.
    initial_width: rx.Var[int]
    #: Accessible label for the chart (REQ-CH-017).
    aria_label: rx.Var[str]
    #: CSS variables --ts-chart-* for theming (REQ-CH-018).
    theme_vars: rx.Var[dict[str, str]]

    #: REQ-CH-008/010 — focused point (sanitized dict) or None.
    on_focus_change: rx.EventHandler[lambda point: [point]]
    #: REQ-CH-009 — selected point (click/Enter).
    on_select: rx.EventHandler[lambda point: [point]]


def _validate_marks(marks: Any) -> list[Any]:
    if isinstance(marks, rx.Var):
        return marks
    if not isinstance(marks, list) or not marks:
        raise ValueError(f"{_TAG} INVALID_MARKS: marks must be a non-empty list of mark dicts")
    for m in marks:
        if isinstance(m, rx.Var):
            continue
        if not isinstance(m, dict) or "type" not in m:
            raise ValueError(
                f"{_TAG} INVALID_MARKS: each mark must be a dict produced by a mark "
                f"helper (line_y, bar_y, ...); got {m!r}"
            )
    return marks


def build_chart_spec(
    *,
    marks: list[Any],
    x: dict[str, Any] | None = None,
    y: dict[str, Any] | None = None,
    color: dict[str, Any] | None = None,
    tooltip: bool = False,
    animate: bool = False,
) -> dict[str, Any]:
    """Build the root ChartSpec v1 (Data Model §2.1)."""
    return {
        "version": SPEC_VERSION,
        "marks": _validate_marks(marks),
        "x": x,
        "y": y,
        "color": color,
        "tooltip": tooltip,
        "animate": animate,
    }


def tanstack_chart(
    *,
    marks: list[Any],
    x: dict[str, Any] | None = None,
    y: dict[str, Any] | None = None,
    color: dict[str, Any] | None = None,
    height: int | rx.Var[int] | None = None,
    aspect_ratio: float | None = None,
    initial_width: int | None = None,
    aria_label: str | None = None,
    tooltip: bool = False,
    animate: bool = False,
    theme: dict[str, str] | None = None,
    on_focus_change: Any = None,
    on_select: Any = None,
    **props: Any,
) -> rx.Component:
    """Create a TanStack Charts chart from a declarative ChartSpec.

    Minimal example::

        tanstack_chart(
            marks=[bar_y(data, x="letter", y="frequency")],
            y=axis(grid=True, label="Frequency"),
            aria_label="Letter frequencies",
        )
    """
    spec = build_chart_spec(marks=marks, x=x, y=y, color=color, tooltip=tooltip, animate=animate)

    # REQ-CH-016: sizing
    if height is not None and aspect_ratio is not None:
        raise ValueError(f"{_TAG} provide either height or aspect_ratio, not both")
    if isinstance(height, int) and height <= 0:
        raise ValueError(f"{_TAG} height must be a positive number of pixels; got {height}")
    if aspect_ratio is not None and aspect_ratio <= 0:
        raise ValueError(f"{_TAG} aspect_ratio must be positive; got {aspect_ratio}")
    if height is None and aspect_ratio is None:
        height = 320

    # REQ-CH-017: accessibility
    if aria_label is None:
        warnings.warn(
            f"{_TAG} no aria_label provided; charts should have an accessible label",
            UserWarning,
            stacklevel=2,
        )

    kwargs: dict[str, Any] = {"spec": spec, **props}
    if height is not None:
        kwargs["height"] = height
    if aspect_ratio is not None:
        kwargs["aspect_ratio"] = aspect_ratio
    if initial_width is not None:
        kwargs["initial_width"] = initial_width
    if aria_label is not None:
        kwargs["aria_label"] = aria_label
    if theme is not None:
        kwargs["theme_vars"] = theme
    if on_focus_change is not None:
        kwargs["on_focus_change"] = on_focus_change
    if on_select is not None:
        kwargs["on_select"] = on_select

    return TanStackChart.create(**kwargs)
