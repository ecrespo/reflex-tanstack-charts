# reflex-tanstack-charts — Wrapper de TanStack Charts para Reflex

## Product Requirements Document (PRD)

| Campo | Valor |
|---|---|
| **Autor** | Ernesto Crespo |
| **Estado** | `DRAFT` |
| **Versión** | 1.0 |
| **Fecha** | 2026-08-07 |
| **Reviewers** | — |
| **Última actualización** | 2026-08-07 |

---

## 1. Resumen Ejecutivo

`reflex-tanstack-charts` es un componente personalizado de Reflex (paquete PyPI
instalable con `pip/uv add reflex-tanstack-charts`) que envuelve **TanStack Charts**
(`@tanstack/charts` 0.7.2 + adaptador `@tanstack/react-charts`), una gramática de
gráficos tipada, tree-shakeable y accesible (SVG por defecto, ~16 KiB gzip para una
línea compacta frente a 153+ KiB de Recharts, la librería que Reflex envuelve hoy).

El componente permite a desarrolladores Python declarar gráficos con la gramática de
marcas de TanStack (`line_y`, `bar_y`, `dot`, `area_y`, `rule_y`, `pie`, …) usando
solo estructuras serializables (dicts/listas/Vars de estado Reflex), sin escribir
JavaScript. Un único componente bridge (`TanStackChartBridge.jsx`) traduce ese
`ChartSpec` JSON a la llamada `defineChart` en el cliente.

Resuelve la ausencia total de bindings de TanStack Charts para Python: hoy quien usa
Reflex está limitado a Recharts/Plotly (pesados, sin gramática componible ni foco
accesible por teclado).

## 2. Contexto y Problema

### 2.1 Situación Actual
Reflex incluye `rx.recharts` y `rx.plotly`. TanStack Charts (lanzada como parte del
ecosistema TanStack, hoy en 0.7.2 pre-alpha) no tiene wrapper para Reflex ni para
ningún framework Python. La gramática de TanStack (marcas + canales + escalas,
inspirada en Observable Plot) está diseñada explícitamente para autoría por humanos
*y* por agentes de IA, con tipado estricto y salida SVG accesible.

### 2.2 Problema
Un desarrollador Reflex que quiere gráficos ligeros, componibles por capas
(línea + banda + reglas + anotaciones sobre las mismas escalas), con foco por
teclado y tooltips nativos, no tiene opción: debe envolver React a mano en cada
proyecto (JSX + `rx.asset` + serialización ad-hoc), un trabajo repetitivo y propenso
a errores de contrato Python↔JS.

### 2.3 Oportunidad
Ser el primer wrapper de TanStack Charts del ecosistema Reflex, publicado en PyPI y
compartido en la galería de componentes (`reflex component share`). La estructura
declarativa JSON del spec lo hace además idóneo para generación por agentes.

## 3. Usuarios Objetivo

### Persona 1: Desarrollador Python full-stack (Reflex)
- **Descripción:** construye dashboards y apps de datos en Reflex; no quiere tocar JS.
- **Necesidad principal:** declarar gráficos desde estado Reflex y recibir eventos de interacción en Python.
- **Frecuencia de uso:** diaria.
- **Nivel técnico:** medio-alto en Python, bajo en JS.

### Persona 2: Agente de IA generador de UIs
- **Descripción:** agentes que generan apps Reflex; TanStack documenta "AI authoring" como caso de primera clase.
- **Necesidad principal:** un contrato JSON estable y validado para componer gráficos sin inventar JS.
- **Frecuencia de uso:** eventual/batch.
- **Nivel técnico:** n/a.

## 4. Objetivos y Métricas de Éxito

### 4.1 Objetivos del Negocio

| Objetivo | Métrica | Target | Plazo |
|---|---|---|---|
| Publicar en PyPI | `uv publish` exitoso; instalable | v0.1.0 | fin de fase 4 |
| Cobertura de la gramática núcleo | marcas MUST soportadas | 14/14 | v0.1.0 |
| Demo pública | galería demo con 1 ejemplo por marca MUST | 100% marcas MUST | v0.1.0 |

