# Tasks — reflex-tanstack-charts v0.1.0

> Source specs: `specs/prd/reflex-tanstack-charts.md` · `specs/api/component-api-v1.md`
> · `specs/technical/architecture.md` · `specs/data-model/chartspec-schema.md`
> · `specs/plans/implementation-plan.md`
> Phases covered: F1–F4 complete · Generated: 2026-08-07

## Conventions for this file

- Order = execution order except for [P].
- States: `[ ]` pending · `[~]` in progress · `[x] {date}` done · `[!]` blocked (note).
- **First supervised batch: T-001..T-005** (the spike). Review before scaling up.

## Tasks

### T-001 · Custom component scaffolding `[x] 2026-08-07`
- **What**: `reflex component init` structure adapted to the existing repo: `pyproject.toml` (name `reflex-tanstack-charts`, Apache-2.0, `requires-python >=3.12`, dep `reflex>=0.8`, uv-compatible build backend), `custom_components/reflex_tanstack_charts/__init__.py`, demo folder `tanstack_charts_demo/`.
- **REQ**: REQ-CH-019
- **Files**: `pyproject.toml`, `custom_components/reflex_tanstack_charts/*`, `tanstack_charts_demo/*`
- **Depends on**: —
- **Done**: `uv sync && uv run python -c "import reflex_tanstack_charts"` OK (editable).

### T-002 · Pin the npm version trio (GATE) `[x] 2026-08-07`
- **What**: query npm and pin the exact compatible versions of `@tanstack/charts`, `@tanstack/charts-scales`, `@tanstack/react-charts`, `d3-scale`; document them in the `LIB_DEPENDENCIES` constant and in the Tech Design (close open question 1).
- **REQ**: REQ-CH-020
- **Files**: `custom_components/reflex_tanstack_charts/component.py`, `specs/technical/architecture.md`
- **Depends on**: —  [P] with T-001
- **Done**: `npm view @tanstack/react-charts@<ver> peerDependencies` consistent with the pins; note written in Tech Design §10.

### T-003 · Minimal Python component `[x] 2026-08-07`
- **What**: `TanStackChart(rx.Component)` with `library = "$/public" + rx.asset("TanStackChartBridge.jsx", shared=True)`, `tag="TanStackChartBridge"`, `lib_dependencies` (T-002), props `spec: rx.Var[dict]`, `height`, `aria_label`; `tanstack_chart()` function with `INVALID_MARKS` validation.
- **REQ**: REQ-CH-001
- **Depends on**: T-001, T-002
- **Done**: `uv run pytest tests/test_component.py::test_req_ch_001_component_compiles` green.

### T-004 · Bridge v0 (spike): barY + band/linear `[x] 2026-08-07`
- **What**: `TanStackChartBridge.jsx` with `MARK_REGISTRY={barY}`, `SCALE_REGISTRY={band, linear}`, `buildDefinition(spec)` with `useMemo`, rendering `<Chart definition height ariaLabel/>`.
- **REQ**: REQ-CH-002
- **Depends on**: T-003
- **Done**: the demo (T-005) shows the bar chart; no console errors.

### T-005 · Demo v0 + export (spike closure) `[x] 2026-08-07`
- **What**: demo page with a letter-frequency bar chart, 100% Python; validate the full pipeline.
- **REQ**: REQ-CH-021 (partial), REQ-CH-002
- **Depends on**: T-004
- **Done**: `cd tanstack_charts_demo && uv run reflex export --frontend-only` with no errors.

--- checkpoint: review T-001..T-005 before continuing ---

### T-006 · Mark core: base + serialization `[x] 2026-08-07`
- **What**: `marks.py` with `_mark(type, data, **channels)`: field validation (UNKNOWN_FIELD), snake→camelCase, datetime/date→ISO + `temporal_fields`, NaN/inf rejection, None omission.
- **REQ**: REQ-CH-011, REQ-CH-012
- **Depends on**: T-005
- **Done**: `uv run pytest tests/test_marks.py -k "req_ch_011 or req_ch_012"` green.

### T-007 · The 13 remaining helpers (Python) `[x] 2026-08-07`
- **What**: `line_y/line_x/area_y/area_x/bar_x/dot/rule_x/rule_y/text/tick_x/tick_y/cell/pie` following the catalog in API Spec §2.2 (required/optional channels, `curve` catalog).
- **REQ**: REQ-CH-003
- **Depends on**: T-006
- **Done**: snapshot test per helper (`tests/test_spec_contract.py`) green.

