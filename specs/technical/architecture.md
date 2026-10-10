# reflex-tanstack-charts — Technical Design Document

## Metadata

| Field | Value |
|---|---|
| **Author** | Ernesto Crespo |
| **Status** | `DRAFT` |
| **Version** | 1.0 |
| **Date** | 2026-08-07 |
| **Related PRD** | `specs/prd/reflex-tanstack-charts.md` |
| **Related API Spec** | `specs/api/component-api-v1.md` |

---

## 1. Context

TanStack Charts exposes its API as JS calls (`defineChart({ marks: [barY(data,
{...})], x: { scale: scaleBand }, ... })`) with factories and closures — **not
serializable**. Reflex, on the other hand, compiles Python to React by passing
serializable props. The bridge between both worlds is the heart of the design: a
local React component (`TanStackChartBridge.jsx`, shipped in the package via
`rx.asset(shared=True)` and referenced with `library="$/public/..."`) that receives
a JSON `ChartSpec` and **interprets** it against a static registry of marks and
scales imported from `@tanstack/charts*`.

It is built as an official Reflex custom component (`reflex component init`
layout), publishable on PyPI with uv.

## 2. Technical Goals

- **Correctness:** the ChartSpec renders exactly the equivalent TanStack definition; compilation tests per mark.
- **Performance:** memoization by spec identity; bundle ≤ ~35 KiB gzip added.
- **Maintainability:** the mark registry is a single dict; adding a new mark ≈ 5 lines of JS + a Python helper + a test.
- **Robustness:** no invalid input breaks the page (error boundary + placeholders).

## 3. Proposed Architecture

### 3.1 High-level diagram

```
┌────────────────────────────┐ compiles ┌──────────────────────────────┐
│  Reflex app (Python)       │ ───────▶ │  React frontend (.web)       │
│                            │          │                              │
│ tanstack_chart(            │  JSON    │  <TanStackChartBridge        │
│   marks=[bar_y(data,…)],   │  props   │     spec={…}                 │
│   y=axis(grid=True),       │ ───────▶ │     onFocusChange={…}/>      │
│   on_select=State.pick)    │          │      │ interprets            │
└────────────┬───────────────┘          │      ▼                       │
             │ events (payload §5 API)  │  MARK_REGISTRY / SCALES      │
             ◀──────────────────────────│  defineChart + useMemo       │
   State.pick(point) in Python          │      │                       │
                                        │      ▼                       │
                                        │  <Chart> @tanstack/          │
                                        │   react-charts (SVG)         │
                                        └──────────────────────────────┘
```

### 3.2 Components

| Component | Technology | Responsibility |
|---|---|---|
| `TanStackChart(rx.Component)` | Python / Reflex | Declare props (`spec`, `height`, …), `library="$/public"+rx.asset("TanStackChartBridge.jsx", shared=True)`, `tag="TanStackChartBridge"`, EventHandlers |
| Mark helpers (`marks.py`) | Python | Build/validate mark dicts (REQ-CH-012), serialize datetimes, mark `temporal_fields` |
| `scales.py` / `axis.py` | Python | `scale()`, `axis()`, catalog validation |
| `TanStackChartBridge.jsx` | React 19 + `@tanstack/*` | Interpret spec → `defineChart`; registry of marks/scales/curves/formats; error boundary; sanitize event payloads |
| Demo app | Reflex | Gallery of the 14 marks + reactivity + events |

### 3.3 Data Flow

**Flow: initial render**

```
1. The user calls tanstack_chart(marks=[...], ...) on a Reflex page
2. Helpers validate (fail-fast) and produce a ChartSpec dict
3. Reflex serializes the spec as a prop (rx.Var if state is involved)
4. Bridge mounts: useMemo(spec) → buildDefinition(spec)
   a. for each mark: MARK_REGISTRY[type](rehydrate(data), mapOptions(options))
   b. rehydrate: temporal_fields → new Date(iso)
   c. axes: SCALE_REGISTRY[scale.type](options), formats → Intl.*Format
   d. tooltip=true → adds the tooltip from @tanstack/charts/tooltip
5. <Chart definition height ariaLabel onFocusChange onSelect/> renders the SVG
```