### 4.2 Objetivos de Usuario

| Objetivo del Usuario | Indicador |
|---|---|
| Gráfico funcional en < 10 líneas de Python | ejemplo del README lo demuestra |
| Datos reactivos (Var de estado → re-render) | demo con botón que muta datos |
| Interacción de vuelta a Python | demo con `on_select` que actualiza estado |

## 5. Alcance

### 5.1 In Scope (v0.1.0)
- [ ] Componente `tanstack_chart` (clase `TanStackChart(rx.Component)`) + bridge JSX único.
- [ ] Marcas cartesianas núcleo: `line_y`, `line_x`, `area_y`, `area_x`, `bar_y`, `bar_x`, `dot`, `rule_x`, `rule_y`, `text`, `tick_x`, `tick_y`, `cell`, y polar `pie` (14 marcas MUST).
- [ ] Escalas: `linear`, `band`, `point`, `ordinal` (compactas de `@tanstack/charts-scales`); `utc`, `time`, `log`, `sqrt` (vía `d3-scale`).
- [ ] Ejes (label, grid, nice, formato de ticks por patrón), tooltip nativo, animación opcional.
- [ ] Eventos `on_focus_change` y `on_select` con payload serializado hacia handlers Reflex.
- [ ] Helpers Python tipados que validan el spec en construcción (fail-fast en Python).
- [ ] Sizing responsive: `height` fijo o `aspect_ratio` + `initial_width`.
- [ ] Theming por variables CSS `--ts-chart-*` y props de estilo por marca (`fill`, `stroke`, …).
- [ ] Empaquetado como custom component Reflex: `reflex component init` layout, build con uv, README con ejemplos, demo app.

### 5.2 Out of Scope (v0.1.0)
- Marcas avanzadas: `treemap`, `sunburst`, `sankeyDiagram`, `geoShape`, `contour`, `hexbin`, `densityContour`, `voronoi`, `delaunayLink`, `forceLayout`, `violin`, `ridgeline`, `waffle`, `box`, `difference`, regresiones — razón: superficie enorme y opciones no serializables; entran por Delta Specs incrementales.
- Interacciones avanzadas: `brushX`, `zoomX`, `crosshair`, leyendas interactivas, `renderTooltipBody` custom — requieren canal de estado bidireccional más rico.
- Renderer Canvas (`@tanstack/react-charts/canvas`) — SVG cubre el caso común.
- Transforms de datos del lado JS (`window`, `stack`, `group`, `fold`, `waterfall`) — la preparación de datos se hace en Python (pandas/polars), acorde a la filosofía de ownership de TanStack.
- Facetas y composición de vistas (`facetChart`, `composeViews`).

### 5.3 Futuras Consideraciones
- v0.2: marcas de distribución (`box`, `violin`, `ridgeline`, `waffle`) y `difference`/regresión.
- v0.3: jerárquicas y redes (`treemap`, `sunburst`, `sankey`), `crosshair`, brush/zoom con Var bidireccional.
- Registro de marcas extensible para que apps inyecten marcas custom.

## 6. Requisitos Funcionales (EARS)

### RF-Núcleo: renderizado

**REQ-CH-001 (ubicuo) · MUST** — EL SISTEMA DEBERÁ exponer una función pública
`tanstack_chart(spec=..., height=..., aria_label=...)` que compile a un componente
React `<TanStackChartBridge>` montado vía `rx.asset` + `$/public`, sin requerir que
el usuario escriba JavaScript.

**REQ-CH-002 (evento) · MUST** — CUANDO el `ChartSpec` contenga una marca soportada
con dataset no vacío y campos existentes, EL SISTEMA DEBERÁ renderizar SVG con esa
marca mediante `defineChart` + `mountChart` (DOM host vanilla de
`@tanstack/charts`). *(Enmendado por Delta bridge-dom-host: el adaptador React usa
hooks y falla con doble React en vite dev.)*

