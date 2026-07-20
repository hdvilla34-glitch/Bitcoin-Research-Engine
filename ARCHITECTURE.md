# BRE — Bitcoin Research Engine

# Arquitectura

BRE está construido como un sistema modular.

Cada módulo tiene una única responsabilidad.

Ningún módulo debe asumir responsabilidades de otro.

---

# Arquitectura General

Dataset
    │
    ▼
Data Manager
    │
    ▼
Feature Engine
    │
    ▼
Hypothesis Engine
    │
    ▼
Filter Engine
    │
    ▼
Experiment Engine
    │
    ▼
Scoring Engine
    │
    ▼
Knowledge Base

Todo es coordinado por:

BRE Engine

---

# Módulos

## BRE Engine

Coordina el sistema.

No calcula.

No experimenta.

No puntúa.

Solo orquesta.

---

## Registry

Mantiene registrados todos los componentes.

Contiene:

- Dataset Registry
- Feature Registry
- Hypothesis Registry
- Experiment Registry

---

## Data Manager

Responsable del Dataset Maestro.

Funciones:

- cargar datos
- validar datos
- limpiar datos
- exportar parquet

---

## Feature Engine

Construye variables derivadas.

Nunca crea indicadores sin una hipótesis.

Las features deben responder a preguntas de investigación.

---

## Hypothesis Engine

La unidad fundamental de BRE.

Una hipótesis contiene:

- código
- pregunta
- condiciones
- variable objetivo
- prioridad
- estado

---

## Filter Engine

Aplica las condiciones de una hipótesis sobre el Dataset Maestro.

Devuelve únicamente los casos que cumplen la evidencia buscada.

---

## Experiment Engine

Ejecuta experimentos reproducibles.

Genera:

- tamaño de muestra
- métricas
- resultados
- evidencia

---

## Scoring Engine

Evalúa la calidad de la evidencia.

No mide ganancias.

Mide robustez del conocimiento.

---

## Knowledge Base

Es el activo principal del proyecto.

Almacena únicamente conocimiento validado.

Debe responder preguntas como:

- ¿Qué sabemos?
- ¿Qué hipótesis funcionan?
- ¿Qué evidencia existe?
- ¿Qué fue rechazado?

---

# Principios

Toda línea de código debe justificar una necesidad arquitectónica o una hipótesis científica.

Nada entra al proyecto por moda.

Todo entra por evidencia.
