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
    priority=1,
    status=HypothesisStatus.RECHAZADA,
    notes=(
        "Primera hipótesis del proyecto (CHANGELOG v0.1.0). "
        "Scoring Engine (v0.3.0): rechazada. El efecto cambia de signo "
        "entre train (+0.56pp) y test (-0.61pp) — no replica out-of-sample. "
        "p=0.43 en test, muy lejos de cualquier umbral de significancia."
    ),
)