**REQ-CH-003 (ubicuo) · MUST** — EL SISTEMA DEBERÁ soportar las 14 marcas núcleo:
`line_y`, `line_x`, `area_y`, `area_x`, `bar_y`, `bar_x`, `dot`, `rule_x`, `rule_y`,
`text`, `tick_x`, `tick_y`, `cell`, `pie`; cada una con sus canales serializables
documentados en el API Spec §4.

**REQ-CH-004 (ubicuo) · MUST** — EL SISTEMA DEBERÁ resolver escalas por nombre:
`linear`, `band`, `point`, `ordinal` desde `@tanstack/charts-scales`; `utc`, `time`,
`log`, `sqrt` desde `d3-scale`; con opciones serializables (`domain`, `nice`,
`padding`, `base`).

**REQ-CH-005 (evento) · MUST** — CUANDO un `rx.Var` de estado ligado al spec cambie
(datos, colores, opciones), EL SISTEMA DEBERÁ recomputar la definición
(identidad nueva del spec → `useMemo` invalida) y re-renderizar el gráfico sin
recargar la página.

**REQ-CH-006 (opcional) · MUST** — DONDE `tooltip=True` en el spec, EL SISTEMA
DEBERÁ activar el tooltip nativo de `@tanstack/charts/tooltip`.

**REQ-CH-007 (opcional) · SHOULD** — DONDE `animate=True`, EL SISTEMA DEBERÁ pasar
`animate: true` a la definición para transiciones interrumpibles.

### RF-Interacción

**REQ-CH-008 (evento) · MUST** — CUANDO el usuario enfoque un punto (puntero o
teclado) y exista handler `on_focus_change`, EL SISTEMA DEBERÁ invocar el
EventHandler de Reflex con payload `{mark_id, key, x_value, y_value, datum}`
serializado a JSON.

**REQ-CH-009 (evento) · MUST** — CUANDO el usuario seleccione un punto (click/Enter)
y exista handler `on_select`, EL SISTEMA DEBERÁ invocar el EventHandler con el mismo
payload de REQ-CH-008.

**REQ-CH-010 (evento) · MUST** — CUANDO el foco salga del gráfico, EL SISTEMA DEBERÁ
invocar `on_focus_change` con payload `None` (limpieza de foco).

### RF-Frontera de datos

**REQ-CH-011 (ubicuo) · MUST** — EL SISTEMA DEBERÁ aceptar en el spec únicamente
valores JSON-serializables; las fechas se aceptan como `datetime`/`date` en Python,
se serializan ISO-8601, y el bridge DEBERÁ rehidratarlas a `Date` para los campos
mapeados a una escala `utc`/`time`.

**REQ-CH-012 (no deseado) · MUST** — SI un helper Python recibe, **con datos
literales**, un campo `x`/`y` que no existe en el primer registro del dataset,
ENTONCES EL SISTEMA DEBERÁ lanzar `ValueError` en construcción (fail-fast en
Python). SI los datos llegan como `rx.Var`, la validación se difiere a la
degradación del bridge (REQ-CH-013/014). *(Enmendado por Analyze A-04.)*

**REQ-CH-013 (no deseado) · MUST** — SI el bridge recibe una marca de tipo no
soportado, ENTONCES EL SISTEMA DEBERÁ omitir esa marca, emitir `console.warn` con el
tipo recibido y renderizar un aviso visible dentro del contenedor del gráfico.

**REQ-CH-014 (no deseado) · MUST** — SI un dataset llega vacío, ENTONCES EL SISTEMA
DEBERÁ renderizar el gráfico sin esa marca (ejes/estructura intactos) sin lanzar
excepción no capturada.

**REQ-CH-015 (no deseado) · SHOULD** — SI la construcción de `defineChart` lanza en
runtime, ENTONCES el bridge DEBERÁ capturar el error (error boundary), mostrar un
placeholder con el mensaje y no propagar la excepción a la app Reflex.

### RF-Presentación

