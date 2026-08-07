"""
Hypothesis Engine
=================

"La unidad fundamental de BRE." (ARCHITECTURE.md)

Una hipótesis contiene: código, pregunta, condiciones, variable
objetivo, prioridad, estado.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class HypothesisStatus(str, Enum):
    DRAFT = "draft"
    EN_INVESTIGACION = "en_investigacion"
    VALIDADA = "validada"
    RECHAZADA = "rechazada"


@dataclass
class Hypothesis:
    code: str
    question: str
    condition: str  # expresión evaluable con DataFrame.query()
    target: str  # nombre de la columna objetivo, ej. "ret_4"
    research_question: str = ""  # código de RESEARCH_QUESTIONS, ej. "RQ-003"
    priority: int = 3
    status: HypothesisStatus = HypothesisStatus.DRAFT
    notes: str = ""
    tags: tuple[str, ...] = field(default_factory=tuple)

    def as_dict(self) -> dict:
        return {
            "code": self.code,
            "question": self.question,
            "condition": self.condition,
            "target": self.target,
            "research_question": self.research_question,
            "priority": self.priority,
            "status": self.status.value,
            "notes": self.notes,
            "tags": list(self.tags),
        }


# ---------------------------------------------------------------------
# Registro de hipótesis conocidas (Hypothesis Registry, ver ARCHITECTURE.md)
# ---------------------------------------------------------------------

HYP_0001 = Hypothesis(
    code="HYP_0001",
    question="¿Los cuerpos grandes presentan continuidad?",
    condition="BODY_RATIO >= 0.70",
    target="ret_4",
    research_question="RQ-003",
    priority=1,
    status=HypothesisStatus.RECHAZADA,
    notes=(
        "Primera hipótesis del proyecto (CHANGELOG v0.1.0). "
        "Scoring Engine (v0.3.0): rechazada. El efecto cambia de signo "
        "entre train (+0.56pp) y test (-0.61pp) — no replica out-of-sample. "
        "p=0.43 en test, muy lejos de cualquier umbral de significancia."
    ),
)

# Registro central de todas las hipótesis del proyecto. Cada hipótesis nueva
# se agrega aquí — es lo que el Catálogo (bre/catalog.py) recorre para
# construir la vista consolidada por pregunta de investigación.
HYPOTHESES: list[Hypothesis] = [
    HYP_0001,
]

HYP_0002 = Hypothesis(
    code="HYP_0002",
    question=(
        "¿Los toques de EMA21 en desacuerdo con VWAP de sesión (lados "
        "opuestos del precio) tienen mayor tasa de rebote que los "
        "toques alineados?"
    ),
    condition="TOUCHES_EMA_21 == True and EMA_VWAP_DISAGREEMENT == True",
    target="BOUNCE_SIGNAL_EMA_21",
    research_question="RQ-003",
    priority=1,
    status=HypothesisStatus.RECHAZADA,
    notes=(
        "Formalización de un hallazgo de research previo (fuera de BRE): "
        "+11.8pp de bounce rate en toques EMA21 con desacuerdo vs "
        "alineados. Scoring Engine: RECHAZADA. Effect size train=-1.60pp, "
        "test=-0.33pp (dirección OPUESTA a la esperada, sin significancia). "
        "No replica con esta implementación — ver HYP_0003 para la versión "
        "restringida a sesión NY, y CHANGELOG v0.7.0 para discusión de "
        "posibles diferencias metodológicas vs el hallazgo original."
    ),
)

HYPOTHESES.append(HYP_0002)

HYP_0003 = Hypothesis(
    code="HYP_0003",
    question=(
        "¿Los toques de EMA21 en desacuerdo con VWAP de sesión, DENTRO "
        "de la ventana de sesión NY (8:00-12:00 ET), tienen mayor tasa "
        "de rebote que los toques alineados en esa misma ventana?"
    ),
    condition=(
        "TOUCHES_EMA_21 == True and EMA_VWAP_DISAGREEMENT == True "
        "and NY_HOUR >= 8 and NY_HOUR < 12"
    ),
    target="BOUNCE_SIGNAL_EMA_21",
    research_question="RQ-001",
    priority=1,
    status=HypothesisStatus.RECHAZADA,
    notes=(
        "Réplica fiel del hallazgo original (que sí estaba acotado a "
        "sesión NY), a diferencia de HYP_0002 que probó las 24h. "
        "Scoring Engine: RECHAZADA. Effect size train=-4.68pp, "
        "test=-1.46pp — dirección OPUESTA a la esperada (+11.8pp "
        "original), muestra chica (378/333). No replica. Diferencias "
        "metodológicas probables: definición exacta de 'rebote', anclaje "
        "del VWAP de sesión (aquí: 00:00 UTC), o ventana horaria exacta. "
        "Pendiente: revisar metodología original con Hernán antes de "
        "descartar el hallazgo por completo."
    ),
)

HYPOTHESES.append(HYP_0003)
