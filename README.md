# reflex-tanstack-charts

Componente personalizado de [Reflex](https://reflex.dev) que envuelve
[TanStack Charts](https://tanstack.com/charts/latest): una gramática de gráficos
tipada, componible por capas y accesible (SVG, foco por teclado, ~16 KiB gzip para
una línea compacta). Declara gráficos 100 % en Python; sin JavaScript.

> TanStack Charts está en **pre-alpha (0.7.2)**; las versiones npm van fijadas
> (pinned) y los bumps entran por Delta Spec (ver `specs/`).

## Instalación

```bash
uv add reflex-tanstack-charts        # o pip install reflex-tanstack-charts
```

## Ejemplo mínimo

```python
import reflex as rx
from reflex_tanstack_charts import tanstack_chart, bar_y, axis, scale

data = [{"letter": "E", "frequency": 0.127}, {"letter": "T", "frequency": 0.091}]

def page() -> rx.Component:
    return tanstack_chart(
        marks=[bar_y(data, x="letter", y="frequency")],
        x=axis(scale=scale("band", padding=0.18)),
        y=axis(grid=True, label="Frequency", ticks={"format": {"style": "percent"}}),
        tooltip=True,
        aria_label="Letter frequencies",
    )
```

## Marcas soportadas (contrato v1)

| Helper Python | Marca TanStack | Uso típico |
|---|---|---|
| `line_y` / `line_x` | `lineY` / `lineX` | tendencias, series temporales |
| `area_y` / `area_x` | `areaY` / `areaX` | áreas y bandas (`y1`+`y2` / `x1`+`x2`) |
| `bar_y` / `bar_x` | `barY` / `barX` | barras verticales / ranking horizontal |
| `dot` | `dot` | scatter, burbujas (`r` numérico o campo) |
| `rule_x` / `rule_y` | `ruleX` / `ruleY` | líneas de referencia y metas |
| `tick_x` / `tick_y` | `tickX` / `tickY` | strip plots, rangos |
| `cell` | `cell` | heatmaps ordinales |
| `text` | `text` | anotaciones |
| `pie` | `pie` (polar) | pie y donut (`inner_radius`) |

Las marcas se componen por capas sobre escalas compartidas, igual que en TanStack:

```python
tanstack_chart(
    marks=[
        area_y(weeks, x="week", y1="lo", y2="hi", fill_opacity=0.2),
        rule_y([70], stroke_dasharray="7 7"),
        line_y(weeks, x="week", y="rate", curve="monotone-x", points=True),
        text(releases, x="week", y="rate", text="label", dy=-16),
    ],
    x=axis(scale=scale("utc"), ticks={"format": {"month": "short", "day": "numeric"}}),
    y=axis(grid=True, label="Activación (%)"),
    aria_label="Activación semanal",
)
```

## Escalas

`linear`, `band`, `point`, `ordinal` (compactas de `@tanstack/charts-scales`) y
`utc`, `time`, `log`, `sqrt` (vía `d3-scale`). Los `datetime`/`date` de Python se
serializan a ISO-8601 y el bridge los rehidrata a `Date`.

## Eventos hacia Python

```python
class S(rx.State):
    @rx.event
    def pick(self, point: dict | None):  # {"mark_id", "key", "x_value", "y_value", "datum"}
        ...

tanstack_chart(..., on_focus_change=S.pick, on_select=S.pick)
```

## Datos reactivos

Pasa un `rx.Var` como dataset y el gráfico se re-renderiza al mutar el estado
(con `animate=True`, con transición):

```python
tanstack_chart(marks=[bar_y(State.data, x="cat", y="val")], animate=True, ...)
```

## Theming

```python
tanstack_chart(..., theme={"--ts-chart-grid": "#33415555"})
```

## Demo

Galería con las 14 marcas, eventos, reactividad y degradación:

```bash
uv sync
cd tanstack_charts_demo
uv run reflex run
```

## Desarrollo

Proyecto spec-anchored (SDD): las specs viven en `specs/` (constitución, PRD con
criterios EARS, API spec, tech design, data model, plan, tasks y gate Analyze).
Los tests citan los REQ que verifican.

```bash
uv sync
uv run pytest
uv run ruff check custom_components tests
```

## Licencia

MIT © Ernesto Crespo