**REQ-CH-016 (ubicuo) · MUST** — EL SISTEMA DEBERÁ soportar sizing responsive:
`height` fijo (default 320 px) o `aspect_ratio` + `initial_width`; con ancho fluido
del contenedor en ambos casos.

**REQ-CH-017 (ubicuo) · MUST** — EL SISTEMA DEBERÁ pasar `aria_label` al `<Chart>`;
SI no se provee, el componente Python DEBERÁ emitir un warning de accesibilidad en
consola del backend en modo dev.

**REQ-CH-018 (opcional) · SHOULD** — DONDE se provea `theme` (dict de variables
`--ts-chart-*` u overrides), EL SISTEMA DEBERÁ aplicarlas como estilo inline del
contenedor para integrarse con light/dark mode.

### RF-Empaquetado

**REQ-CH-019 (ubicuo) · MUST** — EL SISTEMA DEBERÁ publicarse como paquete
`reflex-tanstack-charts` (import `reflex_tanstack_charts`) con layout de custom
component de Reflex, licencia Apache-2.0, construible con `uv build` y publicable
con `uv publish`.

**REQ-CH-020 (ubicuo) · MUST** — EL SISTEMA DEBERÁ declarar en `lib_dependencies`
versiones exactas: `@tanstack/charts@0.7.2`, `@tanstack/charts-scales@0.7.2`,
`d3-scale@4.0.2` y `d3-shape@3.2.0`. *(Enmendado por Delta bridge-dom-host:
`@tanstack/react-charts` retirado — el bridge monta con el DOM host.)*

**REQ-CH-021 (ubicuo) · MUST** — EL SISTEMA DEBERÁ incluir una demo app Reflex
(`tanstack_charts_demo/`) con ≥1 ejemplo por marca MUST, ejemplos de reactividad
(REQ-CH-005) y de eventos (REQ-CH-008/009).

**REQ-CH-022 (ubicuo) · SHOULD** — EL SISTEMA DEBERÁ documentar en README:
instalación, ejemplo mínimo (<10 líneas), tabla de marcas soportadas y matriz de
paridad con la gramática TanStack.

**REQ-CH-023 (opcional) · SHOULD** — DONDE se provea `color` con escala `ordinal`
(`domain` + `range` de colores), EL SISTEMA DEBERÁ aplicarla como escala de color
del gráfico para las series (`z`). *(Añadido por Analyze A-01.)*

## 7. Requisitos No Funcionales

### Rendimiento
- Bundle añadido al frontend ≤ ~35 KiB gzip (rango publicado del suite de 12 charts de TanStack: 26.6–32.1 KiB).
- Re-render por cambio de Var sin trabajo perceptible extra: el spec se memoiza por identidad.

### Seguridad
- Sin `eval`/`new Function` en el bridge; sin JS arbitrario desde Python (Constitución Art. 2).
- Formatos de ticks como patrones declarativos (ej. `{"style": "percent"}`), nunca funciones serializadas.

### Compatibilidad
- Python ≥ 3.12, Reflex ≥ 0.8. TanStack Charts 0.7.2 exacto (pre-alpha; ver Riesgos).

### Accesibilidad
- SVG accesible por defecto de TanStack; `aria_label` promovido a prop de primera clase; foco por teclado habilitado por defecto.

### Observabilidad
- Errores del bridge con `console.warn`/`console.error` prefijados `[reflex-tanstack-charts]`.

## 8. Restricciones y Dependencias

### Restricciones Técnicas
- La API de TanStack (`defineChart` con funciones factory) no es serializable → obliga al patrón bridge con registro de marcas/escalas por nombre.
- Reflex no permite hooks de su sistema de eventos desde JS arbitrario → los eventos se declaran como `rx.EventHandler` con spec de argumentos serializables.

### Restricciones de Negocio
- Licencia Apache-2.0; prefijo `reflex-` en el nombre del paquete.

### Dependencias Externas

