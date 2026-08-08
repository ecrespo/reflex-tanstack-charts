"""Galería reflex-tanstack-charts basada en https://tanstack.com/charts/catalog.

Replica, con la gramática del contrato v1 (14 marcas + escalas + color + tooltip
+ eventos), todos los ejemplos del catálogo factibles sin marcas avanzadas.
Cada tarjeta cita el id del ejemplo original. Los datos y transforms (bins,
stacking, medias móviles, regresión, ranks…) viven en `_data.py` (Python puro),
siguiendo el reparto de responsabilidades de TanStack.

Los ejemplos del catálogo que requieren marcas fuera del contrato v1
(treemap, sankey, geo, violin, box, radar, brush/zoom, motion…) se listan al
final como fuera de alcance (PRD §5.2 → v0.2+).
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

# --- Estado (reactividad y eventos) -------------------------------------------


class ChartsState(rx.State):
    """Estado de la demo: datos reactivos y punto seleccionado."""

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
        """REQ-CH-005: mutar el Var re-renderiza con transición."""
        self.live_data = [{"cat": c, "val": random.randint(10, 90)} for c in ["A", "B", "C", "D"]]

    @rx.event
    def on_focus(self, point: dict | None):
        self.focused = "sin foco" if point is None else str(point.get("datum"))

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
                rx.badge(f"catálogo: {catalog_id}", variant="outline", color_scheme="gray"),
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
    """Encabezado a ancho completo + sus tarjetas en rejilla de 3 columnas.

    Cada `*_section()` devuelve `[category_heading, card, card, …]`; solo las
    tarjetas entran en la rejilla. Baja a 2 y 1 columna en pantallas estrechas
    para que las gráficas no queden ilegibles.
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
    """Rampa secuencial cuantizada del heatmap de bins (canal `color`)."""
    return {"scale": scale("ordinal", domain=D.BINNED_2D_BUCKETS, range=D.BINNED_2D_COLORS)}


def calendar_color_scale() -> dict:
    """Rampa secuencial cuantizada del calendario de lluvia (canal `color`)."""
    return {"scale": scale("ordinal", domain=D.CALENDAR_BUCKETS, range=D.CALENDAR_COLORS)}


# --- Secciones: BAR --------------------------------------------------------------


def bars_section() -> list[rx.Component]:
    return [
        category_heading("Barras"),
        card(
            "Barras verticales ordenadas",
            "bar-vertical-sorted",
            "bar",
            "Frecuencia de letras ordenada descendente.",
            tanstack_chart(
                marks=[bar_y(D.LETTERS_SORTED, x="letter", y="frequency", fill="#4f46e5")],
                x=axis(
                    scale=scale(
                        "band", padding=0.18, domain=[r["letter"] for r in D.LETTERS_SORTED]
                    )
                ),
                y=axis(grid=True, nice=True, ticks={"format": {"style": "percent"}}),
                tooltip=True,
                aria_label="Frecuencia de letras ordenada",
                height=280,
            ),
        ),
        card(
            "Ranking horizontal con etiquetas largas",
            "bar-horizontal-ranking",
            "bar",
            "Índice por ciudad, ordenado.",
            tanstack_chart(
                marks=[bar_x(D.CITIES_SORTED, y="city", x="v2024", fill="#0ea5e9")],
                y=axis(
                    scale=scale("band", padding=0.25, domain=[r["city"] for r in D.CITIES_SORTED])
                ),
                x=axis(grid=True, label="Índice 2024"),
                tooltip=True,
                aria_label="Ranking de ciudades",
                height=300,
            ),
        ),
        card(
            "Barras agrupadas",
            "bar-grouped",
            "bar",
            "Pingüinos por especie y sexo (categorías compuestas; ♂ azul, ♀ rosa).",
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
                y=axis(grid=True, label="Ejemplares"),
                tooltip=True,
                aria_label="Pingüinos por especie y sexo",
                height=280,
            ),
        ),
        card(
            "Barras apiladas",
            "bar-stacked",
            "bar",
            "Revenue trimestral por producto (apilado por acumulados, técnica painter).",
            tanstack_chart(
                marks=[
                    bar_y(D.STACKED_BARS[p], x="quarter", y="cum", fill=c)
                    for p, c in zip(reversed(D.PRODUCTS), reversed(D.PRODUCT_COLORS), strict=True)
                ],
                x=axis(scale=scale("band", padding=0.3)),
                y=axis(grid=True, label="Revenue ($k)"),
                tooltip=True,
                aria_label="Revenue apilado por producto",
                height=280,
            ),
        ),
        card(
            "Barras de agregación (media)",
            "59-grouped-reducer-bars",
            "bar",
            "Masa media por especie, calculada en Python (reduce en la capa de datos).",
            tanstack_chart(
                marks=[bar_y(D.PENGUIN_MEANS, x="species", y="mean_mass", fill="#10b981")],
                x=axis(scale=scale("band", padding=0.3)),
                y=axis(grid=True, label="Masa media (g)"),
                tooltip=True,
                aria_label="Masa media por especie",
                height=260,
            ),
        ),
    ]


