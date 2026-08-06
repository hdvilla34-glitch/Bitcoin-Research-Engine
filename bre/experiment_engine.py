"""
Experiment Engine
=================

"Ejecuta experimentos reproducibles. Genera: tamaño de muestra,
métricas, resultados, evidencia." (ARCHITECTURE.md)

Este módulo NO decide si una hipótesis es buena o mala (eso es
responsabilidad del Scoring Engine). Solo mide, de forma reproducible,
qué pasó en los datos.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from bre.filter_engine import apply_filter
from bre.hypothesis import Hypothesis

DEFAULT_LOG_PATH = Path("data/experiments/experiment_log.jsonl")


@dataclass
class ExperimentResult:
    hypothesis_code: str
    question: str
    condition: str
    target: str
    run_at_utc: str
    dataset_rows: int
    dataset_hash: str
    sample_size: int
    sample_pct_of_dataset: float
    target_mean: float
    target_median: float
    target_std: float
    win_rate: float
    baseline_win_rate: float
    win_rate_delta_pp: float
    z_stat: float
    p_value: float
    significant_95: bool

    def to_dict(self) -> dict:
        return asdict(self)


def _dataset_hash(df: pd.DataFrame) -> str:
    """Hash reproducible del dataset usado (para trazabilidad del experimento)."""
    payload = f"{len(df)}|{df.index.min()}|{df.index.max()}"
    return hashlib.sha256(payload.encode()).hexdigest()[:16]


def _two_proportion_z_test(p1: float, n1: int, p2: float, n2: int) -> tuple[float, float]:
    """
    Z-test de dos proporciones (muestra filtrada vs baseline).
    Devuelve (z_stat, p_value de dos colas). Sin dependencia de scipy
    para el cálculo del estadístico; usa la aproximación normal estándar
    para el p-value.
    """
    if n1 == 0 or n2 == 0:
        return float("nan"), float("nan")

    p_pool = (p1 * n1 + p2 * n2) / (n1 + n2)
    se = np.sqrt(p_pool * (1 - p_pool) * (1 / n1 + 1 / n2))
    if se == 0:
        return 0.0, 1.0

    z = (p1 - p2) / se

    # CDF normal estándar via erf (sin scipy)
    p_value = 2 * (1 - 0.5 * (1 + math.erf(abs(z) / np.sqrt(2))))
    return float(z), float(p_value)


def run_experiment(
    df: pd.DataFrame,
    hypothesis: Hypothesis,
    alpha: float = 0.05,
) -> ExperimentResult:
    """
    Corre un experimento reproducible: aplica el Filter Engine, calcula
    métricas del target dentro del subconjunto filtrado, y las compara
    contra el baseline (todo el dataset) con un test de proporciones
    sobre el win rate (target > 0).
    """
    filtered = apply_filter(df, hypothesis)
    target = hypothesis.target

    valid_full = df[target].dropna()
    valid_filtered = filtered[target].dropna()

    sample_size = len(valid_filtered)
    baseline_win_rate = float((valid_full > 0).mean()) if len(valid_full) else float("nan")
    win_rate = float((valid_filtered > 0).mean()) if sample_size else float("nan")

    z_stat, p_value = _two_proportion_z_test(
        p1=win_rate, n1=sample_size,
        p2=baseline_win_rate, n2=len(valid_full),
    )

    result = ExperimentResult(
        hypothesis_code=hypothesis.code,
        question=hypothesis.question,
        condition=hypothesis.condition,
        target=target,
        run_at_utc=datetime.now(timezone.utc).isoformat(),
        dataset_rows=len(df),
        dataset_hash=_dataset_hash(df),
        sample_size=sample_size,
        sample_pct_of_dataset=round(100 * sample_size / len(df), 4) if len(df) else 0.0,
        target_mean=float(valid_filtered.mean()) if sample_size else float("nan"),
        target_median=float(valid_filtered.median()) if sample_size else float("nan"),
        target_std=float(valid_filtered.std()) if sample_size else float("nan"),
        win_rate=win_rate,
        baseline_win_rate=baseline_win_rate,
        win_rate_delta_pp=round(100 * (win_rate - baseline_win_rate), 4)
            if sample_size else float("nan"),
        z_stat=z_stat,
        p_value=p_value,
        significant_95=bool(p_value < alpha) if not np.isnan(p_value) else False,
    )
    return result


def log_experiment(result: ExperimentResult, log_path: str | Path = DEFAULT_LOG_PATH) -> None:
    """Registra el experimento en un log JSONL append-only (evidencia acumulada)."""
    log_path = Path(log_path)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(result.to_dict(), ensure_ascii=False) + "\n")


def load_experiment_log(log_path: str | Path = DEFAULT_LOG_PATH) -> pd.DataFrame:
    """Carga el historial completo de experimentos como DataFrame."""
    log_path = Path(log_path)
    if not log_path.exists():
        return pd.DataFrame()
    rows = [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines()]
    return pd.DataFrame(rows)