| Dependencia | Tipo | Owner | Estado | Riesgo |
|---|---|---|---|---|
| `@tanstack/charts` 0.7.2 | npm | TanStack | pre-alpha | **Alto**: API inestable |
| `@tanstack/react-charts` | npm | TanStack | pre-alpha | Alto |
| `@tanstack/charts-scales` | npm | TanStack | pre-alpha | Medio |
| `d3-scale` | npm | d3 | estable | Bajo |
| `reflex` ≥ 0.8 | PyPI | Reflex | estable | Bajo |

## 9. User Stories

### Épica: Gráficos declarativos en Reflex

**US-001:** Como desarrollador Reflex, quiero declarar un gráfico de barras desde una
lista de dicts de mi estado, para visualizar datos sin escribir JS.
- Criterios: REQ-CH-001, 002, 003, 016.

**US-002:** Como desarrollador Reflex, quiero que el gráfico se actualice cuando mi
estado cambie, para construir dashboards vivos.
- Criterios: REQ-CH-005.

**US-003:** Como desarrollador Reflex, quiero recibir en un handler de Python el
punto que el usuario seleccionó, para hacer drill-down.
- Criterios: REQ-CH-008, 009, 010.

**US-004:** Como agente de IA, quiero un contrato JSON validado (helpers fail-fast),
para generar gráficos correctos sin inspeccionar JS.
- Criterios: REQ-CH-011, 012, 013.

**US-005:** Como mantenedor, quiero publicar el paquete en PyPI con uv, para
compartirlo con la comunidad Reflex.
- Criterios: REQ-CH-019, 020, 021, 022.

## 10. Wireframes / Mockups
- Referencia visual: catálogo oficial <https://tanstack.com/charts/catalog> (categorías: bar, trend, distribution, polar, interaction, composition, comparison…). La demo replica en Reflex los ejemplos `bar-grouped`, `01-line-gaps`, `77-donut`, `scatter-bubble`, `03-temperature-range-band`.

## 11. Riesgos y Mitigaciones

| Riesgo | Probabilidad | Impacto | Mitigación |
|---|---|---|---|
| TanStack Charts 0.7.x rompe API (pre-alpha) | Alta | Alto | Pin exacto (Art. 4); bumps solo por Delta Spec; matriz de marcas re-verificada |
| Payload de eventos no serializable (datum con Date) | Media | Medio | Sanitizador de payload en bridge (Date→ISO) antes de emitir a Reflex |
| Divergencia versión charts vs charts-scales vs react-charts | Media | Medio | Verificar versiones publicadas en npm en F1-02 y fijar el trío coherente |
| `rx.asset` + JSX con imports npm no resuelve en build | Baja | Alto | Spike temprano (T-004) que compila la demo antes de seguir |

## 12. Timeline Estimado

| Fase | Duración Estimada | Entregable |
|---|---|---|
| Spec & Design (SDD) | hecho | specs/ aprobadas |
| F1 Scaffolding + spike bridge | 2-3 d | demo compila con 1 marca |
| F2 Núcleo (spec, helpers, escalas) | 3-4 d | 14 marcas MUST |
| F3 Interacción + theming | 2 d | eventos y tooltip |
| F4 Empaquetado + demo + docs | 2 d | `uv build` OK, README |

---

## Constitution check
- Art. 1 (uv): plan y tasks usan solo uv. ✓
- Art. 2 (frontera serializable): REQ-CH-011/012; sin JS desde Python. ✓
- Art. 3 (paridad de nombres): REQ-CH-003 usa nombres TanStack en snake_case. ✓
- Art. 4 (pins npm): REQ-CH-020. ✓
- Art. 7 (degradación): REQ-CH-013/014/015. ✓

## Historial de Cambios

| Versión | Fecha | Autor | Cambios |
|---|---|---|---|
| 1.0 | 2026-08-07 | Ernesto Crespo | Versión inicial |

## Aprobaciones

| Rol | Nombre | Fecha | Estado |
|---|---|---|---|
| Product/Tech Lead | Ernesto Crespo | | ☐ Pendiente |
