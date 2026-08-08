"""Serialización Python → JSON del ChartSpec.

Implementa REQ-CH-011: fechas a ISO-8601 + `temporal_fields`; rechazo de NaN/Inf;
frontera exclusivamente JSON-serializable (Constitución Art. 2).
Spec: specs/data-model/chartspec-schema.md §3
"""

from __future__ import annotations

import math
from datetime import date, datetime
from typing import Any

_TAG = "[reflex-tanstack-charts]"


def _serialize_value(field: str, value: Any, temporal: set[str]) -> Any:
    """Serializa un valor escalar de un registro. Lanza ValueError si no es JSON-safe."""
    if isinstance(value, datetime):
        temporal.add(field)
        return value.isoformat()
    if isinstance(value, date):
        temporal.add(field)
        return value.isoformat()
    if isinstance(value, bool) or value is None or isinstance(value, (str, int)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError(
                f"{_TAG} field {field!r} has value {value!r}, "
                "which is not JSON-serializable (NaN/Infinity)"
            )
        return value
    raise ValueError(
        f"{_TAG} field {field!r} has type {type(value).__name__}, "
        "which is not JSON-serializable in a ChartSpec dataset"
    )


def serialize_dataset(data: list[Any]) -> tuple[list[Any], list[str]]:
    """Serializa un dataset (list[dict] homogéneo o list[num] para rules).

    Retorna (data_serializada, temporal_fields). No muta el original.
    """
    temporal: set[str] = set()
    if not data:
        return [], []
    if all(isinstance(row, (int, float)) and not isinstance(row, bool) for row in data):
        for i, v in enumerate(data):
            if isinstance(v, float) and not math.isfinite(v):
                raise ValueError(
                    f"{_TAG} reference value at index {i} is not JSON-serializable (NaN/Infinity)"
                )
        return list(data), []
    out: list[dict[str, Any]] = []
    for row in data:
        if not isinstance(row, dict):
            raise ValueError(
                f"{_TAG} dataset rows must be dicts (or numbers for rules); got "
                f"{type(row).__name__}"
            )
        out.append({k: _serialize_value(k, v, temporal) for k, v in row.items()})
    return out, sorted(temporal)
