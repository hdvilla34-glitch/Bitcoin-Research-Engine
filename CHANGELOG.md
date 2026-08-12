# CHANGELOG

Todos los cambios importantes del proyecto BRE quedan registrados aquí.

---

## v0.1.0 — Fundación del proyecto

### Arquitectura

- Se define BRE como un motor de investigación científica.
- Se establece el manifiesto del proyecto.
- Se define la arquitectura modular.
- Se crea el roadmap oficial.

### Datos

- Pipeline ZIP → CSV → Dataset Maestro.
- Dataset BTCUSDT 15m cargado correctamente.
- Corrección del problema de cabeceras del CSV.

### Núcleo

Implementados:

- BRE Engine
- Registry
- Data Manager
- Feature Engine
- Hypothesis Engine
- Filter Engine

### Primera hipótesis

HYP_0001

Pregunta:

¿Los cuerpos grandes presentan continuidad?

Condición:

BODY_RATIO ≥ 0.70

Target:

ret_4

Resultados:

- Casos encontrados: 10,938
- Se ejecutó correctamente el primer experimento del proyecto.

Estado:

🟡 En investigación

---

Próximo objetivo:

Construir el Experiment Engine y comenzar a registrar automáticamente todos los experimentos.

---

## v0.2.0 — Implementación real del núcleo (Fase 1 y Experiment Engine)

### Contexto

Hasta esta versión, el repositorio solo contenía documentación (arquitectura,
manifiesto, roadmap). El código de Fase 1 se había corrido en Colab pero
nunca se había subido a GitHub. Esta versión lo implementa de verdad,
como código versionado en `bre/`.

### Implementado

- `bre/data_manager.py`: pipeline ZIP mensual (Binance klines, 12 columnas
  sin encabezado, timestamps en microsegundos) a Dataset Maestro. Deduplica
  copias idénticas de Drive por hash de contenido, detecta huecos en la
  serie de 15m, exporta a Parquet.
- `bre/feature_engine.py`: BODY_RATIO y ret_N (retornos hacia adelante),
  documentando la pregunta de investigación que justifica cada feature.
- `bre/hypothesis.py`: dataclass Hypothesis + registro de hipótesis
  conocidas (HYP_0001).
- `bre/filter_engine.py`: aplica la condición de una hipótesis sobre el
  Dataset Maestro.
- `bre/experiment_engine.py`: corre experimentos reproducibles (sample
  size, win rate, comparación contra baseline con z-test de dos
  proporciones, hash del dataset para trazabilidad) y los registra en
  data/experiments/experiment_log.jsonl (append-only).

### Validación end-to-end

Se corrió el pipeline completo sobre el dataset real (2025-04 a
2026-06, con hueco conocido en 2025-05): 40,800 filas.

HYP_0001 re-ejecutada con el pipeline nuevo:

- Sample size: 10,938 (coincide con el valor original de v0.1.0)
- Win rate filtrado: 50.01% vs baseline 50.06%
- p-value: 0.92 (no significativo al 95%)

Conclusión honesta: HYP_0001 no muestra evidencia de continuidad.
Se mantiene como hipótesis rechazada en esta forma; queda documentada
como conocimiento negativo, no se descarta silenciosamente.

### Datos detectados durante la carga

- Hueco confirmado: falta el mes 2025-05 completo en la carpeta
  raw csv processed de Drive.
- Copias duplicadas (Drive sync) detectadas y deduplicadas en: 2025-09,
  2026-02, 2026-03, 2026-04 (dos copias extra), 2026-05, 2026-06.

---

## v0.3.0 — Scoring Engine

### Implementado

- `bre/scoring_engine.py`: decide de forma sistemática (no a ojo) si una
  hipótesis pasa a "validada" o queda "rechazada", con 3 criterios:
  1. Split cronológico train/test obligatorio (50/50): el efecto tiene
     que sostenerse en la mitad que el análisis nunca vio.
  2. Umbral de tamaño de efecto (win_rate_delta_pp mínimo), no solo
     p-value — con datasets grandes, diferencias mínimas pueden salir
     "significativas" sin ser útiles en la práctica.
  3. Dos niveles de significancia: p<0.05 (prometedora, sigue en
     investigación) vs p<0.01 (validada, pasa a Knowledge Base).
- Registro de veredictos en `data/experiments/score_log.jsonl`
  (append-only, auditable).

### HYP_0001 re-evaluada con el Scoring Engine

**Veredicto: RECHAZADA.** El efecto cambia de signo entre train
(+0.56pp) y test (-0.61pp) — no replica out-of-sample. p=0.43 en test,
muy lejos de cualquier umbral de significancia. Se actualiza el status
de HYP_0001 en el registro de hipótesis (`bre/hypothesis.py`) de
"en_investigacion" a "rechazada", con la evidencia documentada.

