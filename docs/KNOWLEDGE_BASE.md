# Knowledge Base — BRE

Generado automáticamente por `bre/knowledge_base.py`. No editar a mano.

Conocimiento validado **y rechazado**: según el manifiesto de BRE, un rechazo documentado con evidencia es tan valioso como una validación.

**Resumen:** 0 validadas · 0 prometedoras · 3 rechazadas · 0 con muestra insuficiente.

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

## ❌ HYP_0002 — RECHAZADA

**Pregunta:** ¿Los toques de EMA21 en desacuerdo con VWAP de sesión (lados opuestos del precio) tienen mayor tasa de rebote que los toques alineados?

**Condición:** `TOUCHES_EMA_21 == True and EMA_VWAP_DISAGREEMENT == True` → target `BOUNCE_SIGNAL_EMA_21`

**Effect size:** train -1.600pp · test -0.325pp
**p-value (test):** 0.8035

**Razones del veredicto:**
- Effect size: train=-1.600pp, test=-0.325pp (mínimo exigido: ±2.0pp)
- p-value en test: 0.8035 (informacional<0.05, validada<0.01)
- No cumple los criterios mínimos de evidencia.

_Última evaluación: 2026-08-07T02:55:31.978076+00:00_

---

## ❌ HYP_0003 — RECHAZADA

**Pregunta:** ¿Los toques de EMA21 en desacuerdo con VWAP de sesión, DENTRO de la ventana de sesión NY (8:00-12:00 ET), tienen mayor tasa de rebote que los toques alineados en esa misma ventana?

**Condición:** `TOUCHES_EMA_21 == True and EMA_VWAP_DISAGREEMENT == True and NY_HOUR >= 8 and NY_HOUR < 12` → target `BOUNCE_SIGNAL_EMA_21`

**Effect size:** train -4.681pp · test -1.460pp
**p-value (test):** 0.6035

**Razones del veredicto:**
- Effect size: train=-4.681pp, test=-1.460pp (mínimo exigido: ±2.0pp)
- p-value en test: 0.6035 (informacional<0.05, validada<0.01)
- No cumple los criterios mínimos de evidencia.

_Última evaluación: 2026-08-07T02:56:33.383651+00:00_

---
