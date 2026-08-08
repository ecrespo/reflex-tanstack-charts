# Delta Spec — Bridge without the React adapter (vanilla DOM host)

> Status: `APPLIED` (2026-08-07) · Affects: Tech Design (DD-006), PRD REQ-CH-002 and
> REQ-CH-020, the JSX bridge, `LIB_DEPENDENCIES`. It does not change the Python API
> nor the ChartSpec v1 contract.

## Originating bug (user report)

`reflex run` (vite dev) raised
`TypeError: can't access property "useMemo", resolveDispatcher() is null` when
mounting `TanStackChartBridge`.

**Root cause:** the bridge is served from `/public/external/...` — Vite treats
`public/` as static assets and does NOT include it in the optimizeDeps scan. Its
dependencies are discovered at runtime → a second optimization pass → two
pre-bundled copies of React coexist (different `?v=` hashes: `react.js?v=324d…`
vs `react-dom_client.js?v=1b3d…`). With two copies, the hook dispatcher is `null`.
The production build does not suffer from it because everything is bundled into a
single graph — which is why the SSR export passed and dev did not.

Reproduced deterministically in a sandbox: a bridge bundle with its own inlined
copy of React + an external `react-dom` → identical crash; first in the bridge's
`useMemo` and, once that was removed, **inside `<Chart>` from
`@tanstack/react-charts`** (the adapter also uses hooks). Removing hooks only from
the bridge was not enough.

## Decision (DD-006)

The bridge drops the React adapter and mounts with the **vanilla DOM host**
(`mountChart` from `@tanstack/charts/dom`, framework-free, zero hooks) from a
**class component** (`componentDidMount`/`DidUpdate`/`WillUnmount` +
`host.update()`/`destroy()`). Class components and element creation work across
React copies; hooks do not → immune by construction.

- `useMemo` → `WeakMap` keyed by spec identity (same semantics, REQ-CH-005).
- Error boundary → `try/catch` on mount + `setState` with a placeholder
  (REQ-CH-015 intact).
- `ChartHostOptions` covers 1:1 what `<Chart>` used: `definition`, `height`,
  `aspectRatio`, `initialWidth`, `ariaLabel`, `onFocusChange`, `onSelect`.

## Amendments

- **REQ-CH-002**: "…render SVG with that mark through `defineChart` +
  `mountChart` (DOM host of `@tanstack/charts`)" (previously: `<Chart>` from
  `@tanstack/react-charts`).
- **REQ-CH-020**: the pins become `@tanstack/charts@0.7.2`,
  `@tanstack/charts-scales@0.7.2`, `d3-scale@4.0.2`, `d3-shape@3.2.0` —
  `@tanstack/react-charts` is no longer a dependency.

## Accepted trade-off

The DOM host mounts on the client: the prerendered HTML no longer contains the
SVGs (it contains the containers, which hydrate on load). We lose the prerender's
static SVG in exchange for a dev server that can serve from `public/` with no risk
of double React. Revisitable if TanStack publishes a hook-free adapter or Reflex
exposes `optimizeDeps` for assets.

## Verification

- jsdom + **two copies of React** (the bug scenario): 11/11 cases render SVG
  (including nested pie, temporal layers, degradation, future version).
- `pytest` 56/56 (pin updated through TDD) · `ruff` clean.
- Production export: prerender green, 52 containers in `index.html`, complete
  gallery present.

## Operational note

After updating, **clear the Vite cache** to remove the duplicated graphs that are
already persisted: `rm -rf tanstack_charts_demo/.web` (or at least
`.web/node_modules/.vite`) before `reflex run`.
