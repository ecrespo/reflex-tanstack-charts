"""Synthetic datasets and Python-side transforms for the catalog gallery.

TanStack philosophy (Tech Design §"ownership"): data preparation (bins, moving
averages, stacking, regression, ranks, normalization) lives in the data layer —
here, pure deterministic Python (fixed seed).
"""

from __future__ import annotations

import math
import random
from datetime import date, timedelta

rng = random.Random(7)


def quantize(rows, field, edges, colors, labels=None, out="bucket"):
    """Quantize a numeric field into ordinal buckets to color heatmaps.

    The v1 contract only exposes ordinal color scales (REQ-CH-023): in TanStack
    Charts a string `fill` is a literal CSS color and the data-driven channel is `color`,
    which is painted with the chart's color scale. That is why heatmaps quantize
    here (data layer) and color by bucket.

    `edges` are the exclusive upper cuts; one more color than cuts is required.
    Returns `(rows_with_bucket, domain, range)`, ready for
    `scale("ordinal", domain=…, range=…)`.
    """
    if len(colors) != len(edges) + 1:
        raise ValueError(f"quantize({field!r}): {len(edges)} cuts require {len(edges) + 1} colors")
    if labels is None:
        labels = [f"< {edges[0]:g}"]
        labels += [f"{lo:g}–{hi:g}" for lo, hi in zip(edges, edges[1:], strict=False)]
        labels.append(f"≥ {edges[-1]:g}")

    def bucket_of(value):
        for i, edge in enumerate(edges):
            if value < edge:
                return labels[i]
        return labels[-1]

    return [{**r, out: bucket_of(r[field])} for r in rows], labels, list(colors)


# --- Letters (pie, donut, waffle, sorted bars) --------------------------------

LETTERS = [
    {"letter": "E", "frequency": 0.127},
    {"letter": "T", "frequency": 0.091},
    {"letter": "A", "frequency": 0.082},
    {"letter": "O", "frequency": 0.075},
    {"letter": "I", "frequency": 0.070},
    {"letter": "N", "frequency": 0.067},
    {"letter": "S", "frequency": 0.063},
    {"letter": "H", "frequency": 0.061},
    {"letter": "R", "frequency": 0.060},
    {"letter": "D", "frequency": 0.043},
    {"letter": "L", "frequency": 0.040},
    {"letter": "U", "frequency": 0.028},
]

LETTERS_SORTED = sorted(LETTERS, key=lambda r: -r["frequency"])

PALETTE = [
    "#4f46e5",
    "#0ea5e9",
    "#10b981",
    "#f59e0b",
    "#ef4444",
    "#8b5cf6",
    "#ec4899",
    "#14b8a6",
    "#84cc16",
    "#f97316",
    "#6366f1",
    "#94a3b8",
]