# --- Secciones: TREND ------------------------------------------------------------


def trend_section() -> list[rx.Component]:
    return [
        category_heading("Tendencia"),
        card(
            "Línea con huecos estacionales",
            "01-line-gaps",
            "trend",
            "Valores None cortan la línea (gaps).",
            tanstack_chart(
                marks=[line_y(D.AAPL_GAPS, x="day", y="close", stroke="#4f46e5", stroke_width=2)],
                x=axis(scale=scale("utc"), ticks={"format": {"month": "short"}}),
                y=axis(grid=True, label="Close (USD)"),
                tooltip=True,
                aria_label="Serie con huecos",
                height=280,
            ),
        ),
        card(
            "Multilínea con etiquetas al final",
            "02-multi-line-end-labels",
            "trend",
            "Cuatro industrias; color por serie (z) y etiqueta en el último punto.",
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
                y=axis(grid=True, label="Desempleo (%)"),
                color=industry_color_scale(),
                tooltip=True,
                aria_label="Desempleo por industria",
                height=320,
            ),
        ),
        card(
            "Medias móviles",
            "19-moving-average-line",
            "trend",
            "Serie diaria con MA7 y MA30 precalculadas.",
            tanstack_chart(
                marks=[
                    line_y(D.AAPL, x="day", y="close", stroke="#cbd5e1", stroke_width=1),
                    line_y(D.AAPL_MA7, x="day", y="ma7", stroke="#0ea5e9", stroke_width=2),
                    line_y(D.AAPL_MA30, x="day", y="ma30", stroke="#4f46e5", stroke_width=2.5),
                ],
                x=axis(scale=scale("utc"), ticks={"format": {"month": "short"}}),
                y=axis(grid=True),
                tooltip=True,
                aria_label="Medias móviles",
                height=280,
            ),
        ),
        card(
            "Banda de Bollinger",
            "22-bollinger-band",
            "trend",
            "Media ± 2σ en ventana de 20 días.",
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
                aria_label="Banda de Bollinger",
                height=300,
            ),
        ),
        card(
            "Extremos anotados",
            "58-select-extrema",
            "trend",
            "Mínimo y máximo seleccionados en Python y anotados.",
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
                aria_label="Extremos anotados",
                height=280,
            ),
        ),
        card(
            "Multilínea indexada (base 100)",
            "55-indexed-multi-line",
            "trend",
            "Cada industria indexada a su primer mes.",
            tanstack_chart(
                marks=[
                    line_y(
                        D.INDUSTRIES_INDEXED, x="month", y="index", z="industry", stroke_width=2
                    ),
                    rule_y([100], stroke_dasharray="5 5", stroke_opacity=0.6),
                ],
                x=axis(scale=scale("utc"), ticks={"format": {"month": "short"}}),
                y=axis(grid=True, label="Índice (base 100)"),
                color=industry_color_scale(),
                tooltip=True,
                aria_label="Series indexadas",
                height=300,
            ),
        ),
    ]


# --- Secciones: CHANGE / COMPARISON ----------------------------------------------


