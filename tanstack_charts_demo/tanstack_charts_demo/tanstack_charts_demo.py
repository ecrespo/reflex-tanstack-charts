"""reflex-tanstack-charts gallery based on https://tanstack.com/charts/catalog.

Reproduces, with the v1 contract grammar (14 marks + scales + color + tooltip
+ events), every catalog example that is feasible without advanced marks.
Each card cites the id of the original example. The data and transforms (bins,
stacking, moving averages, regression, ranks…) live in `_data.py` (pure Python),
following TanStack's split of responsibilities.

Catalog examples that require marks outside the v1 contract (treemap, sankey,
geo, violin, box, radar, brush/zoom, motion…) are listed at the end as out of
scope (PRD §5.2 → v0.2+).
"""

import random
from typing import Any

import reflex as rx
from reflex_tanstack_charts import (
    area_x,
    area_y,
    axis,
    bar_x,
    bar_y,
    cell,
    dot,
    line_x,
    line_y,
    pie,
    rule_x,
    rule_y,
    scale,
    tanstack_chart,
    text,
    tick_x,
    tick_y,
)

from . import _data as D

# --- State (reactivity and events) --------------------------------------------


class ChartsState(rx.State):
    """Demo state: reactive data and selected point."""

    live_data: list[dict[str, Any]] = [
        {"cat": "A", "val": 30},
        {"cat": "B", "val": 55},
        {"cat": "C", "val": 42},
        {"cat": "D", "val": 68},
    ]
    focused: str = "—"
    selected: str = "—"

    @rx.event
    def randomize(self):
        """REQ-CH-005: mutating the Var re-renders with a transition."""
        self.live_data = [{"cat": c, "val": random.randint(10, 90)} for c in ["A", "B", "C", "D"]]

    @rx.event
    def on_focus(self, point: dict | None):
        self.focused = "no focus" if point is None else str(point.get("datum"))

    @rx.event
    def on_select(self, point: dict | None):
        if point is not None:
            self.selected = str(point.get("datum"))


# --- Layout ---------------------------------------------------------------------


def card(title: str, catalog_id: str, category: str, description: str, *children):
    return rx.card(
        rx.vstack(
            rx.heading(title, size="4"),
            rx.hstack(
                rx.badge(category, variant="soft"),
                rx.badge(f"catalog: {catalog_id}", variant="outline", color_scheme="gray"),
                rx.text(description, size="2", color_scheme="gray"),
                align="center",
                spacing="2",
                wrap="wrap",
            ),
            *children,
            spacing="3",
            width="100%",
        ),
        width="100%",
    )


def category_heading(name: str) -> rx.Component:
    return rx.heading(name, size="6", margin_top="0.8em")


def grid_section(items: list[rx.Component]) -> list[rx.Component]:
    """Full-width heading + its cards in a 3-column grid.

    Each `*_section()` returns `[category_heading, card, card, …]`; only the
    cards go into the grid. It drops to 2 and 1 columns on narrow screens so the
    charts do not become illegible.
    """
    heading, *cards = items
    return [
        heading,
        rx.grid(
            *cards,
            columns={"initial": "1", "md": "2", "lg": "3"},
            spacing="4",
            width="100%",
            align="stretch",
        ),
    ]


def industry_color_scale() -> dict:
    return {
        "scale": scale(
            "ordinal",
            domain=D.INDUSTRY_NAMES,
            range=[D.INDUSTRY_COLORS[n] for n in D.INDUSTRY_NAMES],
        )
    }


def binned_color_scale() -> dict:
    """Quantized sequential ramp of the binned heatmap (`color` channel)."""
    return {"scale": scale("ordinal", domain=D.BINNED_2D_BUCKETS, range=D.BINNED_2D_COLORS)}


def calendar_color_scale() -> dict:
    """Quantized sequential ramp of the rainfall calendar (`color` channel)."""
    return {"scale": scale("ordinal", domain=D.CALENDAR_BUCKETS, range=D.CALENDAR_COLORS)}


# --- Sections: BAR ---------------------------------------------------------------


def bars_section() -> list[rx.Component]:
    return [
        category_heading("Bars"),
        card(
            "Sorted vertical bars",
            "bar-vertical-sorted",
            "bar",
            "Letter frequency sorted descending.",
            tanstack_chart(
                marks=[bar_y(D.LETTERS_SORTED, x="letter", y="frequency", fill="#4f46e5")],
                x=axis(
                    scale=scale(
                        "band", padding=0.18, domain=[r["letter"] for r in D.LETTERS_SORTED]
                    )
                ),
                y=axis(grid=True, nice=True, ticks={"format": {"style": "percent"}}),
                tooltip=True,
                aria_label="Sorted letter frequency",
                height=280,
            ),
        ),
        card(
            "Horizontal ranking with long labels",
            "bar-horizontal-ranking",
            "bar",
            "Index per city, sorted.",
            tanstack_chart(
                marks=[bar_x(D.CITIES_SORTED, y="city", x="v2024", fill="#0ea5e9")],
                y=axis(
                    scale=scale("band", padding=0.25, domain=[r["city"] for r in D.CITIES_SORTED])
                ),
                x=axis(grid=True, label="2024 index"),
                tooltip=True,
                aria_label="City ranking",
                height=300,
            ),
        ),
        card(
            "Grouped bars",
            "bar-grouped",
            "bar",
            "Penguins by species and sex (composite categories; ♂ blue, ♀ pink).",
            tanstack_chart(
                marks=[
                    bar_y(
                        [r for r in D.PENGUIN_GROUPS if r["sex"] == "MALE"],
                        x="group",
                        y="count",
                        fill="#38bdf8",
                    ),
                    bar_y(
                        [r for r in D.PENGUIN_GROUPS if r["sex"] == "FEMALE"],
                        x="group",
                        y="count",
                        fill="#f472b6",
                    ),
                ],
                x=axis(
                    scale=scale("band", padding=0.25, domain=[r["group"] for r in D.PENGUIN_GROUPS])
                ),
                y=axis(grid=True, label="Individuals"),
                tooltip=True,
                aria_label="Penguins by species and sex",
                height=280,
            ),
        ),
        card(
            "Stacked bars",
            "bar-stacked",
            "bar",
            "Quarterly revenue per product (stacked by cumulative totals, painter technique).",
            tanstack_chart(
                marks=[
                    bar_y(D.STACKED_BARS[p], x="quarter", y="cum", fill=c)
                    for p, c in zip(reversed(D.PRODUCTS), reversed(D.PRODUCT_COLORS), strict=True)
                ],
                x=axis(scale=scale("band", padding=0.3)),
                y=axis(grid=True, label="Revenue ($k)"),
                tooltip=True,
                aria_label="Stacked revenue per product",
                height=280,
            ),
        ),
        card(
            "Aggregation bars (mean)",
            "59-grouped-reducer-bars",
            "bar",
            "Mean mass per species, computed in Python (reduce in the data layer).",
            tanstack_chart(
                marks=[bar_y(D.PENGUIN_MEANS, x="species", y="mean_mass", fill="#10b981")],
                x=axis(scale=scale("band", padding=0.3)),
                y=axis(grid=True, label="Mean mass (g)"),
                tooltip=True,
                aria_label="Mean mass per species",
                height=260,
            ),
        ),
    ]


