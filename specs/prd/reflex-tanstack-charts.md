# reflex-tanstack-charts — TanStack Charts wrapper for Reflex

## Product Requirements Document (PRD)

| Field | Value |
|---|---|
| **Author** | Ernesto Crespo |
| **Status** | `DRAFT` |
| **Version** | 1.0 |
| **Date** | 2026-08-07 |
| **Reviewers** | — |
| **Last updated** | 2026-08-07 |

---

## 1. Executive Summary

`reflex-tanstack-charts` is a Reflex custom component (a PyPI package installable
with `pip/uv add reflex-tanstack-charts`) that wraps **TanStack Charts**
(`@tanstack/charts` 0.7.2 + the `@tanstack/react-charts` adapter), a typed,
tree-shakable and accessible chart grammar (SVG by default, ~16 KiB gzip for a
compact line chart against 153+ KiB for Recharts, the library Reflex wraps today).

The component lets Python developers declare charts with TanStack's mark grammar
(`line_y`, `bar_y`, `dot`, `area_y`, `rule_y`, `pie`, …) using only serializable
structures (dicts/lists/Reflex state Vars), without writing JavaScript. A single
bridge component (`TanStackChartBridge.jsx`) translates that JSON `ChartSpec` into
the `defineChart` call on the client.

It solves the complete absence of TanStack Charts bindings for Python: today,
anyone using Reflex is limited to Recharts/Plotly (heavy, with no composable
grammar and no accessible keyboard focus).

## 2. Context and Problem

### 2.1 Current situation
Reflex ships `rx.recharts` and `rx.plotly`. TanStack Charts (released as part of
the TanStack ecosystem, currently 0.7.2 pre-alpha) has no wrapper for Reflex nor
for any Python framework. TanStack's grammar (marks + channels + scales, inspired
by Observable Plot) is explicitly designed for authoring by humans *and* by AI
agents, with strict typing and accessible SVG output.

### 2.2 Problem
A Reflex developer who wants lightweight, layer-composable charts (line + band +
rules + annotations over the same scales), with keyboard focus and native
tooltips, has no option: they must wrap React by hand in every project (JSX +
`rx.asset` + ad-hoc serialization), repetitive work that is prone to Python↔JS
contract errors.

### 2.3 Opportunity
Being the first TanStack Charts wrapper in the Reflex ecosystem, published on PyPI
and shared in the component gallery (`reflex component share`). The spec's
declarative JSON structure also makes it well suited for agent generation.

## 3. Target Users

### Persona 1: Full-stack Python developer (Reflex)
- **Description:** builds dashboards and data apps in Reflex; does not want to touch JS.
- **Main need:** declare charts from Reflex state and receive interaction events in Python.
- **Usage frequency:** daily.
- **Technical level:** medium-high in Python, low in JS.

### Persona 2: AI agent generating UIs
- **Description:** agents that generate Reflex apps; TanStack documents "AI authoring" as a first-class use case.
- **Main need:** a stable, validated JSON contract to compose charts without inventing JS.
- **Usage frequency:** occasional/batch.
- **Technical level:** n/a.

## 4. Goals and Success Metrics

### 4.1 Business goals

| Goal | Metric | Target | Deadline |
|---|---|---|---|
| Publish on PyPI | successful `uv publish`; installable | v0.1.0 | end of phase 4 |
| Core grammar coverage | supported MUST marks | 14/14 | v0.1.0 |
| Public demo | demo gallery with 1 example per MUST mark | 100% of MUST marks | v0.1.0 |

### 4.2 User goals

| User goal | Indicator |
|---|---|
| Working chart in < 10 lines of Python | the README example demonstrates it |
| Reactive data (state Var → re-render) | demo with a button that mutates the data |
| Interaction back into Python | demo with `on_select` that updates state |

## 5. Scope

### 5.1 In Scope (v0.1.0)
- [ ] `tanstack_chart` component (class `TanStackChart(rx.Component)`) + a single JSX bridge.
- [ ] Core cartesian marks: `line_y`, `line_x`, `area_y`, `area_x`, `bar_y`, `bar_x`, `dot`, `rule_x`, `rule_y`, `text`, `tick_x`, `tick_y`, `cell`, plus polar `pie` (14 MUST marks).
- [ ] Scales: `linear`, `band`, `point`, `ordinal` (compact ones from `@tanstack/charts-scales`); `utc`, `time`, `log`, `sqrt` (via `d3-scale`).
- [ ] Axes (label, grid, nice, tick format by pattern), native tooltip, optional animation.
- [ ] `on_focus_change` and `on_select` events with a serialized payload towards Reflex handlers.
- [ ] Typed Python helpers that validate the spec at construction time (fail-fast in Python).
- [ ] Responsive sizing: fixed `height` or `aspect_ratio` + `initial_width`.
- [ ] Theming through `--ts-chart-*` CSS variables and per-mark style props (`fill`, `stroke`, …).
- [ ] Packaged as a Reflex custom component: `reflex component init` layout, build with uv, README with examples, demo app.