**Flow: reactive update (REQ-CH-005)**

```
1. A Python event mutates State.data → Reflex re-renders with a new spec prop
2. The spec identity changes → useMemo recomputes the definition → Chart re-renders
   (with animate=true, TanStack's interruptible transition)
```

**Error / degradation flow**

```
1. Unknown mark → skipped, console.warn, overlay "mark X unsupported"          (REQ-CH-013)
2. Empty dataset → mark skipped silently                                       (REQ-CH-014)
3. Throw in defineChart/render → ErrorBoundary → placeholder with the message   (REQ-CH-015)
4. spec.version > supported → placeholder "update reflex-tanstack-charts"
```

## 4. Design Decisions

### DD-001: Interpreter bridge with a static registry (vs. generating JS code)

- **Decision:** a single JSX file that interprets a JSON ChartSpec against static mark/scale registries.
- **Context:** `defineChart` requires JS factories; Reflex only passes serializable props.
- **Alternatives evaluated:**

| Option | Pros | Cons |
|---|---|---|
| **A (chosen): interpreter bridge + registry** | Serializable, safe (no eval), testable, controlled tree-shaking, agent-friendly | Surface limited to what is registered |
| B: generate JS code per chart (`rx.Var` strings / custom_code) | Full TanStack surface | Code injection, impossible to validate, fragile at compile time |
| C: 1:1 wrapper of each mark as a Reflex component | Idiomatic Reflex | `defineChart` is not composable JSX; marks are not React components |

- **Justification:** the only option that satisfies Constitution Art. 2 and serves the agent use case (US-004).
- **Consequences:** each new mark requires touching the JS registry + a Python helper (cheap, ~5 lines on each side).

### DD-002: Static imports of all MUST marks (vs. dynamic import)

- **Decision:** the bridge statically imports `barY, lineY, … , pie` and the 4 compact scales + 4 from d3-scale.
- **Context:** tree-shaking removes unused code only with statically analyzable imports; dynamic import complicates Reflex SSR.
- **Justification:** the 14 core marks are small (the full 12-chart package ≈ 26-32 KiB gzip); simplicity > micro-optimization.
- **Consequences:** a fixed bundle even if the app uses 1 mark; acceptable against the NFR (≤ ~35 KiB).

### DD-003: Declarative tick formats via Intl (vs. functions)

- **Decision:** `ticks.format` is an options object for `Intl.NumberFormat` / `Intl.DateTimeFormat`, never a function.
- **Justification:** serializable (Art. 2), covers percent/currency/compact/dates — 95% of the cases in the TanStack catalog.
- **Consequences:** exotic formats will require a future catalog extension (Delta).

### DD-004: Per-mark data (mark-local data), no named shared datasets

- **Decision:** each mark carries its own embedded `data`, just like the TanStack grammar (mark-local data).
- **Alternative:** a `datasets` section with references by name — less duplication if several marks share data.
- **Justification:** 1:1 parity with TanStack (Art. 3); JSON duplication between marks is rare and cheap. Revisitable through a Delta if real pain shows up.

### DD-005: Events with a single sanitized dict argument

- **Decision:** `on_focus_change`/`on_select` emit a single dict (or None) already sanitized in JS.
- **Context:** Reflex event triggers declare serializable argument specs; `point.datum` may contain a `Date`.
- **Justification:** a stable and simple contract for Python handlers (`point: dict | None`).

## 5. Patterns and Conventions

### 5.1 Code Structure (Reflex custom component layout)