# --- Sections: TREND -------------------------------------------------------------


def trend_section() -> list[rx.Component]:
    return [
        category_heading("Trend"),
        card(
            "Line with seasonal gaps",
            "01-line-gaps",
            "trend",
            "None values break the line (gaps).",
            tanstack_chart(
                marks=[line_y(D.AAPL_GAPS, x="day", y="close", stroke="#4f46e5", stroke_width=2)],
                x=axis(scale=scale("utc"), ticks={"format": {"month": "short"}}),
                y=axis(grid=True, label="Close (USD)"),
                tooltip=True,
                aria_label="Series with gaps",
                height=280,
            ),
        ),
        card(
            "Multi-line with end labels",
            "02-multi-line-end-labels",
            "trend",
            "Four industries; color per series (z) and a label on the last point.",
            tanstack_chart(
                marks=[
                    line_y(D.INDUSTRIES, x="month", y="rate", z="industry", stroke_width=2),
                    text(
                        D.INDUSTRY_END_LABELS,
                        x="month",
                        y="rate",
                        text="label",
                        dx=8,
                        text_anchor="start",
                        font_size=11,
                    ),
                ],
                x=axis(scale=scale("utc"), ticks={"format": {"month": "short"}}),
                y=axis(grid=True, label="Unemployment (%)"),
                color=industry_color_scale(),
                tooltip=True,
                aria_label="Unemployment by industry",
                height=320,
            ),
        ),
        card(
            "Moving averages",
            "19-moving-average-line",
            "trend",
            "Daily series with precomputed MA7 and MA30.",
            tanstack_chart(
                marks=[
                    line_y(D.AAPL, x="day", y="close", stroke="#cbd5e1", stroke_width=1),
                    line_y(D.AAPL_MA7, x="day", y="ma7", stroke="#0ea5e9", stroke_width=2),
                    line_y(D.AAPL_MA30, x="day", y="ma30", stroke="#4f46e5", stroke_width=2.5),
                ],
                x=axis(scale=scale("utc"), ticks={"format": {"month": "short"}}),
                y=axis(grid=True),
                tooltip=True,
                aria_label="Moving averages",
                height=280,
            ),
        ),
        card(
            "Bollinger band",
            "22-bollinger-band",
            "trend",
            "Mean ± 2σ over a 20-day window.",
            tanstack_chart(
                marks=[
                    area_y(
                        D.AAPL_BOLLINGER,
                        x="day",
                        y1="lo",
                        y2="hi",
                        fill="#818cf8",
                        fill_opacity=0.18,
                    ),
                    line_y(
                        D.AAPL_BOLLINGER,
                        x="day",
                        y="mid",
                        stroke="#6366f1",
                        stroke_width=1.5,
                        stroke_dasharray="4 3",
                    ),
                    line_y(D.AAPL, x="day", y="close", stroke="#0f172a", stroke_width=1.5),
                ],
                x=axis(scale=scale("utc"), ticks={"format": {"month": "short"}}),
                y=axis(grid=True),
                tooltip=True,
                aria_label="Bollinger band",
                height=300,
            ),
        ),
        card(
            "Annotated extrema",
            "58-select-extrema",
            "trend",
            "Minimum and maximum selected in Python and annotated.",
            tanstack_chart(
                marks=[
                    line_y(D.AAPL, x="day", y="close", stroke="#64748b", stroke_width=1.5),
                    dot(D.AAPL_EXTREMA, x="day", y="close", r=5, fill="#ef4444"),
                    text(
                        D.AAPL_EXTREMA,
                        x="day",
                        y="close",
                        text="label",
                        dy=-14,
                        font_size=11,
                        font_weight=600,
                    ),
                ],
                x=axis(scale=scale("utc"), ticks={"format": {"month": "short"}}),
                y=axis(grid=True),
                aria_label="Annotated extrema",
                height=280,
            ),
        ),
        card(
            "Indexed multi-line (base 100)",
            "55-indexed-multi-line",
            "trend",
            "Each industry indexed to its first month.",
            tanstack_chart(
                marks=[
                    line_y(
                        D.INDUSTRIES_INDEXED, x="month", y="index", z="industry", stroke_width=2
                    ),
                    rule_y([100], stroke_dasharray="5 5", stroke_opacity=0.6),
                ],
                x=axis(scale=scale("utc"), ticks={"format": {"month": "short"}}),
                y=axis(grid=True, label="Index (base 100)"),
                color=industry_color_scale(),
                tooltip=True,
                aria_label="Indexed series",
                height=300,
            ),
        ),
    ]


