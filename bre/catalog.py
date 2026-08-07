"""
Catálogo de Hipótesis
======================

Fase 3 — Descubrimiento (ROADMAP.md).

"Toda nueva feature, experimento o módulo debe responder al menos una
[pregunta de investigación]." (RESEARCH_QUESTIONS.md)

El catálogo agrupa `bre.hypothesis.HYPOTHESES` por `research_question`,
cruzándolo contra el registro completo de `bre.research_questions`. Esto
es lo que lo distingue de simplemente listar hipótesis: muestra también
las preguntas que TODAVÍA no tienen ninguna hipótesis asociada — el
vacío es tan informativo como lo que sí está cubierto.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from bre.hypothesis import HYPOTHESES, Hypothesis
from bre.research_questions import RESEARCH_QUESTIONS, ResearchQuestion

DEFAULT_CATALOG_JSON = Path("data/knowledge/hypothesis_catalog.json")
DEFAULT_CATALOG_MARKDOWN = Path("docs/HYPOTHESIS_CATALOG.md")


@dataclass
class CatalogGroup:
    research_question: ResearchQuestion
    hypotheses: list[Hypothesis]

    @property
    def is_covered(self) -> bool:
        return len(self.hypotheses) > 0

    @property
    def has_validated(self) -> bool:
        return any(h.status.value == "validada" for h in self.hypotheses)


def build_catalog(
    hypotheses: list[Hypothesis] | None = None,
    research_questions: list[ResearchQuestion] | None = None,
) -> list[CatalogGroup]:
    """
    Agrupa las hipótesis por research_question. Incluye TODAS las
    research questions del registro, aunque tengan cero hipótesis —
    ese es el punto: mostrar el vacío, no solo lo cubierto.

    Hipótesis sin research_question asignado (o con un código que no
    existe en el registro) se agrupan aparte, bajo "SIN_CLASIFICAR",
    para que no desaparezcan silenciosamente.
    """
    hypotheses = hypotheses if hypotheses is not None else HYPOTHESES
    research_questions = research_questions if research_questions is not None else RESEARCH_QUESTIONS

    valid_codes = {rq.code for rq in research_questions}
    by_rq: dict[str, list[Hypothesis]] = {rq.code: [] for rq in research_questions}
    unclassified: list[Hypothesis] = []

    for h in hypotheses:
        if h.research_question in valid_codes:
            by_rq[h.research_question].append(h)
        else:
            unclassified.append(h)

    groups = [CatalogGroup(research_question=rq, hypotheses=by_rq[rq.code]) for rq in research_questions]

    if unclassified:
        groups.append(
            CatalogGroup(
                research_question=ResearchQuestion(
                    code="SIN_CLASIFICAR",
                    question="Hipótesis sin research_question válido asignado",
                ),
                hypotheses=unclassified,
            )
        )

    return groups


def write_catalog_json(groups: list[CatalogGroup], out_path: str | Path = DEFAULT_CATALOG_JSON) -> None:
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "groups": [
            {
                "research_question_code": g.research_question.code,
                "research_question": g.research_question.question,
                "is_covered": g.is_covered,
                "hypotheses": [h.as_dict() for h in g.hypotheses],
            }
            for g in groups
        ],
    }
    out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def write_catalog_markdown(groups: list[CatalogGroup], out_path: str | Path = DEFAULT_CATALOG_MARKDOWN) -> None:
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    covered = sum(1 for g in groups if g.is_covered)
    total = len(groups)

    lines = [
        "# Catálogo de Hipótesis — BRE",
        "",
        "Generado automáticamente por `bre/catalog.py`. No editar a mano.",
        "",
        f"**Cobertura:** {covered}/{total} preguntas de investigación tienen al menos una hipótesis.",
        "",
    ]

    for g in groups:
        icon = "✅" if g.has_validated else ("🟡" if g.is_covered else "⚪")
        lines.append(f"## {icon} {g.research_question.code} — {g.research_question.question}")
        lines.append("")
        if g.research_question.objective:
            lines.append(f"_Objetivo: {g.research_question.objective}_")
            lines.append("")

        if not g.hypotheses:
            lines.append("**Sin hipótesis todavía.** Pregunta abierta.")
        else:
            for h in g.hypotheses:
                lines.append(f"- **{h.code}** [{h.status.value}] — {h.question}")
                lines.append(f"  - `{h.condition}` → target `{h.target}`")
        lines.append("")
        lines.append("---")
        lines.append("")

    out_path.write_text("\n".join(lines), encoding="utf-8")


def refresh_catalog(
    json_out: str | Path = DEFAULT_CATALOG_JSON,
    markdown_out: str | Path = DEFAULT_CATALOG_MARKDOWN,
) -> list[CatalogGroup]:
    groups = build_catalog()
    write_catalog_json(groups, json_out)
    write_catalog_markdown(groups, markdown_out)
    return groups