def change_section() -> list[rx.Component]:
    return [
        category_heading("Cambio y comparación"),
        card(
            "Slopegraph de dos períodos",
            "30-slopegraph",
            "change",
            "2019 → 2024 por ciudad; una línea por serie (z).",
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
                aria_label="Slopegraph de ciudades",
                height=360,
            ),
        ),
        card(
            "Close vs media móvil (diferencia)",
            "33-difference-chart",
            "change",
            "Aproximación v1: banda neutra entre las curvas (differenceY con signo llega en v0.2).",
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
                aria_label="Diferencia close vs MA30",
                height=280,
            ),
        ),
        card(
            "Dumbbell",
            "17-dumbbell",
            "comparison",
            "Segmento 2019–2024 por ciudad (línea z) con extremos coloreados.",
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
                x=axis(grid=True, label="Índice (gris 2019 → azul 2024)"),
                tooltip=True,
                aria_label="Dumbbell por ciudad",
                height=320,
            ),
        ),
        card(
            "Lollipop ordenado",
            "16-lollipop",
            "comparison",
            "Tallo (línea z de 0 al valor) + punto.",
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
                aria_label="Lollipop de ciudades",
                height=300,
            ),
        ),
        card(
            "Pirámide de población",
            "71-recharts-population-pyramid",
            "comparison",
            "Machos a la izquierda (negativo), hembras a la derecha.",
            tanstack_chart(
                marks=[
                    bar_x(D.PENGUIN_PYRAMID_M, y="species", x="count", fill="#38bdf8"),
                    bar_x(D.PENGUIN_PYRAMID_F, y="species", x="count", fill="#f472b6"),
                    rule_x([0], stroke_opacity=0.6),
                ],
                y=axis(scale=scale("band", padding=0.3)),
                x=axis(grid=True, label="♂ ← ejemplares → ♀"),
                tooltip=True,
                aria_label="Pirámide por especie y sexo",
                height=240,
            ),
        ),
    ]


# --- Secciones: DISTRIBUTION -----------------------------------------------------


def distribution_section() -> list[rx.Component]:
    return [
        category_heading("Distribución"),
        card(
            "Histograma",
            "histogram",
            "distribution",
            "Retornos diarios (%) binned en Python.",
            tanstack_chart(
                marks=[bar_y(D.RETURNS_HIST, x="bin", y="count", fill="#0ea5e9")],
                x=axis(scale=scale("band", padding=0.08), label="Retorno (%)"),
                y=axis(grid=True, label="Frecuencia"),
                tooltip=True,
                aria_label="Histograma de retornos",
                height=260,
            ),
        ),
        card(
            "Histograma acumulado",
            "18-cumulative-histogram",
            "distribution",
            "Acumulado de los mismos bins.",
            tanstack_chart(
                marks=[bar_y(D.RETURNS_HIST, x="bin", y="cum", fill="#6366f1")],
                x=axis(scale=scale("band", padding=0.08)),
                y=axis(grid=True, label="Acumulado"),
                tooltip=True,
                aria_label="Histograma acumulado",
                height=260,
            ),
        ),
        card(
            "Distribución acumulada empírica (ECDF)",
            "50-empirical-cdf",
            "distribution",
            "Curva step-after sobre los retornos ordenados.",
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
                x=axis(grid=True, label="Retorno (%)"),
                y=axis(grid=True, ticks={"format": {"style": "percent"}}),
                aria_label="ECDF de retornos",
                height=260,
            ),
        ),
        card(
            "Heatmap binned cuantitativo",
            "24-quantitative-binned-heatmap",
            "distribution",
            "Bins 2D de una nube gaussiana; intensidad = conteo cuantizado.",
            tanstack_chart(
                marks=[cell(D.BINNED_2D, x="xbin", y="ybin", color="bucket", inset=1)],
                x=axis(scale=scale("band", domain=[f"{b}…{b + 1}" for b in range(-2, 3)])),
                y=axis(scale=scale("band", domain=[f"{b}…{b + 1}" for b in range(2, -3, -1)])),
                color=binned_color_scale(),
                tooltip=True,
                aria_label="Heatmap binned",
                height=280,
            ),
        ),
    ]


# --- Secciones: RELATIONSHIP -----------------------------------------------------


