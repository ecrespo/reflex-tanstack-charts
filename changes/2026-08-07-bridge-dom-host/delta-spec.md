# Delta Spec — Bridge sin adaptador React (DOM host vanilla)

> Estado: `APPLIED` (2026-08-07) · Afecta a: Tech Design (DD-006), PRD REQ-CH-002 y
> REQ-CH-020, bridge JSX, `LIB_DEPENDENCIES`. No cambia la API Python ni el
> contrato ChartSpec v1.

## Bug origen (reporte del usuario)

`reflex run` (vite dev) lanzaba
`TypeError: can't access property "useMemo", resolveDispatcher() is null` al
montar `TanStackChartBridge`.

**Causa raíz:** el bridge se sirve desde `/public/external/...` — Vite trata
`public/` como assets estáticos y NO lo incluye en el escaneo de optimizeDeps.
Sus dependencias se descubren en runtime → segunda pasada de optimización → dos
copias pre-empaquetadas de React coexisten (hashes `?v=` distintos: `react.js
?v=324d…` vs `react-dom_client.js?v=1b3d…`). Con dos copias, el dispatcher de
hooks es `null`. El build de producción no lo sufre porque todo se empaqueta en
un solo grafo — por eso el export SSR pasaba y el dev no.

Reproducido de forma determinista en sandbox: bundle del bridge con su propia
copia de React inlined + `react-dom` externo → crash idéntico; primero en el
`useMemo` del bridge y, eliminado ese, **dentro de `<Chart>` de
`@tanstack/react-charts`** (el adaptador también usa hooks). Quitar hooks solo
del bridge era insuficiente.

## Decisión (DD-006)

El bridge abandona el adaptador React y monta con el **DOM host vanilla**
(`mountChart` de `@tanstack/charts/dom`, framework-free, cero hooks) desde un
**class component** (`componentDidMount`/`DidUpdate`/`WillUnmount` +
`host.update()`/`destroy()`). Los class components y la creación de elementos
funcionan entre copias de React; los hooks no → inmune por construcción.

- `useMemo` → `WeakMap` por identidad del spec (misma semántica, REQ-CH-005).
- Error boundary → `try/catch` en el montaje + `setState` con placeholder
  (REQ-CH-015 intacto).
- `ChartHostOptions` cubre 1:1 lo que usaba `<Chart>`: `definition`, `height`,
  `aspectRatio`, `initialWidth`, `ariaLabel`, `onFocusChange`, `onSelect`.

## Enmiendas

- **REQ-CH-002**: "…renderizar SVG con esa marca mediante `defineChart` +
  `mountChart` (DOM host de `@tanstack/charts`)" (antes: `<Chart>` de
  `@tanstack/react-charts`).
- **REQ-CH-020**: pins quedan en `@tanstack/charts@0.7.2`,
  `@tanstack/charts-scales@0.7.2`, `d3-scale@4.0.2`, `d3-shape@3.2.0` —
  `@tanstack/react-charts` deja de ser dependencia.

## Trade-off aceptado

El DOM host monta en cliente: el HTML prerenderizado ya no contiene los SVG
(contiene los contenedores, que hidratan al cargar). Se pierde el SVG estático
del prerender a cambio de dev servible desde `public/` sin riesgo de doble
React. Revisitable si TanStack publica un adaptador sin hooks o Reflex expone
`optimizeDeps` para assets.

## Verificación

- jsdom + **dos copias de React** (escenario del bug): 11/11 casos renderizan
  SVG (incl. pie anidado, capas temporales, degradación, versión futura).
- `pytest` 56/56 (pin actualizado por TDD) · `ruff` limpio.
- Export producción: prerender verde, 52 contenedores en `index.html`, galería
  completa presente.

## Nota operativa

Tras actualizar, **borrar la caché de Vite** para eliminar los grafos duplicados
ya persistidos: `rm -rf tanstack_charts_demo/.web` (o al menos
`.web/node_modules/.vite`) antes de `reflex run`.
