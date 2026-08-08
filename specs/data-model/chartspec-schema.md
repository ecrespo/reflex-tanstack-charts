# ChartSpec — Data Model Specification

## Metadata

| Field | Value |
|---|---|
| **Author** | Ernesto Crespo |
| **Status** | `DRAFT` |
| **Version** | 1.0 (`ChartSpec.version = 1`) |
| **Date** | 2026-08-07 |
| **Database** | N/A — in-memory JSON contract (component prop) |
| **Related Tech Design** | `specs/technical/architecture.md` |

> Adaptation note: this project does not persist data. The "data model" is the
> **`ChartSpec` schema**, the JSON object that crosses the Python→JS boundary. It is
> the most critical contract in the system: every API Spec field must exist here.

---

## 1. Model Overview

Entities: `ChartSpec` (root) → `MarkSpec[]` (each with an embedded dataset,
mark-local data, DD-004) + `AxisSpec` (x, y) → `ScaleSpec` + `TicksSpec` +
`FormatSpec`. On the event side: `PointPayload` (bridge → Reflex).

### Relationship Diagram

```
┌───────────┐ 1:N ┌───────────┐        ┌────────────┐
│ ChartSpec │────▶│  MarkSpec │        │PointPayload│  (event, JS→Python)
└─────┬─────┘     │  .data[]  │        └────────────┘
      │ 1:2       └───────────┘
┌─────▼─────┐ 1:1 ┌───────────┐ 1:1 ┌────────────┐
│ AxisSpec  │────▶│ ScaleSpec │     │ FormatSpec │
│  (x, y)   │────▶│ TicksSpec │────▶└────────────┘
└───────────┘     └───────────┘
```

## 2. Schemas

### 2.1 `ChartSpec` (root)

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

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `version` | int | Yes | `1` | Contract version; the bridge rejects anything > supported |
| `marks` | `MarkSpec[]` | Yes (≥1) | — | REQ-CH-003 |
| `x`, `y` | `AxisSpec\|null` | No | `null` (TanStack inference) | REQ-CH-004 |
| `color` | `ColorSpec\|null` | No | `null` | color/series scale |
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

| Field | Type | Required | Description |
|---|---|---|---|
| `type` | string enum | Yes | One of: `lineY`, `lineX`, `areaY`, `areaX`, `barY`, `barX`, `dot`, `ruleX`, `ruleY`, `text`, `tickX`, `tickY`, `cell`, `pie` (exact TanStack names, Art. 3) |
| `data` | `object[]` \| `number[]` | Yes | Homogeneous records; `number[]` only for `ruleX`/`ruleY` (reference values) |
| `temporal_fields` | `string[]` | Yes (may be `[]`) | Fields to rehydrate with `new Date(iso)` in the bridge (REQ-CH-011) |
| `options` | object | Yes | Serializable per-mark channels and styles (catalog in API Spec §2.2); keys in JS camelCase (`strokeWidth`), converted from snake_case by the helper |

**`options` invariants (validated in Python, REQ-CH-012):**
- Every channel naming a field (`x`, `y`, `y1`, `y2`, `z`, `color`, `r` if a string, `text`, `value`, `label`, `key`) must exist in `data[0]`.
- `fill` and `stroke` are **not** channels: in TanStack 0.7.2 they are literal CSS colors. To color by data, use `color` (or `z`) with the `ColorSpec` scale.
- `curve` ∈ `{"linear","monotone-x","natural","step","step-after","step-before","basis","catmull-rom"}`.
- `id` optional string; recommended for tracing events (`PointPayload.mark_id`).

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

| Field | Type | Applies to | Notes |
|---|---|---|---|
| `type` | enum `linear\|band\|point\|ordinal\|utc\|time\|log\|sqrt` | all | REQ-CH-004 |
| `domain` | `[number,number]` \| `string[]` \| `[iso,iso]` | opt. | ISO-8601 if `utc`/`time` (rehydrated) |
| `nice` | bool | continuous | — |
| `padding` | float 0..1 | `band`/`point` | TanStack default 0 / band 0.18 recommended |
| `range` | `string[]` (colors) | `ordinal` in `color` | — |
| `base` | number | `log` | default 10 |

