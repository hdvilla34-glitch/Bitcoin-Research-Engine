"""
Scoring Engine
==============

"Mide qué tan buena es la evidencia de un experimento y decide si una
hipótesis pasa a validada o rechazada." (ARCHITECTURE.md)

Criterios de diseño (decididos en conjunto, no arbitrarios):

1. Dos niveles de significancia:
   - alpha_informational (default 0.05): "vale la pena seguir investigando"
   - alpha_validated      (default 0.01): umbral real para pasar a la
     Knowledge Base como conocimiento validado.

2. Validación out-of-sample OBLIGATORIA: el dataset se parte
   cronológicamente en train/test. El efecto tiene que sostenerse en
   la mitad que el análisis nunca vio. Esto es lo que hubiera evitado
   el caso de la "ventana dorada" que no replicó en datos limpios.

3. Umbral de tamaño de efecto (no solo p-value): con datasets grandes,
   diferencias mínimas pueden salir "significativas" y ser inútiles en
   la práctica. Se exige un win_rate_delta_pp mínimo, no solo un p bajo.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path

import pandas as pd

from bre.experiment_engine import ExperimentResult, run_experiment
from bre.hypothesis import Hypothesis

DEFAULT_SCORE_LOG_PATH = Path("data/experiments/score_log.jsonl")


class ScoreVerdict(str, Enum):
    VALIDADA = "validada"
    PROMETEDORA = "prometedora"  # significativa en alpha_informational pero no en alpha_validated, o no replica out-of-sample
    RECHAZADA = "rechazada"
    MUESTRA_INSUFICIENTE = "muestra_insuficiente"


@dataclass
class ScoringConfig:
    alpha_informational: float = 0.05
    alpha_validated: float = 0.01
    min_sample_size: int = 300
    min_effect_size_pp: float = 2.0  # win_rate_delta_pp mínimo, en valor absoluto
    train_fraction: float = 0.5  # split cronológico train/test


@dataclass
class ScoreReport:
    hypothesis_code: str
    verdict: ScoreVerdict
    reasons: list[str] = field(default_factory=list)
    train_result: ExperimentResult | None = None
    test_result: ExperimentResult | None = None

    def summary(self) -> str:
        lines = [f"{self.hypothesis_code}: {self.verdict.value.upper()}"]
        for r in self.reasons:
            lines.append(f"  - {r}")
        return "\n".join(lines)


def split_chronological(df: pd.DataFrame, train_fraction: float = 0.5) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Parte el dataset en train/test respetando el orden temporal (NO random
    shuffle: es una serie de tiempo, mezclar filas invalidaría el split).
    """
    df = df.sort_index()
    cut = int(len(df) * train_fraction)
    train = df.iloc[:cut]
    test = df.iloc[cut:]
    return train, test


def score_hypothesis(
    df: pd.DataFrame,
    hypothesis: Hypothesis,
    config: ScoringConfig | None = None,
) -> ScoreReport:
    """
    Corre el experimento por separado en train y test (split cronológico)
    y aplica los 3 criterios de validación. Devuelve un veredicto con las
    razones explícitas, para que quede como evidencia auditable.
    """
    config = config or ScoringConfig()
    reasons: list[str] = []

    train_df, test_df = split_chronological(df, config.train_fraction)
    train_result = run_experiment(train_df, hypothesis, alpha=config.alpha_validated)
    test_result = run_experiment(test_df, hypothesis, alpha=config.alpha_validated)

    # --- criterio 1: tamaño de muestra minimo, en AMBAS mitades ---
    if train_result.sample_size < config.min_sample_size or test_result.sample_size < config.min_sample_size:
        reasons.append(
            f"Muestra insuficiente: train={train_result.sample_size}, "
            f"test={test_result.sample_size} (mínimo requerido: {config.min_sample_size})"
        )
        return ScoreReport(
            hypothesis_code=hypothesis.code,
            verdict=ScoreVerdict.MUESTRA_INSUFICIENTE,
            reasons=reasons,
            train_result=train_result,
            test_result=test_result,
        )

    # --- criterio 2: tamaño de efecto minimo, en AMBAS mitades ---
    train_effect_ok = abs(train_result.win_rate_delta_pp) >= config.min_effect_size_pp
    test_effect_ok = abs(test_result.win_rate_delta_pp) >= config.min_effect_size_pp
    reasons.append(
        f"Effect size: train={train_result.win_rate_delta_pp:+.3f}pp, "
        f"test={test_result.win_rate_delta_pp:+.3f}pp (mínimo exigido: ±{config.min_effect_size_pp}pp)"
    )

    # --- criterio 3: consistencia de signo train vs test (mismo sentido del edge) ---
    same_direction = (
        train_result.win_rate_delta_pp * test_result.win_rate_delta_pp > 0
    )
    if not same_direction:
        reasons.append("El efecto cambia de dirección entre train y test: no replica out-of-sample.")

    # --- criterio 4: significancia estadistica en test (la mitad que "no vimos") ---
    test_significant_informational = test_result.p_value < config.alpha_informational
    test_significant_validated = test_result.p_value < config.alpha_validated
    reasons.append(
        f"p-value en test: {test_result.p_value:.4f} "
        f"(informacional<{config.alpha_informational}, validada<{config.alpha_validated})"
    )

    # --- veredicto ---
    if (
        train_effect_ok
        and test_effect_ok
        and same_direction
        and test_significant_validated
    ):
        verdict = ScoreVerdict.VALIDADA
        reasons.append("Cumple los 4 criterios: muestra, effect size, replicación out-of-sample y significancia estricta.")
    elif same_direction and test_significant_informational:
        verdict = ScoreVerdict.PROMETEDORA
        reasons.append("Pasa el umbral informacional pero no el de validación estricta y/o el effect size mínimo. Sigue en investigación, no pasa a Knowledge Base todavía.")
    else:
        verdict = ScoreVerdict.RECHAZADA
        reasons.append("No cumple los criterios mínimos de evidencia.")

    return ScoreReport(
        hypothesis_code=hypothesis.code,
        verdict=verdict,
        reasons=reasons,
        train_result=train_result,
        test_result=test_result,
    )


def log_score(report: ScoreReport, log_path: str | Path = DEFAULT_SCORE_LOG_PATH) -> None:
    """Registra el veredicto en un log JSONL append-only (auditable, igual que experiment_engine)."""
    log_path = Path(log_path)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "hypothesis_code": report.hypothesis_code,
        "verdict": report.verdict.value,
        "reasons": report.reasons,
        "scored_at_utc": datetime.now(timezone.utc).isoformat(),
        "train_result": report.train_result.to_dict() if report.train_result else None,
        "test_result": report.test_result.to_dict() if report.test_result else None,
    }
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False) + "\n")
