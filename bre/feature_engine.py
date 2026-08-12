"""
Feature Engine
==============

"Construye variables derivadas. Nunca crea indicadores sin una
hipótesis. Las features deben responder a preguntas de investigación."
(ARCHITECTURE.md)

Regla de fase actual (ver MANIFESTO.md, Regla 5): BRE NO usa
indicadores técnicos (EMA, VWAP, RSI, ADX, etc.) mientras la
investigación se enfoca en efectos de calendario y estructura de
sesión (RQ-001, RQ-002, RQ-006). Toda feature de este módulo se deriva
de tres fuentes únicamente:

1. Precio crudo (OHLC)
2. Volumen / actividad cruda (volume, trades, taker buy/sell)
3. Tiempo (calendario UTC/NY, sesión)

Si en el futuro una hipótesis específica justifica un indicador, se
agrega en un módulo aparte y se documenta la razón — no se mezcla acá.

Orden de uso recomendado (ver build_features() al final del archivo):

    add_forward_returns -> add_backward_returns -> add_body_ratio ->
    add_candle_geometry -> add_taker_buy_ratio -> add_calendar ->
    add_session_tag -> add_session_relative -> add_prior_session_return
"""

from __future__ import annotations

import pandas as pd


# ---------------------------------------------------------------------
# Retornos (targets de las hipótesis)
# ---------------------------------------------------------------------

def add_forward_returns(
    df: pd.DataFrame, periods: tuple[int, ...] = (1, 4, 8, 16)
) -> pd.DataFrame:
    """
    ret_N: retorno porcentual N velas hacia adelante desde el cierre
    actual. Es el target típico de las hipótesis de BRE (ver RQ-003).
    Genera NaN en las últimas N filas del dataset (no hay futuro para
    calcularlo) — se excluyen solas al usar .dropna() en Filter/
    Experiment Engine.
    """
    df = df.copy()
    for n in periods:
        df[f"ret_{n}"] = df["close"].shift(-n) / df["close"] - 1.0
    return df


def add_backward_returns(
    df: pd.DataFrame, periods: tuple[int, ...] = (1, 4, 8, 16)
) -> pd.DataFrame:
    """
    ret_back_N: retorno porcentual de las N velas anteriores hasta el
    cierre actual. Retorno crudo, no indicador — permite condicionar
    hipótesis en momentum/reversión reciente sin usar EMA/RSI/etc.
    """
    df = df.copy()
    for n in periods:
        df[f"ret_back_{n}"] = df["close"] / df["close"].shift(n) - 1.0
    return df


# ---------------------------------------------------------------------
# Geometría de vela (precio crudo — no es un indicador)
# ---------------------------------------------------------------------

def add_body_ratio(df: pd.DataFrame) -> pd.DataFrame:
    """
    BODY_RATIO: tamaño del cuerpo de la vela relativo a su rango total
    (high-low). 1.0 = vela sin mechas. 0.0 = doji perfecto.
    Justificación (RQ-003 / HYP_0001).
    """
    df = df.copy()
    rng = (df["high"] - df["low"]).replace(0, pd.NA)
    df["BODY_RATIO"] = (df["close"] - df["open"]).abs() / rng
    return df


def add_candle_geometry(df: pd.DataFrame) -> pd.DataFrame:
    """
    Geometría adicional de la vela, toda derivada de OHLC crudo:

    - RANGE_PCT: rango (high-low) como % del close. Mide volatilidad
      intra-vela sin usar ningún indicador (no es ATR ni similar).
    - UPPER_WICK_RATIO / LOWER_WICK_RATIO: tamaño de cada mecha
      relativo al rango total de la vela.
    - DIRECTION: +1 vela alcista, -1 bajista, 0 doji exacto
      (close == open).
    """
    df = df.copy()
    rng = (df["high"] - df["low"]).replace(0, pd.NA)

    df["RANGE_PCT"] = (df["high"] - df["low"]) / df["close"]
    df["UPPER_WICK_RATIO"] = (df["high"] - df[["open", "close"]].max(axis=1)) / rng
    df["LOWER_WICK_RATIO"] = (df[["open", "close"]].min(axis=1) - df["low"]) / rng

    direction = pd.Series(0, index=df.index)
    direction[df["close"] > df["open"]] = 1
    direction[df["close"] < df["open"]] = -1
    df["DIRECTION"] = direction
    return df


# ---------------------------------------------------------------------
# Volumen / actividad cruda (sin indicadores de volumen)
# ---------------------------------------------------------------------

