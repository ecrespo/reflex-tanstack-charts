# Delta Spec — Demo based on the official TanStack Charts catalog

> Status: `APPLIED` (2026-08-07) · Affects: PRD REQ-CH-021 (demo) and the demo app.
> It modifies neither the ChartSpec v1 contract nor the Python API.

## Motivation

User request: the demo must replicate the examples from
<https://tanstack.com/charts/catalog> instead of a minimal per-mark gallery.

## Change

REQ-CH-021 is extended: the demo SHALL replicate every official catalog example
that is expressible with the v1 contract (14 marks + 8 scales + ordinal color +
tooltip + events), with the data transforms (bins, painter stacking, moving
averages, OLS, ranks, streamgraph, waffle, diverging Likert) implemented in Python
(`_data.py`), and SHALL explicitly list the examples that are not expressible along
with the mark/extension they require (v0.2+ roadmap).

## Result

- 33 catalog replicas + 4 remaining-grammar cards + 3 interaction cards
  (50 chart instances on the page; 51 prerendered SVGs verified through SSR).
- Mark coverage: 14/14 MUSTs are still present (the original REQ-CH-021 intact).
- Out of scope documented on the page itself: advanced distribution, spatial/geo,
  hierarchy/networks, advanced polar, financial/rect, advanced interaction
  (brush/zoom/cursors), motion — with the catalog example and the required mark per
  group.
- Approximations declared on the card: `bar-grouped` (composite categories),
  `bar-stacked`/stacked areas (painter technique with cumulative totals),
  `33-difference` (neutral band without segmentation by sign),
  `16-lollipop`/`17-dumbbell`/`14-error-bars` (segments as 2-point z series).

## Verification

`pytest` 56/56 · `ruff` clean · SSR export: `index.html` with 51 `<svg>` elements
and the 32 content probes present.