```
reflex-tanstack-charts/
├── pyproject.toml                  # hatchling/uv_build; deps: reflex>=0.8
├── README.md
├── LICENSE                          # Apache-2.0
├── specs/                           # SDD (this directory)
├── custom_components/
│   └── reflex_tanstack_charts/
│       ├── __init__.py              # re-exports the public API from API Spec §2.1
│       ├── component.py             # TanStackChart(rx.Component) + tanstack_chart()
│       ├── marks.py                 # 14 helpers + _Mark base + validation
│       ├── scales.py                # scale(), catalog, validation
│       ├── axis.py                  # axis(), declarative formats
│       ├── _serialize.py            # datetime→ISO, temporal_fields detection
│       └── TanStackChartBridge.jsx  # bridge (next to the .py, local components pattern)
├── tanstack_charts_demo/            # Reflex demo app (gallery)
│   ├── rxconfig.py
│   └── tanstack_charts_demo/tanstack_charts_demo.py
└── tests/
    ├── test_marks.py                # validation and serialization per mark
    ├── test_scales_axis.py
    ├── test_component.py            # the component compiles; correct props
    └── test_spec_contract.py        # ChartSpec snapshots (v1 contract)
```

### 5.2 Applied Patterns

| Pattern | Where | Why |
|---|---|---|
| Registry | bridge (`MARK_REGISTRY`, `SCALE_REGISTRY`, `CURVES`, formats) | dispatch by name without eval |
| Builder + fail-fast validation | Python helpers | errors in the layer where the user sees them (REQ-CH-012) |
| Error Boundary | bridge | REQ-CH-015 |
| Snapshot testing | `test_spec_contract.py` | freezes the JSON v1 contract |

### 5.3 Error Handling

```python
# Python: ValueError with actionable messages (error code from API Spec §6)
raise ValueError(
    "[reflex-tanstack-charts] UNKNOWN_FIELD: channel x='letters' "
    "not found in dataset fields ['letter', 'frequency']"
)
```

```jsx
// JS: never throw towards the app; shared prefix in the console
console.warn("[reflex-tanstack-charts] UNSUPPORTED_MARK:", mark.type)
```

## 6. Security

### 6.1 Attack Surface

| Vector | Mitigation |
|---|---|
| JS injection via the spec | No eval/new Function; dispatch through the registry only (DD-001) |
| XSS via data values in `text`/tooltip | TanStack renders text as SVG text nodes, not innerHTML; the bridge never uses dangerouslySetInnerHTML |
| Compromised npm dependency | Exact pinned versions (Art. 4) |
| Event payload with malicious nested objects | Sanitizer: plain JSON types only |

