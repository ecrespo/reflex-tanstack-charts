# reflex-tanstack-charts — Implementation Plan

## Metadata

| Campo | Valor |
|---|---|
| **Autor** | Ernesto Crespo |
| **Estado** | `DRAFT` |
| **Versión** | 1.0 |
| **Fecha** | 2026-08-07 |
| **PRD** | `specs/prd/reflex-tanstack-charts.md` |
| **Tech Design** | `specs/technical/architecture.md` |
| **Data Model** | `specs/data-model/chartspec-schema.md` |
| **API Spec** | `specs/api/component-api-v1.md` |

---

## 1. Resumen de Implementación

4 fases secuenciales con un **spike de riesgo al frente** (F1 valida que
`rx.asset` + imports npm del bridge compilan antes de invertir en la superficie
completa). Desarrollo en solitario con agente; primera tanda supervisada de 3-5
tareas por fase.

**Duración total estimada:** 9-11 días efectivos.
**Equipo requerido:** 1 dev (+ agente).
**Fecha objetivo:** v0.1.0 en PyPI ~2026-08-21.

## 2. Pre-requisitos

| Pre-requisito | Owner | Estado | Fecha Límite |
|---|---|---|---|
| Specs SDD aprobadas (este directorio) | Ernesto | ☐ Pendiente | antes de F1 |
| Cuenta PyPI + token (`uv publish`) | Ernesto | ☐ Pendiente | antes de F4 |
| Node/npm disponible vía Reflex (`.web`) | Reflex CLI | ☑ implícito | — |
| Verificar en npm el trío de versiones `@tanstack/charts@0.7.2` / `charts-scales` / `react-charts` compatibles | Ernesto | ☐ Pendiente | F1 (gate T-002) |

## 3. Fases de Implementación

---

### Fase 1: Scaffolding + Spike del bridge (riesgo primero)

**Duración:** 2-3 días
**Objetivo:** estructura de custom component funcionando end-to-end con **una** marca (`barY`) renderizando en la demo. Desriesga R4 (asset+npm) y la pregunta abierta de versiones.

| ID | Tarea | Estimación | Dependencia | REQs |
|---|---|---|---|---|
| F1-01 | `reflex component init` (uv como gestor; ajustar pyproject: nombre, Apache-2.0, python>=3.12) | 0.5d | — | REQ-CH-019 |
| F1-02 | Verificar/fijar versiones npm del trío TanStack + d3-scale | 0.5d | — | REQ-CH-020 |
| F1-03 | `TanStackChart(rx.Component)` mínimo: `library=$/public+rx.asset`, tag, props `spec/height/ariaLabel` | 0.5d | F1-01 | REQ-CH-001 |
| F1-04 | Bridge v0: registro con `barY` + escalas `band`/`linear`, `<Chart>` render | 1d | F1-02, F1-03 | REQ-CH-002 |
| F1-05 | Demo app: página con bar chart estático; `reflex run` y `reflex export` verdes | 0.5d | F1-04 | REQ-CH-021 (parcial) |

**Done:** demo muestra el bar chart de frecuencia de letras (ejemplo React Quick
Start de TanStack) declarado 100% en Python; `reflex export` sin errores.

---

### Fase 2: Superficie núcleo (14 marcas, escalas, ejes, validación)

**Duración:** 3-4 días
**Objetivo:** todos los MUST de renderizado y frontera de datos.

| ID | Tarea | Estimación | Dependencia | REQs |
|---|---|---|---|---|
| F2-01 | `marks.py`: base `_mark()` + validación campos + snake→camel + serialización datetime/`temporal_fields` | 1d | F1-05 | REQ-CH-011, 012 |
| F2-02 | 13 helpers restantes + registro JS correspondiente | 1.5d | F2-01 | REQ-CH-003 |
| F2-03 | `scales.py` + `axis.py` + registros JS (8 escalas, curvas, Intl formats) | 1d | F2-01 | REQ-CH-004 |
| F2-04 | Degradación en bridge: marca desconocida, dataset vacío, error boundary, gate de `version` | 0.5d | F2-02 | REQ-CH-013, 014, 015 |
| F2-05 | Tests unit + snapshots de contrato (14 marcas) | 1d | F2-02..04 | Art. 6 |

**Done:** `pytest` verde; snapshot por marca; demo renderiza línea con fechas
(escala `utc`) y donut (`pie` con `inner_radius`).

---