### 5.2 Out of Scope (v0.1.0)
- Advanced marks: `treemap`, `sunburst`, `sankeyDiagram`, `geoShape`, `contour`, `hexbin`, `densityContour`, `voronoi`, `delaunayLink`, `forceLayout`, `violin`, `ridgeline`, `waffle`, `box`, `difference`, regressions — reason: huge surface and non-serializable options; they come in through incremental Delta Specs.
- Advanced interactions: `brushX`, `zoomX`, `crosshair`, interactive legends, custom `renderTooltipBody` — they require a richer bidirectional state channel.
- Canvas renderer (`@tanstack/react-charts/canvas`) — SVG covers the common case.
- JS-side data transforms (`window`, `stack`, `group`, `fold`, `waterfall`) — data preparation happens in Python (pandas/polars), in line with TanStack's ownership philosophy.
- Facets and view composition (`facetChart`, `composeViews`).

### 5.3 Future Considerations
- v0.2: distribution marks (`box`, `violin`, `ridgeline`, `waffle`) and `difference`/regression.
- v0.3: hierarchical and network marks (`treemap`, `sunburst`, `sankey`), `crosshair`, brush/zoom with a bidirectional Var.
- An extensible mark registry so apps can inject custom marks.

## 6. Functional Requirements (EARS)

### FR-Core: rendering

**REQ-CH-001 (ubiquitous) · MUST** — THE SYSTEM SHALL expose a public function
`tanstack_chart(spec=..., height=..., aria_label=...)` that compiles to a React
`<TanStackChartBridge>` component mounted via `rx.asset` + `$/public`, without
requiring the user to write JavaScript.

**REQ-CH-002 (event) · MUST** — WHEN the `ChartSpec` contains a supported mark
with a non-empty dataset and existing fields, THE SYSTEM SHALL render SVG with
that mark through `defineChart` + `mountChart` (vanilla DOM host of
`@tanstack/charts`). *(Amended by Delta bridge-dom-host: the React adapter uses
hooks and fails with double React in vite dev.)*

**REQ-CH-003 (ubiquitous) · MUST** — THE SYSTEM SHALL support the 14 core marks:
`line_y`, `line_x`, `area_y`, `area_x`, `bar_y`, `bar_x`, `dot`, `rule_x`, `rule_y`,
`text`, `tick_x`, `tick_y`, `cell`, `pie`; each with its serializable channels
documented in API Spec §4.

**REQ-CH-004 (ubiquitous) · MUST** — THE SYSTEM SHALL resolve scales by name:
`linear`, `band`, `point`, `ordinal` from `@tanstack/charts-scales`; `utc`, `time`,
`log`, `sqrt` from `d3-scale`; with serializable options (`domain`, `nice`,
`padding`, `base`).

**REQ-CH-005 (event) · MUST** — WHEN a state `rx.Var` bound to the spec changes
(data, colors, options), THE SYSTEM SHALL recompute the definition (a new spec
identity invalidates `useMemo`) and re-render the chart without reloading the page.

**REQ-CH-006 (optional) · MUST** — WHERE `tooltip=True` in the spec, THE SYSTEM
SHALL enable the native tooltip from `@tanstack/charts/tooltip`.

**REQ-CH-007 (optional) · SHOULD** — WHERE `animate=True`, THE SYSTEM SHALL pass
`animate: true` to the definition for interruptible transitions.

### FR-Interaction

**REQ-CH-008 (event) · MUST** — WHEN the user focuses a point (pointer or
keyboard) and an `on_focus_change` handler exists, THE SYSTEM SHALL invoke the
Reflex EventHandler with the payload `{mark_id, key, x_value, y_value, datum}`
serialized to JSON.

**REQ-CH-009 (event) · MUST** — WHEN the user selects a point (click/Enter) and an
`on_select` handler exists, THE SYSTEM SHALL invoke the EventHandler with the same
payload as REQ-CH-008.