# --- Sections: CHANGE / COMPARISON -----------------------------------------------


def change_section() -> list[rx.Component]:
    return [
        category_heading("Change and comparison"),
        card(
            "Two-period slopegraph",
            "30-slopegraph",
            "change",
            "2019 → 2024 per city; one line per series (z).",
            tanstack_chart(
                marks=[
                    line_y(
                        D.CITIES_LONG,
                        x="year",
                        y="value",
                        z="city",
                        stroke="#64748b",
                        stroke_width=1.5,
                        points=True,
                    ),
                    text(
                        [r for r in D.CITIES_LONG if r["year"] == "2019"],
                        x="year",
                        y="value",
                        text="city",
                        dx=-8,
                        text_anchor="end",
                        font_size=10,
                    ),
                ],
                x=axis(scale=scale("point", padding=0.35)),
                y=axis(grid=True),
                aria_label="City slopegraph",
                height=360,
            ),
        ),
        card(
            "Close vs moving average (difference)",
            "33-difference-chart",
            "change",
            "v1 approximation: neutral band between the curves (signed differenceY lands in v0.2).",
            tanstack_chart(
                marks=[
                    area_y(
                        D.AAPL_MA30,
                        x="day",
                        y1="ma30",
                        y2="close",
                        fill="#a78bfa",
                        fill_opacity=0.25,
                    ),
                    line_y(
                        D.AAPL_MA30,
                        x="day",
                        y="ma30",
                        stroke="#475569",
                        stroke_width=1.5,
                        stroke_dasharray="4 3",
                    ),
                    line_y(D.AAPL_MA30, x="day", y="close", stroke="#7c3aed", stroke_width=1.5),
                ],
                x=axis(scale=scale("utc"), ticks={"format": {"month": "short"}}),
                y=axis(grid=True),
                tooltip=True,
                aria_label="Close vs MA30 difference",
                height=280,
            ),
        ),
        card(
            "Dumbbell",
            "17-dumbbell",
            "comparison",
            "2019–2024 segment per city (z line) with colored endpoints.",
            tanstack_chart(
                marks=[
                    line_y(
                        D.CITIES_LONG,
                        x="value",
                        y="city",
                        z="city",
                        stroke="#94a3b8",
                        stroke_width=2,
                    ),
                    dot(
                        [r for r in D.CITIES_LONG if r["year"] == "2019"],
                        x="value",
                        y="city",
                        r=5,
                        fill="#94a3b8",
                    ),
                    dot(
                        [r for r in D.CITIES_LONG if r["year"] == "2024"],
                        x="value",
                        y="city",
                        r=5,
                        fill="#4f46e5",
                    ),
                ],
                y=axis(scale=scale("point", padding=0.5)),
                x=axis(grid=True, label="Index (gray 2019 → blue 2024)"),
                tooltip=True,
                aria_label="Dumbbell per city",
                height=320,
            ),
        ),
        card(
            "Sorted lollipop",
            "16-lollipop",
            "comparison",
            "Stem (z line from 0 to the value) + dot.",
            tanstack_chart(
                marks=[
                    line_y(
                        [
                            {"city": r["city"], "v": v, "s": r["city"]}
                            for r in D.CITIES_SORTED
                            for v in (0, r["v2024"])
                        ],
                        x="city",
                        y="v",
                        z="s",
                        stroke="#64748b",
                        stroke_width=2,
                    ),
                    dot(D.CITIES_SORTED, x="city", y="v2024", r=6, fill="#4f46e5"),
                ],
                x=axis(
                    scale=scale("point", padding=0.4, domain=[r["city"] for r in D.CITIES_SORTED])
                ),
                y=axis(grid=True),
                tooltip=True,
                aria_label="City lollipop",
                height=300,
            ),
        ),
        card(
            "Population pyramid",
            "71-recharts-population-pyramid",
            "comparison",
            "Males on the left (negative), females on the right.",
            tanstack_chart(
                marks=[
                    bar_x(D.PENGUIN_PYRAMID_M, y="species", x="count", fill="#38bdf8"),
                    bar_x(D.PENGUIN_PYRAMID_F, y="species", x="count", fill="#f472b6"),
                    rule_x([0], stroke_opacity=0.6),
                ],
                y=axis(scale=scale("band", padding=0.3)),
                x=axis(grid=True, label="♂ ← individuals → ♀"),
                tooltip=True,
                aria_label="Pyramid by species and sex",
                height=240,
            ),
        ),
    ]


# --- Sections: DISTRIBUTION ------------------------------------------------------


def distribution_section() -> list[rx.Component]:
    return [
        category_heading("Distribution"),
        card(
            "Histogram",
            "histogram",
            "distribution",
            "Daily returns (%) binned in Python.",
            tanstack_chart(
                marks=[bar_y(D.RETURNS_HIST, x="bin", y="count", fill="#0ea5e9")],
                x=axis(scale=scale("band", padding=0.08), label="Return (%)"),
                y=axis(grid=True, label="Frequency"),
                tooltip=True,
                aria_label="Histogram of returns",
                height=260,
            ),
        ),
        card(
            "Cumulative histogram",
            "18-cumulative-histogram",
            "distribution",
            "Cumulative total of the same bins.",
            tanstack_chart(
                marks=[bar_y(D.RETURNS_HIST, x="bin", y="cum", fill="#6366f1")],
                x=axis(scale=scale("band", padding=0.08)),
                y=axis(grid=True, label="Cumulative"),
                tooltip=True,
                aria_label="Cumulative histogram",
                height=260,
            ),
        ),
        card(
            "Empirical cumulative distribution (ECDF)",
            "50-empirical-cdf",
            "distribution",
            "Step-after curve over the sorted returns.",
            tanstack_chart(
                marks=[
                    line_y(
                        D.RETURNS_ECDF,
                        x="value",
                        y="p",
                        stroke="#0891b2",
                        stroke_width=2,
                        curve="step-after",
                    ),
                    rule_y([0.5], stroke_dasharray="4 4", stroke_opacity=0.5),
                ],
                x=axis(grid=True, label="Return (%)"),
                y=axis(grid=True, ticks={"format": {"style": "percent"}}),
                aria_label="ECDF of returns",
                height=260,
            ),
        ),
        card(
            "Quantitative binned heatmap",
            "24-quantitative-binned-heatmap",
            "distribution",
            "2D bins of a Gaussian cloud; intensity = quantized count.",
            tanstack_chart(
                marks=[cell(D.BINNED_2D, x="xbin", y="ybin", color="bucket", inset=1)],
                x=axis(scale=scale("band", domain=[f"{b}…{b + 1}" for b in range(-2, 3)])),
                y=axis(scale=scale("band", domain=[f"{b}…{b + 1}" for b in range(2, -3, -1)])),
                color=binned_color_scale(),
                tooltip=True,
                aria_label="Binned heatmap",
                height=280,
            ),
        ),
    ]


