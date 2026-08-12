# Reporte de Investigación — BRE

_Generado: 2026-08-12T03:08:45.158202+00:00_

## Dataset usado

- Símbolo: BTCUSDT (15m)
- Rango: 2025-04-01 00:00:00+00:00 → 2026-06-30 23:45:00+00:00
- Filas: 43776
- Hash del dataset: `08e277b67b864d39`
- Huecos conocidos: 0

## Hipótesis evaluadas

**Resumen:** rechazada: 3 (total: 3)

### HYP_0001 — RECHAZADA
- Pregunta: ¿Los cuerpos grandes presentan continuidad?
- Condición: `BODY_RATIO >= 0.70` → target `ret_4`
- Effect size: train +0.558pp · test -0.605pp
- p-value (test): 0.4256

### HYP_0002 — RECHAZADA
- Pregunta: ¿Los toques de EMA21 en desacuerdo con VWAP de sesión (lados opuestos del precio) tienen mayor tasa de rebote que los toques alineados?
- Condición: `TOUCHES_EMA_21 == True and EMA_VWAP_DISAGREEMENT == True` → target `BOUNCE_SIGNAL_EMA_21`
- Effect size: train -1.600pp · test -0.325pp
- p-value (test): 0.8035

### HYP_0003 — RECHAZADA
- Pregunta: ¿Los toques de EMA21 en desacuerdo con VWAP de sesión, DENTRO de la ventana de sesión NY (8:00-12:00 ET), tienen mayor tasa de rebote que los toques alineados en esa misma ventana?
- Condición: `TOUCHES_EMA_21 == True and EMA_VWAP_DISAGREEMENT == True and NY_HOUR >= 8 and NY_HOUR < 12` → target `BOUNCE_SIGNAL_EMA_21`
- Effect size: train -4.681pp · test -1.460pp
- p-value (test): 0.6035