def relationship_section() -> list[rx.Component]:
    return [
        category_heading("Relación"),
        card(
            "Scatter de burbujas",
            "scatter-bubble",
            "relationship",
            "Radio como canal (r = campo).",
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
                aria_label="Burbujas de cuentas",
                height=300,
            ),
        ),
        card(
            "Scatter con regresión lineal",
            "31-linear-regression",
            "relationship",
            "OLS calculada en Python; recta como línea de dos puntos.",
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
                x=axis(grid=True, label="Masa (g)"),
                y=axis(grid=True, label="Aleta (mm)"),
                tooltip=True,
                aria_label="Regresión masa-aleta",
                height=300,
            ),
        ),
        card(
            "Scatter conectado dirigido",
            "56-connected-scatter",
            "relationship",
            "Trayectoria anual desempleo vs inflación con etiquetas.",
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
                x=axis(grid=True, label="Desempleo (%)"),
                y=axis(grid=True, label="Inflación (%)"),
                aria_label="Scatter conectado",
                height=320,
            ),
        ),
        card(
            "Autocorrelación lag-1",
            "60-lag-autocorrelation",
            "relationship",
            "Retorno t-1 vs retorno t con reglas en 0.",
            tanstack_chart(
                marks=[
                    dot(D.AAPL_LAG, x="prev", y="curr", r=2.5, fill="#8b5cf6", opacity=0.6),
                    rule_x([0], stroke_opacity=0.4),
                    rule_y([0], stroke_opacity=0.4),
                ],
                x=axis(grid=True, label="Retorno t-1 (%)"),
                y=axis(grid=True, label="Retorno t (%)"),
                aria_label="Autocorrelación lag-1",
                height=300,
            ),
        ),
        card(
            "Scatter en escala log-log",
            "53-log-scale-scatter",
            "relationship",
            "Tamaño de paquete vs descargas, ambas en log.",
            tanstack_chart(
                marks=[
                    dot(D.LOG_SCATTER, x="size_kb", y="downloads", r=3, fill="#f59e0b", opacity=0.7)
                ],
                x=axis(scale=scale("log"), grid=True, label="Tamaño (KiB, log)"),
                y=axis(
                    scale=scale("log"),
                    grid=True,
                    label="Descargas (log)",
                    ticks={"format": {"style": "compact"}},
                ),
                tooltip=True,
                aria_label="Scatter log-log",
                height=300,
            ),
        ),
        card(
            "Scatter de muchos puntos",
            "73-many-point-scatter",
            "performance",
            "400 puntos con opacidad baja.",
            tanstack_chart(
                marks=[dot(D.MANY_POINTS, x="x", y="y", r=2, fill="#334155", opacity=0.35)],
                x=axis(grid=True),
                y=axis(grid=True),
                aria_label="Nube de puntos",
                height=300,
            ),
        ),
    ]