### 6.2 Sensitive Data
Not applicable: the library does not persist or transmit data of its own; user data
travels over the standard Reflex channel (the app's own websocket).

## 7. Observability

- Browser console: warnings/errors prefixed with `[reflex-tanstack-charts]` (PRD §7 requirement).
- Dev backend: warning if `aria_label` is missing (REQ-CH-017).
- No metrics/telemetry of our own (a library, not a service).

## 8. Testing Strategy

| Level | Coverage target | Tools | What it covers |
|---|---|---|---|
| Unit (Python) | > 85% of `marks/scales/axis/_serialize` | pytest | REQ-CH-012 validations, REQ-CH-011 serialization, REQ-CH-004 catalog |
| Contract | 14 marks × snapshot | pytest + JSON snapshots | stable ChartSpec v1 (REQ-CH-003) |
| Component | compiles | pytest + `app._compile()` / page render | REQ-CH-001, declared props and events (REQ-CH-008/009) |
| Manual/CI E2E | the demo compiles and starts | `reflex export` of the demo | the bridge + npm deps resolve (risk R4) |

Every test cites its REQ in the name or docstring (Constitution Art. 6):
`test_req_ch_012_unknown_field_raises`.

## 9. Migration / Rollout Plan

- Greenfield project: no migration.
- Rollout: `0.1.0a1` (TestPyPI) → validate installation in a clean app → `0.1.0` on PyPI → `reflex component share`.
- Backward compatibility: `ChartSpec.version` governs the contract (API Spec §7).

## 10. Open Questions

- [x] 2026-08-07 — npm versions verified in the registry: `@tanstack/charts@0.7.2`, `@tanstack/react-charts@0.7.2`, `@tanstack/charts-scales@0.7.2`, `d3-scale@4.0.2`, `d3-shape@3.2.0` (curves). react-charts peer deps: react ^19.
- [x] 2026-08-07 — Confirmed with the installed package: `pie` is exported from `@tanstack/charts/polar`; `tooltip` from `@tanstack/charts/tooltip`; the root exports `defineChart`, `barY`…`cell`, `text`, `d3Curve`.
- [x] 2026-10-10 — Upgraded to `@tanstack/charts@1.1.0`; `charts-scales` folded into `@tanstack/charts/scales/*` (see `changes/2026-10-10-tanstack-charts-1.1/delta-spec.md` and finding 5).
- [ ] Is 0.8 the minimum Reflex version with a stable `rx.asset(shared=True)`? Confirm in T-001 with the installed version.

## 11. Implementation Findings (2026-08-07, folded back from execution)

1. **Scales are mandatory in 0.7.2.** The published version of `@tanstack/charts`
   (0.7.2) requires a configured scale per axis for every cartesian mark (the docs
   track `main`, which does infer them). The bridge implements the inference that
   API Spec §2.3 already promised as the default: sample the first value of the
   axis channel → `Date`/temporal → `scaleUtc`; number → `scaleLinear`; string →
   `scaleBand` (if there is a `barY/barX/cell` on that axis) or `scalePoint`. Axes
   with no channel (strip plots with only `tickX`/`ruleX`) → `scaleLinear` with
   domain `[0,1]`. Polar marks do not require cartesian scales.
2. **`pie` is a transform in 0.7.2.** `pie(data, {value, label, padAngle})`
   returns slice rows (`startAngle`, `endAngle`, …); the renderable mark is
   `polar({marks: [radialArc(slices, {...})]})`. The bridge composes this
   internally (`makePieMark`); the Python contract (`pie(...)` from API Spec §2.2)
   does not change. `inner_radius`/`outer_radius`/`corner_radius` map to
   `radialArc`; `label` feeds the per-slice color channel (`z`).
3. **Real SSR (historical).** With the React adapter, the prerender executed the
   scene on the server and the exported HTML included the SVGs. Superseded by
   finding 4.
4. **DD-006 — DOM host instead of the React adapter (Delta bridge-dom-host).**
   In vite dev, the bridge served from `/public` is left out of the optimizeDeps
   scan → its deps are discovered late → re-optimization → **two copies of React**
   (different `?v=` hashes) → `null` hook dispatcher ("resolveDispatcher() is
   null"), both in the bridge and inside `<Chart>` from `@tanstack/react-charts`.
   Solution: the bridge is a **class component** that mounts `mountChart`
   (`@tanstack/charts/dom`, framework-free, no hooks); memoization with a WeakMap
   by spec identity; try/catch + setState as an error boundary.
   `@tanstack/react-charts` removed from `LIB_DEPENDENCIES`. Trade-off: the
   prerender no longer emits SVG (containers that hydrate on the client). Verified
   with jsdom under two copies of React (11/11 cases).
5. **1.x definition shape (Delta tanstack-charts-1.1, 2026-10-10).** Cartesian
   scales moved from root `x`/`y` into a `scales: {x, y}` registry where both
   reserved entries are mandatory (`null` for pure polar charts); `polar()` needs
   `scales: {angle, radius}` (both `null` for pies); `animate` became
   `svgAnimation`; the y grid no longer defaults to on. `pie()`'s gap option is
   `gapAngle` (the bridge used to pass a non-existent `padAngle`). Scale
   inference (finding 1) is still required.

---

## Constitution check
- Art. 2: DD-001/DD-003 guarantee a serializable boundary. ✓
- Art. 3: the registry uses TanStack names; snake_case helpers 1:1. ✓
- Art. 4: DD-002 + open question 1 pin the version trio. ✓
- Art. 7: degradation flows in §3.3. ✓

## Change History

| Version | Date | Author | Changes |
|---|---|---|---|
| 1.0 | 2026-08-07 | Ernesto Crespo | Initial version |
