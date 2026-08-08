# reflex-tanstack-charts — API Specification (Component API)

## Metadata

| Campo | Valor |
|---|---|
| **Autor** | Ernesto Crespo |
| **Estado** | `DRAFT` |
| **Versión API** | v1.0 (paquete 0.1.0) |
| **Fecha** | 2026-08-07 |
| **PRD Relacionado** | `specs/prd/reflex-tanstack-charts.md` |
| **Superficie** | API Python pública + contrato JSON `ChartSpec` + props del bridge JSX |

> Nota de adaptación: este proyecto no expone HTTP. El "API" son tres contratos
> acoplados: (1) la API Python importable, (2) el `ChartSpec` JSON que viaja
> Python→JS, (3) las props/eventos del componente bridge. Los tres se versionan juntos.

---

## 1. Visión General

Consumidores: apps Reflex (humanos y agentes). Todo lo público se importa desde el
paquete raíz:

```python
from reflex_tanstack_charts import (
    tanstack_chart,          # componente
    line_y, line_x, area_y, area_x, bar_y, bar_x,
    dot, rule_x, rule_y, text, tick_x, tick_y, cell, pie,   # marcas (14)
    scale,                   # constructor de escalas
)
```

## 2. API Python

### 2.1 `tanstack_chart(...) -> rx.Component`

| Parámetro | Tipo Python | Requerido | Default | Descripción |
|---|---|---|---|---|
| `marks` | `list[Mark \| rx.Var]` | Sí | — | Lista de marcas (dicts producidos por los helpers §2.2) |
| `x` | `AxisSpec \| None` | No | inferida | Config del eje/escala X (§2.3) |
| `y` | `AxisSpec \| None` | No | inferida | Config del eje/escala Y |
| `color` | `dict \| None` | No | `None` | Escala de color (`{"scheme": [...]}` u `ordinal`) |
| `height` | `int \| rx.Var[int]` | No | `320` | Alto fijo en px (REQ-CH-016) |
| `aspect_ratio` | `float \| None` | No | `None` | Alternativa a `height` |
| `initial_width` | `int \| None` | No | `None` | Ancho SSR con `aspect_ratio` |
| `aria_label` | `str` | Recomendado | `None` (warn) | REQ-CH-017 |
| `tooltip` | `bool` | No | `False` | REQ-CH-006 |
| `animate` | `bool` | No | `False` | REQ-CH-007 |
| `theme` | `dict[str, str] \| None` | No | `None` | Vars CSS `--ts-chart-*` (REQ-CH-018) |
| `on_focus_change` | `rx.EventHandler` | No | — | REQ-CH-008/010 |
| `on_select` | `rx.EventHandler` | No | — | REQ-CH-009 |

**Validaciones (fail-fast en Python):**

| Regla | Error si falla |
|---|---|
| `marks` no vacía y cada item es `Mark` válido o Var | `ValueError("marks must be a non-empty list…")` |
| `height` > 0; `aspect_ratio` > 0; no ambos explícitos | `ValueError` |
| Tipo de escala ∈ catálogo §2.3 | `ValueError` con tipos válidos listados |

### 2.2 Helpers de marcas (14 MUST)

Firma común: `mark(data, **channels) -> Mark` donde `data` es
`list[dict] | rx.Var`. Con `rx.Var` la validación de campos se difiere al bridge
(REQ-CH-012 aplica solo a datos literales).

| Helper | Marca TanStack | Canales requeridos | Canales opcionales (serializables) |
|---|---|---|---|
| `line_y` | `lineY` | `x`, `y` | `z` (serie), `stroke`, `stroke_width`, `stroke_dasharray`, `opacity`, `points`, `curve`, `key`, `id` |
| `line_x` | `lineX` | `x`, `y` | ídem `line_y` |
| `area_y` | `areaY` | `x`, (`y` \| `y1`+`y2`) | `z`, `fill`, `fill_opacity`, `stroke`, `curve`, `key`, `id` |
| `area_x` | `areaX` | `y`, (`x` \| `x1`+`x2`) | ídem `area_y` |
| `bar_y` | `barY` | `x`, `y` | `z`, `fill`, `fill_opacity`, `stroke`, `inset`, `rx`, `key`, `id` |
| `bar_x` | `barX` | `y`, `x` | ídem `bar_y` |
| `dot` | `dot` | `x`, `y` | `r` (número o campo), `z`, `fill`, `stroke`, `stroke_width`, `opacity`, `symbol`, `key`, `id` |
| `rule_x` | `ruleX` | valores o `x` | `stroke`, `stroke_width`, `stroke_dasharray`, `stroke_opacity`, `id` |
| `rule_y` | `ruleY` | valores o `y` | ídem `rule_x` |
| `text` | `text` | `x`, `y`, `text` | `fill`, `font_size`, `font_weight`, `dx`, `dy`, `text_anchor`, `key`, `id` |
| `tick_x` | `tickX` | `x` | `y`, `stroke`, `stroke_width`, `id` |
| `tick_y` | `tickY` | `y` | `x`, `stroke`, `stroke_width`, `id` |
| `cell` | `cell` | `x`, `y` | `color` (campo), `inset`, `rx`, `key`, `id` |
| `pie` | `pie` (`@tanstack/charts/polar`) | `value` | `label` (campo), `inner_radius` (donut), `outer_radius`, `pad_angle`, `corner_radius`, `fill`, `key`, `id` |

`curve` acepta solo nombres del catálogo: `"linear" | "monotone-x" | "natural" |
"step" | "step-after" | "step-before" | "basis" | "catmull-rom"` (el bridge los
mapea a `d3Curve(curveX)`).

