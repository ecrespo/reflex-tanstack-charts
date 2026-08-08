"""Constructor de escalas — catálogo cerrado por nombre.

REQ: REQ-CH-004. Specs: specs/api/component-api-v1.md §2.3 ·
specs/data-model/chartspec-schema.md §2.4.
El bridge resuelve: compactas (`@tanstack/charts-scales`) y avanzadas (`d3-scale`).
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

_TAG = "[reflex-tanstack-charts]"

#: tipo → opciones permitidas
SCALE_TYPES: dict[str, set[str]] = {
    "linear": {"domain", "nice"},
    "band": {"domain", "padding"},
    "point": {"domain", "padding"},
    "ordinal": {"domain", "range"},
    "utc": {"domain", "nice"},
    "time": {"domain", "nice"},
    "log": {"domain", "nice", "base"},
    "sqrt": {"domain", "nice"},
}

ScaleSpec = dict[str, Any]


def _serialize_domain(domain: list[Any]) -> list[Any]:
    out = []
    for v in domain:
        if isinstance(v, (datetime, date)):
            out.append(v.isoformat())
        else:
            out.append(v)
    return out


def scale(
    type: str,  # noqa: A002 - paridad con el contrato JSON
    *,
    domain: list[Any] | None = None,
    nice: bool | None = None,
    padding: float | None = None,
    range: list[str] | None = None,  # noqa: A002
    base: float | None = None,
) -> ScaleSpec:
    """Construye un ScaleSpec serializable. Lanza ValueError ante tipo desconocido."""
    if type not in SCALE_TYPES:
        raise ValueError(
            f"{_TAG} UNKNOWN_SCALE: {type!r}; valid scale types: {sorted(SCALE_TYPES)}"
        )
    allowed = SCALE_TYPES[type]
    provided = {
        "domain": _serialize_domain(domain) if domain is not None else None,
        "nice": nice,
        "padding": padding,
        "range": range,
        "base": base,
    }
    spec: ScaleSpec = {"type": type}
    for key, value in provided.items():
        if value is None:
            continue
        if key not in allowed:
            raise ValueError(
                f"{_TAG} scale {type!r} does not accept option {key!r}; allowed: {sorted(allowed)}"
            )
        spec[key] = value
    if padding is not None and not (0 <= padding <= 1):
        raise ValueError(f"{_TAG} scale padding must be within [0, 1]; got {padding}")
    return spec
