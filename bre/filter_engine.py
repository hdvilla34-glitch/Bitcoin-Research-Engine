"""
Filter Engine
=============

"Aplica las condiciones de una hipótesis sobre el Dataset Maestro.
Devuelve únicamente los casos que cumplen la evidencia buscada."
(ARCHITECTURE.md)
"""

from __future__ import annotations

import pandas as pd

from bre.hypothesis import Hypothesis


def apply_filter(df: pd.DataFrame, hypothesis: Hypothesis) -> pd.DataFrame:
    """
    Devuelve el subconjunto de `df` que cumple `hypothesis.condition`.

    La condición se evalúa con `DataFrame.query`, así que debe ser una
    expresión válida en términos de las columnas del dataset
    (incluyendo features generadas por el Feature Engine).
    """
    if hypothesis.target not in df.columns:
        raise KeyError(
            f"La columna objetivo '{hypothesis.target}' de {hypothesis.code} "
            f"no existe en el dataset. ¿Corriste el Feature Engine primero?"
        )

    filtered = df.query(hypothesis.condition)
    return filtered