# --- Secciones: COMPOSITION / PART-TO-WHOLE --------------------------------------


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
        category_heading("Composición y parte-de-un-todo"),
        card(
            "Área apilada temporal",
            "04-stacked-time-area",
            "composition",
            "Acumulados por industria (painter, precalculado en Python).",
            tanstack_chart(
                marks=stacked_marks,
                x=axis(scale=scale("utc"), ticks={"format": {"month": "short"}}),
                y=axis(grid=True, label="Desempleo acumulado (pp)"),
                aria_label="Área apilada",
                height=300,
            ),
        ),
        card(
            "Área apilada normalizada",
            "20-normalized-stacked-area",
            "composition",
            "Share de cada industria sobre el total.",
            tanstack_chart(
                marks=normalized_marks,
                x=axis(scale=scale("utc"), ticks={"format": {"month": "short"}}),
                y=axis(grid=True, ticks={"format": {"style": "percent"}}),
                aria_label="Área normalizada",
                height=280,
            ),
        ),
        card(
            "Streamgraph",
            "21-streamgraph",
            "composition",
            "Bandas y1/y2 con línea base centrada, calculadas en Python.",
            tanstack_chart(
                marks=stream_marks,
                x=axis(scale=scale("utc"), ticks={"format": {"month": "short"}}),
                y=axis(grid=False),
                aria_label="Streamgraph",
                height=300,
            ),
        ),
        card(
            "Waffle de unidades",
            "41-waffle-unit-chart",
            "part-to-whole",
            "Cuadrícula 10×10 de celdas asignadas por frecuencia (cell).",
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
                aria_label="Waffle de letras",
                height=340,
            ),
        ),
        card(
            "Pie",
            "76-pie",
            "polar",
            "Frecuencia de letras.",
            tanstack_chart(
                marks=[pie(D.LETTERS_SORTED[:6], value="frequency", label="letter")],
                tooltip=True,
                aria_label="Pie de letras",
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
                aria_label="Donut de letras",
                height=280,
            ),
        ),
        card(
            "Donut con total centrado",
            "94-center-donut",
            "polar",
            "Overlay de Reflex sobre el hueco del donut.",
            rx.box(
                tanstack_chart(
                    marks=[
                        pie(
                            D.LETTERS_SORTED[:6], value="frequency", label="letter", inner_radius=78
                        )
                    ],
                    tooltip=True,
                    aria_label="Donut con total",
                    height=300,
                ),
                rx.center(
                    rx.vstack(
                        rx.text(f"{D.DONUT_TOTAL:.0%}", size="7", weight="bold"),
                        rx.text("del corpus", size="1", color_scheme="gray"),
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
            "Donut redondeado",
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
                aria_label="Donut redondeado",
                height=280,
            ),
        ),
        card(
            "Donut anidado",
            "96-nested-donut",
            "polar",
            "Dos marcas pie con radios concéntricos (paquetes / módulos).",
            tanstack_chart(
                marks=[
                    pie(D.NESTED_INNER, value="size", label="pkg", outer_radius=62),
                    pie(
                        D.NESTED_OUTER, value="size", label="pkg", inner_radius=68, outer_radius=100
                    ),
                ],
                tooltip=True,
                aria_label="Donut anidado",
                height=300,
            ),
        ),
    ]


# --- Secciones: RANGE / UNCERTAINTY / TIME ---------------------------------------


def range_time_section() -> list[rx.Component]:
    return [
        category_heading("Rangos, incertidumbre y tiempo"),
        card(
            "Banda de rango de temperatura",
            "03-temperature-range-band",
            "range",
            "Mín–máx mensual como banda + líneas.",
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
                aria_label="Rango de temperaturas",
                height=280,
            ),
        ),
        card(
            "Cinta de percentiles",
            "61-quantile-ribbon",
            "uncertainty",
            "Bandas p10–p90 y p25–p75 + mediana.",
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
                y=axis(grid=True, label="Tasa (%)"),
                aria_label="Cinta de percentiles",
                height=300,
            ),
        ),
        card(
            "Puntos con barras de error",
            "14-error-bars",
            "uncertainty",
            "Segmento vertical por ensayo (línea z) + media.",
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
                y=axis(grid=True, label="Medición"),
                tooltip=True,
                aria_label="Barras de error",
                height=280,
            ),
        ),
        card(
            "Calendario heatmap",
            "25-calendar-heatmap · 118-token-usage-calendar",
            "time",
            "26 semanas × 7 días; intensidad = mm de lluvia cuantizados.",
            tanstack_chart(
                marks=[cell(D.CALENDAR, x="week", y="day", color="bucket", inset=1)],
                x=axis(scale=scale("band", domain=[f"S{w + 1:02d}" for w in range(26)])),
                y=axis(scale=scale("band", domain=D.DAYS_ES)),
                color=calendar_color_scale(),
                tooltip=True,
                aria_label="Calendario de lluvia",
                height=240,
            ),
        ),
        card(
            "Heatmap ordinal etiquetado",
            "heatmap-labeled",
            "matrix",
            "cell + text con el valor dentro de cada celda.",
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
                aria_label="Heatmap etiquetado",
                height=280,
            ),
        ),
    ]


# --- Secciones: RANKING / MULTIVARIATE / SURVEY ----------------------------------


def ranking_section() -> list[rx.Component]:
    return [
        category_heading("Ranking, multivariable y encuestas"),
        card(
            "Bump chart de ranking",
            "54-bump-ranking",
            "ranking",
            "Posición mensual por industria (eje y invertido: 1 arriba).",
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
                aria_label="Bump de industrias",
                height=280,
            ),
        ),
        card(
            "Coordenadas paralelas",
            "27-parallel-coordinates",
            "multivariate",
            "14 autos × 4 dimensiones normalizadas; una polilínea por auto (z).",
            tanstack_chart(
                marks=[
                    line_y(
                        [r for r in D.PARALLEL if r["kind"] == "deportivo"],
                        x="dim",
                        y="value",
                        z="car",
                        stroke="#ef4444",
                        stroke_width=1.5,
                        stroke_opacity=0.55,
                    ),
                    line_y(
                        [r for r in D.PARALLEL if r["kind"] == "familiar"],
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
                aria_label="Coordenadas paralelas",
                height=300,
            ),
        ),
        card(
            "Likert divergente",
            "26-diverging-likert",
            "survey",
            "Acumulados painter a cada lado del cero.",
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
                x=axis(grid=True, label="← desacuerdo · respuestas · acuerdo →"),
                tooltip=True,
                aria_label="Likert divergente",
                height=300,
            ),
        ),
    ]


