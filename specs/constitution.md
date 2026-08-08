# Constitution — reflex-tanstack-charts

> Version 1.0 · Ratified: 2026-08-07 · Last amendment: 2026-08-07
> Scope: repository `reflex-tanstack-charts` (Reflex custom component wrapping TanStack Charts)

## Articles

### Art. 1 — Python dependency management
THE TEAM SHALL use `uv` as the single package and environment manager (install,
lock, build and publish with `uv build` / `uv publish`); no `pip install` or
`poetry` in scripts, CI or documentation.
*Rationale: a single reproducible manager; the repo owner standardized on uv.*

### Art. 2 — Serializable boundary
THE SYSTEM SHALL accept in its Python API only JSON-serializable values (the
`ChartSpec`); no public API shall accept arbitrary JavaScript strings to inject
into the frontend. Dates travel as ISO-8601 and are rehydrated to `Date` in the
JS bridge.
*Rationale: prevents XSS/injection and keeps the Python↔JS contract verifiable.*

### Art. 3 — Vocabulary parity with TanStack
THE SYSTEM SHALL preserve the names of the TanStack Charts grammar (`lineY`,
`barY`, `dot`, `ruleY`, channels `x/y/z/fill/stroke`…) translated only to
snake_case in Python (`line_y`, `bar_y`); no custom semantic renaming.
*Rationale: upstream documentation stays valid for the user; less terminology drift.*

### Art. 4 — Pinned npm dependencies
THE SYSTEM SHALL declare `@tanstack/charts`, `@tanstack/charts-scales` and
`@tanstack/react-charts` with an exact (pinned) version in `lib_dependencies`, and
every upstream version bump SHALL go through a Delta Spec with the mark matrix re-verified.
*Rationale: TanStack Charts is pre-alpha (0.7.x); its API may break between releases.*

### Art. 5 — Code quality
THE TEAM SHALL keep `ruff check` + `ruff format --check` + `ty check` (or
`pyright`) green before every merge; the JSX bridge goes through `prettier --check`.
*Rationale: cheap automated gate; the repo is a public library.*

### Art. 6 — Requirement traceability
THE SYSTEM SHALL cover every MUST requirement (REQ-CH-NNN) with ≥1 task in
`specs/tasks/` and ≥1 automated test citing the REQ in its name or docstring before
closing the task.
*Rationale: the backbone of SDD; without this the spec is theater.*

### Art. 7 — Degradation without breakage
THE SYSTEM SHALL degrade with a visible message and `console.warn` — never with an
uncaught exception that breaks the page — on invalid specs, unsupported marks or
empty datasets.
*Rationale: a broken chart must not take down the user's Reflex app.*

### Art. 8 — Spec-anchored process
THE TEAM SHALL obtain an approved spec before implementing work ≥ medium feature;
changes to already-specced features come in through `changes/` as a Delta Spec and
are folded into `specs/` once approved. Updating the spec is part of the Definition of Done.
*Rationale: the specs in `specs/` are the project's current truth.*

## Stack constraints

Decided, not re-discussed per feature:

| Area | Decision |
|---|---|
| Backend language | Python ≥ 3.12 (repo `.python-version`) |
| Framework | Reflex ≥ 0.8 (custom component, `reflex component init/build`) |
| Python manager | uv (Art. 1) |
| Chart library | TanStack Charts 0.7.2 (pre-alpha) + `@tanstack/react-charts` |
| Compact scales | `@tanstack/charts-scales` (linear, band, point, ordinal) |
| Advanced scales | `d3-scale` only for `utc`, `time`, `log`, `sqrt` |
| Frontend bridge | A single local `TanStackChartBridge.jsx` via `rx.asset(shared=True)` + `$/public` |
| License | MIT (amendment 2026-08-07: the repo already had the author's MIT LICENSE; it prevails over Reflex's Apache-2.0 default) |
| Package name | `reflex-tanstack-charts` (the `reflex-` prefix is mandatory for PyPI discoverability) |
| Tests | pytest (unit and component compilation); JS validation through the demo app build |

## Amendments

| Date | Article | Change | Reason | Approved by |
|---|---|---|---|---|
| 2026-08-07 | Stack (license) | Apache-2.0 → MIT | Author's pre-existing MIT LICENSE in the repo | Ernesto |

## Constitution check (use in every artifact)

At the end of each PRD / Tech Design / Plan: which articles apply and how they are
met, or which exception is requested and why. An exception without a written
justification = a violation.
