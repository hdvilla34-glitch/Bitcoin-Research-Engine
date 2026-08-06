# Knowledge Base — BRE

Generado automáticamente por `bre/knowledge_base.py`. No editar a mano.

Conocimiento validado **y rechazado**: según el manifiesto de BRE, un rechazo documentado con evidencia es tan valioso como una validación.

**Resumen:** 0 validadas · 0 prometedoras · 1 rechazadas · 0 con muestra insuficiente.

## ❌ HYP_0001 — RECHAZADA

**Pregunta:** ¿Los cuerpos grandes presentan continuidad?

**Condición:** `BODY_RATIO >= 0.70` → target `ret_4`

**Effect size:** train +0.558pp · test -0.605pp
**p-value (test):** 0.4256

**Razones del veredicto:**
- Effect size: train=+0.558pp, test=-0.605pp (mínimo exigido: ±2.0pp)
- El efecto cambia de dirección entre train y test: no replica out-of-sample.
- p-value en test: 0.4256 (informacional<0.05, validada<0.01)
- No cumple los criterios mínimos de evidencia.

_Última evaluación: 2026-08-06T02:55:22.554022+00:00_

---
