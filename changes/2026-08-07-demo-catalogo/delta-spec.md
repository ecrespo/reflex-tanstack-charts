# Delta Spec — Demo basada en el catálogo oficial de TanStack Charts

> Estado: `APPLIED` (2026-08-07) · Afecta a: PRD REQ-CH-021 (demo) y demo app.
> No modifica el contrato ChartSpec v1 ni la API Python.

## Motivación

Petición del usuario: la demo debe replicar los ejemplos de
<https://tanstack.com/charts/catalog> en lugar de una galería mínima por marca.

## Cambio

REQ-CH-021 se amplía: la demo DEBERÁ replicar todo ejemplo del catálogo oficial
que sea expresable con el contrato v1 (14 marcas + 8 escalas + color ordinal +
tooltip + eventos), con los transforms de datos (bins, stacking painter, medias
móviles, OLS, ranks, streamgraph, waffle, likert divergente) implementados en
Python (`_data.py`), y DEBERÁ listar explícitamente los ejemplos no expresables
con la marca/extensión que requieren (mapa de ruta v0.2+).

## Resultado

- 33 réplicas del catálogo + 4 tarjetas de gramática restante + 3 de interacción
  (50 instancias de chart en la página; 51 SVG prerenderizados verificados por SSR).
- Cobertura de marcas: 14/14 MUST siguen presentes (REQ-CH-021 original intacto).
- Fuera de alcance documentado en la propia página: distribución avanzada,
  espacial/geo, jerarquía/redes, polar avanzado, financieros/rect, interacción
  avanzada (brush/zoom/cursores), motion — con el ejemplo del catálogo y la marca
  requerida por grupo.
- Aproximaciones declaradas en tarjeta: `bar-grouped` (categorías compuestas),
  `bar-stacked`/áreas apiladas (técnica painter con acumulados), `33-difference`
  (banda neutra sin segmentación por signo), `16-lollipop`/`17-dumbbell`/
  `14-error-bars` (segmentos como series z de 2 puntos).

## Verificación

`pytest` 56/56 · `ruff` limpio · export SSR: `index.html` con 51 `<svg>` y las
32 sondas de contenido presentes.
