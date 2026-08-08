# reflex-tanstack-charts — Technical Design Document

## Metadata

| Campo | Valor |
|---|---|
| **Autor** | Ernesto Crespo |
| **Estado** | `DRAFT` |
| **Versión** | 1.0 |
| **Fecha** | 2026-08-07 |
| **PRD Relacionado** | `specs/prd/reflex-tanstack-charts.md` |
| **API Spec Relacionado** | `specs/api/component-api-v1.md` |

---

## 1. Contexto

TanStack Charts expone su API como llamadas JS (`defineChart({ marks: [barY(data,
{...})], x: { scale: scaleBand }, ... })`) con factories y closures — **no
serializable**. Reflex, en cambio, compila Python a React pasando props
serializables. El puente entre ambos mundos es el corazón del diseño: un
componente React local (`TanStackChartBridge.jsx`, incluido en el paquete vía
`rx.asset(shared=True)` y referenciado con `library="$/public/..."`) que recibe un
`ChartSpec` JSON y lo **interpreta** contra un registro estático de marcas y
escalas importadas de `@tanstack/charts*`.

Se construye como custom component oficial de Reflex (layout de
`reflex component init`), publicable en PyPI con uv.

## 2. Objetivos Técnicos

- **Correctitud:** el ChartSpec renderiza exactamente la definición TanStack equivalente; tests de compilación por marca.
- **Rendimiento:** memoización por identidad del spec; bundle ≤ ~35 KiB gzip añadidos.
- **Mantenibilidad:** registro de marcas = un dict; añadir una marca nueva ≈ 5 líneas JS + helper Python + test.
- **Robustez:** ninguna entrada inválida rompe la página (error boundary + placeholders).

## 3. Arquitectura Propuesta

### 3.1 Diagrama de Alto Nivel

```
┌────────────────────────────┐ compila  ┌──────────────────────────────┐
│  App Reflex (Python)       │ ───────▶ │  Frontend React (.web)       │
│                            │          │                              │
│ tanstack_chart(            │  props   │  <TanStackChartBridge        │
│   marks=[bar_y(data,…)],   │  JSON    │     spec={…}                 │
│   y=axis(grid=True),       │ ───────▶ │     onFocusChange={…}/>      │
│   on_select=State.pick)    │          │      │ interpreta            │
└────────────┬───────────────┘          │      ▼                       │
             │ eventos (payload §5 API) │  MARK_REGISTRY / SCALES      │
             ◀──────────────────────────│  defineChart + useMemo       │
   State.pick(point) en Python          │      │                       │
                                        │      ▼                       │
                                        │  <Chart> @tanstack/          │
                                        │   react-charts (SVG)         │
                                        └──────────────────────────────┘
```

### 3.2 Componentes

| Componente | Tecnología | Responsabilidad |
|---|---|---|
| `TanStackChart(rx.Component)` | Python / Reflex | Declarar props (`spec`, `height`, …), `library="$/public"+rx.asset("TanStackChartBridge.jsx", shared=True)`, `tag="TanStackChartBridge"`, EventHandlers |
| Helpers de marcas (`marks.py`) | Python | Construir/validar dicts de marca (REQ-CH-012), serializar datetimes, marcar `temporal_fields` |
| `scales.py` / `axis.py` | Python | `scale()`, `axis()`, validación de catálogo |
| `TanStackChartBridge.jsx` | React 19 + `@tanstack/*` | Interpretar spec → `defineChart`; registro de marcas/escalas/curvas/formatos; error boundary; sanitizar payloads de eventos |
| Demo app | Reflex | Galería de las 14 marcas + reactividad + eventos |

### 3.3 Flujo de Datos

**Flujo: render inicial**

```
1. Usuario llama tanstack_chart(marks=[...], ...) en una página Reflex
2. Helpers validan (fail-fast) y producen ChartSpec dict
3. Reflex serializa el spec como prop (rx.Var si hay estado)
4. Bridge monta: useMemo(spec) → buildDefinition(spec)
   a. por cada mark: MARK_REGISTRY[type](rehidratar(data), mapOptions(options))
   b. rehidratar: temporal_fields → new Date(iso)
   c. ejes: SCALE_REGISTRY[scale.type](options), formatos → Intl.*Format
   d. tooltip=true → añade tooltip de @tanstack/charts/tooltip
5. <Chart definition height ariaLabel onFocusChange onSelect/> renderiza SVG
```