# --- Sections: RELATIONSHIP ------------------------------------------------------


def relationship_section() -> list[rx.Component]:
    return [
        category_heading("Relationship"),
        card(
            "Bubble scatter",
            "scatter-bubble",
            "relationship",
            "Radius as a channel (r = field).",
            tanstack_chart(
                marks=[
                    dot(
                        [
                            {"revenue": 12, "retention": 0.71, "seats": 8, "segment": "SMB"},
                            {"revenue": 28, "retention": 0.78, "seats": 22, "segment": "SMB"},
                            {"revenue": 45, "retention": 0.83, "seats": 40, "segment": "Growth"},
                            {"revenue": 61, "retention": 0.87, "seats": 55, "segment": "Growth"},
                            {
                                "revenue": 83,
                                "retention": 0.92,
                                "seats": 90,
                                "segment": "Enterprise",
                            },
                            {
                                "revenue": 97,
                                "retention": 0.95,
                                "seats": 120,
                                "segment": "Enterprise",
                            },
                        ],
                        x="revenue",
                        y="retention",
                        r="seats",
                        z="segment",
                    )
                ],
                x=axis(grid=True, label="Revenue ($k)"),
                y=axis(grid=True, ticks={"format": {"style": "percent"}}),
                color={
                    "scale": scale(
                        "ordinal",
                        domain=["SMB", "Growth", "Enterprise"],
                        range=["#38bdf8", "#a78bfa", "#f472b6"],
                    )
                },
                tooltip=True,
                aria_label="Account bubbles",
                height=300,
            ),
        ),
        card(
            "Scatter with linear regression",
            "31-linear-regression",
            "relationship",
            "OLS computed in Python; the fit as a two-point line.",
            tanstack_chart(
                marks=[
                    dot(D.PENGUINS, x="mass", y="flipper", r=2.5, fill="#0ea5e9", opacity=0.6),
                    line_y(
                        D.PENGUIN_REGRESSION,
                        x="mass",
                        y="flipper",
                        stroke="#ef4444",
                        stroke_width=2,
                    ),
                ],
                x=axis(grid=True, label="Mass (g)"),
                y=axis(grid=True, label="Flipper (mm)"),
                tooltip=True,
                aria_label="Mass-flipper regression",
                height=300,
            ),
        ),
        card(
            "Directed connected scatter",
            "56-connected-scatter",
            "relationship",
            "Yearly unemployment vs inflation trajectory with labels.",
            tanstack_chart(
                marks=[
                    line_y(
                        D.CONNECTED,
                        x="unemployment",
                        y="inflation",
                        stroke="#94a3b8",
                        stroke_width=1.5,
                        curve="catmull-rom",
                    ),
                    dot(D.CONNECTED, x="unemployment", y="inflation", r=4, fill="#4f46e5"),
                    text(
                        D.CONNECTED,
                        x="unemployment",
                        y="inflation",
                        text="year",
                        dy=-10,
                        font_size=10,
                    ),
                ],
                x=axis(grid=True, label="Unemployment (%)"),
                y=axis(grid=True, label="Inflation (%)"),
                aria_label="Connected scatter",
                height=320,
            ),
        ),
        card(
            "Lag-1 autocorrelation",
            "60-lag-autocorrelation",
            "relationship",
            "Return t-1 vs return t with rules at 0.",
            tanstack_chart(
                marks=[
                    dot(D.AAPL_LAG, x="prev", y="curr", r=2.5, fill="#8b5cf6", opacity=0.6),
                    rule_x([0], stroke_opacity=0.4),
                    rule_y([0], stroke_opacity=0.4),
                ],
                x=axis(grid=True, label="Return t-1 (%)"),
                y=axis(grid=True, label="Return t (%)"),
                aria_label="Lag-1 autocorrelation",
                height=300,
            ),
        ),
        card(
            "Log-log scale scatter",
            "53-log-scale-scatter",
            "relationship",
            "Package size vs downloads, both on a log scale.",
            tanstack_chart(
                marks=[
                    dot(D.LOG_SCATTER, x="size_kb", y="downloads", r=3, fill="#f59e0b", opacity=0.7)
                ],
                x=axis(scale=scale("log"), grid=True, label="Size (KiB, log)"),
                y=axis(
                    scale=scale("log"),
                    grid=True,
                    label="Downloads (log)",
                    ticks={"format": {"style": "compact"}},
                ),
                tooltip=True,
                aria_label="Log-log scatter",
                height=300,
            ),
        ),
        card(
            "Many-point scatter",
            "73-many-point-scatter",
            "performance",
            "400 points with low opacity.",
            tanstack_chart(
                marks=[dot(D.MANY_POINTS, x="x", y="y", r=2, fill="#334155", opacity=0.35)],
                x=axis(grid=True),
                y=axis(grid=True),
                aria_label="Point cloud",
                height=300,
            ),
        ),
    ]


