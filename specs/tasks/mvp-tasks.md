# Tasks — reflex-tanstack-charts v0.1.0

> Specs de origen: `specs/prd/reflex-tanstack-charts.md` · `specs/api/component-api-v1.md`
> · `specs/technical/architecture.md` · `specs/data-model/chartspec-schema.md`
> · `specs/plans/implementation-plan.md`
> Fases que cubre: F1–F4 completas · Generado: 2026-08-07

## Convenciones de este archivo

- Orden = orden de ejecución salvo [P].
- Estados: `[ ]` pendiente · `[~]` en curso · `[x] {fecha}` hecha · `[!]` bloqueada (nota).
- **Primera tanda supervisada: T-001..T-005** (el spike). Revisar antes de escalar.

## Tareas

### T-001 · Scaffolding del custom component `[x] 2026-08-07`
- **Qué**: estructura de `reflex component init` adaptada al repo existente: `pyproject.toml` (nombre `reflex-tanstack-charts`, Apache-2.0, `requires-python >=3.12`, dep `reflex>=0.8`, build backend compatible uv), `custom_components/reflex_tanstack_charts/__init__.py`, carpeta demo `tanstack_charts_demo/`.
- **REQ**: REQ-CH-019
- **Archivos**: `pyproject.toml`, `custom_components/reflex_tanstack_charts/*`, `tanstack_charts_demo/*`
- **Depende de**: —
- **Done**: `uv sync && uv run python -c "import reflex_tanstack_charts"` OK (editable).

### T-002 · Fijar trío de versiones npm (GATE) `[x] 2026-08-07`
- **Qué**: consultar npm y fijar versiones exactas compatibles de `@tanstack/charts`, `@tanstack/charts-scales`, `@tanstack/react-charts`, `d3-scale`; documentarlas en constante `LIB_DEPENDENCIES` y en Tech Design (cerrar pregunta abierta 1).
- **REQ**: REQ-CH-020
- **Archivos**: `custom_components/reflex_tanstack_charts/component.py`, `specs/technical/architecture.md`
- **Depende de**: —  [P] con T-001
- **Done**: `npm view @tanstack/react-charts@<ver> peerDependencies` coherente con los pins; nota escrita en Tech Design §10.

### T-003 · Componente Python mínimo `[x] 2026-08-07`
- **Qué**: `TanStackChart(rx.Component)` con `library = "$/public" + rx.asset("TanStackChartBridge.jsx", shared=True)`, `tag="TanStackChartBridge"`, `lib_dependencies` (T-002), props `spec: rx.Var[dict]`, `height`, `aria_label`; función `tanstack_chart()` con validación `INVALID_MARKS`.
- **REQ**: REQ-CH-001
- **Depende de**: T-001, T-002
- **Done**: `uv run pytest tests/test_component.py::test_req_ch_001_component_compiles` verde.

### T-004 · Bridge v0 (spike): barY + band/linear `[x] 2026-08-07`
- **Qué**: `TanStackChartBridge.jsx` con `MARK_REGISTRY={barY}`, `SCALE_REGISTRY={band, linear}`, `buildDefinition(spec)` con `useMemo`, render `<Chart definition height ariaLabel/>`.
- **REQ**: REQ-CH-002
- **Depende de**: T-003
- **Done**: demo (T-005) muestra el bar chart; sin errores en consola.

### T-005 · Demo v0 + export (cierre del spike) `[x] 2026-08-07`
- **Qué**: página demo con bar chart de frecuencia de letras 100% Python; validar pipeline completo.
- **REQ**: REQ-CH-021 (parcial), REQ-CH-002
- **Depende de**: T-004
- **Done**: `cd tanstack_charts_demo && uv run reflex export --frontend-only` sin errores.

--- checkpoint: revisar T-001..T-005 antes de continuar ---

### T-006 · Núcleo de marcas: base + serialización `[x] 2026-08-07`
- **Qué**: `marks.py` con `_mark(type, data, **channels)`: validación de campos (UNKNOWN_FIELD), snake→camelCase, datetime/date→ISO + `temporal_fields`, rechazo NaN/inf, omisión de None.
- **REQ**: REQ-CH-011, REQ-CH-012
- **Depende de**: T-005
- **Done**: `uv run pytest tests/test_marks.py -k "req_ch_011 or req_ch_012"` verde.

### T-007 · 13 helpers restantes (Python) `[x] 2026-08-07`
- **Qué**: `line_y/line_x/area_y/area_x/bar_x/dot/rule_x/rule_y/text/tick_x/tick_y/cell/pie` según catálogo API Spec §2.2 (canales requeridos/opcionales, catálogo `curve`).
- **REQ**: REQ-CH-003
- **Depende de**: T-006
- **Done**: snapshot test por helper (`tests/test_spec_contract.py`) verde.

