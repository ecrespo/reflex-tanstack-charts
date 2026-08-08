"""Axis builder with declarative formats (DD-003).

REQ: REQ-CH-004 (axis config) — formats go through Intl in the bridge, never functions.
Specs: specs/api/component-api-v1.md §2.3 · specs/data-model/chartspec-schema.md §2.3/2.5
"""

from __future__ import annotations

from typing import Any

from .scales import ScaleSpec

_TAG = "[reflex-tanstack-charts]"

_NUMBER_STYLES = {"decimal", "percent", "currency", "compact"}
_TICKS_KEYS = {"count", "format"}

AxisSpec = dict[str, Any]


def _validate_format(fmt: dict[str, Any]) -> None:
    style = fmt.get("style")
    if style is not None:
        if style not in _NUMBER_STYLES:
            raise ValueError(
                f"{_TAG} unknown format style {style!r}; valid styles: {sorted(_NUMBER_STYLES)}"
            )
        if style == "currency" and "currency" not in fmt:
            raise ValueError(f"{_TAG} format style 'currency' requires a 'currency' ISO-4217 code")


def axis(
    *,
    scale: ScaleSpec | None = None,
    label: str | None = None,
    grid: bool | None = None,
    nice: bool | None = None,
    ticks: dict[str, Any] | None = None,
) -> AxisSpec:
    """Build a serializable AxisSpec (shape from Data Model §2.3)."""
    if ticks is not None:
        unknown = set(ticks) - _TICKS_KEYS
        if unknown:
            raise ValueError(
                f"{_TAG} unknown ticks options {sorted(unknown)}; allowed: {sorted(_TICKS_KEYS)}"
            )
        fmt = ticks.get("format")
        if fmt is not None:
            _validate_format(fmt)
    spec: AxisSpec = {}
    if scale is not None:
        spec["scale"] = scale
    if grid is not None:
        spec["grid"] = grid
    if nice is not None:
        spec["nice"] = nice
    inner: dict[str, Any] = {}
    if label is not None:
        inner["label"] = label
    if ticks is not None:
        inner["ticks"] = ticks
    if inner:
        spec["axis"] = inner
    return spec
