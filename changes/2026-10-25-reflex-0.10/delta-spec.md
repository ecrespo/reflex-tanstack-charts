# Delta Spec — Reflex ≥ 0.10 and release 0.3.0

> Status: `APPLIED` (2026-10-25) · Affects: Constitution stack table (+ amendment),
> PRD dependency table, Tech Design §8 / §10, `pyproject.toml`, the demo
> `requirements.txt`, CI/CD (new). It does not change the Python API, the
> ChartSpec v1 contract, nor the npm pins (TanStack Charts stays at 1.1.0).

## Context

Reflex `0.10.0` is the latest release on PyPI. The project policy is to track the
latest Reflex, so the dependency floor moves from `reflex>=0.8` to
`reflex>=0.10.0`. Because the floor change drops support for older Reflex
versions, the package version moves to **0.3.0** (minor bump, pre-1.0).

The repo also had no automation; this change adds GitHub Actions for CI and for
publishing to PyPI on tags, running every action on Node 24.

## Changes

| Area | Before | After |
|---|---|---|
| `pyproject.toml` dependency | `reflex>=0.8` | `reflex>=0.10.0` |
| Package version | `0.2.0` | `0.3.0` (`pyproject.toml` and `__version__`) |
| Demo `requirements.txt` | `reflex==0.9.8` | `reflex==0.10.0` |
| `uv.lock` | Reflex 0.9.x graph | Reflex 0.10.0 graph (pydantic no longer pulled in) |
| CI | none | `.github/workflows/ci.yml`: ruff, pytest on 3.12/3.13, build + `twine check` + wheel smoke test, demo `reflex export` on Node 24 |
| Release | manual `uv publish` | `.github/workflows/publish.yml`: on a `vX.Y.Z` tag on `main` → CI, tag/version check, build, publish to PyPI, GitHub release |

### Node 24

All actions are on majors whose runtime is `node24` (`actions/checkout@v7`,
`actions/setup-node@v7`, `astral-sh/setup-uv@v10.3.2`,
`actions/upload-artifact@v7`). `FORCE_JAVASCRIPT_ACTIONS_TO_NODE24` is also set,
and the demo build installs Node 24 with `setup-node`.

### PyPI authentication

`publish.yml` uses **Trusted Publishing** (OIDC, `id-token: write`, environment
`pypi`). If a `PYPI_API_TOKEN` repository secret exists it is used instead.
One-time setup for Trusted Publishing on PyPI → project
`reflex-tanstack-charts` → *Publishing* → add a GitHub publisher:
owner `ecrespo`, repo `reflex-tanstack-charts`, workflow `publish.yml`,
environment `pypi`.

## Release procedure

1. Bump `version` in `pyproject.toml` **and** `__version__` (CI checks both match).
2. Merge `develop` → `main` through a PR with green CI.
3. Tag `main`: `git tag -a vX.Y.Z -m "…" && git push origin vX.Y.Z`.
4. `publish.yml` verifies that the tag matches the version and that the commit
   is on `main`, then publishes and creates the GitHub release.

## Verification (Reflex 0.10.0, local)

- `pytest` 56/56 · `ruff check` + `ruff format --check` clean.
- `reflex export --frontend-only` of the demo: compiles with no deprecation warnings.
- `reflex run` + headless Chromium: 50 chart SVGs mounted, none empty;
  "Randomize data" re-renders; the only console notice is the intentional
  `UNSUPPORTED_MARK: treemap` card (REQ-CH-013).