**`fill`/`stroke` son colores CSS literales, nunca nombres de campo.** El canal de
color dirigido por datos es `color` (y `z` para identidad de serie), que se pinta
con la escala de `ColorSpec` del gráfico — así lo tipa TanStack 0.7.2
(`RectOptions.fill?: string` vs. `color?: Channel<…>`). Corregido el 2026-08-08:
esta tabla anunciaba `cell.fill` como «campo o color», y pasar un nombre de campo
emitía el literal como atributo SVG `fill` (heatmaps sin color).

Los helpers con datos literales validan: dataset es lista de dicts homogéneos; todo
canal que nombre un campo existe en el primer registro (REQ-CH-012); los valores
`datetime`/`date` se serializan ISO-8601 y se marca el campo en
`temporal_fields` del dataset (REQ-CH-011).

### 2.3 `scale(type, **options) -> ScaleSpec` y `AxisSpec`

| `type` | Origen JS | Opciones serializables |
|---|---|---|
| `linear` | `@tanstack/charts-scales/linear` | `domain: [min, max]`, `nice: bool` |
| `band` | `@tanstack/charts-scales/band` | `padding: float`, `domain: list` |
| `point` | `@tanstack/charts-scales/point` | `padding`, `domain` |
| `ordinal` | `@tanstack/charts-scales/ordinal` | `domain`, `range` (colores) |
| `utc` | `d3-scale scaleUtc` | `domain: [iso, iso]`, `nice` |
| `time` | `d3-scale scaleTime` | ídem `utc` |
| `log` | `d3-scale scaleLog` | `base`, `domain`, `nice` |
| `sqrt` | `d3-scale scaleSqrt` | `domain`, `nice` |

`AxisSpec` (dict o kwargs de `axis(...)`):

```python
{
  "scale": ScaleSpec,          # opcional; default: banda si x categórico, linear si numérico
  "label": "Frequency",        # opcional
  "grid": True,                # opcional, default False
  "nice": True,                # opcional
  "ticks": {                   # opcional
     "count": 5,
     "format": {"style": "percent", "maximum_fraction_digits": 1}
     #  formatos declarativos → Intl.NumberFormat / Intl.DateTimeFormat en el bridge
     #  styles: "decimal" | "percent" | "currency" (+"currency": "USD") | "compact"
     #  fechas: {"date_style": "..."} o {"month": "short", "day": "numeric"}
  },
}
```

## 3. Contrato JSON `ChartSpec` (Python → bridge)

Producido por `tanstack_chart`; el detalle campo a campo vive en el Data Model
(`specs/data-model/chartspec-schema.md`). Forma general:

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

**Regla de versionado:** `version` entero; el bridge rechaza (placeholder de error,
REQ-CH-013) un `version` mayor al que conoce.

## 4. Props del bridge `TanStackChartBridge` (JSX)

| Prop | Tipo JS | Descripción |
|---|---|---|
| `spec` | `object` | `ChartSpec` §3 |
| `height` | `number?` | px |
| `aspectRatio` | `number?` | alternativa a height |
| `initialWidth` | `number?` | SSR |
| `ariaLabel` | `string?` | pasa a `<Chart ariaLabel>` |
| `themeVars` | `object?` | estilo inline del contenedor |
| `onFocusChange` | `(payload) => void` | REQ-CH-008/010 |
| `onSelect` | `(payload) => void` | REQ-CH-009 |

## 5. Payload de eventos (bridge → Reflex)

`on_focus_change` y `on_select` reciben **un** argumento posicional:

```json
{
  "mark_id": "sales-line",
  "key": "2026-03",
  "x_value": "2026-03-01T00:00:00.000Z",
  "y_value": 1250.5,
  "datum": {"month": "2026-03-01T00:00:00.000Z", "revenue": 1250.5}
}
```

- Foco perdido → `null` (REQ-CH-010).
- Sanitización: `Date` → ISO-8601, `undefined` → `null`, funciones/objetos no
  planos eliminados (REQ-CH-011; riesgo R2 del PRD).
- Firma del handler Reflex: `def handle(self, point: dict | None)`.

## 6. Errores del dominio

| Código | Dónde | Cuándo | Comportamiento |
|---|---|---|---|
| `INVALID_MARKS` | Python | `marks` vacía / tipo inválido | `ValueError` en construcción |
| `UNKNOWN_FIELD` | Python | canal referencia campo inexistente (datos literales) | `ValueError` (REQ-CH-012) |
| `UNKNOWN_SCALE` | Python | tipo de escala fuera de catálogo | `ValueError` |
| `UNSUPPORTED_MARK` | Bridge | `type` no registrado | omite marca + `console.warn` + aviso visible (REQ-CH-013) |
| `SPEC_VERSION` | Bridge | `version` > soportada | placeholder de error |
| `RENDER_ERROR` | Bridge | `defineChart`/render lanza | error boundary + placeholder (REQ-CH-015) |
| — | Bridge | dataset vacío | render sin la marca, sin excepción (REQ-CH-014) |

## 7. Versionado

- Paquete: SemVer 0.x (`0.1.0` inicial). Pre-1.0: minor puede romper.
- `ChartSpec.version` sube solo con cambios incompatibles del contrato JSON.
- Bump de `@tanstack/charts` → Delta Spec (Constitución Art. 4).

---

## Historial de Cambios

| Versión | Fecha | Cambios |
|---|---|---|
| 1.0 | 2026-08-07 | Versión inicial |
