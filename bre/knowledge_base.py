"""
Knowledge Base
===============

"Almacena conocimiento validado (y rechazado) de forma consultable."
(ARCHITECTURE.md)

Un log JSONL es un registro; esto es conocimiento: por cada hipótesis,
consolida el ÚLTIMO veredicto del Scoring Engine (si una hipótesis se
re-corre, el conocimiento vigente es el más reciente, no el histórico
completo) y lo expone en dos formatos:

- JSON estructurado (`data/knowledge/knowledge_base.json`), para que
  otros módulos de BRE lo consulten programáticamente.
- Markdown legible (`docs/KNOWLEDGE_BASE.md`), para lectura humana
  directa en GitHub.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_SCORE_LOG = Path("data/experiments/score_log.jsonl")
DEFAULT_KB_JSON = Path("data/knowledge/knowledge_base.json")
DEFAULT_KB_MARKDOWN = Path("docs/KNOWLEDGE_BASE.md")


@dataclass
class KnowledgeEntry:
    hypothesis_code: str
    question: str
    condition: str
    target: str
    verdict: str
    reasons: list[str]
    train_win_rate_delta_pp: float
    test_win_rate_delta_pp: float
    test_p_value: float
    last_scored_utc: str

    def to_dict(self) -> dict:
        return {
            "hypothesis_code": self.hypothesis_code,
            "question": self.question,
            "condition": self.condition,
            "target": self.target,
            "verdict": self.verdict,
            "reasons": self.reasons,
            "train_win_rate_delta_pp": self.train_win_rate_delta_pp,
            "test_win_rate_delta_pp": self.test_win_rate_delta_pp,
            "test_p_value": self.test_p_value,
            "last_scored_utc": self.last_scored_utc,
        }


def _load_score_log(log_path: str | Path = DEFAULT_SCORE_LOG) -> list[dict]:
    log_path = Path(log_path)
    if not log_path.exists():
        return []
    return [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines()]


def build_knowledge_base(log_path: str | Path = DEFAULT_SCORE_LOG) -> list[KnowledgeEntry]:
    """
    Consolida el score_log.jsonl en una entrada por hipótesis, quedándose
    con el veredicto MÁS RECIENTE de cada código (por si se re-corrió).
    """
    rows = _load_score_log(log_path)
    latest_by_code: dict[str, dict] = {}
    for row in rows:
        code = row["hypothesis_code"]
        if code not in latest_by_code or row["scored_at_utc"] > latest_by_code[code]["scored_at_utc"]:
            latest_by_code[code] = row

    entries = []
    for code, row in sorted(latest_by_code.items()):
        train = row.get("train_result") or {}
        test = row.get("test_result") or {}
        entries.append(
            KnowledgeEntry(
                hypothesis_code=code,
                question=test.get("question", train.get("question", "")),
                condition=test.get("condition", train.get("condition", "")),
                target=test.get("target", train.get("target", "")),
                verdict=row["verdict"],
                reasons=row["reasons"],
                train_win_rate_delta_pp=train.get("win_rate_delta_pp", float("nan")),
                test_win_rate_delta_pp=test.get("win_rate_delta_pp", float("nan")),
                test_p_value=test.get("p_value", float("nan")),
                last_scored_utc=row["scored_at_utc"],
            )
        )
    return entries


def write_knowledge_base_json(
    entries: list[KnowledgeEntry],
    out_path: str | Path = DEFAULT_KB_JSON,
) -> None:
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "entries": [e.to_dict() for e in entries],
    }
    out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


_VERDICT_EMOJI = {
    "validada": "✅",
    "prometedora": "🟡",
    "rechazada": "❌",
    "muestra_insuficiente": "⚪",
}


def write_knowledge_base_markdown(
    entries: list[KnowledgeEntry],
    out_path: str | Path = DEFAULT_KB_MARKDOWN,
) -> None:
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "# Knowledge Base — BRE",
        "",
        "Generado automáticamente por `bre/knowledge_base.py`. No editar a mano.",
        "",
        "Conocimiento validado **y rechazado**: según el manifiesto de BRE, un "
        "rechazo documentado con evidencia es tan valioso como una validación.",
        "",
    ]

    if not entries:
        lines.append("_Todavía no hay hipótesis evaluadas por el Scoring Engine._")
    else:
        validated = [e for e in entries if e.verdict == "validada"]
        promising = [e for e in entries if e.verdict == "prometedora"]
        rejected = [e for e in entries if e.verdict == "rechazada"]
        insufficient = [e for e in entries if e.verdict == "muestra_insuficiente"]

        lines.append(
            f"**Resumen:** {len(validated)} validadas · {len(promising)} prometedoras · "
            f"{len(rejected)} rechazadas · {len(insufficient)} con muestra insuficiente."
        )
        lines.append("")

        for e in entries:
            emoji = _VERDICT_EMOJI.get(e.verdict, "")
            lines.append(f"## {emoji} {e.hypothesis_code} — {e.verdict.upper()}")
            lines.append("")
            lines.append(f"**Pregunta:** {e.question}")
            lines.append("")
            lines.append(f"**Condición:** `{e.condition}` → target `{e.target}`")
            lines.append("")
            lines.append(
                f"**Effect size:** train {e.train_win_rate_delta_pp:+.3f}pp · "
                f"test {e.test_win_rate_delta_pp:+.3f}pp"
            )
            lines.append(f"**p-value (test):** {e.test_p_value:.4f}")
            lines.append("")
            lines.append("**Razones del veredicto:**")
            for r in e.reasons:
                lines.append(f"- {r}")
            lines.append("")
            lines.append(f"_Última evaluación: {e.last_scored_utc}_")
            lines.append("")
            lines.append("---")
            lines.append("")

    out_path.write_text("\n".join(lines), encoding="utf-8")


def refresh_knowledge_base(
    score_log_path: str | Path = DEFAULT_SCORE_LOG,
    json_out: str | Path = DEFAULT_KB_JSON,
    markdown_out: str | Path = DEFAULT_KB_MARKDOWN,
) -> list[KnowledgeEntry]:
    """Pipeline completo: lee el score_log, y regenera JSON + Markdown."""
    entries = build_knowledge_base(score_log_path)
    write_knowledge_base_json(entries, json_out)
    write_knowledge_base_markdown(entries, markdown_out)
    return entries
