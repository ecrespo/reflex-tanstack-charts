/**
 * TanStackChartBridge — interpreta un ChartSpec JSON (contrato v1) y lo compila a
 * defineChart de @tanstack/charts, renderizando <Chart> de @tanstack/react-charts.
 *
 * REQs: REQ-CH-002/003 (registro de marcas), REQ-CH-004 (registro de escalas),
 * REQ-CH-006/007 (tooltip/animate), REQ-CH-008/009/010 (eventos sanitizados),
 * REQ-CH-011 (rehidratación temporal), REQ-CH-013/014/015 (degradación),
 * REQ-CH-023 (color ordinal).
 * Specs: specs/technical/architecture.md DD-001/002/003 · specs/data-model §2.
 * Sin eval / new Function / dangerouslySetInnerHTML (Constitución Art. 2).
 */

// ARQUITECTURA SIN HOOKS NI ADAPTADOR REACT (Delta 2026-08-07 bridge-dom-host):
// Vite (dev) sirve este archivo desde /public/external/... fuera del grafo
// optimizado; sus imports de "react" pueden resolver a una copia pre-empaquetada
// distinta a la de react-dom (hashes ?v= diferentes). Con dos copias, el
// dispatcher de hooks es null → "resolveDispatcher() is null" en useMemo — tanto
// en este archivo como DENTRO de <Chart> de @tanstack/react-charts. Por eso el
// bridge monta con el DOM host vanilla de @tanstack/charts (framework-free, sin
// ningún hook) desde un class component: las clases y la creación de elementos
// funcionan entre copias de React; los hooks no. Memoización por identidad del
// spec vía WeakMap (REQ-CH-005).
import React from "react"
import {
  defineChart,
  d3Curve,
  lineY,
  lineX,
  areaY,
  areaX,
  barY,
  barX,
  dot,
  ruleX,
  ruleY,
  text,
  tickX,
  tickY,
  cell,
} from "@tanstack/charts"
import { pie, polar, radialArc } from "@tanstack/charts/polar"
import { tooltip } from "@tanstack/charts/tooltip"
import { mountChart } from "@tanstack/charts/dom"
import { scaleBand } from "@tanstack/charts-scales/band"
import { scaleLinear } from "@tanstack/charts-scales/linear"
import { scaleOrdinal } from "@tanstack/charts-scales/ordinal"
import { scalePoint } from "@tanstack/charts-scales/point"
import { scaleUtc, scaleTime, scaleLog, scaleSqrt } from "d3-scale"
import {
  curveLinear,
  curveMonotoneX,
  curveNatural,
  curveStep,
  curveStepAfter,
  curveStepBefore,
  curveBasis,
  curveCatmullRom,
} from "d3-shape"

const TAG = "[reflex-tanstack-charts]"
const SUPPORTED_SPEC_VERSION = 1

// --- Registros (DD-001/DD-002) ----------------------------------------------

/**
 * Marcas cartesianas 1:1. `pie` se maneja aparte: en 0.7.2 `pie()` es un
 * transform de slices y la marca real es `polar({marks:[radialArc(...)]})`.
 */
const MARK_REGISTRY = {
  lineY,
  lineX,
  areaY,
  areaX,
  barY,
  barX,
  dot,
  ruleX,
  ruleY,
  text,
  tickX,
  tickY,
  cell,
}

function makePieMark(rows, options) {
  const { value, label, padAngle, innerRadius, outerRadius, cornerRadius, id, ...rest } = options
  const sliceOptions = { value }
  if (label !== undefined) sliceOptions.label = label
  if (padAngle !== undefined) sliceOptions.padAngle = padAngle
  const slices = pie(rows, sliceOptions)
  const arcOptions = {
    startAngle: "startAngle",
    endAngle: "endAngle",
    padAngle: "padAngle",
    ...rest,
  }
  if (label !== undefined && arcOptions.z === undefined && arcOptions.fill === undefined) {
    arcOptions.z = label // color por slice a partir de la etiqueta
  }
  if (innerRadius !== undefined) arcOptions.innerRadius = innerRadius
  if (outerRadius !== undefined) arcOptions.outerRadius = outerRadius
  if (cornerRadius !== undefined) arcOptions.cornerRadius = cornerRadius
  return polar({ ...(id !== undefined ? { id } : {}), marks: [radialArc(slices, arcOptions)] })
}

const SUPPORTED_MARK_TYPES = new Set([...Object.keys(MARK_REGISTRY), "pie"])

const COMPACT_SCALES = { linear: scaleLinear, band: scaleBand, point: scalePoint, ordinal: scaleOrdinal }
const D3_SCALES = { utc: scaleUtc, time: scaleTime, log: scaleLog, sqrt: scaleSqrt }
const TEMPORAL_SCALES = new Set(["utc", "time"])