### T-008 · Registro JS completo de marcas `[x] 2026-08-07`
- **Qué**: ampliar `MARK_REGISTRY` a las 14 marcas (imports estáticos, DD-002); rehidratación `temporal_fields`; mapeo `curve`→`d3Curve`.
- **REQ**: REQ-CH-003, REQ-CH-011
- **Depende de**: T-007
- **Done**: demo renderiza línea temporal (utc) y donut; consola limpia.

### T-009 · Escalas, ejes y color `[x] 2026-08-07`
- **Qué**: `scales.py` (catálogo 8 tipos, UNKNOWN_SCALE) + `axis.py` (label/grid/nice/ticks + FormatSpec) + `color` ordinal (REQ-CH-023) y sus registros JS (charts-scales + d3-scale + Intl). *(Secuencial tras T-008: comparten el bridge — Analyze A-03.)*
- **REQ**: REQ-CH-004, REQ-CH-023
- **Depende de**: T-006
- **Done**: `uv run pytest tests/test_scales_axis.py` verde; eje con formato percent visible en demo.

### T-010 · Degradación y robustez del bridge `[x] 2026-08-07`
- **Qué**: marca desconocida → warn+overlay (UNSUPPORTED_MARK); dataset vacío → omitir; ErrorBoundary (RENDER_ERROR); gate `spec.version`.
- **REQ**: REQ-CH-013, REQ-CH-014, REQ-CH-015
- **Depende de**: T-008
- **Done**: página demo "edge cases" con spec inválido muestra placeholder; la página sigue viva.

### T-011 · Tests de contrato y unidad completos `[x] 2026-08-07`
- **Qué**: completar suite: snapshots 14 marcas, validaciones, serialización, componente compila con todas las props.
- **REQ**: Art. 6 (todos los MUST citados)
- **Depende de**: T-007, T-009, T-010
- **Done**: `uv run pytest` verde; grep confirma que todo REQ MUST aparece en ≥1 test.

### T-012 · Eventos hacia Python `[x] 2026-08-07`
- **Qué**: `on_focus_change`/`on_select` como `rx.EventHandler` (spec de 1 arg dict|None); sanitizador de `PointPayload` en bridge (Date→ISO, undefined→null, solo planos); foco perdido → None.
- **REQ**: REQ-CH-008, REQ-CH-009, REQ-CH-010
- **Depende de**: T-008
- **Done**: demo drill-down: click en punto actualiza `rx.text` con el datum; test de trigger declarado.

### T-013 · Tooltip y animación `[x] 2026-08-07` [P con T-012]
- **Qué**: `tooltip=True` → import `@tanstack/charts/tooltip` en definition; `animate=True`.
- **REQ**: REQ-CH-006, REQ-CH-007
- **Depende de**: T-009
- **Done**: tooltip visible al hover en demo; transición al mutar datos.

### T-014 · Sizing, aria y theming `[x] 2026-08-07` [P con T-012]
- **Qué**: `aspect_ratio`+`initial_width` (excluyente con height explícito), warning dev sin `aria_label`, `theme` dict → estilo inline contenedor.
- **REQ**: REQ-CH-016, REQ-CH-017, REQ-CH-018
- **Depende de**: T-009
- **Done**: tests de validación verdes; demo con tema custom en dark mode.

### T-015 · Demo de reactividad `[x] 2026-08-07`
- **Qué**: página con Var de datos + botón randomize (REQ-CH-005) y página de eventos (T-012).
- **REQ**: REQ-CH-005, REQ-CH-021
- **Depende de**: T-012, T-013
- **Done**: interacción manual verificada; `reflex export` verde.

### T-016 · Galería completa demo `[x] 2026-08-07`
- **Qué**: 1 ejemplo por marca MUST (referencias del catálogo TanStack: bar-grouped, line-gaps, donut, scatter-bubble, range-band, heatmap con cell, waffle-like con tick…).
- **REQ**: REQ-CH-021
- **Depende de**: T-015
- **Done**: 14/14 marcas visibles en la galería; consola limpia.

### T-017 · README y docs `[x] 2026-08-07` [P con T-016]
- **Qué**: instalación (uv/pip), ejemplo <10 líneas, tabla de marcas, matriz de paridad, sección de eventos y theming.
- **REQ**: REQ-CH-022
- **Depende de**: T-015
- **Done**: README renderiza bien en preview; ejemplo del README copiado a demo y funciona.

### T-018 · Build y validación de paquete `[~]` (build OK; instalación de wheel en app limpia pendiente en máquina del autor)
- **Qué**: `uv build`; instalar wheel en app Reflex limpia y verificar asset JSX + npm deps.
- **REQ**: REQ-CH-019, REQ-CH-020
- **Depende de**: T-016, T-017
- **Done**: app limpia renderiza un chart usando solo el wheel instalado.

### T-019 · Publicación `[ ]`
- **Qué**: `0.1.0a1` a TestPyPI (`uv publish --index testpypi`) → validar instalación → `0.1.0` a PyPI → `reflex component share`.
- **REQ**: REQ-CH-019
- **Depende de**: T-018
- **Done**: `uv pip install reflex-tanstack-charts` desde PyPI funciona en entorno nuevo.