### T-008 · Complete JS mark registry `[x] 2026-08-07`
- **What**: extend `MARK_REGISTRY` to the 14 marks (static imports, DD-002); `temporal_fields` rehydration; `curve`→`d3Curve` mapping.
- **REQ**: REQ-CH-003, REQ-CH-011
- **Depends on**: T-007
- **Done**: the demo renders a temporal line (utc) and a donut; clean console.

### T-009 · Scales, axes and color `[x] 2026-08-07`
- **What**: `scales.py` (8-type catalog, UNKNOWN_SCALE) + `axis.py` (label/grid/nice/ticks + FormatSpec) + ordinal `color` (REQ-CH-023) and their JS registries (charts-scales + d3-scale + Intl). *(Sequential after T-008: they share the bridge — Analyze A-03.)*
- **REQ**: REQ-CH-004, REQ-CH-023
- **Depends on**: T-006
- **Done**: `uv run pytest tests/test_scales_axis.py` green; an axis with percent format visible in the demo.

### T-010 · Bridge degradation and robustness `[x] 2026-08-07`
- **What**: unknown mark → warn+overlay (UNSUPPORTED_MARK); empty dataset → skip; ErrorBoundary (RENDER_ERROR); `spec.version` gate.
- **REQ**: REQ-CH-013, REQ-CH-014, REQ-CH-015
- **Depends on**: T-008
- **Done**: an "edge cases" demo page with an invalid spec shows a placeholder; the page stays alive.

### T-011 · Complete contract and unit tests `[x] 2026-08-07`
- **What**: complete the suite: 14 mark snapshots, validations, serialization, the component compiles with all props.
- **REQ**: Art. 6 (all MUSTs cited)
- **Depends on**: T-007, T-009, T-010
- **Done**: `uv run pytest` green; grep confirms every MUST REQ appears in ≥1 test.

### T-012 · Events into Python `[x] 2026-08-07`
- **What**: `on_focus_change`/`on_select` as `rx.EventHandler` (1-arg dict|None spec); `PointPayload` sanitizer in the bridge (Date→ISO, undefined→null, plain values only); focus lost → None.
- **REQ**: REQ-CH-008, REQ-CH-009, REQ-CH-010
- **Depends on**: T-008
- **Done**: demo drill-down: clicking a point updates an `rx.text` with the datum; declared-trigger test.

### T-013 · Tooltip and animation `[x] 2026-08-07` [P with T-012]
- **What**: `tooltip=True` → import `@tanstack/charts/tooltip` into the definition; `animate=True`.
- **REQ**: REQ-CH-006, REQ-CH-007
- **Depends on**: T-009
- **Done**: tooltip visible on hover in the demo; transition when mutating the data.

### T-014 · Sizing, aria and theming `[x] 2026-08-07` [P with T-012]
- **What**: `aspect_ratio`+`initial_width` (mutually exclusive with an explicit height), dev warning without `aria_label`, `theme` dict → inline container style.
- **REQ**: REQ-CH-016, REQ-CH-017, REQ-CH-018
- **Depends on**: T-009
- **Done**: validation tests green; demo with a custom theme in dark mode.

### T-015 · Reactivity demo `[x] 2026-08-07`
- **What**: page with a data Var + randomize button (REQ-CH-005) and events page (T-012).
- **REQ**: REQ-CH-005, REQ-CH-021
- **Depends on**: T-012, T-013
- **Done**: manual interaction verified; `reflex export` green.

### T-016 · Complete demo gallery `[x] 2026-08-07`
- **What**: 1 example per MUST mark (TanStack catalog references: bar-grouped, line-gaps, donut, scatter-bubble, range-band, heatmap with cell, waffle-like with tick…).
- **REQ**: REQ-CH-021
- **Depends on**: T-015
- **Done**: 14/14 marks visible in the gallery; clean console.

### T-017 · README and docs `[x] 2026-08-07` [P with T-016]
- **What**: installation (uv/pip), <10-line example, mark table, parity matrix, events and theming sections.
- **REQ**: REQ-CH-022
- **Depends on**: T-015
- **Done**: README renders well in preview; the README example copied into the demo and works.

### T-018 · Package build and validation `[~]` (build OK; wheel installation in a clean app pending on the author's machine)
- **What**: `uv build`; install the wheel in a clean Reflex app and verify the JSX asset + npm deps.
- **REQ**: REQ-CH-019, REQ-CH-020
- **Depends on**: T-016, T-017
- **Done**: a clean app renders a chart using only the installed wheel.

### T-019 · Publication `[ ]`
- **What**: `0.1.0a1` to TestPyPI (`uv publish --index testpypi`) → validate the installation → `0.1.0` to PyPI → `reflex component share`.
- **REQ**: REQ-CH-019
- **Depends on**: T-018
- **Done**: `uv pip install reflex-tanstack-charts` from PyPI works in a fresh environment.