**Flujo: actualización reactiva (REQ-CH-005)**

```
1. Evento Python muta State.data → Reflex re-renderiza con nuevo prop spec
2. Identidad de spec cambia → useMemo recomputa definition → Chart re-renderiza
   (con animate=true, transición interrumpible de TanStack)
```

**Flujo de error / degradación**

```
1. Marca desconocida → se omite, console.warn, overlay "marca X no soportada"  (REQ-CH-013)
2. Dataset vacío → marca omitida silenciosamente                              (REQ-CH-014)
3. Throw en defineChart/render → ErrorBoundary → placeholder con mensaje       (REQ-CH-015)
4. spec.version > soportada → placeholder "actualiza reflex-tanstack-charts"
```

## 4. Decisiones de Diseño

### DD-001: Bridge interpretador con registro estático (vs. generación de código JS)

- **Decisión:** un único JSX que interpreta un ChartSpec JSON contra registros estáticos de marcas/escalas.
- **Contexto:** `defineChart` exige factories JS; Reflex solo pasa props serializables.
- **Alternativas evaluadas:**

| Opción | Pros | Contras |
|---|---|---|
| **A (elegida): bridge intérprete + registro** | Serializable, seguro (sin eval), testeable, tree-shaking controlado, apto para agentes | Superficie limitada a lo registrado |
| B: generar código JS por gráfico (`rx.Var` strings / custom_code) | Superficie total de TanStack | Inyección de código, imposible de validar, frágil al compilar |
| C: wrapper 1:1 de cada mark como componente Reflex | Idiomático Reflex | `defineChart` no es JSX componible; los marks no son componentes React |

- **Justificación:** única opción que cumple la Constitución Art. 2 y sirve el caso de agentes (US-004).
- **Consecuencias:** cada marca nueva requiere tocar registro JS + helper Python (barato, ~5 líneas cada lado).

### DD-002: Imports estáticos de todas las marcas MUST (vs. dynamic import)

- **Decisión:** el bridge importa estáticamente `barY, lineY, … , pie` y las 4 escalas compactas + 4 de d3-scale.
- **Contexto:** tree-shaking elimina lo no usado solo con imports estáticos analizables; dynamic import complica SSR de Reflex.
- **Justificación:** 14 marcas núcleo son pequeñas (paquete completo 12-charts ≈ 26-32 KiB gzip); simplicidad > micro-optimización.
- **Consecuencias:** bundle fijo aunque la app use 1 marca; aceptable frente al NFR (≤ ~35 KiB).

### DD-003: Formatos de ticks declarativos vía Intl (vs. funciones)

- **Decisión:** `ticks.format` es un objeto de opciones para `Intl.NumberFormat` / `Intl.DateTimeFormat`, nunca una función.
- **Justificación:** serializable (Art. 2), cubre percent/currency/compact/fechas — el 95% de los casos del catálogo TanStack.
- **Consecuencias:** formatos exóticos requerirán extensión futura del catálogo (Delta).

### DD-004: Datos por marca (mark-local data), sin datasets compartidos nombrados

- **Decisión:** cada marca lleva su propio `data` embebido, igual que la gramática TanStack (mark-local data).
- **Alternativa:** sección `datasets` con referencias por nombre — menos duplicación si varias marcas comparten datos.
- **Justificación:** paridad 1:1 con TanStack (Art. 3); la duplicación JSON entre marcas es rara y barata. Revisitable por Delta si aparece dolor real.

### DD-005: Eventos con un solo argumento dict sanitizado

- **Decisión:** `on_focus_change`/`on_select` emiten un único dict (o None) ya sanitizado en JS.
- **Contexto:** los event triggers de Reflex declaran specs de argumentos serializables; `point.datum` puede contener `Date`.
- **Justificación:** contrato estable y simple para handlers Python (`point: dict | None`).

## 5. Patrones y Convenciones