# --- Sections: COMPOSITION / PART-TO-WHOLE ---------------------------------------


def composition_section() -> list[rx.Component]:
    stacked_marks = [
        area_y(
            D.STACKED_AREAS[n],
            x="month",
            y="cum",
            fill=D.INDUSTRY_COLORS[n],
            fill_opacity=0.85,
            curve="monotone-x",
        )
        for n in reversed(D.INDUSTRY_NAMES)
    ]
    normalized_marks = [
        area_y(
            D.NORMALIZED_AREAS[n],
            x="month",
            y="share",
            fill=D.INDUSTRY_COLORS[n],
            fill_opacity=0.85,
            curve="monotone-x",
        )
        for n in reversed(D.INDUSTRY_NAMES)
    ]
    stream_marks = [
        area_y(
            D.STREAM_AREAS[n],
            x="month",
            y1="y1",
            y2="y2",
            fill=D.INDUSTRY_COLORS[n],
            fill_opacity=0.85,
            curve="basis",
        )
        for n in D.INDUSTRY_NAMES
    ]
    return [
        category_heading("Composition and part-to-whole"),
        card(
            "Stacked time area",
            "04-stacked-time-area",
            "composition",
            "Cumulative totals per industry (painter, precomputed in Python).",
            tanstack_chart(
                marks=stacked_marks,
                x=axis(scale=scale("utc"), ticks={"format": {"month": "short"}}),
                y=axis(grid=True, label="Cumulative unemployment (pp)"),
                aria_label="Stacked area",
                height=300,
            ),
        ),
        card(
            "Normalized stacked area",
            "20-normalized-stacked-area",
            "composition",
            "Share of each industry over the total.",
            tanstack_chart(
                marks=normalized_marks,
                x=axis(scale=scale("utc"), ticks={"format": {"month": "short"}}),
                y=axis(grid=True, ticks={"format": {"style": "percent"}}),
                aria_label="Normalized area",
                height=280,
            ),
        ),
        card(
            "Streamgraph",
            "21-streamgraph",
            "composition",
            "y1/y2 bands with a centered baseline, computed in Python.",
            tanstack_chart(
                marks=stream_marks,
                x=axis(scale=scale("utc"), ticks={"format": {"month": "short"}}),
                y=axis(grid=False),
                aria_label="Streamgraph",
                height=300,
            ),
        ),
        card(
            "Unit waffle",
            "41-waffle-unit-chart",
            "part-to-whole",
            "10×10 grid of cells allocated by frequency (cell).",
            tanstack_chart(
                marks=[cell(D.WAFFLE, x="col", y="row", color="key", inset=2)],
                x=axis(scale=scale("band", domain=[str(i) for i in range(10)])),
                y=axis(scale=scale("band", domain=[str(i) for i in range(10)])),
                color={
                    "scale": scale(
                        "ordinal",
                        domain=[r["letter"] for r in D.LETTERS_SORTED[:8]],
                        range=D.PALETTE[:8],
                    )
                },
                tooltip=True,
                aria_label="Letter waffle",
                height=340,
            ),
        ),
        card(
            "Pie",
            "76-pie",
            "polar",
            "Letter frequency.",
            tanstack_chart(
                marks=[pie(D.LETTERS_SORTED[:6], value="frequency", label="letter")],
                tooltip=True,
                aria_label="Letter pie",
                height=280,
            ),
        ),
        card(
            "Donut",
            "77-donut",
            "polar",
            "inner_radius > 0.",
            tanstack_chart(
                marks=[
                    pie(D.LETTERS_SORTED[:6], value="frequency", label="letter", inner_radius=70)
                ],
                tooltip=True,
                aria_label="Letter donut",
                height=280,
            ),
        ),
        card(
            "Donut with centered total",
            "94-center-donut",
            "polar",
            "Reflex overlay on top of the donut hole.",
            rx.box(
                tanstack_chart(
                    marks=[
                        pie(
                            D.LETTERS_SORTED[:6], value="frequency", label="letter", inner_radius=78
                        )
                    ],
                    tooltip=True,
                    aria_label="Donut with total",
                    height=300,
                ),
                rx.center(
                    rx.vstack(
                        rx.text(f"{D.DONUT_TOTAL:.0%}", size="7", weight="bold"),
                        rx.text("of the corpus", size="1", color_scheme="gray"),
                        spacing="0",
                        align="center",
                    ),
                    position="absolute",
                    inset="0",
                    pointer_events="none",
                ),
                position="relative",
                width="100%",
            ),
        ),
        card(
            "Rounded donut",
            "95-rounded-donut",
            "polar",
            "corner_radius + pad_angle.",
            tanstack_chart(
                marks=[
                    pie(
                        D.LETTERS_SORTED[:6],
                        value="frequency",
                        label="letter",
                        inner_radius=70,
                        corner_radius=6,
                        pad_angle=0.03,
                    )
                ],
                tooltip=True,
                aria_label="Rounded donut",
                height=280,
            ),
        ),
        card(
            "Nested donut",
            "96-nested-donut",
            "polar",
            "Two pie marks with concentric radii (packages / modules).",
            tanstack_chart(
                marks=[
                    pie(D.NESTED_INNER, value="size", label="pkg", outer_radius=62),
                    pie(
                        D.NESTED_OUTER, value="size", label="pkg", inner_radius=68, outer_radius=100
                    ),
                ],
                tooltip=True,
                aria_label="Nested donut",
                height=300,
            ),
        ),
    ]


# --- Sections: RANGE / UNCERTAINTY / TIME ----------------------------------------