**REQ-CH-010 (event) · MUST** — WHEN focus leaves the chart, THE SYSTEM SHALL
invoke `on_focus_change` with a `None` payload (focus cleanup).

### FR-Data boundary

**REQ-CH-011 (ubiquitous) · MUST** — THE SYSTEM SHALL accept only
JSON-serializable values in the spec; dates are accepted as `datetime`/`date` in
Python, serialized to ISO-8601, and the bridge SHALL rehydrate them to `Date` for
the fields mapped to a `utc`/`time` scale.

**REQ-CH-012 (unwanted) · MUST** — IF a Python helper receives, **with literal
data**, an `x`/`y` field that does not exist in the first record of the dataset,
THEN THE SYSTEM SHALL raise `ValueError` at construction time (fail-fast in
Python). IF the data arrives as an `rx.Var`, validation is deferred to the bridge's
graceful degradation (REQ-CH-013/014). *(Amended by Analyze A-04.)*

**REQ-CH-013 (unwanted) · MUST** — IF the bridge receives a mark of an unsupported
type, THEN THE SYSTEM SHALL skip that mark, emit `console.warn` with the received
type and render a visible notice inside the chart container.

**REQ-CH-014 (unwanted) · MUST** — IF a dataset arrives empty, THEN THE SYSTEM
SHALL render the chart without that mark (axes/structure intact) without raising an
uncaught exception.

**REQ-CH-015 (unwanted) · SHOULD** — IF building `defineChart` throws at runtime,
THEN the bridge SHALL catch the error (error boundary), show a placeholder with the
message and not propagate the exception to the Reflex app.

### FR-Presentation

**REQ-CH-016 (ubiquitous) · MUST** — THE SYSTEM SHALL support responsive sizing:
fixed `height` (default 320 px) or `aspect_ratio` + `initial_width`; with fluid
container width in both cases.

**REQ-CH-017 (ubiquitous) · MUST** — THE SYSTEM SHALL pass `aria_label` to
`<Chart>`; IF it is not provided, the Python component SHALL emit an accessibility
warning in the backend console in dev mode.

**REQ-CH-018 (optional) · SHOULD** — WHERE `theme` is provided (a dict of
`--ts-chart-*` variables or overrides), THE SYSTEM SHALL apply them as inline
styles on the container to integrate with light/dark mode.

### FR-Packaging

**REQ-CH-019 (ubiquitous) · MUST** — THE SYSTEM SHALL be published as the package
`reflex-tanstack-charts` (import `reflex_tanstack_charts`) with a Reflex custom
component layout, Apache-2.0 license, buildable with `uv build` and publishable
with `uv publish`.

**REQ-CH-020 (ubiquitous) · MUST** — THE SYSTEM SHALL declare exact versions in
`lib_dependencies`: `@tanstack/charts@0.7.2`, `@tanstack/charts-scales@0.7.2`,
`d3-scale@4.0.2` and `d3-shape@3.2.0`. *(Amended by Delta bridge-dom-host:
`@tanstack/react-charts` removed — the bridge mounts with the DOM host.)*

**REQ-CH-021 (ubiquitous) · MUST** — THE SYSTEM SHALL include a Reflex demo app
(`tanstack_charts_demo/`) with ≥1 example per MUST mark, reactivity examples
(REQ-CH-005) and event examples (REQ-CH-008/009).

**REQ-CH-022 (ubiquitous) · SHOULD** — THE SYSTEM SHALL document in the README:
installation, minimal example (<10 lines), table of supported marks and a parity
matrix against the TanStack grammar.

**REQ-CH-023 (optional) · SHOULD** — WHERE `color` is provided with an `ordinal`
scale (`domain` + color `range`), THE SYSTEM SHALL apply it as the chart's color
scale for the series (`z`). *(Added by Analyze A-01.)*

## 7. Non-Functional Requirements

