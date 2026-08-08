"""reflex-tanstack-charts — Reflex custom component wrapping TanStack Charts.

API pública (API Spec §1): componente, 14 marcas, escalas y ejes.
"""

from .axis import axis
from .component import (
    LIB_DEPENDENCIES,
    SPEC_VERSION,
    TanStackChart,
    build_chart_spec,
    tanstack_chart,
)
from .marks import (
    CURVES,
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
from .scales import SCALE_TYPES, scale

__version__ = "0.1.0"

__all__ = [
    "CURVES",
    "LIB_DEPENDENCIES",
    "SCALE_TYPES",
    "SPEC_VERSION",
    "TanStackChart",
    "area_x",
    "area_y",
    "axis",
    "bar_x",
    "bar_y",
    "build_chart_spec",
    "cell",
    "dot",
    "line_x",
    "line_y",
    "pie",
    "rule_x",
    "rule_y",
    "scale",
    "tanstack_chart",
    "text",
    "tick_x",
    "tick_y",
]
