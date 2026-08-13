"""
Hypothesis Engine
=================

"La unidad fundamental de BRE." (ARCHITECTURE.md)

Una hipótesis contiene: código, pregunta, condiciones, variable
objetivo, prioridad, estado.

Regla de fase actual (2026-08-11, MANIFESTO.md Regla 5): BRE no usa
indicadores técnicos mientras la investigación se enfoca en efectos de
calendario y estructura de sesión. Las hipótesis basadas en EMA21/VWAP
(HYP_0002, HYP_0003) se retiraron del catálogo ACTIVO por esta razón —
no porque el conocimiento generado se haya invalidado. Siguen
existiendo como código (ARCHIVED_HYPOTHESES, más abajo) y su evidencia
sigue en data/experiments/score_log.jsonl y docs/KNOWLEDGE_BASE.md,
por la Regla 4: "BRE acumula conocimiento. Nunca reemplaza
conocimiento."
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class HypothesisStatus(str, Enum):
    DRAFT = "draft"
    EN_INVESTIGACION = "en_investigacion"
    VALIDADA = "validada"
    RECHAZADA = "rechazada"
    ARCHIVADA = "archivada"  # retirada del catálogo activo, nunca borrada (Regla 4)


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
# Registro de hipótesis ACTIVAS (Hypothesis Registry, ver ARCHITECTURE.md)
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

# Registro central de todas las hipótesis ACTIVAS del proyecto. Cada
# hipótesis nueva se agrega acá — es lo que el Catálogo (bre/catalog.py)
# recorre para construir la vista consolidada por pregunta de
# investigación. Las hipótesis retiradas van en ARCHIVED_HYPOTHESES,
# no acá.
HYPOTHESES: list[Hypothesis] = [
    HYP_0001,
]


# ---------------------------------------------------------------------
# HYP_0004 / HYP_0005 — efectos de calendario y sesión (sin indicadores)
# ---------------------------------------------------------------------
# Primeras hipótesis 100% libres de indicadores técnicos: usan solo
# retorno crudo de sesión (open->close) y calendario. Requieren
# feature_engine.build_features() (o al menos add_calendar,
# add_session_tag, add_session_relative, add_prior_session_return)
# corrido sobre el Dataset Maestro.

HYP_0004 = Hypothesis(
    code="HYP_0004",
    question=(
        "¿La dirección de una sesión predice la dirección de la sesión "
        "inmediatamente siguiente (Asia→Londres, Londres→NY), en "
        "general, en cualquier día de la semana?"
    ),
    condition="PREV_SESSION_DIRECTION != 0",
    target="ret_4",
    research_question="RQ-006",
    priority=1,
    status=HypothesisStatus.DRAFT,
    notes=(
        "Se prueba primero el efecto GENERAL (todos los días) antes de "
        "restringir a lunes en HYP_0005 — probar lo general primero es "
        "más honesto metodológicamente que ir directo al caso "
        "específico que se quiere encontrar (el mismo error que ya "
        "cometimos una vez con HYP_0002/0003 al formalizar un hallazgo "
        "puntual sin antes chequear su versión general)."
    ),
    tags=("calendario", "sesion", "sin_indicadores"),
)

HYPOTHESES.append(HYP_0004)

HYP_0005 = Hypothesis(
    code="HYP_0005",
    question=(
        "¿El efecto de HYP_0004 (sesión previa predice la siguiente) es "
        "más fuerte específicamente los lunes — 'Monday Asia effect' "
        "(la sesión Asia del lunes predice la sesión Londres del "
        "mismo lunes)?"
    ),
    condition="PREV_SESSION_DIRECTION != 0 and WEEKDAY == 0",
    target="ret_4",
    research_question="RQ-006",
    priority=1,
    status=HypothesisStatus.DRAFT,
    notes=(
        "Versión acotada a lunes de HYP_0004. Corré HYP_0004 primero: "
        "si el efecto general no existe, un resultado positivo acá con "
        "muestra mucho más chica (1/7 de los días) es más sospechoso de "
        "sobreajuste por multiple testing que evidencia real — "
        "documentarlo así explícitamente si el Scoring Engine lo marca "
        "como prometedor o validado."
    ),
    tags=("calendario", "sesion", "monday_effect", "sin_indicadores"),
)

HYPOTHESES.append(HYP_0005)


# ---------------------------------------------------------------------
# HYP_0006 — "Monday Asia Open Effect" (calibrada sobre evidencia externa)
# ---------------------------------------------------------------------
# A diferencia de HYP_0004/0005 (bandas genéricas ASIA/LONDON/NEWYORK
# en UTC, definición propia de BRE), HYP_0006 usa la ventana horaria
# EXACTA que reporta Concretum Research en "Seasonality in Bitcoin
# Intraday Trend Trading" (ene-2026): 24h desde la apertura de la Bolsa
# de Tokio, que — al no tener Japón horario de verano — equivale
# exactamente a "todo el lunes en UTC" (ver nota metodológica en
# feature_engine.add_tokyo_open_window).
#
# Tampoco mide lo mismo que HYP_0004/0005: esas miden DIRECCIÓN
# (¿sesión previa predice el signo de la siguiente?). Concretum mide
# INTENSIDAD DE TENDENCIA (¿hay más movimiento persistente/explotable
# en esa ventana?), usando un benchmark de trend-following long-short
# — que es un indicador, y por Regla 5 no lo replicamos. HYP_0006 usa
# el análogo sin indicadores más cercano: la magnitud absoluta del
# retorno (ABS_RET_4), como proxy crudo de "cuánto se mueve el precio"
# en esa ventana vs. el resto de la semana.

HYP_0006 = Hypothesis(
    code="HYP_0006",
    question=(
        "¿La magnitud del movimiento de precio (|ret_4|) es mayor "
        "durante la ventana de apertura de Tokio (24h desde lunes 00:00 "
        "UTC) que en el resto de la semana — el 'Monday Asia Open "
        "Effect' documentado externamente por Concretum Research?"
    ),
    condition="IN_TOKYO_OPEN_WINDOW == True",
    target="ABS_RET_4",
    research_question="RQ-006",
    priority=1,
    status=HypothesisStatus.DRAFT,
    notes=(
        "Ventana calibrada sobre evidencia externa (Concretum Research, "
        "'Seasonality in Bitcoin Intraday Trend Trading', ene-2026: "
        "https://concretumgroup.com/seasonality-in-bitcoin-intraday-trend-trading/), "
        "no sobre una banda genérica propia. Mide intensidad de "
        "movimiento (ABS_RET_4), no dirección — es una pregunta "
        "distinta a HYP_0004/0005, más cercana a lo que Concretum "
        "reportó. Antes de considerarla validada: (1) correr bootstrap "
        "sobre los retornos de test, no solo p-value (ver 'Trading "
        "Strategy Evaluation Using p-Values and Bootstrapping' de "
        "Concretum); (2) si da positiva, verificar las velas de "
        "apertura de sesión (00:00 UTC lunes) contra un segundo "
        "proveedor de datos (Bitstamp/Kraken) antes de confiar en el "
        "resultado — ver 'Backtesting Data Quality' de Concretum sobre "
        "cómo un solo proveedor puede inflar o inventar un efecto en "
        "los timestamps límite."
    ),
    tags=("calendario", "sesion", "monday_effect", "tokyo_open", "sin_indicadores"),
)

HYPOTHESES.append(HYP_0006)


# ---------------------------------------------------------------------
# ARCHIVADAS — retiradas del catálogo activo el 2026-08-11
# ---------------------------------------------------------------------
# Estudio de EMA21/VWAP. Se conserva el código y toda la evidencia
# (score_log.jsonl, KNOWLEDGE_BASE.md) por la Regla 4 del manifiesto,
# pero NO forman parte de HYPOTHESES: no aparecen en el catálogo activo
# ni se vuelven a correr en el Experiment Engine mientras dure la fase
# "sin indicadores". feature_engine.py ya no tiene las funciones
# (add_ema, add_session_vwap, add_ema_vwap_disagreement,
# add_ema_touch_and_bounce) que estas hipótesis necesitaban para correr
# — si se reactivan en el futuro, hay que restaurar esas funciones
# también (ver historial de git).

HYP_0002_ARCHIVADA = Hypothesis(
    code="HYP_0002",
    question=(
        "¿Los toques de EMA21 en desacuerdo con VWAP de sesión (lados "
        "opuestos del precio) tienen mayor tasa de rebote que los "
        "toques alineados?"
    ),
    condition="TOUCHES_EMA_21 == True and EMA_VWAP_DISAGREEMENT == True",
    target="BOUNCE_SIGNAL_EMA_21",
    research_question="RQ-003",
    priority=3,
    status=HypothesisStatus.ARCHIVADA,
    notes=(
        "RECHAZADA por el Scoring Engine (v0.7.0): effect size "
        "train=-1.60pp, test=-0.33pp, dirección opuesta a la esperada, "
        "sin significancia. ARCHIVADA el 2026-08-11: BRE dejó de "
        "investigar con indicadores técnicos por decisión de producto. "
        "Ver CHANGELOG v0.8.0."
    ),
)

HYP_0003_ARCHIVADA = Hypothesis(
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
    priority=3,
    status=HypothesisStatus.ARCHIVADA,
    notes=(
        "RECHAZADA por el Scoring Engine (v0.7.0): effect size "
        "train=-4.68pp, test=-1.46pp, dirección opuesta a la esperada "
        "(+11.8pp original), muestra chica (378/333). ARCHIVADA el "
        "2026-08-11 junto con HYP_0002. Ver CHANGELOG v0.8.0."
    ),
)

ARCHIVED_HYPOTHESES: list[Hypothesis] = [
    HYP_0002_ARCHIVADA,
    HYP_0003_ARCHIVADA,
]