### Performance
- Bundle added to the frontend ≤ ~35 KiB gzip (published range for TanStack's 12-chart suite: 26.6–32.1 KiB).
- Re-render on Var change with no perceptible extra work: the spec is memoized by identity.

### Security
- No `eval`/`new Function` in the bridge; no arbitrary JS from Python (Constitution Art. 2).
- Tick formats as declarative patterns (e.g. `{"style": "percent"}`), never serialized functions.

### Compatibility
- Python ≥ 3.12, Reflex ≥ 0.8. TanStack Charts exactly 0.7.2 (pre-alpha; see Risks).

### Accessibility
- TanStack's accessible SVG by default; `aria_label` promoted to a first-class prop; keyboard focus enabled by default.

### Observability
- Bridge errors with `console.warn`/`console.error` prefixed with `[reflex-tanstack-charts]`.

## 8. Constraints and Dependencies

### Technical constraints
- TanStack's API (`defineChart` with factory functions) is not serializable → this forces the bridge pattern with mark/scale registries keyed by name.
- Reflex does not allow hooking into its event system from arbitrary JS → events are declared as `rx.EventHandler` with serializable argument specs.

### Business constraints
- Apache-2.0 license; `reflex-` prefix in the package name.

### External dependencies

| Dependency | Type | Owner | Status | Risk |
|---|---|---|---|---|
| `@tanstack/charts` 0.7.2 | npm | TanStack | pre-alpha | **High**: unstable API |
| `@tanstack/react-charts` | npm | TanStack | pre-alpha | High |
| `@tanstack/charts-scales` | npm | TanStack | pre-alpha | Medium |
| `d3-scale` | npm | d3 | stable | Low |
| `reflex` ≥ 0.10 | PyPI | Reflex | stable | Low |

## 9. User Stories

### Epic: Declarative charts in Reflex

**US-001:** As a Reflex developer, I want to declare a bar chart from a list of
dicts in my state, so I can visualize data without writing JS.
- Criteria: REQ-CH-001, 002, 003, 016.

**US-002:** As a Reflex developer, I want the chart to update when my state
changes, so I can build live dashboards.
- Criteria: REQ-CH-005.

**US-003:** As a Reflex developer, I want to receive the point the user selected
in a Python handler, so I can drill down.
- Criteria: REQ-CH-008, 009, 010.

**US-004:** As an AI agent, I want a validated JSON contract (fail-fast helpers),
so I can generate correct charts without inspecting JS.
- Criteria: REQ-CH-011, 012, 013.

**US-005:** As a maintainer, I want to publish the package on PyPI with uv, so I
can share it with the Reflex community.
- Criteria: REQ-CH-019, 020, 021, 022.

## 10. Wireframes / Mockups
- Visual reference: the official catalog <https://tanstack.com/charts/catalog> (categories: bar, trend, distribution, polar, interaction, composition, comparison…). The demo replicates in Reflex the examples `bar-grouped`, `01-line-gaps`, `77-donut`, `scatter-bubble`, `03-temperature-range-band`.

## 11. Risks and Mitigations

| Risk | Probability | Impact | Mitigation |
|---|---|---|---|
| TanStack Charts 0.7.x breaks the API (pre-alpha) | High | High | Exact pin (Art. 4); bumps only via Delta Spec; mark matrix re-verified |
| Non-serializable event payload (datum with Date) | Medium | Medium | Payload sanitizer in the bridge (Date→ISO) before emitting to Reflex |
| Version divergence between charts, charts-scales and react-charts | Medium | Medium | Verify the published versions on npm in F1-02 and pin a coherent trio |
| `rx.asset` + JSX with npm imports does not resolve at build time | Low | High | Early spike (T-004) that compiles the demo before going further |

## 12. Estimated Timeline

| Phase | Estimated duration | Deliverable |
|---|---|---|
| Spec & Design (SDD) | done | approved specs/ |
| F1 Scaffolding + bridge spike | 2-3 d | demo compiles with 1 mark |
| F2 Core (spec, helpers, scales) | 3-4 d | 14 MUST marks |
| F3 Interaction + theming | 2 d | events and tooltip |
| F4 Packaging + demo + docs | 2 d | `uv build` OK, README |

---

## Constitution check
- Art. 1 (uv): plan and tasks use only uv. ✓
- Art. 2 (serializable boundary): REQ-CH-011/012; no JS from Python. ✓
- Art. 3 (name parity): REQ-CH-003 uses TanStack names in snake_case. ✓
- Art. 4 (npm pins): REQ-CH-020. ✓
- Art. 7 (degradation): REQ-CH-013/014/015. ✓

## Change History

| Version | Date | Author | Changes |
|---|---|---|---|
| 1.0 | 2026-08-07 | Ernesto Crespo | Initial version |

## Approvals

| Role | Name | Date | Status |
|---|---|---|---|
| Product/Tech Lead | Ernesto Crespo | | ☐ Pending |
