# Catálogo de Hipótesis — BRE

Generado automáticamente por `bre/catalog.py`. No editar a mano.

**Cobertura:** 2/5 preguntas de investigación tienen al menos una hipótesis.

## 🟡 RQ-001 — ¿Existen horarios del día con ventajas estadísticas persistentes?

_Objetivo: Determinar si ciertas franjas horarias presentan diferencias estadísticamente significativas en retorno, volatilidad o volumen._

- **HYP_0003** [rechazada] — ¿Los toques de EMA21 en desacuerdo con VWAP de sesión, DENTRO de la ventana de sesión NY (8:00-12:00 ET), tienen mayor tasa de rebote que los toques alineados en esa misma ventana?
  - `TOUCHES_EMA_21 == True and EMA_VWAP_DISAGREEMENT == True and NY_HOUR >= 8 and NY_HOUR < 12` → target `BOUNCE_SIGNAL_EMA_21`

---

## ⚪ RQ-002 — ¿La apertura de Nueva York genera un cambio estructural en el comportamiento del precio?

**Sin hipótesis todavía.** Pregunta abierta.

---

## 🟡 RQ-003 — ¿Qué variables explican mejor el movimiento de las siguientes cuatro velas?

- **HYP_0001** [rechazada] — ¿Los cuerpos grandes presentan continuidad?
  - `BODY_RATIO >= 0.70` → target `ret_4`
- **HYP_0002** [rechazada] — ¿Los toques de EMA21 en desacuerdo con VWAP de sesión (lados opuestos del precio) tienen mayor tasa de rebote que los toques alineados?
  - `TOUCHES_EMA_21 == True and EMA_VWAP_DISAGREEMENT == True` → target `BOUNCE_SIGNAL_EMA_21`

---

## ⚪ RQ-004 — ¿Qué factores permanecen estables en diferentes regímenes de mercado?

**Sin hipótesis todavía.** Pregunta abierta.

---

## ⚪ RQ-005 — ¿Qué combinaciones de factores producen la mayor capacidad predictiva?

**Sin hipótesis todavía.** Pregunta abierta.

---
