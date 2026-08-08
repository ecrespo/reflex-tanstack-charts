# reflex-tanstack-charts — Implementation Plan

## Metadata

| Field | Value |
|---|---|
| **Author** | Ernesto Crespo |
| **Status** | `DRAFT` |
| **Version** | 1.0 |
| **Date** | 2026-08-07 |
| **PRD** | `specs/prd/reflex-tanstack-charts.md` |
| **Tech Design** | `specs/technical/architecture.md` |
| **Data Model** | `specs/data-model/chartspec-schema.md` |
| **API Spec** | `specs/api/component-api-v1.md` |

---

## 1. Implementation Summary

4 sequential phases with a **risk spike up front** (F1 validates that `rx.asset` +
the bridge's npm imports compile before investing in the full surface). Solo
development with an agent; the first batch of 3-5 tasks per phase is supervised.

**Total estimated duration:** 9-11 effective days.
**Team required:** 1 dev (+ agent).
**Target date:** v0.1.0 on PyPI ~2026-08-21.

## 2. Prerequisites

| Prerequisite | Owner | Status | Deadline |
|---|---|---|---|
| Approved SDD specs (this directory) | Ernesto | ☐ Pending | before F1 |
| PyPI account + token (`uv publish`) | Ernesto | ☐ Pending | before F4 |
| Node/npm available through Reflex (`.web`) | Reflex CLI | ☑ implicit | — |
| Verify on npm the compatible version trio `@tanstack/charts@0.7.2` / `charts-scales` / `react-charts` | Ernesto | ☐ Pending | F1 (gate T-002) |

## 3. Implementation Phases

---

### Phase 1: Scaffolding + bridge spike (risk first)

**Duration:** 2-3 days
**Goal:** custom component structure working end-to-end with **one** mark (`barY`) rendering in the demo. De-risks R4 (asset+npm) and the open question about versions.

| ID | Task | Estimate | Dependency | REQs |
|---|---|---|---|---|
| F1-01 | `reflex component init` (uv as the manager; adjust pyproject: name, Apache-2.0, python>=3.12) | 0.5d | — | REQ-CH-019 |
| F1-02 | Verify/pin the npm versions of the TanStack trio + d3-scale | 0.5d | — | REQ-CH-020 |
| F1-03 | Minimal `TanStackChart(rx.Component)`: `library=$/public+rx.asset`, tag, props `spec/height/ariaLabel` | 0.5d | F1-01 | REQ-CH-001 |
| F1-04 | Bridge v0: registry with `barY` + `band`/`linear` scales, `<Chart>` render | 1d | F1-02, F1-03 | REQ-CH-002 |
| F1-05 | Demo app: page with a static bar chart; `reflex run` and `reflex export` green | 0.5d | F1-04 | REQ-CH-021 (partial) |

**Done:** the demo shows the letter-frequency bar chart (TanStack's React Quick
Start example) declared 100% in Python; `reflex export` with no errors.

---

### Phase 2: Core surface (14 marks, scales, axes, validation)

**Duration:** 3-4 days
**Goal:** all rendering and data-boundary MUSTs.

| ID | Task | Estimate | Dependency | REQs |
|---|---|---|---|---|
| F2-01 | `marks.py`: `_mark()` base + field validation + snake→camel + datetime serialization/`temporal_fields` | 1d | F1-05 | REQ-CH-011, 012 |
| F2-02 | The 13 remaining helpers + the corresponding JS registry | 1.5d | F2-01 | REQ-CH-003 |
| F2-03 | `scales.py` + `axis.py` + JS registries (8 scales, curves, Intl formats) | 1d | F2-01 | REQ-CH-004 |
| F2-04 | Bridge degradation: unknown mark, empty dataset, error boundary, `version` gate | 0.5d | F2-02 | REQ-CH-013, 014, 015 |
| F2-05 | Unit tests + contract snapshots (14 marks) | 1d | F2-02..04 | Art. 6 |

**Done:** `pytest` green; a snapshot per mark; the demo renders a line with dates
(`utc` scale) and a donut (`pie` with `inner_radius`).

---

### Phase 3: Interaction, reactivity and theming

**Duration:** 2 days

| ID | Task | Estimate | Dependency | REQs |
|---|---|---|---|---|
| F3-01 | `on_focus_change`/`on_select` EventHandlers + payload sanitizer in the bridge | 1d | F2-02 | REQ-CH-008, 009, 010 |
| F3-02 | `tooltip` and `animate` in the spec and the bridge | 0.5d | F2-03 | REQ-CH-006, 007 |
| F3-03 | Sizing (`aspect_ratio`/`initial_width`) + `theme` CSS vars + aria_label warning | 0.5d | F2-03 | REQ-CH-016, 017, 018 |
| F3-04 | Demo: reactivity page (mutate a Var) + events page (drill-down into state) | 0.5d | F3-01 | REQ-CH-005, 021 |

**Done:** in the demo, clicking a point updates Python state text; a "randomize"
button re-renders the animated chart.

---

### Phase 4: Packaging, docs and publication

**Duration:** 2 days

| ID | Task | Estimate | Dependency | REQs |
|---|---|---|---|---|
| F4-01 | README: installation, <10-line example, mark table, TanStack parity matrix | 0.5d | F3-04 | REQ-CH-022 |
| F4-02 | Complete demo gallery: 1 example per MUST mark (TanStack catalog reference) | 1d | F3-04 | REQ-CH-021 |
| F4-03 | `uv build` (equivalent to `reflex component build`) + install the wheel in a clean app | 0.5d | F4-01 | REQ-CH-019 |
| F4-04 | Publish `0.1.0a1` to TestPyPI → validate → `0.1.0` to PyPI → `reflex component share` | 0.5d | F4-03 | REQ-CH-019 |

**Global done:** see §7.

## 4. Dependency Map

```
F1 (bridge spike) ──▶ F2 (core surface) ──▶ F3 (interaction) ──▶ F4 (publication)
     │
     └─ F1-02 (npm versions) is a hard gate: if the trio is not coherent,
        go back to Tech Design (open question 1) before F2.
```

## 5. Implementation Risks

| Risk | Probability | Impact | Mitigation | Owner |
|---|---|---|---|---|
| The 0.7.x API differs from the docs (pre-alpha, docs track main) | High | High | F1 spike with the real installed package; adjust the registry, not the Python API | Ernesto |
| `pie`/polar not exported as the API Spec assumes | Medium | Medium | confirm the import in F1; if missing, downgrade `pie` to SHOULD and open a Delta | Ernesto |
| The event payload differs from the documented typing | Medium | Medium | log the real object in the spike; tolerant sanitizer | Ernesto |
| `rx.asset(shared=True)` does not copy the JSX in the package build | Low | High | F4-03 installs the wheel in a clean app and verifies it | Ernesto |

## 6. Communication and Tracking

Solo project: progress is marked in `specs/tasks/mvp-tasks.md` (checkbox + date) —
any session (human or agent) picks up from there. Spec deviations → stop, update the
spec or open a Delta in `changes/`, then continue.

## 7. Definition of Done (Global v0.1.0)

- [ ] The 14 MUST marks render in the demo (REQ-CH-003, 021)
- [ ] `pytest` green; every MUST with a test citing its REQ (Art. 6)
- [ ] `ruff check` + `ruff format --check` + `ty check` green (Art. 5; tool pinned: `ty` — Analyze A-07)
- [ ] `reflex export` of the demo with no errors
- [ ] `uv build` produces sdist+wheel; the wheel installs in a clean app
- [ ] Complete README; specs updated if there were changes
- [ ] Published on PyPI and shared with `reflex component share`

---

## Constitution check
- Art. 1: every task uses uv (`uv build`, `uv publish`, `uv run pytest`). ✓
- Art. 6: F2-05 and the traceability matrix in tasks. ✓
- Art. 8: phases gated by approved specs (prerequisite 1). ✓

## Change History

| Version | Date | Author | Changes |
|---|---|---|---|
| 1.0 | 2026-08-07 | Ernesto Crespo | Initial version |
