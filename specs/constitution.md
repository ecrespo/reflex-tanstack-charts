# Constitución — reflex-tanstack-charts

> Versión 1.0 · Ratificada: 2026-08-07 · Última enmienda: 2026-08-07
> Ámbito: repositorio `reflex-tanstack-charts` (componente personalizado de Reflex que envuelve TanStack Charts)

## Artículos

### Art. 1 — Gestión de dependencias Python
EL EQUIPO DEBERÁ usar `uv` como único gestor de paquetes y entornos (instalación,
lock, build y publish con `uv build` / `uv publish`); ningún `pip install` ni
`poetry` en scripts, CI o documentación.
*Racional: un solo gestor reproducible; el usuario del repo estandarizó uv.*

### Art. 2 — Frontera serializable
EL SISTEMA DEBERÁ aceptar en su API Python únicamente valores serializables a JSON
(el `ChartSpec`); ninguna API pública aceptará strings de JavaScript arbitrario para
inyectar en el frontend. Fechas viajan como ISO-8601 y se rehidratan a `Date` en el
bridge JS.
*Racional: evita XSS/inyección y mantiene el contrato Python↔JS verificable.*

### Art. 3 — Paridad de vocabulario con TanStack
EL SISTEMA DEBERÁ conservar los nombres de la gramática de TanStack Charts
(`lineY`, `barY`, `dot`, `ruleY`, canales `x/y/z/fill/stroke`…) traducidos solo a
snake_case en Python (`line_y`, `bar_y`); ningún renombre semántico propio.
*Racional: la documentación upstream sigue siendo válida para el usuario; menos deriva terminológica.*

### Art. 4 — Dependencias npm fijadas
EL SISTEMA DEBERÁ declarar `@tanstack/charts`, `@tanstack/charts-scales` y
`@tanstack/react-charts` con versión exacta (pinned) en `lib_dependencies`, y todo
bump de versión upstream DEBERÁ entrar vía Delta Spec con la matriz de marcas re-verificada.
*Racional: TanStack Charts es pre-alpha (0.7.x); su API puede romper entre releases.*

### Art. 5 — Calidad de código
EL EQUIPO DEBERÁ mantener `ruff check` + `ruff format --check` + `ty check` (o
`pyright`) en verde antes de cada merge; el bridge JSX pasa por `prettier --check`.
*Racional: gate automático barato; el repo es una librería pública.*

### Art. 6 — Trazabilidad de requisitos
EL SISTEMA DEBERÁ cubrir todo requisito MUST (REQ-CH-NNN) con ≥1 tarea en
`specs/tasks/` y ≥1 test automatizado que cite el REQ en su nombre o docstring antes
de cerrar la tarea.
*Racional: columna vertebral del SDD; sin esto la spec es teatro.*

### Art. 7 — Degradación sin ruptura
EL SISTEMA DEBERÁ degradar con mensaje visible y `console.warn` — nunca con una
excepción no capturada que rompa la página — ante specs inválidos, marcas no
soportadas o datasets vacíos.
*Racional: un chart roto no puede tumbar la app Reflex del usuario.*

### Art. 8 — Proceso spec-anchored
EL EQUIPO DEBERÁ obtener spec aprobada antes de implementar trabajo ≥ feature media;
cambios a features ya spec-adas entran por `changes/` como Delta Spec y se pliegan a
`specs/` al aprobarse. Actualizar la spec es parte del Definition of Done.
*Racional: las specs de `specs/` son la verdad actual del proyecto.*

## Restricciones del stack

Decidido, no se rediscute por feature:

| Área | Decisión |
|---|---|
| Lenguaje backend | Python ≥ 3.12 (`.python-version` del repo) |
| Framework | Reflex ≥ 0.8 (custom component, `reflex component init/build`) |
| Gestor Python | uv (Art. 1) |
| Librería de charts | TanStack Charts 0.7.2 (pre-alpha) + `@tanstack/react-charts` |
| Escalas compactas | `@tanstack/charts-scales` (linear, band, point, ordinal) |
| Escalas avanzadas | `d3-scale` solo para `utc`, `time`, `log`, `sqrt` |
| Bridge frontend | Un único `TanStackChartBridge.jsx` local vía `rx.asset(shared=True)` + `$/public` |
| Licencia | MIT (enmienda 2026-08-07: el repo ya tenía LICENSE MIT del autor; prevalece sobre el default Apache-2.0 de Reflex) |
| Nombre del paquete | `reflex-tanstack-charts` (prefijo `reflex-` obligatorio para búsqueda en PyPI) |
| Tests | pytest (unidad y compilación de componente); validación JS por build de la demo app |

## Enmiendas

| Fecha | Artículo | Cambio | Razón | Aprobado por |
|---|---|---|---|---|
| 2026-08-07 | Stack (licencia) | Apache-2.0 → MIT | LICENSE MIT preexistente del autor en el repo | Ernesto |

## Constitution check (usar en cada artefacto)

Al final de cada PRD / Tech Design / Plan: qué artículos aplican y cómo se cumplen,
o qué excepción se pide y por qué. Excepción sin justificación escrita = violación.