const CURVES = {
  linear: curveLinear,
  "monotone-x": curveMonotoneX,
  natural: curveNatural,
  step: curveStep,
  "step-after": curveStepAfter,
  "step-before": curveStepBefore,
  basis: curveBasis,
  "catmull-rom": curveCatmullRom,
}

// --- Escalas y formatos (REQ-CH-004, DD-003) --------------------------------

function makeScaleFactory(scaleSpec) {
  if (!scaleSpec) return undefined
  const { type, domain, padding, range, base } = scaleSpec
  const isTemporal = TEMPORAL_SCALES.has(type)
  const factory = COMPACT_SCALES[type] || D3_SCALES[type]
  if (!factory) {
    console.warn(`${TAG} UNKNOWN_SCALE:`, type)
    return undefined
  }
  return () => {
    let s = factory()
    if (base !== undefined && s.base) s = s.base(base)
    if (padding !== undefined && s.padding) s = s.padding(padding)
    if (domain !== undefined && s.domain) {
      const d = isTemporal ? domain.map((v) => new Date(v)) : domain
      s = s.domain(d)
    }
    if (range !== undefined && s.range) s = s.range(range)
    return s
  }
}

function makeTickFormat(fmt) {
  if (!fmt) return undefined
  const locale = fmt.locale || "en-US"
  // Formato de fechas: presencia de claves Intl.DateTimeFormat
  if (fmt.date_style || fmt.month || fmt.day || fmt.year || fmt.hour || fmt.minute) {
    const options = { timeZone: fmt.time_zone || "UTC" }
    if (fmt.date_style) options.dateStyle = fmt.date_style
    for (const k of ["year", "month", "day", "hour", "minute"]) {
      if (fmt[k]) options[k] = fmt[k]
    }
    const f = new Intl.DateTimeFormat(locale, options)
    return (value) => f.format(value instanceof Date ? value : new Date(value))
  }
  const options = {}
  const style = fmt.style || "decimal"
  if (style === "compact") {
    options.notation = "compact"
  } else {
    options.style = style
  }
  if (fmt.currency) options.currency = fmt.currency
  if (fmt.maximum_fraction_digits !== undefined)
    options.maximumFractionDigits = fmt.maximum_fraction_digits
  if (fmt.minimum_fraction_digits !== undefined)
    options.minimumFractionDigits = fmt.minimum_fraction_digits
  const f = new Intl.NumberFormat(locale, options)
  return (value) => f.format(value)
}

function buildAxis(axisSpec) {
  if (!axisSpec) return undefined
  const out = {}
  const scaleFactory = makeScaleFactory(axisSpec.scale)
  if (scaleFactory) out.scale = scaleFactory
  if (axisSpec.nice !== undefined) out.nice = axisSpec.nice
  if (axisSpec.grid !== undefined) out.grid = axisSpec.grid
  if (axisSpec.axis) {
    const inner = {}
    if (axisSpec.axis.label !== undefined) inner.label = axisSpec.axis.label
    if (axisSpec.axis.ticks) {
      const ticks = {}
      if (axisSpec.axis.ticks.count !== undefined) ticks.count = axisSpec.axis.ticks.count
      const format = makeTickFormat(axisSpec.axis.ticks.format)
      if (format) ticks.format = format
      if (Object.keys(ticks).length) inner.ticks = ticks
    }
    if (Object.keys(inner).length) out.axis = inner
  }
  return Object.keys(out).length ? out : undefined
}

// --- Datos y opciones (REQ-CH-011) ------------------------------------------

function rehydrate(data, temporalFields) {
  if (!Array.isArray(data)) return []
  if (!temporalFields || temporalFields.length === 0) return data
  return data.map((row) => {
    const out = { ...row }
    for (const field of temporalFields) {
      if (out[field] != null) out[field] = new Date(out[field])
    }
    return out
  })
}

function mapOptions(options) {
  const out = { ...options }
  if (typeof out.curve === "string") {
    const curve = CURVES[out.curve]
    if (curve) {
      out.curve = d3Curve(curve)
    } else {
      console.warn(`${TAG} unknown curve:`, out.curve)
      delete out.curve
    }
  }
  return out
}

// --- Definición (DD-001) -----------------------------------------------------

/**
 * Inferencia de escalas: TanStack Charts 0.7.2 (versión publicada) exige una
 * escala configurada por eje para toda marca cartesiana — sin ella el
 * SSR/prerender lanza "Chart scale 'y' requires a configured scale". Se infiere
 * del primer valor de los canales del eje: Date→utc, number→linear,
 * string→band (si hay barras/celdas en el eje) o point.
 */