## Matriz de trazabilidad

| REQ | Prioridad | Tareas | Tests que lo citan (planificados) |
|---|---|---|---|
| REQ-CH-001 | MUST | T-003 | `test_req_ch_001_component_compiles` |
| REQ-CH-002 | MUST | T-004, T-005 | `test_req_ch_002_spec_renders_mark` (snapshot) + demo export |
| REQ-CH-003 | MUST | T-007, T-008 | `test_req_ch_003_snapshot_<mark>` ×14 |
| REQ-CH-004 | MUST | T-009 | `test_req_ch_004_scale_catalog` |
| REQ-CH-005 | MUST | T-015 | demo reactividad + `test_req_ch_005_spec_is_var_compatible` |
| REQ-CH-006 | MUST | T-013 | `test_req_ch_006_tooltip_flag` |
| REQ-CH-007 | SHOULD | T-013 | `test_req_ch_007_animate_flag` |
| REQ-CH-008 | MUST | T-012 | `test_req_ch_008_focus_trigger_declared` |
| REQ-CH-009 | MUST | T-012 | `test_req_ch_009_select_trigger_declared` |
| REQ-CH-010 | MUST | T-012 | verificación manual demo + sanitizador unit |
| REQ-CH-011 | MUST | T-006, T-008 | `test_req_ch_011_datetime_iso_temporal_fields` |
| REQ-CH-012 | MUST | T-006 | `test_req_ch_012_unknown_field_raises` |
| REQ-CH-013 | MUST | T-010 | `test_req_ch_013_unsupported_mark_spec` + demo edge |
| REQ-CH-014 | MUST | T-010 | `test_req_ch_014_empty_dataset_ok` + demo edge |
| REQ-CH-015 | SHOULD | T-010 | demo edge cases |
| REQ-CH-016 | MUST | T-014 | `test_req_ch_016_sizing_validation` |
| REQ-CH-017 | MUST | T-014 | `test_req_ch_017_aria_warning` |
| REQ-CH-018 | SHOULD | T-014 | `test_req_ch_018_theme_vars` |
| REQ-CH-019 | MUST | T-001, T-018, T-019 | build + install en app limpia |
| REQ-CH-020 | MUST | T-002, T-018 | `test_req_ch_020_pinned_lib_dependencies` |
| REQ-CH-021 | MUST | T-005, T-015, T-016 | galería 14/14 + export verde |
| REQ-CH-022 | SHOULD | T-017 | revisión manual README |

SHOULD sin tarea: ninguno. Diferidos (out of scope v0.1.0): marcas avanzadas e
interacciones brush/zoom — ver PRD §5.2/§5.3.

## Registro de ejecución

| Fecha | Tareas | Resultado | Notas |
|---|---|---|---|
| 2026-08-07 | T-001..T-005 (spike) | ✅ | Versiones npm confirmadas: trío 0.7.2 + d3-scale 4.0.2 + d3-shape 3.2.0. `pie`/`tooltip` verificados con paquete instalado |
| 2026-08-07 | T-006..T-011 (TDD) | ✅ | 56 tests verdes; ruff limpio. Tests escritos antes que la implementación |
| 2026-08-07 | T-012..T-017 | ✅ | Demo: 1 página con 14/14 marcas + reactividad + eventos + theming + degradación |
| 2026-08-07 | Export E2E | ✅ | `reflex export` produce `index.html` con 15 SVG prerenderizados (SSR). **Desviaciones descubiertas → spec actualizada (Tech Design §11)**: (1) TanStack 0.7.2 publicado NO infiere escalas → el bridge infiere por tipo de dato; (2) `pie()` en 0.7.2 es un transform: la marca real es `polar({marks:[radialArc(slices)]})` — la API Python no cambia |
| 2026-08-07 | T-018 | 🔶 | `uv build` OK (wheel incluye el JSX). Instalación de wheel en app limpia + `reflex run` con bun: pendiente en máquina del autor (el sandbox no puede descargar bun; se validó con npm + timeout) |
| 2026-08-07 | T-019 | ⏸ | Requiere token PyPI del autor |
| 2026-08-07 | Delta demo-catálogo | ✅ | `changes/2026-08-07-demo-catalogo/`: demo reescrita replicando el catálogo oficial (33 réplicas + gramática completa; 51 SVG prerenderizados). REQ-CH-021 ampliado |
| 2026-08-07 | Delta bridge-dom-host | ✅ | Bug "resolveDispatcher() is null" en `reflex run` (doble React en vite dev por servir el bridge desde /public). Bridge migrado a class + `mountChart` (DOM host sin hooks); `@tanstack/react-charts` retirado; REQ-CH-002/020 enmendados. Verificado con jsdom bajo dos copias de React |

Si al implementar se descubre que la spec estaba mal: **parar, actualizar la spec
(o abrir un Delta en `changes/`), y solo entonces seguir.**
