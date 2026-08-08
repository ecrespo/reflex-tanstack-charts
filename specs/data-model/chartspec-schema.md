# ChartSpec — Data Model Specification

## Metadata

| Campo | Valor |
|---|---|
| **Autor** | Ernesto Crespo |
| **Estado** | `DRAFT` |
| **Versión** | 1.0 (`ChartSpec.version = 1`) |
| **Fecha** | 2026-08-07 |
| **Base de Datos** | N/A — contrato JSON en memoria (prop de componente) |
| **Tech Design Relacionado** | `specs/technical/architecture.md` |

> Nota de adaptación: este proyecto no persiste datos. El "modelo de datos" es el
> **schema del `ChartSpec`**, el objeto JSON que cruza la frontera Python→JS. Es el
> contrato más crítico del sistema: todo campo del API Spec debe existir aquí.

---

## 1. Visión General del Modelo

Entidades: `ChartSpec` (raíz) → `MarkSpec[]` (cada una con dataset embebido,
mark-local data, DD-004) + `AxisSpec` (x, y) → `ScaleSpec` + `TicksSpec` +
`FormatSpec`. Del lado de eventos: `PointPayload` (bridge → Reflex).

### Diagrama de Relaciones

```
┌───────────┐ 1:N ┌───────────┐        ┌────────────┐
│ ChartSpec │────▶│  MarkSpec │        │PointPayload│  (evento, JS→Python)
└─────┬─────┘     │  .data[]  │        └────────────┘
      │ 1:2       └───────────┘
┌─────▼─────┐ 1:1 ┌───────────┐ 1:1 ┌────────────┐
│ AxisSpec  │────▶│ ScaleSpec │     │ FormatSpec │
│  (x, y)   │────▶│ TicksSpec │────▶└────────────┘
└───────────┘     └───────────┘
```

## 2. Schemas

### 2.1 `ChartSpec` (raíz)

```json
{
  "version": 1,
  "marks":   [ MarkSpec, "..." ],
  "x":       AxisSpec | null,
  "y":       AxisSpec | null,
  "color":   ColorSpec | null,
  "tooltip": false,
  "animate": false
}
```

| Campo | Tipo | Requerido | Default | Descripción |
|---|---|---|---|---|
| `version` | int | Sí | `1` | Versión del contrato; bridge rechaza > soportada |
| `marks` | `MarkSpec[]` | Sí (≥1) | — | REQ-CH-003 |
| `x`, `y` | `AxisSpec\|null` | No | `null` (inferencia TanStack) | REQ-CH-004 |
| `color` | `ColorSpec\|null` | No | `null` | escala de color/serie |
| `tooltip` | bool | No | `false` | REQ-CH-006 |
| `animate` | bool | No | `false` | REQ-CH-007 |

### 2.2 `MarkSpec`

```json
{
  "type": "barY",
  "data": [ {"letter": "E", "frequency": 0.127}, "..." ],
  "temporal_fields": ["date"],
  "options": { "x": "letter", "y": "frequency", "fill": "#4f46e5", "id": "freq-bars" }
}
```

| Campo | Tipo | Requerido | Descripción |
|---|---|---|---|
| `type` | string enum | Sí | Uno de: `lineY`, `lineX`, `areaY`, `areaX`, `barY`, `barX`, `dot`, `ruleX`, `ruleY`, `text`, `tickX`, `tickY`, `cell`, `pie` (nombres TanStack exactos, Art. 3) |
| `data` | `object[]` \| `number[]` | Sí | Registros homogéneos; `number[]` solo para `ruleX`/`ruleY` (valores de referencia) |
| `temporal_fields` | `string[]` | Sí (puede ser `[]`) | Campos a rehidratar `new Date(iso)` en el bridge (REQ-CH-011) |
| `options` | object | Sí | Canales y estilos serializables por marca (catálogo en API Spec §2.2); claves en camelCase JS (`strokeWidth`), convertidas desde snake_case por el helper |

**Invariantes de `options` (validadas en Python, REQ-CH-012):**
- Todo canal que nombre un campo (`x`, `y`, `y1`, `y2`, `z`, `color`, `r` si string, `text`, `value`, `label`, `key`) debe existir en `data[0]`.
- `fill` y `stroke` **no** son canales: en TanStack 0.7.2 son colores CSS literales. Para colorear por datos se usa `color` (o `z`) con la escala de `ColorSpec`.
- `curve` ∈ `{"linear","monotone-x","natural","step","step-after","step-before","basis","catmull-rom"}`.
- `id` string opcional; recomendado para trazar eventos (`PointPayload.mark_id`).

### 2.3 `AxisSpec`

