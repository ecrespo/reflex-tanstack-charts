"""Mark helpers — the 14 MUST marks of the ChartSpec v1 contract.

REQs: REQ-CH-003 (mark catalog), REQ-CH-011 (serialization),
REQ-CH-012 (fail-fast validation with literal data; deferred with rx.Var).
Specs: specs/api/component-api-v1.md §2.2 · specs/data-model/chartspec-schema.md §2.2

Names follow the TanStack grammar in snake_case (Constitution Art. 3):
`lineY` → `line_y`, etc. Options are emitted in JS camelCase.
"""

from __future__ import annotations

from typing import Any

import reflex as rx

from ._serialize import serialize_dataset

_TAG = "[reflex-tanstack-charts]"

#: Closed curve catalog (DD-003 / API Spec §2.2). The bridge maps them to d3-shape.
CURVES = {
    "linear",
    "monotone-x",
    "natural",
    "step",
    "step-after",
    "step-before",
    "basis",
    "catmull-rom",
}

#: Channels whose string value ALWAYS references a dataset field (Data Model §2.2).
#: `color` is TanStack's data-driven color channel; `fill`/`stroke` are NOT listed
#: here because in 0.7.2 they are literal CSS colors, never field names.
_FIELD_CHANNELS = {"x", "y", "y1", "y2", "z", "color", "text", "value", "label", "key"}

Mark = dict[str, Any]


def _camel(name: str) -> str:
    head, *rest = name.split("_")
    return head + "".join(part.capitalize() for part in rest)


def _is_var(value: Any) -> bool:
    return isinstance(value, rx.Var)


def _validate_fields(type_: str, data: list[Any], channels: dict[str, Any]) -> None:
    """REQ-CH-012: every field-channel must exist in the first record (literal data)."""
    if not data or not isinstance(data[0], dict):
        return
    fields = set(data[0])
    for channel, value in channels.items():
        if value is None or not isinstance(value, str):
            continue
        if channel in _FIELD_CHANNELS or (channel == "r" and isinstance(value, str)):
            if value not in fields:
                raise ValueError(
                    f"{_TAG} UNKNOWN_FIELD: channel {channel}={value!r} of mark "
                    f"{type_!r} not found in dataset fields {sorted(fields)}"
                )


def _mark(type_: str, data: Any, channels: dict[str, Any]) -> Mark:
    channels = {k: v for k, v in channels.items() if v is not None}
    curve = channels.get("curve")
    if curve is not None and curve not in CURVES:
        raise ValueError(
            f"{_TAG} invalid curve {curve!r} for mark {type_!r}; valid curves: {sorted(CURVES)}"
        )
    if _is_var(data):
        serialized, temporal = data, []
    else:
        if not isinstance(data, list):
            raise ValueError(f"{_TAG} mark {type_!r}: data must be a list or rx.Var")
        _validate_fields(type_, data, channels)
        serialized, temporal = serialize_dataset(data)
    return {
        "type": type_,
        "data": serialized,
        "temporal_fields": temporal,
        "options": {_camel(k): v for k, v in channels.items()},
    }


# --- Lines and areas ---------------------------------------------------------


def line_y(data: Any, *, x: str, y: str, **options: Any) -> Mark:
    """Line with y depending on x (TanStack `lineY`)."""
    return _mark("lineY", data, {"x": x, "y": y, **options})


def line_x(data: Any, *, x: str, y: str, **options: Any) -> Mark:
    """Line with x depending on y (TanStack `lineX`)."""
    return _mark("lineX", data, {"x": x, "y": y, **options})


def area_y(
    data: Any,
    *,
    x: str,
    y: str | None = None,
    y1: str | None = None,
    y2: str | None = None,
    **options: Any,
) -> Mark:
    """Vertical area (TanStack `areaY`): channel `y`, or band `y1`+`y2`."""
    if y is None and not (y1 and y2):
        raise ValueError(f"{_TAG} area_y requires channel 'y' or both 'y1' and 'y2'")
    return _mark("areaY", data, {"x": x, "y": y, "y1": y1, "y2": y2, **options})


def area_x(
    data: Any,
    *,
    y: str,
    x: str | None = None,
    x1: str | None = None,
    x2: str | None = None,
    **options: Any,
) -> Mark:
    """Horizontal area (TanStack `areaX`): channel `x`, or band `x1`+`x2`."""
    if x is None and not (x1 and x2):
        raise ValueError(f"{_TAG} area_x requires channel 'x' or both 'x1' and 'x2'")
    return _mark("areaX", data, {"x": x, "x1": x1, "x2": x2, "y": y, **options})


# --- Bars and cells ----------------------------------------------------------


def bar_y(data: Any, *, x: str, y: str, **options: Any) -> Mark:
    """Vertical bars (TanStack `barY`)."""
    return _mark("barY", data, {"x": x, "y": y, **options})


def bar_x(data: Any, *, x: str, y: str, **options: Any) -> Mark:
    """Horizontal bars (TanStack `barX`)."""
    return _mark("barX", data, {"x": x, "y": y, **options})


def cell(data: Any, *, x: str, y: str, **options: Any) -> Mark:
    """Ordinal heatmap cells (TanStack `cell`)."""
    return _mark("cell", data, {"x": x, "y": y, **options})


# --- Points ------------------------------------------------------------------


def dot(data: Any, *, x: str, y: str, **options: Any) -> Mark:
    """Dots/scatter (TanStack `dot`). `r` accepts a number or a field."""
    return _mark("dot", data, {"x": x, "y": y, **options})


# --- Rules and ticks ---------------------------------------------------------


def rule_x(values: Any, **options: Any) -> Mark:
    """Vertical rules at reference x values (TanStack `ruleX`)."""
    return _mark("ruleX", values, options)


def rule_y(values: Any, **options: Any) -> Mark:
    """Horizontal rules at reference y values (TanStack `ruleY`)."""
    return _mark("ruleY", values, options)


def tick_x(data: Any, *, x: str, **options: Any) -> Mark:
    """Vertical ticks (TanStack `tickX`)."""
    return _mark("tickX", data, {"x": x, **options})


def tick_y(data: Any, *, y: str, **options: Any) -> Mark:
    """Horizontal ticks (TanStack `tickY`)."""
    return _mark("tickY", data, {"y": y, **options})


# --- Text --------------------------------------------------------------------


def text(data: Any, *, x: str, y: str, text: str | None = None, **options: Any) -> Mark:
    """Text labels (TanStack `text`). Requires the `text` channel."""
    if text is None:
        raise ValueError(f"{_TAG} text mark requires the 'text' channel (field with the label)")
    return _mark("text", data, {"x": x, "y": y, "text": text, **options})


# --- Polar -------------------------------------------------------------------


def pie(data: Any, *, value: str, label: str | None = None, **options: Any) -> Mark:
    """Pie/donut (TanStack `pie`, exported from `@tanstack/charts/polar`).

    `inner_radius` > 0 produces a donut.
    """
    return _mark("pie", data, {"value": value, "label": label, **options})