def range_time_section() -> list[rx.Component]:
    return [
        category_heading("Ranges, uncertainty and time"),
        card(
            "Temperature range band",
            "03-temperature-range-band",
            "range",
            "Monthly min–max as a band + lines.",
            tanstack_chart(
                marks=[
                    area_y(
                        D.SF_RANGE,
                        x="month",
                        y1="low",
                        y2="high",
                        fill="#38bdf8",
                        fill_opacity=0.25,
                        curve="monotone-x",
                    ),
                    line_y(
                        D.SF_RANGE,
                        x="month",
                        y="low",
                        stroke="#0ea5e9",
                        stroke_width=1.5,
                        curve="monotone-x",
                    ),
                    line_y(
                        D.SF_RANGE,
                        x="month",
                        y="high",
                        stroke="#f87171",
                        stroke_width=1.5,
                        curve="monotone-x",
                    ),
                ],
                x=axis(scale=scale("point", padding=0.2, domain=D.SF_MONTHS)),
                y=axis(grid=True, label="°C"),
                tooltip=True,
                aria_label="Temperature range",
                height=280,
            ),
        ),
        card(
            "Quantile ribbon",
            "61-quantile-ribbon",
            "uncertainty",
            "p10–p90 and p25–p75 bands + median.",
            tanstack_chart(
                marks=[
                    area_y(
                        D.RIBBON,
                        x="month",
                        y1="p10",
                        y2="p90",
                        fill="#a5b4fc",
                        fill_opacity=0.3,
                        curve="monotone-x",
                    ),
                    area_y(
                        D.RIBBON,
                        x="month",
                        y1="p25",
                        y2="p75",
                        fill="#6366f1",
                        fill_opacity=0.35,
                        curve="monotone-x",
                    ),
                    line_y(
                        D.RIBBON,
                        x="month",
                        y="median",
                        stroke="#312e81",
                        stroke_width=2,
                        curve="monotone-x",
                    ),
                ],
                x=axis(scale=scale("utc"), ticks={"format": {"month": "short"}}),
                y=axis(grid=True, label="Rate (%)"),
                aria_label="Quantile ribbon",
                height=300,
            ),
        ),
        card(
            "Dots with error bars",
            "14-error-bars",
            "uncertainty",
            "Vertical segment per trial (z line) + mean.",
            tanstack_chart(
                marks=[
                    line_y(
                        D.ERROR_SEGMENTS,
                        x="trial",
                        y="y",
                        z="seg",
                        stroke="#64748b",
                        stroke_width=2,
                    ),
                    dot(D.ERRORS, x="trial", y="mean", r=5, fill="#4f46e5"),
                ],
                x=axis(scale=scale("point", padding=0.4)),
                y=axis(grid=True, label="Measurement"),
                tooltip=True,
                aria_label="Error bars",
                height=280,
            ),
        ),
        card(
            "Calendar heatmap",
            "25-calendar-heatmap · 118-token-usage-calendar",
            "time",
            "26 weeks × 7 days; intensity = quantized mm of rainfall.",
            tanstack_chart(
                marks=[cell(D.CALENDAR, x="week", y="day", color="bucket", inset=1)],
                x=axis(scale=scale("band", domain=[f"W{w + 1:02d}" for w in range(26)])),
                y=axis(scale=scale("band", domain=D.DAYS)),
                color=calendar_color_scale(),
                tooltip=True,
                aria_label="Rainfall calendar",
                height=240,
            ),
        ),
        card(
            "Labeled ordinal heatmap",
            "heatmap-labeled",
            "matrix",
            "cell + text with the value inside each cell.",
            tanstack_chart(
                marks=[
                    cell(D.BINNED_2D, x="xbin", y="ybin", color="bucket", inset=1),
                    text(
                        D.BINNED_2D, x="xbin", y="ybin", text="count", font_size=11, fill="#0f172a"
                    ),
                ],
                x=axis(scale=scale("band", domain=[f"{b}…{b + 1}" for b in range(-2, 3)])),
                y=axis(scale=scale("band", domain=[f"{b}…{b + 1}" for b in range(2, -3, -1)])),
                color=binned_color_scale(),
                aria_label="Labeled heatmap",
                height=280,
            ),
        ),
    ]


# --- Sections: RANKING / MULTIVARIATE / SURVEY -----------------------------------


def ranking_section() -> list[rx.Component]:
    return [
        category_heading("Ranking, multivariate and surveys"),
        card(
            "Ranking bump chart",
            "54-bump-ranking",
            "ranking",
            "Monthly position per industry (inverted y axis: 1 on top).",
            tanstack_chart(
                marks=[
                    line_y(
                        D.BUMP,
                        x="month",
                        y="rank",
                        z="industry",
                        stroke_width=2.5,
                        curve="monotone-x",
                    ),
                    dot(D.BUMP, x="month", y="rank", z="industry", r=3),
                ],
                x=axis(scale=scale("utc"), ticks={"format": {"month": "short"}}),
                y=axis(scale=scale("linear", domain=[4.5, 0.5]), ticks={"count": 4}, label="Rank"),
                color=industry_color_scale(),
                tooltip=True,
                aria_label="Industry bump chart",
                height=280,
            ),
        ),
        card(
            "Parallel coordinates",
            "27-parallel-coordinates",
            "multivariate",
            "14 cars × 4 normalized dimensions; one polyline per car (z).",
            tanstack_chart(
                marks=[
                    line_y(
                        [r for r in D.PARALLEL if r["kind"] == "sports"],
                        x="dim",
                        y="value",
                        z="car",
                        stroke="#ef4444",
                        stroke_width=1.5,
                        stroke_opacity=0.55,
                    ),
                    line_y(
                        [r for r in D.PARALLEL if r["kind"] == "family"],
                        x="dim",
                        y="value",
                        z="car",
                        stroke="#0ea5e9",
                        stroke_width=1.5,
                        stroke_opacity=0.55,
                    ),
                ],
                x=axis(scale=scale("point", padding=0.15)),
                y=axis(grid=True, ticks={"format": {"style": "percent"}}),
                aria_label="Parallel coordinates",
                height=300,
            ),
        ),
        card(
            "Diverging Likert",
            "26-diverging-likert",
            "survey",
            "Painter cumulative totals on each side of zero.",
            tanstack_chart(
                marks=[
                    bar_x(D.LIKERT_LEFT_OUTER, y="statement", x="v", fill="#dc2626"),
                    bar_x(D.LIKERT_LEFT_INNER, y="statement", x="v", fill="#f87171"),
                    bar_x(D.LIKERT_RIGHT_OUTER, y="statement", x="v", fill="#15803d"),
                    bar_x(D.LIKERT_RIGHT_MID, y="statement", x="v", fill="#4ade80"),
                    bar_x(D.LIKERT_RIGHT_INNER, y="statement", x="v", fill="#d1d5db"),
                    rule_x([0], stroke_opacity=0.7),
                ],
                y=axis(scale=scale("band", padding=0.35)),
                x=axis(grid=True, label="← disagree · responses · agree →"),
                tooltip=True,
                aria_label="Diverging Likert",
                height=300,
            ),
        ),
    ]


