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


def add_ema(df: pd.DataFrame, span: int = 21, price_col: str = "close") -> pd.DataFrame:
    """
    EMA_{span}: media móvil exponencial sobre `price_col`.

    Justificación (RQ-003 / HYP_0002): EMA21 como nivel dinámico de
    soporte/resistencia; se necesita para detectar "toques" del precio
    sobre el nivel.
    """
    df = df.copy()
    df[f"EMA_{span}"] = df[price_col].ewm(span=span, adjust=False).mean()
    return df


def add_session_vwap(df: pd.DataFrame, reset: str = "D") -> pd.DataFrame:
    """
    VWAP anclado por sesión (se reinicia cada día a las 00:00 UTC por
    defecto — ASUNCIÓN documentada, ajustar `reset` si la sesión real
    debe anclarse distinto, ej. a la apertura de NY).

    Justificación (RQ-003 / HYP_0002): VWAP como segundo nivel dinámico,
    para detectar cuándo EMA21 y VWAP están en "desacuerdo" (lados
    opuestos del precio).
    """
    df = df.copy()
    typical_price = (df["high"] + df["low"] + df["close"]) / 3.0
    pv = typical_price * df["volume"]

    session_key = df.index.tz_convert("UTC").floor(reset)
    cum_pv = pv.groupby(session_key).cumsum()
    cum_vol = df["volume"].groupby(session_key).cumsum()

    df["SESSION_VWAP"] = cum_pv / cum_vol.replace(0, pd.NA)
    return df


def add_ema_vwap_disagreement(df: pd.DataFrame, ema_span: int = 21) -> pd.DataFrame:
    """
    EMA_VWAP_DISAGREEMENT: True cuando EMA_{ema_span} y SESSION_VWAP
    quedan en lados opuestos del precio de cierre (uno arriba, el otro
    abajo). Requiere haber corrido add_ema() y add_session_vwap() antes.

    Justificación (HYP_0002): research previo (fuera de BRE) encontró
    que los toques de EMA21 en "desacuerdo" con VWAP tienen ~+11.8pp
    más bounce rate que los toques alineados.
    """
    df = df.copy()
    ema_col = f"EMA_{ema_span}"
    ema_above = df[ema_col] > df["close"]
    vwap_above = df["SESSION_VWAP"] > df["close"]
    df["EMA_VWAP_DISAGREEMENT"] = ema_above != vwap_above
    return df


def add_ny_hour(df: pd.DataFrame) -> pd.DataFrame:
    """
    NY_HOUR: hora del día en zona horaria America/New_York (maneja DST
    automáticamente, a diferencia de un offset fijo UTC-4/UTC-5).

    Justificación (RQ-001 / HYP_0002): el research previo (fuera de BRE)
    que encontró el efecto EMA21/VWAP estaba acotado a la sesión NY
    (8:00-12:00 ET). Sin esta feature, cualquier hipótesis que dependa
    de esa ventana horaria no se puede filtrar correctamente.
    """
    df = df.copy()
    df["NY_HOUR"] = df.index.tz_convert("America/New_York").hour
    return df


def add_ema_touch_and_bounce(
    df: pd.DataFrame,
    ema_span: int = 21,
    trend_lookback: int = 4,
    forward_col: str = "ret_4",
) -> pd.DataFrame:
    """
    TOUCHES_EMA_{span}: True si el rango de la vela (low..high) cruza
    EMA_{span} — el precio "tocó" el nivel dentro de esa barra.

    BOUNCE_SIGNAL_EMA_{span}: +1 / -1 / NaN. Solo definido en barras
    donde hubo toque. +1 si, tras el toque, el precio en `forward_col`
    barras adelante continúa en la misma dirección que la tendencia
    PREVIA al toque (medida sobre las `trend_lookback` barras
    anteriores) — esto se interpreta como "rebote" (el nivel sostuvo la
    tendencia). -1 si continúa en la dirección contraria ("ruptura").
    NaN si no hubo toque, o si la tendencia previa es exactamente plana
    (dirección ambigua, se excluye en vez de forzar un signo).

    Requiere add_ema() y `forward_col` (ej. ret_4 de add_forward_returns)
    ya calculados.
    """
    df = df.copy()
    ema_col = f"EMA_{ema_span}"

    touches = (df["low"] <= df[ema_col]) & (df["high"] >= df[ema_col])
    df[f"TOUCHES_EMA_{ema_span}"] = touches

    prior_trend = df["close"] - df["close"].shift(trend_lookback)
    prior_dir = pd.Series(0, index=df.index)
    prior_dir[prior_trend > 0] = 1
    prior_dir[prior_trend < 0] = -1

    forward_dir = pd.Series(0, index=df.index)
    forward_dir[df[forward_col] > 0] = 1
    forward_dir[df[forward_col] < 0] = -1

    bounce = pd.Series(pd.NA, index=df.index, dtype="Float64")
    valid = touches & (prior_dir != 0) & (forward_dir != 0)
    bounce.loc[valid] = (prior_dir[valid] == forward_dir[valid]).map({True: 1.0, False: -1.0})

    df[f"BOUNCE_SIGNAL_EMA_{ema_span}"] = bounce
    return df