Este resultado valida el diseño del Scoring Engine: es exactamente el
tipo de inestabilidad (efecto que aparenta existir pero cambia de
dirección) que el split out-of-sample estaba pensado para detectar —
el mismo patrón que afectó al hallazgo de la "ventana dorada" en
research anterior.

---

## v0.4.0 — Knowledge Base

### Implementado

- `bre/knowledge_base.py`: consolida `data/experiments/score_log.jsonl`
  en conocimiento consultable (última entrada por hipótesis, no
  histórico crudo). Genera dos salidas:
  - `data/knowledge/knowledge_base.json` (consumo programático)
  - `docs/KNOWLEDGE_BASE.md` (lectura humana en GitHub)

Cierra el ciclo completo de Fase 2: Hypothesis → Filter → Experiment →
Scoring → Knowledge. HYP_0001 queda documentada como conocimiento
rechazado, no solo como una línea en un log.

### Limpieza

- Eliminados `hypothesis.py` y `scoring_engine.py` duplicados que habían
  quedado sueltos en la raíz del repo (fuera de `bre/`) por un upload
  manual anterior.

---

## v0.5.0 — Export Engine (cierra Fase 2)

### Implementado

- `bre/export_engine.py`:
  - `export_scores_csv()`: aplana `score_log.jsonl` (train/test anidados)
    a `data/exports/scores.csv`, una fila por hipótesis evaluada.
  - `generate_research_report()`: combina el Data Manifest + Knowledge
    Base en `data/exports/research_report.md`, un documento único
    archivable/compartible.
  - `export_all()`: corre ambas exportaciones juntas.

**Fase 2 completa**: Data Manager → Feature Engine → Hypothesis Engine
→ Filter Engine → Experiment Engine → Scoring Engine → Knowledge Base
→ Export Engine. Pipeline de investigación de punta a punta, con
HYP_0001 como primer caso corrido y documentado completo.

---

## v0.6.0 — Catálogo de Hipótesis (Fase 3)

### Implementado

- `bre/research_questions.py`: registro machine-readable de RQ-001 a
  RQ-005 (antes solo existían como texto en `docs/RESEARCH_QUESTIONS.md`,
  sin conexión programática con las hipótesis).