# --- Sections: INTERACTION (v1 subset) -------------------------------------------


def interaction_section() -> list[rx.Component]:
    return [
        category_heading("Interaction (v1 subset)"),
        card(
            "Pointer tooltip",
            "34-pointer-tooltip · 35-grouped-tooltip",
            "interaction",
            "Native tooltip over a layered composition.",
            tanstack_chart(
                marks=[
                    area_y(
                        D.SF_RANGE,
                        x="month",
                        y1="low",
                        y2="high",
                        fill="#818cf8",
                        fill_opacity=0.2,
                        curve="monotone-x",
                    ),
                    line_y(
                        D.SF_RANGE,
                        x="month",
                        y="high",
                        stroke="#4f46e5",
                        stroke_width=2.5,
                        points=True,
                        curve="monotone-x",
                    ),
                    rule_y([20], stroke="#f59e0b", stroke_dasharray="7 7"),
                ],
                x=axis(scale=scale("point", padding=0.2, domain=D.SF_MONTHS)),
                y=axis(grid=True, label="°C"),
                tooltip=True,
                aria_label="Pointer tooltip",
                height=280,
            ),
        ),
        card(
            "Linked selection chart → state",
            "82-chart-table-selection",
            "interaction",
            "on_focus_change / on_select arrive sanitized in Python.",
            tanstack_chart(
                marks=[
                    dot(
                        D.PENGUINS[:60],
                        x="mass",
                        y="flipper",
                        r=4,
                        fill="#8b5cf6",
                        id="events-demo",
                    )
                ],
                x=axis(grid=True, label="Mass (g)"),
                y=axis(grid=True, label="Flipper (mm)"),
                tooltip=True,
                aria_label="Interactive scatter",
                height=280,
                on_focus_change=ChartsState.on_focus,
                on_select=ChartsState.on_select,
            ),
            rx.hstack(
                rx.text("Focus: ", weight="bold"),
                rx.code(ChartsState.focused),
                rx.text("Selection: ", weight="bold"),
                rx.code(ChartsState.selected),
                spacing="2",
                wrap="wrap",
            ),
        ),
        card(
            "Live data with transition",
            "86-streaming-window-preservation (approx.)",
            "interaction",
            "State Var + animate: mutating re-renders with a transition.",
            tanstack_chart(
                marks=[bar_y(ChartsState.live_data, x="cat", y="val", fill="#10b981")],
                x=axis(scale=scale("band", padding=0.2)),
                y=axis(grid=True, scale=scale("linear", domain=[0, 100])),
                animate=True,
                tooltip=True,
                aria_label="Reactive bars",
                height=260,
            ),
            rx.button("Randomize data", on_click=ChartsState.randomize),
        ),
    ]


# --- Remaining v1 contract marks (no direct example in the catalog) --------------


