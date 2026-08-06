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