### 5.1 Estructura del Código (layout custom component de Reflex)

```
reflex-tanstack-charts/
├── pyproject.toml                  # hatchling/uv_build; deps: reflex>=0.8
├── README.md
├── LICENSE                          # Apache-2.0
├── specs/                           # SDD (este directorio)
├── custom_components/
│   └── reflex_tanstack_charts/
│       ├── __init__.py              # re-exporta API pública §2.1 del API Spec
│       ├── component.py             # TanStackChart(rx.Component) + tanstack_chart()
│       ├── marks.py                 # 14 helpers + _Mark base + validación
│       ├── scales.py                # scale(), catálogo, validación
│       ├── axis.py                  # axis(), formatos declarativos
│       ├── _serialize.py            # datetime→ISO, detección temporal_fields
│       └── TanStackChartBridge.jsx  # bridge (junto al .py, patrón local components)
├── tanstack_charts_demo/            # demo app Reflex (galería)
│   ├── rxconfig.py
│   └── tanstack_charts_demo/tanstack_charts_demo.py
└── tests/
    ├── test_marks.py                # validación y serialización por marca
    ├── test_scales_axis.py
    ├── test_component.py            # el componente compila; props correctas
    └── test_spec_contract.py        # snapshots del ChartSpec (contrato v1)
```

### 5.2 Patrones Aplicados

| Patrón | Dónde | Por qué |
|---|---|---|
| Registry | bridge (`MARK_REGISTRY`, `SCALE_REGISTRY`, `CURVES`, formatos) | despacho por nombre sin eval |
| Builder + validación fail-fast | helpers Python | errores en la capa donde el usuario los ve (REQ-CH-012) |
| Error Boundary | bridge | REQ-CH-015 |
| Snapshot testing | `test_spec_contract.py` | congela el contrato JSON v1 |

### 5.3 Manejo de Errores

```python
# Python: ValueError con mensajes accionables (código de error del API Spec §6)
raise ValueError(
    "[reflex-tanstack-charts] UNKNOWN_FIELD: channel x='letra' "
    "not found in dataset fields ['letter', 'frequency']"
)
```

```jsx
// JS: nunca throw hacia la app; prefijo común en consola
console.warn("[reflex-tanstack-charts] UNSUPPORTED_MARK:", mark.type)
```

## 6. Seguridad

### 6.1 Superficie de Ataque

| Vector | Mitigación |
|---|---|
| Inyección de JS vía spec | Sin eval/new Function; solo despacho por registro (DD-001) |
| XSS vía valores de datos en `text`/tooltip | TanStack renderiza texto como nodos SVG text, no innerHTML; el bridge nunca usa dangerouslySetInnerHTML |
| Dependencia npm comprometida | Versiones exactas fijadas (Art. 4) |
| Payload de evento con objetos anidados maliciosos | Sanitizador: solo tipos planos JSON |

### 6.2 Datos Sensibles
No aplica: la librería no persiste ni transmite datos propios; los datos del
usuario viajan por el canal estándar Reflex (websocket propio de la app).

## 7. Observabilidad

- Consola navegador: warnings/errores prefijados `[reflex-tanstack-charts]` (REQ del PRD §7).
- Backend dev: warning si falta `aria_label` (REQ-CH-017).
- Sin métricas/telemetría propias (librería, no servicio).

## 8. Testing Strategy

| Nivel | Cobertura Target | Herramientas | Qué cubre |
|---|---|---|---|
| Unit (Python) | > 85% de `marks/scales/axis/_serialize` | pytest | validaciones REQ-CH-012, serialización REQ-CH-011, catálogo REQ-CH-004 |
| Contrato | 14 marcas × snapshot | pytest + JSON snapshots | ChartSpec v1 estable (REQ-CH-003) |
| Componente | compila | pytest + `app._compile()` / render de página | REQ-CH-001, props y eventos declarados (REQ-CH-008/009) |
| E2E manual/CI | demo compila y arranca | `reflex export` de la demo | bridge + npm deps resuelven (riesgo R4) |

Cada test cita su REQ en el nombre o docstring (Constitución Art. 6):
`test_req_ch_012_unknown_field_raises`.