### 2.5 `FormatSpec` (declarative ticks, DD-003)

Numbers → `Intl.NumberFormat`:

| Field | Values |
|---|---|
| `style` | `"decimal" \| "percent" \| "currency" \| "compact"` (`compact` = decimal + `notation:"compact"`) |
| `currency` | ISO 4217, required if `style="currency"` |
| `maximum_fraction_digits`, `minimum_fraction_digits` | int 0..20 |
| `locale` | BCP-47, default `"en-US"` |

Dates (temporal field) → `Intl.DateTimeFormat`: `locale`, `date_style` or a
`year/month/day/hour/minute` combination (standard Intl values), `time_zone`
(default `"UTC"`).

### 2.6 `ColorSpec`

```json
{ "scale": { "type": "ordinal", "domain": ["SMB", "Growth"], "range": ["#0ea5e9", "#f97316"] } }
```

*(The `legend` field was removed from the v1 contract — Analyze A-06; it can be re-added additively.)*

### 2.7 `PointPayload` (JS → Python event; API Spec §5)

| Field | Type | Nullable | Description |
|---|---|---|---|
| `mark_id` | string | Yes | `options.id` of the originating mark |
| `key` | string \| number | Yes | stable key of the point |
| `x_value` | number \| string | Yes | ISO-8601 if temporal |
| `y_value` | number \| string | Yes | — |
| `datum` | plain object | Yes | sanitized original record (Date→ISO, undefined→null, non-plain values removed) |

The whole payload is `null` when focus is lost (REQ-CH-010).

## 3. Serialization Rules (Python → JSON)

| Python type | JSON | Rule |
|---|---|---|
| `datetime` / `date` | ISO-8601 string (UTC if naive → UTC is assumed and documented) | the field is added to `temporal_fields` |
| `Decimal` | number (float) | accepted precision loss: these are visual coordinates, not persisted money — a justified exception to the checklist's "money in Decimal" pattern |
| `int`, `float` | number | `NaN`/`inf` → `ValueError` (not serializable) |
| `None` | null | an absent channel ≠ null: the helpers omit None keys |
| snake_case (Python) | camelCase (JS) in `options` | conversion in the helper, fixed table |

## 4. Critical Queries → Critical bridge accesses

(Adaptation: there is no DB; these are the interpreter's hot paths.)

| Access | Structure | Target |
|---|---|---|
| `MARK_REGISTRY[type]` | plain JS object | O(1) |
| Temporal rehydration | walks `data` × `temporal_fields` | O(n·t), only if `temporal_fields ≠ []` |
| `useMemo` of the definition | identity of the `spec` prop | recomputes only when the state changes |

## 5. Data Migration

No persisted data. Migration = contract evolution:
- Additive changes (a new optional field) → same `version`.
- Incompatible changes → `version + 1`; the bridge keeps the previous version's interpreter for ≥1 package minor.
- The snapshots in `tests/test_spec_contract.py` are the mechanism for detecting accidental breakage.

## 6. Archiving Strategies / 7. Backup
N/A (no persistence).

---

## Constitution check
- Art. 2 (serializable boundary): the whole schema is pure JSON; dates in ISO-8601. ✓
- Justified exception to the Analyze checklist's "money in Decimal" pattern: `Decimal`→float
  is acceptable because the values are visual coordinates, not persisted or transactional
  amounts (Analyze A-08). ✓

## Change History

| Version | Date | Author | Changes |
|---|---|---|---|
| 1.0 | 2026-08-07 | Ernesto Crespo | Initial version |
| 1.1 | 2026-08-07 | Ernesto Crespo | A-06: removed `ColorSpec.legend`; A-08: constitution check |
