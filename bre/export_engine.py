"""
Export Engine
=============

"Exporta resultados de experimentos a formatos legibles y reutilizables
fuera de BRE." (ARCHITECTURE.md)

Los logs JSONL (`score_log.jsonl`, `experiment_log.jsonl`) son el
formato de registro append-only, pensado para escritura, no para
lectura. Este módulo los convierte en:

- CSV (`data/exports/scores.csv`): una fila por hipótesis evaluada, con
  las métricas de train/test aplanadas — listo para abrir en Colab,
  Excel o pandas sin parsear JSON anidado.
- Reporte de investigación (`data/exports/research_report.md`): un solo
  documento humano-legible que combina el Data Manifest (qué dataset se
  usó) con la Knowledge Base (qué se encontró), pensado para compartir
  o archivar como snapshot de un momento de la investigación.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from bre.knowledge_base import DEFAULT_SCORE_LOG, build_knowledge_base

DEFAULT_SCORES_CSV = Path("data/exports/scores.csv")
DEFAULT_RESEARCH_REPORT = Path("data/exports/research_report.md")
DEFAULT_MANIFEST = Path("data/master/manifest.json")


def _load_score_log(log_path: str | Path = DEFAULT_SCORE_LOG) -> list[dict]:
    log_path = Path(log_path)
    if not log_path.exists():
        return []
    return [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines()]


def export_scores_csv(
    score_log_path: str | Path = DEFAULT_SCORE_LOG,
    out_path: str | Path = DEFAULT_SCORES_CSV,
) -> pd.DataFrame:
    """
    Aplana score_log.jsonl (con train_result/test_result anidados) a un
    CSV de una fila por evaluación. Devuelve también el DataFrame, por
    si se quiere inspeccionar directo en el mismo proceso.
    """
    rows = _load_score_log(score_log_path)
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if not rows:
        empty = pd.DataFrame()
        empty.to_csv(out_path, index=False)
        return empty

    flat_rows = []
    for row in rows:
        flat = {
            "hypothesis_code": row["hypothesis_code"],
            "verdict": row["verdict"],
            "scored_at_utc": row["scored_at_utc"],
            "reasons": " | ".join(row.get("reasons", [])),
        }
        for split_name in ("train_result", "test_result"):
            split = row.get(split_name) or {}
            prefix = split_name.replace("_result", "")
            for k, v in split.items():
                flat[f"{prefix}_{k}"] = v
        flat_rows.append(flat)

    df = pd.DataFrame(flat_rows)
    df.to_csv(out_path, index=False)
    return df


def generate_research_report(
    score_log_path: str | Path = DEFAULT_SCORE_LOG,
    manifest_path: str | Path = DEFAULT_MANIFEST,
    out_path: str | Path = DEFAULT_RESEARCH_REPORT,
) -> str:
    """
    Genera un reporte de investigación de una sola pieza: contexto del
    dataset usado (Data Manifest) + resumen de cada hipótesis evaluada
    (Knowledge Base). Pensado como snapshot archivable de un momento de
    la investigación, no como documento que se edita a mano.
    """
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    manifest_path = Path(manifest_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {}

    entries = build_knowledge_base(score_log_path)

    lines = [
        "# Reporte de Investigación — BRE",
        "",
        f"_Generado: {datetime.now(timezone.utc).isoformat()}_",
        "",
        "## Dataset usado",
        "",
    ]
    if manifest:
        lines += [
            f"- Símbolo: {manifest.get('symbol')} ({manifest.get('timeframe')})",
            f"- Rango: {manifest.get('start')} → {manifest.get('end')}",
            f"- Filas: {manifest.get('rows')}",
            f"- Hash del dataset: `{manifest.get('dataset_hash')}`",
            f"- Huecos conocidos: {len(manifest.get('known_gaps', []))}",
        ]
    else:
        lines.append("_No se encontró data/master/manifest.json_")

    lines += ["", "## Hipótesis evaluadas", ""]

    if not entries:
        lines.append("_Todavía no hay hipótesis evaluadas por el Scoring Engine._")
    else:
        by_verdict: dict[str, int] = {}
        for e in entries:
            by_verdict[e.verdict] = by_verdict.get(e.verdict, 0) + 1
        resumen = " · ".join(f"{v}: {c}" for v, c in sorted(by_verdict.items()))
        lines.append(f"**Resumen:** {resumen} (total: {len(entries)})")
        lines.append("")

        for e in entries:
            lines.append(f"### {e.hypothesis_code} — {e.verdict.upper()}")
            lines.append(f"- Pregunta: {e.question}")
            lines.append(f"- Condición: `{e.condition}` → target `{e.target}`")
            lines.append(
                f"- Effect size: train {e.train_win_rate_delta_pp:+.3f}pp · "
                f"test {e.test_win_rate_delta_pp:+.3f}pp"
            )
            lines.append(f"- p-value (test): {e.test_p_value:.4f}")
            lines.append("")

    report = "\n".join(lines)
    out_path.write_text(report, encoding="utf-8")
    return report


def export_all(
    score_log_path: str | Path = DEFAULT_SCORE_LOG,
    manifest_path: str | Path = DEFAULT_MANIFEST,
    scores_csv_out: str | Path = DEFAULT_SCORES_CSV,
    report_out: str | Path = DEFAULT_RESEARCH_REPORT,
) -> None:
    """Corre ambas exportaciones de una sola vez."""
    export_scores_csv(score_log_path, scores_csv_out)
    generate_research_report(score_log_path, manifest_path, report_out)