def add_taker_buy_ratio(df: pd.DataFrame) -> pd.DataFrame:
    """
    TAKER_BUY_RATIO: fracción del volumen de la vela que fue compra
    agresiva (taker buy) sobre volumen total. > 0.5 = presión compradora
    dominante en esa vela. Dato crudo que ya viene en los klines de
    Binance (taker_buy_base) y que el proyecto tenía cargado pero sin
    usar — no es un indicador derivado, es volumen real de la vela.
    """
    df = df.copy()
    df["TAKER_BUY_RATIO"] = df["taker_buy_base"] / df["volume"].replace(0, pd.NA)
    return df


# ---------------------------------------------------------------------
# Calendario
# ---------------------------------------------------------------------

def add_calendar(df: pd.DataFrame) -> pd.DataFrame:
    """
    Variables de calendario puro, sin ningún indicador:

    - WEEKDAY: 0=lunes ... 6=domingo (UTC).
    - IS_MONDAY / IS_FRIDAY / IS_WEEKEND: flags de día.
    - UTC_HOUR: hora del día en UTC.
    - NY_HOUR: hora del día en America/New_York (maneja DST
      automáticamente).
    - WEEK_OF_YEAR, MONTH: para estacionalidad de más largo plazo.

    Justificación: RQ-001 (horarios con ventaja), RQ-002 (apertura NY)
    y RQ-006 (efectos de día de la semana / secuencia de sesiones,
    ej. "Monday Asia effect").
    """
    df = df.copy()
    utc_idx = df.index.tz_convert("UTC")
    ny_idx = df.index.tz_convert("America/New_York")

    df["WEEKDAY"] = utc_idx.dayofweek  # 0=lunes, 6=domingo
    df["IS_MONDAY"] = df["WEEKDAY"] == 0
    df["IS_FRIDAY"] = df["WEEKDAY"] == 4
    df["IS_WEEKEND"] = df["WEEKDAY"] >= 5
    df["UTC_HOUR"] = utc_idx.hour
    df["NY_HOUR"] = ny_idx.hour
    df["WEEK_OF_YEAR"] = utc_idx.isocalendar().week.to_numpy()
    df["MONTH"] = utc_idx.month
    return df


# ---------------------------------------------------------------------
# Sesiones (Asia / Londres / Nueva York)
# ---------------------------------------------------------------------

# ASUNCIÓN METODOLÓGICA (documentada explícitamente, como el resto de
# BRE): bandas FIJAS en UTC, sin ajuste por DST de cada plaza. Es una
# simplificación deliberada para la primera pasada de investigación.
# Si una hipótesis de sesión resulta prometedora, revisar si el
# resultado es sensible a esta simplificación antes de validarla.
SESSION_BOUNDARIES_UTC: dict[str, tuple[int, int]] = {
    "ASIA": (0, 8),  # 00:00-07:59 UTC (Tokio/Hong Kong/Singapur activos)
    "LONDON": (8, 13),  # 08:00-12:59 UTC
    "NEWYORK": (13, 21),  # 13:00-20:59 UTC (solapa con Londres 13-16)
    "OFF_HOURS": (21, 24),  # 21:00-23:59 UTC, baja liquidez
}

# Orden cronológico de sesiones dentro de un mismo día UTC. Se usa para
# construir PREV_SESSION_RET correctamente (ver add_prior_session_return).
_SESSION_ORDER = ["ASIA", "LONDON", "NEWYORK", "OFF_HOURS"]


def add_session_tag(df: pd.DataFrame) -> pd.DataFrame:
    """
    SESSION: etiqueta ASIA / LONDON / NEWYORK / OFF_HOURS según
    UTC_HOUR (requiere add_calendar() antes). Ver SESSION_BOUNDARIES_UTC
    para la definición exacta y su asunción metodológica.
    """
    df = df.copy()
    if "UTC_HOUR" not in df.columns:
        raise ValueError("Corré add_calendar() antes de add_session_tag().")

    session = pd.Series("OFF_HOURS", index=df.index, dtype="object")
    for name, (start, end) in SESSION_BOUNDARIES_UTC.items():
        mask = (df["UTC_HOUR"] >= start) & (df["UTC_HOUR"] < end)
        session[mask] = name
    df["SESSION"] = session
    return df