def grammar_section() -> list[rx.Component]:
    strip = [
        {"value": v} for v in sorted(round(4.5 + abs(hash(str(i))) % 40 / 10, 1) for i in range(15))
    ]
    return [
        category_heading("Complete v1 grammar (remaining marks)"),
        card(
            "Strip plot with ticks",
            "tick_x + rule_x (basis of 13-interval-timeline)",
            "distribution",
            "1D distribution with the median as a rule.",
            tanstack_chart(
                marks=[
                    tick_x(strip, x="value", stroke="#6366f1", stroke_width=2),
                    rule_x(
                        [strip[len(strip) // 2]["value"]],
                        stroke="#ef4444",
                        stroke_width=2,
                        stroke_dasharray="4 4",
                    ),
                ],
                x=axis(grid=True, nice=True, label="Value"),
                aria_label="Strip plot",
                height=140,
            ),
        ),
        card(
            "Ranges with horizontal ticks",
            "tick_y (basis of 03-range)",
            "range",
            "Monthly lows (blue) and highs (red) as ticks.",
            tanstack_chart(
                marks=[
                    tick_y(D.SF_RANGE, y="low", x="month", stroke="#38bdf8", stroke_width=3),
                    tick_y(D.SF_RANGE, y="high", x="month", stroke="#f87171", stroke_width=3),
                    rule_y([0], stroke_opacity=0.4),
                ],
                x=axis(scale=scale("point", padding=0.5, domain=D.SF_MONTHS)),
                y=axis(grid=True, label="°C"),
                aria_label="Range ticks",
                height=240,
            ),
        ),
        card(
            "Vertical profile (X orientation)",
            "line_x + area_x",
            "trend",
            "Water temperature by depth: x depends on y.",
            tanstack_chart(
                marks=[
                    area_x(
                        [
                            {"temp": t, "depth": d}
                            for t, d in [
                                (22.1, 0),
                                (21.4, 10),
                                (18.9, 25),
                                (14.2, 50),
                                (9.8, 100),
                                (6.5, 200),
                            ]
                        ],
                        y="depth",
                        x="temp",
                        fill="#22d3ee",
                        fill_opacity=0.15,
                    ),
                    line_x(
                        [
                            {"temp": t, "depth": d}
                            for t, d in [
                                (22.1, 0),
                                (21.4, 10),
                                (18.9, 25),
                                (14.2, 50),
                                (9.8, 100),
                                (6.5, 200),
                            ]
                        ],
                        y="depth",
                        x="temp",
                        stroke="#0891b2",
                        stroke_width=3,
                        points=True,
                    ),
                ],
                x=axis(grid=True, label="Temperature (°C)"),
                y=axis(label="Depth (m)"),
                tooltip=True,
                aria_label="Temperature profile",
                height=300,
            ),
        ),
        card(
            "Degradation on an unsupported mark",
            "bridge · UNSUPPORTED_MARK",
            "robustness",
            "A mark outside the v1 contract is skipped with a notice; the page lives (REQ-CH-013).",
            tanstack_chart(
                marks=[
                    bar_y(D.LETTERS_SORTED[:6], x="letter", y="frequency", fill="#64748b"),
                    {"type": "treemap", "data": [{"a": 1}], "temporal_fields": [], "options": {}},
                ],
                x=axis(scale=scale("band", padding=0.18)),
                y=axis(grid=True),
                aria_label="Degradation demo",
                height=220,
            ),
        ),
    ]


# --- Out of scope -----------------------------------------------------------------

OUT_OF_SCOPE = [
    (
        "Advanced distribution",
        "15-boxplot · 52-beeswarm · 43-hexbin · 39-density-contours · "
        "62-ridgeline · 63-violin · 51-faceted · 57-marginal-histograms",
        "box/violin/ridgeline/hexbin/densityContour marks + facets",
    ),
    (
        "Spatial and geography",
        "37-delaunay · 38-contour · 42-vector-field · 40-geojson · "
        "102–110 (choropleths, globe, routes, projections)",
        "geoShape, contour, vector, delaunay",
    ),
    (
        "Hierarchy and networks",
        "36-hierarchy-tree · 74-treemap · 101-sunburst · 111-sankey · 40-force-directed",
        "treemap, sunburst, sankeyDiagram, forceLayout",
    ),
    (
        "Advanced polar",
        "75/99-radar · 78-gauge · 97-rose · 98-needle-gauge · "
        "100-radial-bars · 106-polar-line · 107-polar-scatter",
        "radialLine, radialBarAngle/Radius, radialDot, polar guides",
    ),
    (
        "Financial and rectangles",
        "13-interval-timeline · 28-candlestick · 29-waterfall · 64-marimekko · 72-mixed-bars",
        "rect with x1/x2·y1/y2, waterfall transform, stack",
    ),
    (
        "Advanced interaction",
        "65-voronoi · 80/87/88-cursors · 81-interactive-legend · "
        "83-focus-context · 84-pinned-tooltip · 85-lanes · 89-brush · 90-zoom · 91-scrubber · "
        "92-editable-range",
        "brushX, zoomX, crosshair, interactive legends, custom tooltips",
    ),
    ("Motion", "112–117 (entrance, springs, morph, focus motion)", "motion/spring extension"),
    (
        "Others",
        "32-change-arrows · 33-difference (exact) · 44-framed-scatter",
        "arrow, signed differenceY, frame",
    ),
]


def out_of_scope_card() -> rx.Component:
    rows = [
        rx.table.row(
            rx.table.cell(rx.text(grp, weight="bold", size="2")),
            rx.table.cell(rx.text(ids, size="1", color_scheme="gray")),
            rx.table.cell(rx.text(needs, size="1")),
        )
        for grp, ids, needs in OUT_OF_SCOPE
    ]
    return rx.card(
        rx.vstack(
            rx.heading("Catalog examples outside the v1 contract", size="4"),
            rx.text(
                "They require marks/extensions planned for v0.2+ (PRD §5.2-5.3). "
                "The bridge degrades them with a notice if attempted (REQ-CH-013).",
                size="2",
                color_scheme="gray",
            ),
            rx.table.root(
                rx.table.header(
                    rx.table.row(
                        rx.table.column_header_cell("Group"),
                        rx.table.column_header_cell("Catalog examples"),
                        rx.table.column_header_cell("Requires"),
                    )
                ),
                rx.table.body(*rows),
                width="100%",
            ),
            spacing="3",
            width="100%",
        ),
        width="100%",
    )


# --- Page -------------------------------------------------------------------------


def index() -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.heading("reflex-tanstack-charts — catalog", size="7"),
            rx.text(
                "Replica of the tanstack.com/charts/catalog examples that are feasible "
                "with the v1 contract (14 marks, 8 scales, color, tooltip, events). "
                "Data transforms in Python (_data.py): bins, painter stacking, "
                "moving averages, OLS, ranks, streamgraph.",
                color_scheme="gray",
            ),
            *grid_section(bars_section()),
            *grid_section(trend_section()),
            *grid_section(change_section()),
            *grid_section(distribution_section()),
            *grid_section(relationship_section()),
            *grid_section(composition_section()),
            *grid_section(range_time_section()),
            *grid_section(ranking_section()),
            *grid_section(interaction_section()),
            *grid_section(grammar_section()),
            category_heading("Coverage"),
            out_of_scope_card(),
            spacing="5",
            width="100%",
            padding_y="2em",
        ),
        # rx.container caps at 1136 px (size="4"), too narrow for 3 columns of
        # charts; a centered box gives them the width they need.
        max_width="1800px",
        margin="0 auto",
        padding_x="1.5em",
        width="100%",
    )


app = rx.App()
app.add_page(index, title="reflex-tanstack-charts — TanStack catalog")
