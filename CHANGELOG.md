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
