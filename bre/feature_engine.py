"""
Feature Engine
==============

Construye variables derivadas sobre el Dataset Maestro.

Regla de arquitectura (ver ARCHITECTURE.md):
"Nunca crea indicadores sin una hipótesis. Las features deben
responder a preguntas de investigación."

Por eso cada función de este módulo documenta la pregunta que
justifica su existencia.
"""

from __future__ import annotations

import pandas as pd


def add_body_ratio(df: pd.DataFrame) -> pd.DataFrame:
    """
    BODY_RATIO: proporción del rango total de la vela ocupado por el
    cuerpo (open-close) vs la mecha total (high-low).

    Justificación (HYP_0001): "¿Los cuerpos grandes presentan continuidad?"
    Necesita distinguir velas de cuerpo dominante vs velas indecisas/mecha.
    """
    df = df.copy()
    rango = (df["high"] - df["low"]).replace(0, pd.NA)
    df["BODY_RATIO"] = (df["close"] - df["open"]).abs() / rango
    df["BODY_RATIO"] = df["BODY_RATIO"].fillna(0.0)
    return df


def add_forward_returns(df: pd.DataFrame, periods: tuple[int, ...] = (4,)) -> pd.DataFrame:
    """
    ret_N: retorno hacia adelante N barras, medido desde el close de la
    barra actual hasta el close N barras después.

    Justificación (HYP_0001): variable objetivo para medir "continuidad"
    después de una condición observada en la barra actual.
    """
    df = df.copy()
    for n in periods:
        df[f"ret_{n}"] = df["close"].shift(-n) / df["close"] - 1.0
    return df


def build_features(df: pd.DataFrame, ret_periods: tuple[int, ...] = (4,)) -> pd.DataFrame:
    """Aplica el set base de features usado por las hipótesis actuales."""
    df = add_body_ratio(df)
    df = add_forward_returns(df, periods=ret_periods)
    return df