```json
{
  "scale": { "type": "linear", "domain": [0, 100], "nice": true },
  "nice": true,
  "grid": true,
  "axis": {
    "label": "Close (USD)",
    "ticks": { "count": 5, "format": { "style": "percent", "maximum_fraction_digits": 1 } }
  }
}
```

### 2.4 `ScaleSpec`

| Campo | Tipo | Aplica a | Notas |
|---|---|---|---|
| `type` | enum `linear\|band\|point\|ordinal\|utc\|time\|log\|sqrt` | todas | REQ-CH-004 |
| `domain` | `[number,number]` \| `string[]` \| `[iso,iso]` | opc. | ISO-8601 si `utc`/`time` (se rehidrata) |
| `nice` | bool | continuas | — |
| `padding` | float 0..1 | `band`/`point` | default TanStack 0 / band 0.18 recomendado |
| `range` | `string[]` (colores) | `ordinal` en `color` | — |
| `base` | number | `log` | default 10 |

### 2.5 `FormatSpec` (ticks declarativos, DD-003)

Números → `Intl.NumberFormat`:

| Campo | Valores |
|---|---|
| `style` | `"decimal" \| "percent" \| "currency" \| "compact"` (`compact` = decimal + `notation:"compact"`) |
| `currency` | ISO 4217, requerido si `style="currency"` |
| `maximum_fraction_digits`, `minimum_fraction_digits` | int 0..20 |
| `locale` | BCP-47, default `"en-US"` |

Fechas (campo temporal) → `Intl.DateTimeFormat`: `locale`, `date_style` o
combinación `year/month/day/hour/minute` (valores estándar Intl), `time_zone`
(default `"UTC"`).

### 2.6 `ColorSpec`

```json
{ "scale": { "type": "ordinal", "domain": ["SMB", "Growth"], "range": ["#0ea5e9", "#f97316"] } }
```

*(Campo `legend` retirado del contrato v1 — Analyze A-06; re-añadible de forma aditiva.)*

### 2.7 `PointPayload` (evento JS → Python; API Spec §5)

| Campo | Tipo | Nullable | Descripción |
|---|---|---|---|
| `mark_id` | string | Sí | `options.id` de la marca origen |
| `key` | string \| number | Sí | key estable del punto |
| `x_value` | number \| string | Sí | ISO-8601 si temporal |
| `y_value` | number \| string | Sí | — |
| `datum` | object plano | Sí | registro original sanitizado (Date→ISO, undefined→null, no-planos eliminados) |

Payload completo `null` cuando el foco se pierde (REQ-CH-010).

## 3. Reglas de Serialización (Python → JSON)

| Tipo Python | JSON | Regla |
|---|---|---|
| `datetime` / `date` | string ISO-8601 (UTC si naive → se asume UTC y se documenta) | campo se añade a `temporal_fields` |
| `Decimal` | number (float) | pérdida de precisión aceptada: son coordenadas visuales, no dinero persistido — excepción justificada al patrón "dinero en Decimal" del checklist |
| `int`, `float` | number | `NaN`/`inf` → `ValueError` (no serializables) |
| `None` | null | canal ausente ≠ null: los helpers omiten claves None |
| snake_case (Python) | camelCase (JS) en `options` | conversión en el helper, tabla fija |

## 4. Queries Críticas → Accesos críticos del bridge

(Adaptación: no hay DB; estos son los caminos calientes del intérprete.)

| Acceso | Estructura | Target |
|---|---|---|
| `MARK_REGISTRY[type]` | objeto plano JS | O(1) |
| Rehidratación temporal | recorre `data` × `temporal_fields` | O(n·t), solo si `temporal_fields ≠ []` |
| `useMemo` del definition | identidad del prop `spec` | recompute solo al cambiar estado |

## 5. Migración de Datos

Sin datos persistidos. Migración = evolución del contrato:
- Cambios aditivos (campo opcional nuevo) → misma `version`.
- Cambios incompatibles → `version + 1`; el bridge mantiene el intérprete de la versión anterior durante ≥1 minor del paquete.
- Snapshots de `tests/test_spec_contract.py` son el mecanismo de detección de ruptura accidental.

## 6. Estrategias de Archivado / 7. Backup
N/A (sin persistencia).

---

## Constitution check
- Art. 2 (frontera serializable): todo el schema es JSON puro; fechas ISO-8601. ✓
- Excepción justificada al patrón "dinero en Decimal" del checklist Analyze: `Decimal`→float
  es aceptable porque los valores son coordenadas visuales, no montos persistidos ni
  transaccionales (Analyze A-08). ✓

## Historial de Cambios

| Versión | Fecha | Autor | Cambios |
|---|---|---|---|
| 1.0 | 2026-08-07 | Ernesto Crespo | Versión inicial |
| 1.1 | 2026-08-07 | Ernesto Crespo | A-06: retirado `ColorSpec.legend`; A-08: constitution check |
