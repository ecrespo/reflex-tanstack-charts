# reflex-tanstack-charts — API Specification (Component API)

## Metadata

| Field | Value |
|---|---|
| **Author** | Ernesto Crespo |
| **Status** | `DRAFT` |
| **API version** | v1.0 (package 0.1.0) |
| **Date** | 2026-08-07 |
| **Related PRD** | `specs/prd/reflex-tanstack-charts.md` |
| **Surface** | Public Python API + `ChartSpec` JSON contract + JSX bridge props |

> Adaptation note: this project exposes no HTTP. The "API" is three coupled
> contracts: (1) the importable Python API, (2) the `ChartSpec` JSON that travels
> Python→JS, (3) the bridge component's props/events. All three are versioned together.

---

## 1. Overview

Consumers: Reflex apps (humans and agents). Everything public is imported from the
root package:

```python
from reflex_tanstack_charts import (
    tanstack_chart,          # component
    line_y, line_x, area_y, area_x, bar_y, bar_x,
    dot, rule_x, rule_y, text, tick_x, tick_y, cell, pie,   # marks (14)
    scale,                   # scale builder
)
```

## 2. Python API

### 2.1 `tanstack_chart(...) -> rx.Component`

| Parameter | Python type | Required | Default | Description |
|---|---|---|---|---|
| `marks` | `list[Mark \| rx.Var]` | Yes | — | List of marks (dicts produced by the §2.2 helpers) |
| `x` | `AxisSpec \| None` | No | inferred | X axis/scale config (§2.3) |
| `y` | `AxisSpec \| None` | No | inferred | Y axis/scale config |
| `color` | `dict \| None` | No | `None` | Color scale (`{"scheme": [...]}` or `ordinal`) |
| `height` | `int \| rx.Var[int]` | No | `320` | Fixed height in px (REQ-CH-016) |
| `aspect_ratio` | `float \| None` | No | `None` | Alternative to `height` |
| `initial_width` | `int \| None` | No | `None` | SSR width with `aspect_ratio` |
| `aria_label` | `str` | Recommended | `None` (warn) | REQ-CH-017 |
| `tooltip` | `bool` | No | `False` | REQ-CH-006 |
| `animate` | `bool` | No | `False` | REQ-CH-007 |
| `theme` | `dict[str, str] \| None` | No | `None` | `--ts-chart-*` CSS vars (REQ-CH-018) |
| `on_focus_change` | `rx.EventHandler` | No | — | REQ-CH-008/010 |
| `on_select` | `rx.EventHandler` | No | — | REQ-CH-009 |

**Validations (fail-fast in Python):**

| Rule | Error if it fails |
|---|---|
| `marks` non-empty and every item a valid `Mark` or Var | `ValueError("marks must be a non-empty list…")` |
| `height` > 0; `aspect_ratio` > 0; not both explicit | `ValueError` |
| Scale type ∈ catalog §2.3 | `ValueError` listing the valid types |

### 2.2 Mark helpers (14 MUST)

Shared signature: `mark(data, **channels) -> Mark` where `data` is
`list[dict] | rx.Var`. With `rx.Var`, field validation is deferred to the bridge
(REQ-CH-012 applies to literal data only).

| Helper | TanStack mark | Required channels | Optional channels (serializable) |
|---|---|---|---|
| `line_y` | `lineY` | `x`, `y` | `z` (series), `stroke`, `stroke_width`, `stroke_dasharray`, `opacity`, `points`, `curve`, `key`, `id` |
| `line_x` | `lineX` | `x`, `y` | same as `line_y` |
| `area_y` | `areaY` | `x`, (`y` \| `y1`+`y2`) | `z`, `fill`, `fill_opacity`, `stroke`, `curve`, `key`, `id` |
| `area_x` | `areaX` | `y`, (`x` \| `x1`+`x2`) | same as `area_y` |
| `bar_y` | `barY` | `x`, `y` | `z`, `fill`, `fill_opacity`, `stroke`, `inset`, `rx`, `key`, `id` |
| `bar_x` | `barX` | `y`, `x` | same as `bar_y` |
| `dot` | `dot` | `x`, `y` | `r` (number or field), `z`, `fill`, `stroke`, `stroke_width`, `opacity`, `symbol`, `key`, `id` |
| `rule_x` | `ruleX` | values or `x` | `stroke`, `stroke_width`, `stroke_dasharray`, `stroke_opacity`, `id` |
| `rule_y` | `ruleY` | values or `y` | same as `rule_x` |
| `text` | `text` | `x`, `y`, `text` | `fill`, `font_size`, `font_weight`, `dx`, `dy`, `text_anchor`, `key`, `id` |
| `tick_x` | `tickX` | `x` | `y`, `stroke`, `stroke_width`, `id` |
| `tick_y` | `tickY` | `y` | `x`, `stroke`, `stroke_width`, `id` |
| `cell` | `cell` | `x`, `y` | `color` (field), `inset`, `rx`, `key`, `id` |
| `pie` | `pie` (`@tanstack/charts/polar`) | `value` | `label` (field), `inner_radius` (donut), `outer_radius`, `pad_angle`, `corner_radius`, `fill`, `key`, `id` |

`curve` accepts only names from the catalog: `"linear" | "monotone-x" | "natural" |
"step" | "step-after" | "step-before" | "basis" | "catmull-rom"` (the bridge maps
them to `d3Curve(curveX)`).