def waffle_cells(rows: list[dict], value: str, label: str, size: int = 10) -> list[dict]:
    """Assign cells of a size×size grid proportionally to the value."""
    total = sum(r[value] for r in rows)
    cells: list[dict] = []
    acc = 0.0
    for r in rows:
        n = round(r[value] / total * size * size)
        for _ in range(n):
            if acc >= size * size:
                break
            cells.append(
                {
                    "col": str(int(acc) % size),
                    "row": str(int(acc) // size),
                    "key": r[label],
                }
            )
            acc += 1
    return cells


WAFFLE = waffle_cells(LETTERS_SORTED[:8], "frequency", "letter")

# --- AAPL-like series (trend, change, distribution, relationship) -------------


def _walk(n: int, start: float, vol: float) -> list[float]:
    vals = [start]
    for _ in range(n - 1):
        vals.append(max(5.0, vals[-1] * (1 + rng.gauss(0.0005, vol))))
    return vals


_D0 = date(2025, 9, 1)
_CLOSES = _walk(180, 64.0, 0.018)
AAPL = [{"day": _D0 + timedelta(days=i), "close": round(v, 2)} for i, v in enumerate(_CLOSES)]

#: line-gaps: seasonal gaps (None breaks the line)
AAPL_GAPS = [
    {"day": r["day"], "close": (None if 40 <= i < 55 or 120 <= i < 130 else r["close"])}
    for i, r in enumerate(AAPL)
]


def moving_average(rows: list[dict], field: str, window: int) -> list[dict]:
    out = []
    vals = [r[field] for r in rows]
    for i, r in enumerate(rows):
        if i + 1 < window:
            continue
        w = vals[i + 1 - window : i + 1]
        out.append({**r, f"ma{window}": round(sum(w) / window, 2)})
    return out


AAPL_MA7 = moving_average(AAPL, "close", 7)
AAPL_MA30 = moving_average(AAPL, "close", 30)


def bollinger(rows: list[dict], field: str, window: int = 20, k: float = 2.0) -> list[dict]:
    vals = [r[field] for r in rows]
    out = []
    for i, r in enumerate(rows):
        if i + 1 < window:
            continue
        w = vals[i + 1 - window : i + 1]
        mu = sum(w) / window
        sd = math.sqrt(sum((v - mu) ** 2 for v in w) / window)
        out.append(
            {**r, "mid": round(mu, 2), "lo": round(mu - k * sd, 2), "hi": round(mu + k * sd, 2)}
        )
    return out


AAPL_BOLLINGER = bollinger(AAPL, "close")

_closes = [r["close"] for r in AAPL]
_imin = _closes.index(min(_closes))
_imax = _closes.index(max(_closes))
AAPL_EXTREMA = [
    {
        "day": AAPL[_imin]["day"],
        "close": AAPL[_imin]["close"],
        "label": f"Min {AAPL[_imin]['close']}",
    },
    {
        "day": AAPL[_imax]["day"],
        "close": AAPL[_imax]["close"],
        "label": f"Max {AAPL[_imax]['close']}",
    },
]

#: lag-1: scatter of close[t-1] vs close[t] (returns)
AAPL_LAG = [
    {
        "prev": round((_closes[i - 1] / _closes[i - 2] - 1) * 100, 2),
        "curr": round((_closes[i] / _closes[i - 1] - 1) * 100, 2),
    }
    for i in range(2, len(_closes))
]

#: histogram of daily returns (%)
_RETURNS = [round((_closes[i] / _closes[i - 1] - 1) * 100, 3) for i in range(1, len(_closes))]


def histogram(values: list[float], nbins: int = 15) -> list[dict]:
    lo, hi = min(values), max(values)
    step = (hi - lo) / nbins or 1
    bins = [0] * nbins
    for v in values:
        bins[min(nbins - 1, int((v - lo) / step))] += 1
    return [
        {"bin": f"{lo + i * step:.1f}", "count": c, "cum": sum(bins[: i + 1])}
        for i, c in enumerate(bins)
    ]


RETURNS_HIST = histogram(_RETURNS)
RETURNS_ECDF = [
    {"value": v, "p": round((i + 1) / len(_RETURNS), 3)} for i, v in enumerate(sorted(_RETURNS))
]

# --- Industries (multi-line, stacked, streamgraph, bump, indexed) -------------

INDUSTRY_NAMES = ["Construction", "Manufacturing", "Services", "Agriculture"]
_BASES = {"Construction": 9.0, "Manufacturing": 6.5, "Services": 4.2, "Agriculture": 7.1}
MONTHS = [date(2024, 1, 1) + timedelta(days=30 * i) for i in range(24)]

INDUSTRIES: list[dict] = []
for name in INDUSTRY_NAMES:
    v = _BASES[name]
    for m in MONTHS:
        v = max(1.0, v + rng.gauss(-0.02 if name == "Services" else 0.0, 0.35))
        INDUSTRIES.append({"month": m, "industry": name, "rate": round(v, 2)})


def by_industry(name: str) -> list[dict]:
    return [r for r in INDUSTRIES if r["industry"] == name]


INDUSTRY_END_LABELS = [{**by_industry(n)[-1], "label": n} for n in INDUSTRY_NAMES]

#: indexed to 100 on the first month
INDUSTRIES_INDEXED = []
for n in INDUSTRY_NAMES:
    rows = by_industry(n)
    base = rows[0]["rate"]
    INDUSTRIES_INDEXED += [{**r, "index": round(r["rate"] / base * 100, 1)} for r in rows]

#: stacked / normalized / streamgraph (painter technique and per-series bands)
STACKED_AREAS: dict[str, list[dict]] = {}
NORMALIZED_AREAS: dict[str, list[dict]] = {}
STREAM_AREAS: dict[str, list[dict]] = {}
for i, m in enumerate(MONTHS):
    vals = {n: by_industry(n)[i]["rate"] for n in INDUSTRY_NAMES}
    total = sum(vals.values())
    cum = 0.0
    base = -total / 2
    run = base
    for n in INDUSTRY_NAMES:
        cum += vals[n]
        STACKED_AREAS.setdefault(n, []).append({"month": m, "cum": round(cum, 2)})
        NORMALIZED_AREAS.setdefault(n, []).append({"month": m, "share": round(cum / total, 4)})
        STREAM_AREAS.setdefault(n, []).append(
            {"month": m, "y1": round(run, 2), "y2": round(run + vals[n], 2)}
        )
        run += vals[n]

#: bump: monthly rank per industry (1 = highest unemployment)
BUMP: list[dict] = []
for i, m in enumerate(MONTHS):
    ordered = sorted(INDUSTRY_NAMES, key=lambda n: -by_industry(n)[i]["rate"])
    for rank, n in enumerate(ordered, start=1):
        BUMP.append({"month": m, "industry": n, "rank": rank})

INDUSTRY_COLORS = {
    "Construction": "#f59e0b",
    "Manufacturing": "#ef4444",
    "Services": "#4f46e5",
    "Agriculture": "#10b981",
}

# --- Penguins (bar, comparison, relationship) ---------------------------------

SPECIES = ["Adelie", "Chinstrap", "Gentoo"]
_MASS = {"Adelie": (3700, 460), "Chinstrap": (3730, 380), "Gentoo": (5070, 500)}

PENGUINS: list[dict] = []
for sp in SPECIES:
    mu, sd = _MASS[sp]
    for _ in range(40):
        mass = rng.gauss(mu, sd)
        flipper = 0.03 * mass + rng.gauss(80, 6)
        PENGUINS.append(
            {
                "species": sp,
                "sex": rng.choice(["MALE", "FEMALE"]),
                "mass": round(mass),
                "flipper": round(flipper, 1),
            }
        )

#: grouped bars: count per species×sex (composite label)
PENGUIN_GROUPS = [
    {
        "group": f"{sp} · {'♂' if sex == 'MALE' else '♀'}",
        "species": sp,
        "sex": sex,
        "count": sum(1 for p in PENGUINS if p["species"] == sp and p["sex"] == sex),
    }
    for sp in SPECIES
    for sex in ["MALE", "FEMALE"]
]

#: reducer bars: mean mass per species
PENGUIN_MEANS = [
    {
        "species": sp,
        "mean_mass": round(
            sum(p["mass"] for p in PENGUINS if p["species"] == sp)
            / sum(1 for p in PENGUINS if p["species"] == sp)
        ),
    }
    for sp in SPECIES
]

#: pyramid: per species, males on the left (negative)
PENGUIN_PYRAMID_M = [
    {"species": sp, "count": -sum(1 for p in PENGUINS if p["species"] == sp and p["sex"] == "MALE")}
    for sp in SPECIES
]
PENGUIN_PYRAMID_F = [
    {
        "species": sp,
        "count": sum(1 for p in PENGUINS if p["species"] == sp and p["sex"] == "FEMALE"),
    }
    for sp in SPECIES
]


def ols(rows: list[dict], xf: str, yf: str) -> list[dict]:
    """Simple linear regression; returns the two endpoints of the fitted line."""
    n = len(rows)
    sx = sum(r[xf] for r in rows)
    sy = sum(r[yf] for r in rows)
    sxx = sum(r[xf] ** 2 for r in rows)
    sxy = sum(r[xf] * r[yf] for r in rows)
    b = (n * sxy - sx * sy) / (n * sxx - sx * sx)
    a = (sy - b * sx) / n
    x0 = min(r[xf] for r in rows)
    x1 = max(r[xf] for r in rows)
    return [{xf: x0, yf: round(a + b * x0, 1)}, {xf: x1, yf: round(a + b * x1, 1)}]


PENGUIN_REGRESSION = ols(PENGUINS, "mass", "flipper")

#: many-point scatter (performance)
MANY_POINTS = [{"x": round(rng.gauss(0, 1), 3), "y": round(rng.gauss(0, 1), 3)} for _ in range(400)]

#: 2D binned heatmap of MANY_POINTS
BINNED_2D: list[dict] = []
_counts: dict[tuple[int, int], int] = {}
for p in MANY_POINTS:
    key = (max(-2, min(2, int(math.floor(p["x"])))), max(-2, min(2, int(math.floor(p["y"])))))
    _counts[key] = _counts.get(key, 0) + 1
for (bx, by), c in sorted(_counts.items()):
    BINNED_2D.append({"xbin": f"{bx}…{bx + 1}", "ybin": f"{by}…{by + 1}", "count": c})

#: quantized sequential ramp of the count (heatmap `color` channel)
BINNED_2D, BINNED_2D_BUCKETS, BINNED_2D_COLORS = quantize(
    BINNED_2D,
    "count",
    [10, 20, 30, 40],
    ["#eff6ff", "#bfdbfe", "#60a5fa", "#2563eb", "#1e3a8a"],
)

# --- Cities (ranking, lollipop, dumbbell, slopegraph) -------------------------

CITIES = [
    {"city": "Mexico City", "v2019": 62, "v2024": 71},
    {"city": "Bogota", "v2019": 55, "v2024": 66},
    {"city": "Buenos Aires", "v2019": 58, "v2024": 54},
    {"city": "Lima", "v2019": 41, "v2024": 52},
    {"city": "Santiago", "v2019": 68, "v2024": 74},
    {"city": "Caracas", "v2019": 30, "v2024": 45},
    {"city": "Montevideo", "v2019": 64, "v2024": 69},
]
CITIES_SORTED = sorted(CITIES, key=lambda r: -r["v2024"])

#: dumbbell/slopegraph in long format
CITIES_LONG = [
    {"city": r["city"], "year": y, "value": r[f"v{y}"]} for r in CITIES for y in ("2019", "2024")
]

# --- SF temperatures (range band, calendar) -----------------------------------

SF_MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
SF_RANGE = [
    {
        "month": m,
        "low": round(8 + 6 * math.sin((i - 2) * math.pi / 6) + rng.gauss(0, 0.6), 1),
        "high": round(15 + 9 * math.sin((i - 2) * math.pi / 6) + rng.gauss(0, 0.8), 1),
    }
    for i, m in enumerate(SF_MONTHS)
]

DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
CALENDAR = [
    {"week": f"W{w + 1:02d}", "day": d, "mm": round(max(0.0, rng.gauss(2.5, 3.0)), 1)}
    for w in range(26)
    for d in DAYS
]

#: quantized rainfall intensity (calendar `color` channel)
CALENDAR, CALENDAR_BUCKETS, CALENDAR_COLORS = quantize(
    CALENDAR,
    "mm",
    [0.1, 2, 5, 8],
    ["#f1f5f9", "#cffafe", "#67e8f9", "#0891b2", "#164e63"],
    labels=["dry", "0–2 mm", "2–5 mm", "5–8 mm", "≥ 8 mm"],
)

# --- Quantile ribbon / error bars ---------------------------------------------

RIBBON = []
for i, m in enumerate(MONTHS):
    mid = 6 + 1.5 * math.sin(i / 3) + rng.gauss(0, 0.15)
    RIBBON.append(
        {
            "month": m,
            "p10": round(mid - 2.2, 2),
            "p90": round(mid + 2.2, 2),
            "p25": round(mid - 1.0, 2),
            "p75": round(mid + 1.0, 2),
            "median": round(mid, 2),
        }
    )

ERRORS = [{"trial": f"T{i + 1}", "mean": round(rng.uniform(4, 9), 2)} for i in range(8)]
for r in ERRORS:
    ci = round(rng.uniform(0.4, 1.3), 2)
    r["lo"] = round(r["mean"] - ci, 2)
    r["hi"] = round(r["mean"] + ci, 2)
ERROR_SEGMENTS = [
    {"trial": r["trial"], "y": v, "seg": r["trial"]} for r in ERRORS for v in (r["lo"], r["hi"])
]

# --- Diverging Likert ----------------------------------------------------------

LIKERT_STATEMENTS = ["Ease of use", "Documentation", "Performance", "Support", "Price"]
LIKERT: list[dict] = []
for s in LIKERT_STATEMENTS:
    sd_, d = rng.randint(2, 12), rng.randint(5, 18)
    n = rng.randint(8, 20)
    a, sa = rng.randint(15, 35), rng.randint(8, 25)
    LIKERT.append({"statement": s, "sd": sd_, "d": d, "n": n, "a": a, "sa": sa})

#: painter per side: left cumulative negative, right positive
LIKERT_LEFT_OUTER = [{"statement": r["statement"], "v": -(r["sd"] + r["d"])} for r in LIKERT]
LIKERT_LEFT_INNER = [{"statement": r["statement"], "v": -r["d"]} for r in LIKERT]
LIKERT_RIGHT_OUTER = [{"statement": r["statement"], "v": r["n"] + r["a"] + r["sa"]} for r in LIKERT]
LIKERT_RIGHT_MID = [{"statement": r["statement"], "v": r["n"] + r["a"]} for r in LIKERT]
LIKERT_RIGHT_INNER = [{"statement": r["statement"], "v": r["n"]} for r in LIKERT]

# --- Parallel coordinates (cars) ------------------------------------------------

_CAR_DIMS = ["Power", "Weight", "Fuel use", "Acceleration"]
PARALLEL: list[dict] = []
for i in range(14):
    kind = "sports" if i % 2 else "family"
    base = {"sports": [0.8, 0.45, 0.75, 0.85], "family": [0.35, 0.7, 0.4, 0.3]}[kind]
    for dim, b in zip(_CAR_DIMS, base, strict=True):
        PARALLEL.append(
            {
                "car": f"car-{i}",
                "kind": kind,
                "dim": dim,
                "value": round(min(1, max(0, b + rng.gauss(0, 0.12))), 3),
            }
        )

# --- Log scatter (npm packages) --------------------------------------------------

LOG_SCATTER = [
    {"size_kb": round(10 ** rng.uniform(0.5, 3.5), 1), "downloads": round(10 ** rng.uniform(2, 7))}
    for _ in range(60)
]

# --- Connected scatter (inflation vs unemployment per year) ----------------------

CONNECTED = []
_u, _f = 6.0, 3.0
for year in range(2016, 2027):
    _u = max(2, _u + rng.gauss(0, 0.7))
    _f = max(0.5, _f + rng.gauss(0.1, 0.6))
    CONNECTED.append({"year": str(year), "unemployment": round(_u, 2), "inflation": round(_f, 2)})

# --- Stacked bars (revenue per product, painter) ---------------------------------

PRODUCTS = ["Core", "Add-ons", "Services"]
PRODUCT_COLORS = ["#4f46e5", "#0ea5e9", "#94a3b8"]
QUARTERS = ["Q1", "Q2", "Q3", "Q4"]
STACKED_BARS: dict[str, list[dict]] = {p: [] for p in PRODUCTS}
for q in QUARTERS:
    vals = [rng.uniform(20, 60), rng.uniform(10, 35), rng.uniform(5, 20)]
    cum = 0.0
    for p, v in zip(PRODUCTS, vals, strict=True):
        cum += v
        STACKED_BARS[p].append({"quarter": q, "cum": round(cum, 1)})

# --- Nested donuts and donut with total ------------------------------------------

NESTED_INNER = [
    {"pkg": "analytics", "size": 42},
    {"pkg": "vis", "size": 33},
    {"pkg": "util", "size": 25},
]
NESTED_OUTER = [
    {"pkg": "cluster", "size": 18},
    {"pkg": "graph", "size": 24},
    {"pkg": "axis", "size": 15},
    {"pkg": "legend", "size": 18},
    {"pkg": "arrays", "size": 13},
    {"pkg": "math", "size": 12},
]
DONUT_TOTAL = sum(r["frequency"] for r in LETTERS_SORTED[:6])