def add_session_relative(df: pd.DataFrame) -> pd.DataFrame:
    """
    Variables relativas a la sesión en curso (requiere add_session_tag()
    y un índice datetime UTC-aware, ordenado, sin gaps grandes sin
    documentar):

    - SESSION_ID: clave "YYYY-MM-DD_SESSION", usada para agrupar.
    - SESSION_OPEN: precio de apertura de la sesión (primer 'open' del
      bloque).
    - RET_SINCE_SESSION_OPEN: retorno del close actual vs SESSION_OPEN.
    - SESSION_HIGH_SO_FAR / SESSION_LOW_SO_FAR: máximo/mínimo
      acumulado dentro de la sesión en curso (running, sin look-ahead:
      en cada vela solo mira velas anteriores de esa misma sesión).
    """
    df = df.copy()
    if "SESSION" not in df.columns:
        raise ValueError("Corré add_session_tag() antes de add_session_relative().")

    utc_date = df.index.tz_convert("UTC").floor("D")
    df["SESSION_ID"] = utc_date.astype(str) + "_" + df["SESSION"].astype(str)

    df["SESSION_OPEN"] = df.groupby("SESSION_ID")["open"].transform("first")
    df["RET_SINCE_SESSION_OPEN"] = df["close"] / df["SESSION_OPEN"] - 1.0

    df["SESSION_HIGH_SO_FAR"] = df.groupby("SESSION_ID")["high"].cummax()
    df["SESSION_LOW_SO_FAR"] = df.groupby("SESSION_ID")["low"].cummin()
    return df


def add_prior_session_return(df: pd.DataFrame) -> pd.DataFrame:
    """
    PREV_SESSION_RET: retorno total (open->close) de la sesión
    INMEDIATAMENTE anterior — visible durante toda la sesión actual.
    PREV_SESSION_DIRECTION: signo de ese retorno (+1/-1/0).

    Ejemplo: durante toda la sesión Londres del lunes, PREV_SESSION_RET
    es el retorno completo de la sesión Asia de ese mismo lunes. Es la
    variable clave para hipótesis tipo "Monday Asia effect": ¿la
    dirección de una sesión predice la siguiente?

    Requiere add_session_relative() antes. SESSION_ID ("YYYY-MM-DD_ASIA",
    "YYYY-MM-DD_LONDON", ...) ordena correctamente en forma alfabética
    porque ASIA < LONDON < NEWYORK < OFF_HOURS coincide con el orden
    cronológico real (ver _SESSION_ORDER) — se documenta esta
    dependencia para que no se rompa silenciosamente si se agregan
    sesiones nuevas con otro nombre.
    """
    df = df.copy()
    if "SESSION_ID" not in df.columns:
        raise ValueError(
            "Corré add_session_relative() antes de add_prior_session_return()."
        )

    session_summary = df.groupby("SESSION_ID").agg(
        session_open=("open", "first"), session_close=("close", "last")
    )
    session_summary["session_ret"] = (
        session_summary["session_close"] / session_summary["session_open"] - 1.0
    )
    session_summary = session_summary.sort_index()
    session_summary["prev_session_ret"] = session_summary["session_ret"].shift(1)

    df["PREV_SESSION_RET"] = df["SESSION_ID"].map(session_summary["prev_session_ret"])

    direction = pd.Series(0.0, index=df.index)
    direction[df["PREV_SESSION_RET"] > 0] = 1.0
    direction[df["PREV_SESSION_RET"] < 0] = -1.0
    direction[df["PREV_SESSION_RET"].isna()] = float("nan")
    df["PREV_SESSION_DIRECTION"] = direction
    return df


# ---------------------------------------------------------------------
# Pipeline completo
# ---------------------------------------------------------------------

def build_features(
    df: pd.DataFrame,
    forward_periods: tuple[int, ...] = (1, 4, 8, 16),
    backward_periods: tuple[int, ...] = (1, 4, 8, 16),
) -> pd.DataFrame:
    """
    Corre todo el Feature Engine en el orden correcto sobre el Dataset
    Maestro. Pensado para no depender de recordar el orden manual en
    Colab (fuente histórica de errores en el proyecto — ver CHANGELOG).
    """
    df = add_forward_returns(df, forward_periods)
    df = add_backward_returns(df, backward_periods)
    df = add_body_ratio(df)
    df = add_candle_geometry(df)
    df = add_taker_buy_ratio(df)
    df = add_calendar(df)
    df = add_session_tag(df)
    df = add_session_relative(df)
    df = add_prior_session_return(df)
    return df
