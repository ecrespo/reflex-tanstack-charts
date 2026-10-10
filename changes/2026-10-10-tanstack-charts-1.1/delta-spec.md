# Delta Spec — Upgrade TanStack Charts 0.7.2 → 1.1.0

> Status: `APPLIED` (2026-10-10) · Affects: PRD REQ-CH-007 and REQ-CH-020,
> Constitution Art. 4 / tech table, API Spec §2.3, Tech Design §10–11, the JSX
> bridge, `LIB_DEPENDENCIES`. It does not change the Python API nor the
> ChartSpec v1 contract.

## Context

TanStack Charts left Alpha: `1.0.0` (2026-10-03) and `1.1.0` (2026-10-09) are
published on the npm `latest` tag. From 1.0 on, the stable compatibility
contract (`docs/compatibility.md` in the npm package) applies: minor
releases are additive, removals/renames require a major. Constitution Art. 4
still applies: exact pin, bump through a Delta Spec.

## Upstream breaking changes that affect the bridge

| 0.7.2 | 1.1.0 | Bridge change |
|---|---|---|
| `@tanstack/charts-scales/<family>` (separate package) | `@tanstack/charts/scales/<family>` (single package) | Imports moved; `charts-scales` dropped from `LIB_DEPENDENCIES` |
| Root `x` / `y` on the definition | `scales: { x, y }` registry; both reserved entries **required** (`null` if unused) | `buildDefinition` emits `scales`; `{x: null, y: null}` for pure polar charts |
| `polar({ angle, radius, marks })` | `polar({ scales: { angle, radius }, marks })`, both required | `makePieMark` passes `scales: { angle: null, radius: null }` (radialArc uses its own angles) |
| `animate: true` | `svgAnimation: true` | REQ-CH-007 maps `animate=True` → `svgAnimation` |
| y-axis `grid` default `true` | `grid` default `false` on both axes | None: API Spec §2.3 already documents `grid` default `False`; the library now matches the contract. Charts that relied on the implicit y grid must pass `axis(grid=True)` |

## Bug fixed along the way

`pie(..., pad_angle=…)` was forwarded to the `pie()` transform as `padAngle`,
which `pie()` does not accept (in 0.7.2 either) — the gap was silently dropped.
`pie()` takes `gapAngle` and materializes the gap in each slice (its rows carry
`padAngle: 0` so `radialArc` does not pad twice). The bridge now maps
`pad_angle` → `gapAngle`; the "Rounded donut" demo card shows the gaps.

## Amendments

- **REQ-CH-007**: "…pass `svgAnimation: true` to the definition" (previously
  `animate: true`). The Python flag stays `animate=True`.
- **REQ-CH-020**: the pins become `@tanstack/charts@1.1.0`, `d3-scale@4.0.2`,
  `d3-shape@3.2.0`. `@tanstack/charts-scales` is no longer a dependency.

## Verification

- `pytest` 56/56 (pin test updated) · `ruff check` + `ruff format --check` clean.
- `reflex export` (production build) with `@tanstack/charts@1.1.0` resolved in
  `.web/node_modules`: in headless Chromium, 50 chart SVGs mounted, none empty,
  no bridge errors; the only notice is the intentional `UNSUPPORTED_MARK: treemap`
  card (REQ-CH-013). Native tooltip verified on hover.
- `reflex run` (vite dev, fresh `.vite` cache): 50 chart SVGs, no hook/dispatcher
  errors (DD-006 double-React guard holds); "Randomize data" (State Var +
  `animate=True` → `svgAnimation`) re-renders the bars with new heights.

## Operational note

After updating, clear the Vite cache so the stale `charts-scales` graph is not
reused: `rm -rf tanstack_charts_demo/.web/node_modules/.vite` before `reflex run`.
