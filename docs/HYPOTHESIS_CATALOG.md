# Catálogo de Hipótesis — BRE

Generado automáticamente por `bre/catalog.py`. No editar a mano.

**Cobertura:** 2/6 preguntas de investigación tienen al menos una hipótesis.

## ⚪ RQ-001 — ¿Existen horarios del día con ventajas estadísticas persistentes?

_Objetivo: Determinar si ciertas franjas horarias presentan diferencias estadísticamente significativas en retorno, volatilidad o volumen._

**Sin hipótesis todavía.** Pregunta abierta.

---

## ⚪ RQ-002 — ¿La apertura de Nueva York genera un cambio estructural en el comportamiento del precio?

**Sin hipótesis todavía.** Pregunta abierta.

---

## 🟡 RQ-003 — ¿Qué variables explican mejor el movimiento de las siguientes cuatro velas?

- **HYP_0001** [rechazada] — ¿Los cuerpos grandes presentan continuidad?
  - `BODY_RATIO >= 0.70` → target `ret_4`

---

## ⚪ RQ-004 — ¿Qué factores permanecen estables en diferentes regímenes de mercado?

**Sin hipótesis todavía.** Pregunta abierta.

---

## ⚪ RQ-005 — ¿Qué combinaciones de factores producen la mayor capacidad predictiva?

**Sin hipótesis todavía.** Pregunta abierta.

---

## 🟡 RQ-006 — ¿Existen efectos de día de la semana o de secuencia entre sesiones (Asia→Londres→NY) con ventaja estadística persistente, ej. 'Monday Asia effect'?

_Objetivo: Determinar si la dirección de una sesión predice la dirección de la sesión siguiente, y si ese efecto (si existe) es uniforme entre días de la semana o se concentra en días específicos (ej. lunes, tras el fin de semana de menor liquidez)._

- **HYP_0004** [draft] — ¿La dirección de una sesión predice la dirección de la sesión inmediatamente siguiente (Asia→Londres, Londres→NY), en general, en cualquier día de la semana?
  - `PREV_SESSION_DIRECTION != 0` → target `ret_4`
- **HYP_0005** [draft] — ¿El efecto de HYP_0004 (sesión previa predice la siguiente) es más fuerte específicamente los lunes — 'Monday Asia effect' (la sesión Asia del lunes predice la sesión Londres del mismo lunes)?
  - `PREV_SESSION_DIRECTION != 0 and WEEKDAY == 0` → target `ret_4`

---