## 9. Plan de Migración / Rollout

- Proyecto greenfield: sin migración.
- Rollout: `0.1.0a1` (TestPyPI) → validar instalación en app limpia → `0.1.0` en PyPI → `reflex component share`.
- Backward compatibility: `ChartSpec.version` gobierna el contrato (API Spec §7).

## 10. Preguntas Abiertas

- [x] 2026-08-07 — Versiones npm verificadas en registry: `@tanstack/charts@0.7.2`, `@tanstack/react-charts@0.7.2`, `@tanstack/charts-scales@0.7.2`, `d3-scale@4.0.2`, `d3-shape@3.2.0` (curvas). Peer deps de react-charts: react ^19.
- [x] 2026-08-07 — Confirmado con paquete instalado: `pie` se exporta desde `@tanstack/charts/polar`; `tooltip` desde `@tanstack/charts/tooltip`; raíz exporta `defineChart`, `barY`…`cell`, `text`, `d3Curve`.
- [ ] ¿La versión mínima de Reflex con `rx.asset(shared=True)` estable es 0.8? Confirmar en T-001 con la versión instalada.

## 11. Hallazgos de implementación (2026-08-07, plegados desde la ejecución)

1. **Escalas obligatorias en 0.7.2.** La versión publicada de `@tanstack/charts`
   (0.7.2) exige una escala configurada por eje para toda marca cartesiana (los
   docs siguen `main`, que sí infiere). El bridge implementa la inferencia que el
   API Spec §2.3 ya prometía como default: muestra el primer valor del canal del
   eje → `Date`/temporal → `scaleUtc`; número → `scaleLinear`; string → `scaleBand`
   (si hay `barY/barX/cell` en ese eje) o `scalePoint`. Ejes sin canal (strip
   plots con solo `tickX`/`ruleX`) → `scaleLinear` dominio `[0,1]`. Las marcas
   polares no requieren escalas cartesianas.
2. **`pie` es un transform en 0.7.2.** `pie(data, {value, label, padAngle})`
   devuelve filas-slice (`startAngle`, `endAngle`, …); la marca renderizable es
   `polar({marks: [radialArc(slices, {...})]})`. El bridge compone esto
   internamente (`makePieMark`); el contrato Python (`pie(...)` del API Spec §2.2)
   no cambia. `inner_radius`/`outer_radius`/`corner_radius` se mapean a
   `radialArc`; `label` alimenta el canal de color (`z`) por slice.
3. **SSR real (histórico).** Con el adaptador React, el prerender ejecutaba la
   escena en el servidor y el HTML exportado incluía los SVG. Superseded por el
   hallazgo 4.
4. **DD-006 — DOM host en vez de adaptador React (Delta bridge-dom-host).**
   En vite dev, el bridge servido desde `/public` queda fuera del escaneo de
   optimizeDeps → sus deps se descubren tarde → re-optimización → **dos copias
   de React** (hashes `?v=` distintos) → dispatcher de hooks `null`
   ("resolveDispatcher() is null"), tanto en el bridge como dentro de `<Chart>`
   de `@tanstack/react-charts`. Solución: el bridge es un **class component**
   que monta `mountChart` (`@tanstack/charts/dom`, framework-free, sin hooks);
   memoización con WeakMap por identidad del spec; try/catch + setState como
   error boundary. `@tanstack/react-charts` retirado de `LIB_DEPENDENCIES`.
   Trade-off: el prerender ya no emite SVG (contenedores que hidratan en
   cliente). Verificado con jsdom bajo dos copias de React (11/11 casos).

---

## Constitution check
- Art. 2: DD-001/DD-003 garantizan frontera serializable. ✓
- Art. 3: registro usa nombres TanStack; helpers snake_case 1:1. ✓
- Art. 4: DD-002 + pregunta abierta 1 fijan el trío de versiones. ✓
- Art. 7: flujos de degradación §3.3. ✓

## Historial de Cambios

| Versión | Fecha | Autor | Cambios |
|---|---|---|---|
| 1.0 | 2026-08-07 | Ernesto Crespo | Versión inicial |