# --- Secciones: INTERACTION (subconjunto v1) -------------------------------------


def interaction_section() -> list[rx.Component]:
    return [
        category_heading("Interacción (subconjunto v1)"),
        card(
            "Tooltip por puntero",
            "34-pointer-tooltip · 35-grouped-tooltip",
            "interaction",
            "Tooltip nativo sobre composición por capas.",
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
                aria_label="Tooltip por puntero",
                height=280,
            ),
        ),
        card(
            "Selección enlazada chart → estado",
            "82-chart-table-selection",
            "interaction",
            "on_focus_change / on_select llegan sanitizados a Python.",
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
                x=axis(grid=True, label="Masa (g)"),
                y=axis(grid=True, label="Aleta (mm)"),
                tooltip=True,
                aria_label="Scatter interactivo",
                height=280,
                on_focus_change=ChartsState.on_focus,
                on_select=ChartsState.on_select,
            ),
            rx.hstack(
                rx.text("Foco: ", weight="bold"),
                rx.code(ChartsState.focused),
                rx.text("Selección: ", weight="bold"),
                rx.code(ChartsState.selected),
                spacing="2",
                wrap="wrap",
            ),
        ),
        card(
            "Datos vivos con transición",
            "86-streaming-window-preservation (aprox.)",
            "interaction",
            "Var de estado + animate: mutar re-renderiza con transición.",
            tanstack_chart(
                marks=[bar_y(ChartsState.live_data, x="cat", y="val", fill="#10b981")],
                x=axis(scale=scale("band", padding=0.2)),
                y=axis(grid=True, scale=scale("linear", domain=[0, 100])),
                animate=True,
                tooltip=True,
                aria_label="Barras reactivas",
                height=260,
            ),
            rx.button("Randomizar datos", on_click=ChartsState.randomize),
        ),
    ]


# --- Marcas restantes del contrato v1 (sin ejemplo directo en el catálogo) --------


def grammar_section() -> list[rx.Component]:
    strip = [
        {"value": v} for v in sorted(round(4.5 + abs(hash(str(i))) % 40 / 10, 1) for i in range(15))
    ]
    return [
        category_heading("Gramática v1 completa (marcas restantes)"),
        card(
            "Strip plot con ticks",
            "tick_x + rule_x (base de 13-interval-timeline)",
            "distribution",
            "Distribución 1D con la mediana como regla.",
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
                x=axis(grid=True, nice=True, label="Valor"),
                aria_label="Strip plot",
                height=140,
            ),
        ),
        card(
            "Rangos con ticks horizontales",
            "tick_y (base de 03-range)",
            "range",
            "Mínimas (azul) y máximas (rojo) mensuales como ticks.",
            tanstack_chart(
                marks=[
                    tick_y(D.SF_RANGE, y="low", x="month", stroke="#38bdf8", stroke_width=3),
                    tick_y(D.SF_RANGE, y="high", x="month", stroke="#f87171", stroke_width=3),
                    rule_y([0], stroke_opacity=0.4),
                ],
                x=axis(scale=scale("point", padding=0.5, domain=D.SF_MONTHS)),
                y=axis(grid=True, label="°C"),
                aria_label="Ticks de rangos",
                height=240,
            ),
        ),
        card(
            "Perfil vertical (orientación X)",
            "line_x + area_x",
            "trend",
            "Temperatura del agua según profundidad: x depende de y.",
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
                x=axis(grid=True, label="Temperatura (°C)"),
                y=axis(label="Profundidad (m)"),
                tooltip=True,
                aria_label="Perfil de temperatura",
                height=300,
            ),
        ),
        card(
            "Degradación ante marca no soportada",
            "bridge · UNSUPPORTED_MARK",
            "robustez",
            "Una marca fuera del contrato v1 se omite con aviso; la página sobrevive (REQ-CH-013).",
            tanstack_chart(
                marks=[
                    bar_y(D.LETTERS_SORTED[:6], x="letter", y="frequency", fill="#64748b"),
                    {"type": "treemap", "data": [{"a": 1}], "temporal_fields": [], "options": {}},
                ],
                x=axis(scale=scale("band", padding=0.18)),
                y=axis(grid=True),
                aria_label="Demo de degradación",
                height=220,
            ),
        ),
    ]