- `bre/hypothesis.py`: se agrega el campo `research_question` a la
  dataclass `Hypothesis`, y se introduce `HYPOTHESES` como registro
  central extensible (antes solo existía `HYP_0001` suelto). HYP_0001
  se vincula a RQ-003 (coincide con su target `ret_4`, "las siguientes
  cuatro velas").
- `bre/catalog.py`: agrupa `HYPOTHESES` por `research_question`,
  incluyendo las preguntas que aún no tienen ninguna hipótesis asociada
  — el vacío es tan informativo como lo cubierto. Genera
  `data/knowledge/hypothesis_catalog.json` y `docs/HYPOTHESIS_CATALOG.md`.

### Hallazgo

**Cobertura actual: 1/5 preguntas de investigación tienen hipótesis.**
Solo RQ-003 está cubierta (por HYP_0001, rechazada). RQ-001 (¿existen
horarios con ventaja estadística persistente?) es la más relevante para
atacar a continuación: coincide directamente con research previo fuera
de BRE (asimetría EMA21/VWAP, bloque 11:00-12:00 ET) que todavía no está
formalizado como hipótesis dentro del framework.

---

## v0.7.0 — HYP_0002 y HYP_0003: EMA21/VWAP no replica

### Contexto

Se intentó formalizar dentro de BRE un hallazgo de research previo
(fuera del framework): toques de EMA21 en desacuerdo con VWAP de sesión
mostraban ~+11.8pp más bounce rate que toques alineados, con el bloque
11:00-12:00 ET como mejor ventana.

### Features nuevas (bre/feature_engine.py)

- `add_ema()`: EMA de cualquier span (usado con span=21).
- `add_session_vwap()`: VWAP anclado por sesión — **ASUNCIÓN
  METODOLÓGICA**: se reinicia a las 00:00 UTC. Puede no coincidir con
  el anclaje usado en el research original.
- `add_ema_vwap_disagreement()`: True cuando EMA21 y VWAP quedan en
  lados opuestos del precio.
- `add_ema_touch_and_bounce()`: detecta toques de EMA21 y clasifica el
  resultado 4 velas después como "rebote" (+1, continúa la tendencia
  previa) o "ruptura" (-1).
- `add_ny_hour()`: hora en zona horaria America/New_York (maneja DST).

### HYP_0002 (24h, todas las horas) — RECHAZADA

- Effect size: train -1.60pp, test -0.33pp
- p-value test: 0.80
- Dirección OPUESTA a la esperada, sin significancia.

### HYP_0003 (restringida a sesión NY 8:00-12:00 ET) — RECHAZADA

- Effect size: train -4.68pp, test -1.46pp
- p-value test: 0.60
- Muestra pequeña (378/333 casos). Dirección OPUESTA a la esperada.

### Conclusión honesta

**Ninguna de las dos formalizaciones replica el hallazgo original.**
Esto NO se reporta como "el hallazgo original estaba mal" — se reporta
como "esta implementación específica no lo replica", que es una
afirmación más débil y más honesta. Diferencias metodológicas
candidatas entre esta implementación y el análisis original:

1. Definición exacta de "rebote" (aquí: continuidad de tendencia previa
   4 velas después; el análisis original pudo usar otra definición,
   ej. magnitud de reacción o un umbral mínimo de movimiento).
2. Anclaje del VWAP de sesión (aquí: 00:00 UTC).
3. Definición exacta de "toque" de EMA21.

**Pendiente**: revisar la metodología original con Hernán (probablemente
en un notebook de Colab) antes de descartar el hallazgo por completo.
Hasta entonces, ambas hipótesis quedan documentadas como rechazadas
con esta implementación específica — conocimiento negativo válido,
no un callejón sin salida.

---

## v0.8.0 — Sin indicadores: pivot a calendario/sesión (Fase 3/4)

### Contexto

Decisión de producto: mientras dure esta fase, BRE no investiga con
indicadores técnicos (EMA, VWAP, RSI, ADX, etc.). Se documenta como
**Regla 5** en `MANIFESTO.md`. El foco pasa a efectos de calendario y
estructura de sesión — precio, volumen y tiempo crudos, nada derivado
de un indicador.

### Retirado (archivado, no borrado — Regla 4)

- `bre/feature_engine.py`: se eliminan `add_ema()`, `add_session_vwap()`,
  `add_ema_vwap_disagreement()`, `add_ema_touch_and_bounce()`.
- `bre/hypothesis.py`: HYP_0002 y HYP_0003 salen de `HYPOTHESES`
  (catálogo activo) y pasan a `ARCHIVED_HYPOTHESES`. Su evidencia
  (RECHAZADAS, Scoring Engine v0.7.0) sigue intacta en
  `data/experiments/score_log.jsonl` y `docs/KNOWLEDGE_BASE.md`.

### Implementado

- `bre/feature_engine.py`, reescrito sobre 3 fuentes únicamente
  (precio OHLC crudo, volumen/actividad cruda, tiempo):
  - `add_forward_returns()` / `add_backward_returns()`: generaliza
    `ret_4` a cualquier horizonte, hacia adelante y hacia atrás.
  - `add_candle_geometry()`: RANGE_PCT, wicks, DIRECTION — geometría
    de vela adicional a BODY_RATIO, sin indicadores.
  - `add_taker_buy_ratio()`: presión compradora/vendedora usando
    `taker_buy_base` (dato crudo de los klines de Binance, cargado
    desde el inicio del proyecto pero nunca usado).
  - `add_calendar()`: WEEKDAY, IS_MONDAY/FRIDAY/WEEKEND, UTC_HOUR,
    NY_HOUR, WEEK_OF_YEAR, MONTH.
  - `add_session_tag()`: SESSION (ASIA/LONDON/NEWYORK/OFF_HOURS) por
    bandas fijas en UTC (asunción metodológica documentada en el
    código, igual que se hizo con el VWAP en v0.7.0).
  - `add_session_relative()`: SESSION_OPEN, RET_SINCE_SESSION_OPEN,
    SESSION_HIGH/LOW_SO_FAR (running, sin look-ahead).
  - `add_prior_session_return()`: PREV_SESSION_RET y
    PREV_SESSION_DIRECTION — retorno y dirección de la sesión
    inmediatamente anterior, la variable clave para hipótesis tipo
    "Monday Asia effect".
  - `build_features()`: corre todo el pipeline en el orden correcto
    de una sola llamada (evita el error histórico de orden manual en
    Colab).
- `bre/hypothesis.py`:
  - `HYP_0004`: ¿la sesión previa predice la dirección de la sesión
    siguiente, en general (todos los días)? RQ-006.
  - `HYP_0005`: la misma pregunta, acotada a lunes ("Monday Asia
    effect" propiamente dicho). RQ-006. Se prueba después de HYP_0004
    a propósito — el caso general antes que el específico.
- `bre/research_questions.py` + `docs/RESEARCH_QUESTIONS.md`: nueva
  RQ-006 (efectos de calendario / secuencia de sesiones).

### Validación

Pipeline completo (`build_features` → `HYPOTHESES` → `filter_engine`
→ `experiment_engine` → `scoring_engine` → `catalog` → `knowledge_base`
→ `export_engine`) corrido de punta a punta sobre un dataset sintético
de control para confirmar que no rompe nada. HYP_0004/HYP_0005 quedan
en estado `draft`, listas para correr sobre el Dataset Maestro real —
no se generó evidencia falsa en `score_log.jsonl`.

### Pendiente (próximo paso)

Correr HYP_0004 y HYP_0005 sobre el dataset real vía Scoring Engine.