const AXIS_CHANNELS = { x: ["x", "x1", "x2"], y: ["y", "y1", "y2"] }
const RULE_MARKS = { x: "ruleX", y: "ruleY" }
const BAND_PREFERRING = { x: new Set(["barY", "cell"]), y: new Set(["barX", "cell"]) }

function sampleAxisValue(mark, axis) {
  if (mark.type === RULE_MARKS[axis]) {
    const v = (mark.data || []).find((d) => d !== null && d !== undefined)
    return v === undefined ? undefined : { value: v, temporal: false }
  }
  for (const channel of AXIS_CHANNELS[axis]) {
    const field = (mark.options || {})[channel]
    if (typeof field !== "string") continue
    const row = (mark.data || []).find((d) => d && d[field] !== null && d[field] !== undefined)
    if (!row) continue
    return { value: row[field], temporal: (mark.temporal_fields || []).includes(field) }
  }
  return undefined
}

function inferAxisScale(cartesianMarks, axis) {
  let sample
  let preferBand = false
  for (const mark of cartesianMarks) {
    const s = sampleAxisValue(mark, axis)
    if (s !== undefined) {
      sample = sample ?? s
      if (typeof s.value === "string" && BAND_PREFERRING[axis].has(mark.type)) {
        preferBand = true
      }
    }
  }
  if (sample === undefined) return () => scaleLinear().domain([0, 1])
  if (sample.temporal || sample.value instanceof Date) return () => scaleUtc()
  if (typeof sample.value === "number") return scaleLinear
  return preferBand ? () => scaleBand().padding(0.1) : () => scalePoint().padding(0.5)
}

function buildDefinition(spec, problems) {
  const marks = []
  const cartesianMarks = []
  for (const mark of spec.marks || []) {
    if (!SUPPORTED_MARK_TYPES.has(mark.type)) {
      // REQ-CH-013
      console.warn(`${TAG} UNSUPPORTED_MARK:`, mark.type)
      problems.push(`Marca no soportada: ${mark.type}`)
      continue
    }
    const data = rehydrate(mark.data, mark.temporal_fields)
    if (!data.length) {
      // REQ-CH-014: dataset vacío → omitir marca sin romper
      continue
    }
    if (mark.type === "pie") {
      marks.push(makePieMark(data, mapOptions(mark.options || {})))
      continue
    }
    cartesianMarks.push({ ...mark, data })
    marks.push(MARK_REGISTRY[mark.type](data, mapOptions(mark.options || {})))
  }
  if (!marks.length) return null
  const definition = { marks }
  const x = buildAxis(spec.x)
  const y = buildAxis(spec.y)
  if (x) definition.x = x
  if (y) definition.y = y
  if (cartesianMarks.length) {
    if (!definition.x?.scale) {
      definition.x = { ...(definition.x || {}), scale: inferAxisScale(cartesianMarks, "x") }
    }
    if (!definition.y?.scale) {
      definition.y = { ...(definition.y || {}), scale: inferAxisScale(cartesianMarks, "y") }
    }
  }
  if (spec.color && spec.color.scale) {
    // REQ-CH-023
    const colorScale = makeScaleFactory(spec.color.scale)
    if (colorScale) {
      definition.color = { scale: colorScale }
      // `createColorScale` trata un factory como inferible y reemplaza su dominio
      // por los valores observados (orden de aparición), descartando el que se
      // configuró aquí. Reenviarlos como opciones de color los hace autoritativos,
      // así que valor→color es determinista y no depende del orden de las filas.
      const { domain, range } = spec.color.scale
      if (domain !== undefined) definition.color.domain = domain
      if (range !== undefined) definition.color.range = range
    }
  }
  if (spec.tooltip) definition.tooltip = tooltip // REQ-CH-006
  if (spec.animate) definition.animate = true // REQ-CH-007
  return defineChart(definition)
}

// --- Eventos (REQ-CH-008/009/010, DD-005) ------------------------------------

function sanitizeValue(value) {
  if (value instanceof Date) return value.toISOString()
  if (value === undefined) return null
  if (value === null || ["string", "number", "boolean"].includes(typeof value)) return value
  return null
}

function sanitizeDatum(datum) {
  if (datum == null || typeof datum !== "object") return null
  const out = {}
  for (const [k, v] of Object.entries(datum)) {
    const sv = sanitizeValue(v)
    if (sv !== null || v === null || v === undefined) out[k] = sv
  }
  return out
}

function sanitizePoint(point) {
  if (!point) return null // REQ-CH-010
  return {
    mark_id: point.markId ?? point.mark_id ?? null,
    key: sanitizeValue(point.key),
    x_value: sanitizeValue(point.xValue),
    y_value: sanitizeValue(point.yValue),
    datum: sanitizeDatum(point.datum),
  }
}

