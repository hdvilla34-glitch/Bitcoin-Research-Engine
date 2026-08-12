"""
Research Questions Registry
============================

Versión machine-readable de docs/RESEARCH_QUESTIONS.md.

"Toda nueva feature, experimento o módulo debe responder al menos
una de estas preguntas." (RESEARCH_QUESTIONS.md)

Este registro es lo que le permite al Catálogo de Hipótesis (bre/catalog.py)
saber qué preguntas siguen sin ninguna hipótesis asociada, no solo listar
las que sí tienen.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ResearchQuestion:
    code: str
    question: str
    objective: str = ""


RESEARCH_QUESTIONS: list[ResearchQuestion] = [
    ResearchQuestion(
        code="RQ-001",
        question="¿Existen horarios del día con ventajas estadísticas persistentes?",
        objective=(
            "Determinar si ciertas franjas horarias presentan diferencias "
            "estadísticamente significativas en retorno, volatilidad o volumen."
        ),
    ),
    ResearchQuestion(
        code="RQ-002",
        question="¿La apertura de Nueva York genera un cambio estructural en el comportamiento del precio?",
    ),
    ResearchQuestion(
        code="RQ-003",
        question="¿Qué variables explican mejor el movimiento de las siguientes cuatro velas?",
    ),
    ResearchQuestion(
        code="RQ-004",
        question="¿Qué factores permanecen estables en diferentes regímenes de mercado?",
    ),
    ResearchQuestion(
        code="RQ-005",
        question="¿Qué combinaciones de factores producen la mayor capacidad predictiva?",
    ),
    ResearchQuestion(
        code="RQ-006",
        question=(
            "¿Existen efectos de día de la semana o de secuencia entre "
            "sesiones (Asia→Londres→NY) con ventaja estadística "
            "persistente, ej. 'Monday Asia effect'?"
        ),
        objective=(
            "Determinar si la dirección de una sesión predice la "
            "dirección de la sesión siguiente, y si ese efecto (si "
            "existe) es uniforme entre días de la semana o se concentra "
            "en días específicos (ej. lunes, tras el fin de semana de "
            "menor liquidez)."
        ),
    ),
]


def get_research_question(code: str) -> ResearchQuestion | None:
    for rq in RESEARCH_QUESTIONS:
        if rq.code == code:
            return rq
    return None