## Traceability matrix

| REQ | Priority | Tasks | Tests citing it (planned) |
|---|---|---|---|
| REQ-CH-001 | MUST | T-003 | `test_req_ch_001_component_compiles` |
| REQ-CH-002 | MUST | T-004, T-005 | `test_req_ch_002_spec_renders_mark` (snapshot) + demo export |
| REQ-CH-003 | MUST | T-007, T-008 | `test_req_ch_003_snapshot_<mark>` ×14 |
| REQ-CH-004 | MUST | T-009 | `test_req_ch_004_scale_catalog` |
| REQ-CH-005 | MUST | T-015 | reactivity demo + `test_req_ch_005_spec_is_var_compatible` |
| REQ-CH-006 | MUST | T-013 | `test_req_ch_006_tooltip_flag` |
| REQ-CH-007 | SHOULD | T-013 | `test_req_ch_007_animate_flag` |
| REQ-CH-008 | MUST | T-012 | `test_req_ch_008_focus_trigger_declared` |
| REQ-CH-009 | MUST | T-012 | `test_req_ch_009_select_trigger_declared` |
| REQ-CH-010 | MUST | T-012 | manual demo verification + sanitizer unit test |
| REQ-CH-011 | MUST | T-006, T-008 | `test_req_ch_011_datetime_iso_temporal_fields` |
| REQ-CH-012 | MUST | T-006 | `test_req_ch_012_unknown_field_raises` |
| REQ-CH-013 | MUST | T-010 | `test_req_ch_013_unsupported_mark_spec` + demo edge case |
| REQ-CH-014 | MUST | T-010 | `test_req_ch_014_empty_dataset_ok` + demo edge case |
| REQ-CH-015 | SHOULD | T-010 | demo edge cases |
| REQ-CH-016 | MUST | T-014 | `test_req_ch_016_sizing_validation` |
| REQ-CH-017 | MUST | T-014 | `test_req_ch_017_aria_warning` |
| REQ-CH-018 | SHOULD | T-014 | `test_req_ch_018_theme_vars` |
| REQ-CH-019 | MUST | T-001, T-018, T-019 | build + install in a clean app |
| REQ-CH-020 | MUST | T-002, T-018 | `test_req_ch_020_pinned_lib_dependencies` |
| REQ-CH-021 | MUST | T-005, T-015, T-016 | gallery 14/14 + green export |
| REQ-CH-022 | SHOULD | T-017 | manual README review |

SHOULDs without a task: none. Deferred (out of scope for v0.1.0): advanced marks
and brush/zoom interactions — see PRD §5.2/§5.3.

## Execution log

| Date | Tasks | Result | Notes |
|---|---|---|---|
| 2026-08-07 | T-001..T-005 (spike) | ✅ | npm versions confirmed: the 0.7.2 trio + d3-scale 4.0.2 + d3-shape 3.2.0. `pie`/`tooltip` verified with the installed package |
| 2026-08-07 | T-006..T-011 (TDD) | ✅ | 56 tests green; ruff clean. Tests written before the implementation |
| 2026-08-07 | T-012..T-017 | ✅ | Demo: 1 page with 14/14 marks + reactivity + events + theming + degradation |
| 2026-08-07 | E2E export | ✅ | `reflex export` produces an `index.html` with 15 prerendered SVGs (SSR). **Deviations discovered → spec updated (Tech Design §11)**: (1) the published TanStack 0.7.2 does NOT infer scales → the bridge infers them from the data type; (2) `pie()` in 0.7.2 is a transform: the real mark is `polar({marks:[radialArc(slices)]})` — the Python API does not change |
| 2026-08-07 | T-018 | 🔶 | `uv build` OK (the wheel includes the JSX). Installing the wheel in a clean app + `reflex run` with bun: pending on the author's machine (the sandbox cannot download bun; validated with npm + timeout) |
| 2026-08-07 | T-019 | ⏸ | Requires the author's PyPI token |
| 2026-08-07 | Delta demo-catalog | ✅ | `changes/2026-08-07-demo-catalogo/`: demo rewritten to replicate the official catalog (33 replicas + complete grammar; 51 prerendered SVGs). REQ-CH-021 extended |
| 2026-08-07 | Delta bridge-dom-host | ✅ | "resolveDispatcher() is null" bug on `reflex run` (double React in vite dev from serving the bridge out of /public). Bridge migrated to a class + `mountChart` (hook-free DOM host); `@tanstack/react-charts` removed; REQ-CH-002/020 amended. Verified with jsdom under two copies of React |

If, while implementing, the spec turns out to be wrong: **stop, update the spec
(or open a Delta in `changes/`), and only then continue.**