// --- Placeholders y error boundary (REQ-CH-013/015) --------------------------

function Placeholder({ children }) {
  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        minHeight: "80px",
        padding: "12px",
        border: "1px dashed currentColor",
        borderRadius: "8px",
        opacity: 0.7,
        fontSize: "13px",
      }}
      role="note"
    >
      {children}
    </div>
  )
}

// --- Compilación memoizada sin hooks (REQ-CH-005) -----------------------------

const definitionCache = new WeakMap()

function compileSpec(spec) {
  if (!spec || typeof spec !== "object") {
    return { definition: null, problems: ["ChartSpec ausente"], versionError: false }
  }
  const cached = definitionCache.get(spec)
  if (cached) return cached
  let result
  if ((spec.version ?? 1) > SUPPORTED_SPEC_VERSION) {
    console.warn(`${TAG} SPEC_VERSION:`, spec.version)
    result = { definition: null, problems: [], versionError: true }
  } else {
    const problems = []
    let definition = null
    try {
      definition = buildDefinition(spec, problems)
    } catch (error) {
      console.error(`${TAG} RENDER_ERROR while building definition:`, error)
      problems.push(String(error))
    }
    result = { definition, problems, versionError: false }
  }
  definitionCache.set(spec, result)
  return result
}

// --- Componente (class, monta el DOM host vanilla; REQ-CH-015 vía try/catch) --

export class TanStackChartBridge extends React.Component {
  constructor(props) {
    super(props)
    this.containerRef = React.createRef()
    this.host = null
    this.state = { mountError: null }
  }

  buildHostOptions(definition) {
    const { height, aspectRatio, initialWidth, onFocusChange, onSelect } = this.props
    const options = {
      definition,
      ariaLabel: this.props.ariaLabel ?? this.props["aria-label"] ?? "chart",
    }
    if (height !== undefined && height !== null) options.height = height
    if (aspectRatio !== undefined && aspectRatio !== null) options.aspectRatio = aspectRatio
    if (initialWidth !== undefined && initialWidth !== null) options.initialWidth = initialWidth
    if (onFocusChange) options.onFocusChange = (point) => onFocusChange(sanitizePoint(point))
    if (onSelect) options.onSelect = (point) => onSelect(sanitizePoint(point))
    return options
  }

  syncHost() {
    const container = this.containerRef.current
    if (!container) return
    const { definition } = compileSpec(this.props.spec)
    if (!definition) {
      this.teardown()
      return
    }
    try {
      const options = this.buildHostOptions(definition)
      if (this.host) {
        this.host.update(options)
      } else {
        this.host = mountChart(container, options)
      }
      if (this.state.mountError) this.setState({ mountError: null })
    } catch (error) {
      // REQ-CH-015: nunca propagar al árbol de la app
      console.error(`${TAG} RENDER_ERROR:`, error)
      this.teardown()
      this.setState({ mountError: String(error) })
    }
  }

  teardown() {
    if (this.host) {
      try {
        this.host.destroy()
      } catch (error) {
        console.warn(`${TAG} error while destroying chart host:`, error)
      }
      this.host = null
    }
  }

  componentDidMount() {
    this.syncHost()
  }

  componentDidUpdate(prevProps) {
    if (
      prevProps.spec !== this.props.spec ||
      prevProps.height !== this.props.height ||
      prevProps.aspectRatio !== this.props.aspectRatio ||
      prevProps.initialWidth !== this.props.initialWidth ||
      prevProps.ariaLabel !== this.props.ariaLabel
    ) {
      this.syncHost()
    }
  }

  componentWillUnmount() {
    this.teardown()
  }

  render() {
    const { spec, themeVars } = this.props
    const { problems, versionError, definition } = compileSpec(spec)
    return (
      <div style={{ position: "relative", width: "100%", ...(themeVars || {}) }}>
        {versionError ? (
          <Placeholder>
            {`${TAG} ChartSpec version ${spec.version} no soportada; actualiza reflex-tanstack-charts`}
          </Placeholder>
        ) : this.state.mountError ? (
          <Placeholder>{`${TAG} error de render: ${this.state.mountError}`}</Placeholder>
        ) : definition ? (
          <div ref={this.containerRef} style={{ width: "100%" }} />
        ) : (
          <Placeholder>{`${TAG} sin marcas renderizables`}</Placeholder>
        )}
        {problems.length > 0 && !versionError ? (
          <Placeholder>{problems.join(" · ")}</Placeholder>
        ) : null}
      </div>
    )
  }
}

export default TanStackChartBridge
