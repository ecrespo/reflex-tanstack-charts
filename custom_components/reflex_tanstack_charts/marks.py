"""Helpers de marcas — las 14 marcas MUST del contrato ChartSpec v1.

REQs: REQ-CH-003 (catálogo de marcas), REQ-CH-011 (serialización),
REQ-CH-012 (validación fail-fast con datos literales; diferida con rx.Var).
Specs: specs/api/component-api-v1.md §2.2 · specs/data-model/chartspec-schema.md §2.2

Los nombres siguen la gramática TanStack en snake_case (Constitución Art. 3):
`lineY` → `line_y`, etc. Las opciones se emiten en camelCase JS.
"""

from __future__ import annotations

from typing import Any

import reflex as rx

from ._serialize import serialize_dataset

_TAG = "[reflex-tanstack-charts]"

#: Catálogo cerrado de curvas (DD-003 / API Spec §2.2). El bridge mapea a d3-shape.
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

#: Canales cuyo valor string referencia SIEMPRE un campo del dataset (Data Model §2.2).
#: `color` es el canal de color dirigido por datos de TanStack; `fill`/`stroke` NO
#: están aquí porque en 0.7.2 son colores CSS literales, nunca nombres de campo.
_FIELD_CHANNELS = {"x", "y", "y1", "y2", "z", "color", "text", "value", "label", "key"}

Mark = dict[str, Any]


def _camel(name: str) -> str:
    head, *rest = name.split("_")
    return head + "".join(part.capitalize() for part in rest)


def _is_var(value: Any) -> bool:
    return isinstance(value, rx.Var)


def _validate_fields(type_: str, data: list[Any], channels: dict[str, Any]) -> None:
    """REQ-CH-012: todo canal-campo debe existir en el primer registro (datos literales)."""
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


# --- Líneas y áreas ----------------------------------------------------------


def line_y(data: Any, *, x: str, y: str, **options: Any) -> Mark:
    """Línea con y dependiente de x (TanStack `lineY`)."""
    return _mark("lineY", data, {"x": x, "y": y, **options})


def line_x(data: Any, *, x: str, y: str, **options: Any) -> Mark:
    """Línea con x dependiente de y (TanStack `lineX`)."""
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
    """Área vertical (TanStack `areaY`): canal `y`, o banda `y1`+`y2`."""
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
    """Área horizontal (TanStack `areaX`): canal `x`, o banda `x1`+`x2`."""
    if x is None and not (x1 and x2):
        raise ValueError(f"{_TAG} area_x requires channel 'x' or both 'x1' and 'x2'")
    return _mark("areaX", data, {"x": x, "x1": x1, "x2": x2, "y": y, **options})


# --- Barras y celdas ---------------------------------------------------------


def bar_y(data: Any, *, x: str, y: str, **options: Any) -> Mark:
    """Barras verticales (TanStack `barY`)."""
    return _mark("barY", data, {"x": x, "y": y, **options})


def bar_x(data: Any, *, x: str, y: str, **options: Any) -> Mark:
    """Barras horizontales (TanStack `barX`)."""
    return _mark("barX", data, {"x": x, "y": y, **options})


def cell(data: Any, *, x: str, y: str, **options: Any) -> Mark:
    """Celdas de heatmap ordinal (TanStack `cell`)."""
    return _mark("cell", data, {"x": x, "y": y, **options})


# --- Puntos ------------------------------------------------------------------


def dot(data: Any, *, x: str, y: str, **options: Any) -> Mark:
    """Puntos/scatter (TanStack `dot`). `r` acepta número o campo."""
    return _mark("dot", data, {"x": x, "y": y, **options})


# --- Reglas y ticks ----------------------------------------------------------


def rule_x(values: Any, **options: Any) -> Mark:
    """Reglas verticales en valores x de referencia (TanStack `ruleX`)."""
    return _mark("ruleX", values, options)


def rule_y(values: Any, **options: Any) -> Mark:
    """Reglas horizontales en valores y de referencia (TanStack `ruleY`)."""
    return _mark("ruleY", values, options)


def tick_x(data: Any, *, x: str, **options: Any) -> Mark:
    """Ticks verticales (TanStack `tickX`)."""
    return _mark("tickX", data, {"x": x, **options})


def tick_y(data: Any, *, y: str, **options: Any) -> Mark:
    """Ticks horizontales (TanStack `tickY`)."""
    return _mark("tickY", data, {"y": y, **options})


# --- Texto -------------------------------------------------------------------


def text(data: Any, *, x: str, y: str, text: str | None = None, **options: Any) -> Mark:
    """Etiquetas de texto (TanStack `text`). Requiere canal `text`."""
    if text is None:
        raise ValueError(f"{_TAG} text mark requires the 'text' channel (field with the label)")
    return _mark("text", data, {"x": x, "y": y, "text": text, **options})


# --- Polar -------------------------------------------------------------------


def pie(data: Any, *, value: str, label: str | None = None, **options: Any) -> Mark:
    """Pie/donut (TanStack `pie`, export de `@tanstack/charts/polar`).

    `inner_radius` > 0 produce un donut.
    """
    return _mark("pie", data, {"value": value, "label": label, **options})