**`fill`/`stroke` are literal CSS colors, never field names.** The data-driven
color channel is `color` (and `z` for series identity), which is painted with the
chart's `ColorSpec` scale — that is how TanStack 0.7.2 types it
(`RectOptions.fill?: string` vs. `color?: Channel<…>`). Fixed on 2026-08-08: this
table used to advertise `cell.fill` as "field or color", and passing a field name
emitted the literal as the SVG `fill` attribute (colorless heatmaps).

Helpers with literal data validate: the dataset is a list of homogeneous dicts;
every channel naming a field exists in the first record (REQ-CH-012); `datetime`/
`date` values are serialized to ISO-8601 and the field is marked in the dataset's
`temporal_fields` (REQ-CH-011).

### 2.3 `scale(type, **options) -> ScaleSpec` and `AxisSpec`

| `type` | JS origin | Serializable options |
|---|---|---|
| `linear` | `@tanstack/charts-scales/linear` | `domain: [min, max]`, `nice: bool` |
| `band` | `@tanstack/charts-scales/band` | `padding: float`, `domain: list` |
| `point` | `@tanstack/charts-scales/point` | `padding`, `domain` |
| `ordinal` | `@tanstack/charts-scales/ordinal` | `domain`, `range` (colors) |
| `utc` | `d3-scale scaleUtc` | `domain: [iso, iso]`, `nice` |
| `time` | `d3-scale scaleTime` | same as `utc` |
| `log` | `d3-scale scaleLog` | `base`, `domain`, `nice` |
| `sqrt` | `d3-scale scaleSqrt` | `domain`, `nice` |

`AxisSpec` (a dict, or kwargs of `axis(...)`):

```python
{
  "scale": ScaleSpec,          # optional; default: band if x is categorical, linear if numeric
  "label": "Frequency",        # optional
  "grid": True,                # optional, default False
  "nice": True,                # optional
  "ticks": {                   # optional
     "count": 5,
     "format": {"style": "percent", "maximum_fraction_digits": 1}
     #  declarative formats → Intl.NumberFormat / Intl.DateTimeFormat in the bridge
     #  styles: "decimal" | "percent" | "currency" (+"currency": "USD") | "compact"
     #  dates: {"date_style": "..."} or {"month": "short", "day": "numeric"}
  },
}
```

## 3. `ChartSpec` JSON contract (Python → bridge)

Produced by `tanstack_chart`; the field-by-field detail lives in the Data Model
(`specs/data-model/chartspec-schema.md`). General shape:

```json
{
  "version": 1,
  "marks": [
    {
      "type": "barY",
      "data": [{"letter": "E", "frequency": 0.127}],
      "temporal_fields": [],
      "options": {"x": "letter", "y": "frequency", "fill": "#4f46e5"}
    }
  ],
  "x": {"scale": {"type": "band", "padding": 0.18}},
  "y": {"scale": {"type": "linear"}, "nice": true, "grid": true,
        "axis": {"label": "Frequency",
                 "ticks": {"format": {"style": "percent"}}}},
  "color": null,
  "tooltip": true,
  "animate": false
}
```

**Versioning rule:** `version` is an integer; the bridge rejects (with an error
placeholder, REQ-CH-013) a `version` higher than the one it knows.

## 4. `TanStackChartBridge` bridge props (JSX)

| Prop | JS type | Description |
|---|---|---|
| `spec` | `object` | `ChartSpec` §3 |
| `height` | `number?` | px |
| `aspectRatio` | `number?` | alternative to height |
| `initialWidth` | `number?` | SSR |
| `ariaLabel` | `string?` | passed to `<Chart ariaLabel>` |
| `themeVars` | `object?` | inline style of the container |
| `onFocusChange` | `(payload) => void` | REQ-CH-008/010 |
| `onSelect` | `(payload) => void` | REQ-CH-009 |

## 5. Event payload (bridge → Reflex)

`on_focus_change` and `on_select` receive **one** positional argument:

```json
{
  "mark_id": "sales-line",
  "key": "2026-03",
  "x_value": "2026-03-01T00:00:00.000Z",
  "y_value": 1250.5,
  "datum": {"month": "2026-03-01T00:00:00.000Z", "revenue": 1250.5}
}
```

- Focus lost → `null` (REQ-CH-010).
- Sanitization: `Date` → ISO-8601, `undefined` → `null`, functions/non-plain
  objects removed (REQ-CH-011; PRD risk R2).
- Reflex handler signature: `def handle(self, point: dict | None)`.

## 6. Domain errors

| Code | Where | When | Behavior |
|---|---|---|---|
| `INVALID_MARKS` | Python | `marks` empty / invalid type | `ValueError` at construction |
| `UNKNOWN_FIELD` | Python | a channel references a non-existent field (literal data) | `ValueError` (REQ-CH-012) |
| `UNKNOWN_SCALE` | Python | scale type outside the catalog | `ValueError` |
| `UNSUPPORTED_MARK` | Bridge | `type` not registered | skips the mark + `console.warn` + visible notice (REQ-CH-013) |
| `SPEC_VERSION` | Bridge | `version` > supported | error placeholder |
| `RENDER_ERROR` | Bridge | `defineChart`/render throws | error boundary + placeholder (REQ-CH-015) |
| — | Bridge | empty dataset | renders without the mark, no exception (REQ-CH-014) |

## 7. Versioning

- Package: SemVer 0.x (`0.1.0` initial). Pre-1.0: a minor may break.
- `ChartSpec.version` only goes up with incompatible changes to the JSON contract.
- A `@tanstack/charts` bump → Delta Spec (Constitution Art. 4).

---

## Change History

| Version | Date | Changes |
|---|---|---|
| 1.0 | 2026-08-07 | Initial version |