# --- Fuera de alcance -------------------------------------------------------------

OUT_OF_SCOPE = [
    (
        "Distribución avanzada",
        "15-boxplot · 52-beeswarm · 43-hexbin · 39-density-contours · "
        "62-ridgeline · 63-violin · 51-faceted · 57-marginal-histograms",
        "marcas box/violin/ridgeline/hexbin/densityContour + facetas",
    ),
    (
        "Espacial y geografía",
        "37-delaunay · 38-contour · 42-vector-field · 40-geojson · "
        "102–110 (choropleths, globo, rutas, proyecciones)",
        "geoShape, contour, vector, delaunay",
    ),
    (
        "Jerarquía y redes",
        "36-hierarchy-tree · 74-treemap · 101-sunburst · 111-sankey · 40-force-directed",
        "treemap, sunburst, sankeyDiagram, forceLayout",
    ),
    (
        "Polar avanzado",
        "75/99-radar · 78-gauge · 97-rose · 98-needle-gauge · "
        "100-radial-bars · 106-polar-line · 107-polar-scatter",
        "radialLine, radialBarAngle/Radius, radialDot, guías polares",
    ),
    (
        "Financieros y rectángulos",
        "13-interval-timeline · 28-candlestick · 29-waterfall · 64-marimekko · 72-mixed-bars",
        "rect con x1/x2·y1/y2, transform waterfall, stack",
    ),
    (
        "Interacción avanzada",
        "65-voronoi · 80/87/88-cursors · 81-interactive-legend · "
        "83-focus-context · 84-pinned-tooltip · 85-lanes · 89-brush · 90-zoom · 91-scrubber · "
        "92-editable-range",
        "brushX, zoomX, crosshair, leyendas interactivas, tooltips custom",
    ),
    ("Motion", "112–117 (entrance, springs, morph, focus motion)", "extensión motion/spring"),
    (
        "Otros",
        "32-change-arrows · 33-difference exacta · 44-framed-scatter",
        "arrow, differenceY con signo, frame",
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
            rx.heading("Ejemplos del catálogo fuera del contrato v1", size="4"),
            rx.text(
                "Requieren marcas/extensiones planificadas para v0.2+ (PRD §5.2-5.3). "
                "El bridge los degrada con aviso si se intentan (REQ-CH-013).",
                size="2",
                color_scheme="gray",
            ),
            rx.table.root(
                rx.table.header(
                    rx.table.row(
                        rx.table.column_header_cell("Grupo"),
                        rx.table.column_header_cell("Ejemplos del catálogo"),
                        rx.table.column_header_cell("Requiere"),
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


# --- Página -----------------------------------------------------------------------


def index() -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.heading("reflex-tanstack-charts — catálogo", size="7"),
            rx.text(
                "Réplica de los ejemplos de tanstack.com/charts/catalog factibles con "
                "el contrato v1 (14 marcas, 8 escalas, color, tooltip, eventos). "
                "Transforms de datos en Python (_data.py): bins, stacking painter, "
                "medias móviles, OLS, ranks, streamgraph.",
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
            category_heading("Cobertura"),
            out_of_scope_card(),
            spacing="5",
            width="100%",
            padding_y="2em",
        ),
        # rx.container topa en 1136 px (size="4"), demasiado estrecho para 3
        # columnas de gráficas; una caja centrada da el ancho que necesitan.
        max_width="1800px",
        margin="0 auto",
        padding_x="1.5em",
        width="100%",
    )


app = rx.App()
app.add_page(index, title="reflex-tanstack-charts — catálogo TanStack")
