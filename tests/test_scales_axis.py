"""Tests de escalas y ejes.

REQs cubiertos: REQ-CH-004 (catálogo de escalas), formatos declarativos (DD-003).
Specs: specs/api/component-api-v1.md §2.3 · specs/data-model/chartspec-schema.md §2.4-2.5
"""

from datetime import datetime, timezone

import pytest
from reflex_tanstack_charts import axis, scale

UTC = timezone.utc  # compat <3.11 (ver pyproject: ignore UP017)

SUPPORTED = ["linear", "band", "point", "ordinal", "utc", "time", "log", "sqrt"]


def test_req_ch_004_scale_catalog():
    for t in SUPPORTED:
        assert scale(t) == {"type": t}


def test_req_ch_004_unknown_scale_raises():
    with pytest.raises(ValueError, match="UNKNOWN_SCALE"):
        scale("categorical")


def test_req_ch_004_scale_options_serialized():
    s = scale("band", padding=0.18)
    assert s == {"type": "band", "padding": 0.18}
    s = scale("linear", domain=[0, 100], nice=True)
    assert s == {"type": "linear", "domain": [0, 100], "nice": True}
    s = scale("log", base=2)
    assert s == {"type": "log", "base": 2}


def test_req_ch_004_temporal_domain_serialized_iso():
    d0 = datetime(2026, 1, 1, tzinfo=UTC)
    d1 = datetime(2026, 6, 1, tzinfo=UTC)
    s = scale("utc", domain=[d0, d1])
    assert s["domain"] == ["2026-01-01T00:00:00+00:00", "2026-06-01T00:00:00+00:00"]


def test_axis_builds_axis_spec_shape():
    a = axis(
        scale=scale("linear"),
        label="Frequency",
        grid=True,
        nice=True,
        ticks={"count": 5, "format": {"style": "percent", "maximum_fraction_digits": 1}},
    )
    assert a == {
        "scale": {"type": "linear"},
        "grid": True,
        "nice": True,
        "axis": {
            "label": "Frequency",
            "ticks": {"count": 5, "format": {"style": "percent", "maximum_fraction_digits": 1}},
        },
    }


def test_axis_minimal_is_empty_dictless():
    assert axis() == {}
    assert axis(grid=True) == {"grid": True}


def test_axis_rejects_unknown_format_style():
    with pytest.raises(ValueError, match="style"):
        axis(ticks={"format": {"style": "roman-numerals"}})


def test_axis_currency_requires_currency_code():
    with pytest.raises(ValueError, match="currency"):
        axis(ticks={"format": {"style": "currency"}})
    a = axis(ticks={"format": {"style": "currency", "currency": "USD"}})
    assert a["axis"]["ticks"]["format"]["currency"] == "USD"