### Fase 3: Interacción, reactividad y theming

**Duración:** 2 días

| ID | Tarea | Estimación | Dependencia | REQs |
|---|---|---|---|---|
| F3-01 | EventHandlers `on_focus_change`/`on_select` + sanitizador de payload en bridge | 1d | F2-02 | REQ-CH-008, 009, 010 |
| F3-02 | `tooltip` y `animate` en spec y bridge | 0.5d | F2-03 | REQ-CH-006, 007 |
| F3-03 | Sizing (`aspect_ratio`/`initial_width`) + `theme` vars CSS + warning aria_label | 0.5d | F2-03 | REQ-CH-016, 017, 018 |
| F3-04 | Demo: página de reactividad (mutar Var) + página de eventos (drill-down a estado) | 0.5d | F3-01 | REQ-CH-005, 021 |

**Done:** en la demo, click en un punto actualiza texto de estado Python;
botón "randomize" re-renderiza el gráfico animado.

---

### Fase 4: Empaquetado, docs y publicación

**Duración:** 2 días

| ID | Tarea | Estimación | Dependencia | REQs |
|---|---|---|---|---|
| F4-01 | README: instalación, ejemplo <10 líneas, tabla de marcas, matriz paridad TanStack | 0.5d | F3-04 | REQ-CH-022 |
| F4-02 | Galería demo completa: 1 ejemplo por marca MUST (referencia catálogo TanStack) | 1d | F3-04 | REQ-CH-021 |
| F4-03 | `uv build` (equivale a `reflex component build`) + instalar wheel en app limpia | 0.5d | F4-01 | REQ-CH-019 |
| F4-04 | Publicar `0.1.0a1` a TestPyPI → validar → `0.1.0` a PyPI → `reflex component share` | 0.5d | F4-03 | REQ-CH-019 |

**Done global:** ver §7.

## 4. Mapa de Dependencias

```
F1 (spike bridge) ──▶ F2 (superficie núcleo) ──▶ F3 (interacción) ──▶ F4 (publicación)
     │
     └─ F1-02 (versiones npm) es gate duro: si el trío no es coherente,
        volver a Tech Design (pregunta abierta 1) antes de F2.
```

## 5. Riesgos de Implementación

| Riesgo | Probabilidad | Impacto | Mitigación | Owner |
|---|---|---|---|---|
| API 0.7.x difiere de docs (pre-alpha, docs siguen main) | Alta | Alto | Spike F1 con paquete real instalado; ajustar registro, no la API Python | Ernesto |
| `pie`/polar no exportado como asume el API Spec | Media | Medio | confirmar import en F1; si falta, degradar `pie` a SHOULD y abrir Delta | Ernesto |
| Payload de eventos difiere del tipado docs | Media | Medio | log del objeto real en spike; sanitizador tolerante | Ernesto |
| `rx.asset(shared=True)` no copia JSX en build de paquete | Baja | Alto | F4-03 instala wheel en app limpia y lo verifica | Ernesto |

## 6. Comunicación y Seguimiento

Proyecto individual: progreso se marca en `specs/tasks/mvp-tasks.md` (checkbox +
fecha) — cualquier sesión (humana o agente) retoma desde ahí. Desviaciones de spec
→ parar, actualizar spec o abrir Delta en `changes/`, luego seguir.

## 7. Definición de Done (Global v0.1.0)

- [ ] 14 marcas MUST renderizan en la demo (REQ-CH-003, 021)
- [ ] `pytest` verde; todo MUST con test que cita su REQ (Art. 6)
- [ ] `ruff check` + `ruff format --check` + `ty check` verdes (Art. 5; tool fijado: `ty` — Analyze A-07)
- [ ] `reflex export` de la demo sin errores
- [ ] `uv build` produce sdist+wheel; wheel instalable en app limpia
- [ ] README completo; specs actualizadas si hubo cambios
- [ ] Publicado en PyPI y compartido con `reflex component share`

---

## Constitution check
- Art. 1: todas las tareas usan uv (`uv build`, `uv publish`, `uv run pytest`). ✓
- Art. 6: F2-05 y matriz de trazabilidad en tasks. ✓
- Art. 8: fases gated por specs aprobadas (pre-requisito 1). ✓

## Historial de Cambios

| Versión | Fecha | Autor | Cambios |
|---|---|---|---|
| 1.0 | 2026-08-07 | Ernesto Crespo | Versión inicial |
