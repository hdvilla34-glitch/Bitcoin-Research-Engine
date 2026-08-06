"""
Genera el Data Manifest del Dataset Maestro: metadata versionable que
declara rango de fechas, filas, hash y huecos conocidos.

Este archivo es lo que hace que un experimento sea reproducible: sin
esto, "p=0.91 en HYP_0001" no dice nada si el dataset cambia después
sin que quede registrado.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from bre.data_manager import ValidationReport
from bre.experiment_engine import _dataset_hash


def build_manifest(df: pd.DataFrame, report: ValidationReport, source_folder: str) -> dict:
    return {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_folder": source_folder,
        "symbol": "BTCUSDT",
        "timeframe": "15m",
        "rows": report.total_rows,
        "dataset_hash": _dataset_hash(df),
        "start": str(report.start),
        "end": str(report.end),
        "duplicated_timestamps_dropped": report.duplicated_timestamps_dropped,
        "known_gaps": [
            {"after": str(g[0]), "before": str(g[1])} for g in report.gaps
        ],
        "columns": list(df.columns),
    }


def write_manifest(manifest: dict, out_path: str | Path = "data/master/manifest.json") -> None:
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
