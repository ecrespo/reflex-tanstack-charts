# reflex-tanstack-charts

Custom [Reflex](https://reflex.dev) component wrapping
[TanStack Charts](https://tanstack.com/charts/latest): a typed, layer-composable
and accessible chart grammar (SVG, keyboard focus, ~16 KiB gzip for a compact
line chart). Declare charts 100% in Python; no JavaScript.

> Built on TanStack Charts **1.1.0** (stable since 1.0); the npm versions are pinned
> and bumps go through a Delta Spec (see `specs/` and `changes/`).

## Installation

```bash
uv add reflex-tanstack-charts        # or pip install reflex-tanstack-charts
```

## Minimal example

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

## Supported marks (v1 contract)

| Python helper | TanStack mark | Typical use |
|---|---|---|
| `line_y` / `line_x` | `lineY` / `lineX` | trends, time series |
| `area_y` / `area_x` | `areaY` / `areaX` | areas and bands (`y1`+`y2` / `x1`+`x2`) |
| `bar_y` / `bar_x` | `barY` / `barX` | vertical bars / horizontal ranking |
| `dot` | `dot` | scatter, bubbles (`r` as a number or a field) |
| `rule_x` / `rule_y` | `ruleX` / `ruleY` | reference lines and targets |
| `tick_x` / `tick_y` | `tickX` / `tickY` | strip plots, ranges |
| `cell` | `cell` | ordinal heatmaps |
| `text` | `text` | annotations |
| `pie` | `pie` (polar) | pie and donut (`inner_radius`) |

Marks compose in layers over shared scales, just like in TanStack:

```python
tanstack_chart(
    marks=[
        area_y(weeks, x="week", y1="lo", y2="hi", fill_opacity=0.2),
        rule_y([70], stroke_dasharray="7 7"),
        line_y(weeks, x="week", y="rate", curve="monotone-x", points=True),
        text(releases, x="week", y="rate", text="label", dy=-16),
    ],
    x=axis(scale=scale("utc"), ticks={"format": {"month": "short", "day": "numeric"}}),
    y=axis(grid=True, label="Activation (%)"),
    aria_label="Weekly activation",
)
```

## Scales

`linear`, `band`, `point`, `ordinal` (compact ones from `@tanstack/charts/scales/*`)
and `utc`, `time`, `log`, `sqrt` (via `d3-scale`). Python `datetime`/`date` values
are serialized to ISO-8601 and the bridge rehydrates them back to `Date`.

## Events into Python

```python
class S(rx.State):
    @rx.event
    def pick(self, point: dict | None):  # {"mark_id", "key", "x_value", "y_value", "datum"}
        ...

tanstack_chart(..., on_focus_change=S.pick, on_select=S.pick)
```

## Reactive data

Pass an `rx.Var` as the dataset and the chart re-renders when the state mutates
(with `animate=True`, using a transition):

```python
tanstack_chart(marks=[bar_y(State.data, x="cat", y="val")], animate=True, ...)
```

## Theming

```python
tanstack_chart(..., theme={"--ts-chart-grid": "#33415555"})
```

## Demo

Gallery with the 14 marks, events, reactivity and graceful degradation:

```bash
uv sync
cd tanstack_charts_demo
uv run reflex run
```

## Development

Spec-anchored project (SDD): the specs live in `specs/` (constitution, PRD with
EARS criteria, API spec, tech design, data model, plan, tasks and the Analyze
gate). Tests cite the REQs they verify.

```bash
uv sync
uv run pytest
uv run ruff check custom_components tests
```

## License

MIT © Ernesto Crespo
