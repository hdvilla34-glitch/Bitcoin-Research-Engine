"""
Data Manager
============

Responsable del Dataset Maestro (ver ARCHITECTURE.md).

Funciones:
- cargar datos (ZIPs mensuales de Binance klines -> CSV)
- validar datos (huecos, duplicados)
- limpiar datos
- exportar parquet

Formato de origen: Binance klines raw, 12 columnas, SIN encabecera,
timestamps en MICROsegundos:

    open_time, open, high, low, close, volume, close_time,
    quote_asset_volume, num_trades, taker_buy_base, taker_buy_quote, ignore
"""

from __future__ import annotations

import hashlib
import re
import zipfile
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

KLINES_COLUMNS = [
    "open_time",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "close_time",
    "quote_asset_volume",
    "num_trades",
    "taker_buy_base",
    "taker_buy_quote",
    "ignore",
]

TIMEFRAME_MINUTES = 15


@dataclass
class ValidationReport:
    """Resultado de validar el Dataset Maestro."""

    total_rows: int
    start: pd.Timestamp
    end: pd.Timestamp
    duplicated_timestamps_dropped: int
    gaps: list[tuple[pd.Timestamp, pd.Timestamp]] = field(default_factory=list)

    def summary(self) -> str:
        lines = [
            f"Filas totales: {self.total_rows}",
            f"Rango: {self.start} -> {self.end}",
            f"Timestamps duplicados eliminados: {self.duplicated_timestamps_dropped}",
            f"Huecos detectados: {len(self.gaps)}",
        ]
        for gap_start, gap_end in self.gaps:
            lines.append(f"  - hueco entre {gap_start} y {gap_end}")
        return "\n".join(lines)


def _canonical_name(path: Path) -> str:
    """
    Normaliza nombres tipo 'BTCUSDT-15m-2026-04 (1).zip' o
    'BTCUSDT-15m-2025-09(1).zip' a 'BTCUSDT-15m-2026-04' para
    poder deduplicar copias de Drive.
    """
    stem = path.stem
    stem = re.sub(r"\s*\(\d+\)\s*$", "", stem)
    return stem


def _file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def discover_month_files(raw_folder: Path) -> list[Path]:
    """
    Recorre la carpeta de ZIPs mensuales y devuelve una lista deduplicada
    (por nombre canónico + hash de contenido) de archivos a procesar.
    Si hay copias con el mismo nombre canónico pero contenido distinto,
    se conserva la más reciente por mtime y se avisa por stdout.
    """
    all_zips = sorted(raw_folder.glob("*.zip"))
    by_canonical: dict[str, list[Path]] = {}
    for p in all_zips:
        by_canonical.setdefault(_canonical_name(p), []).append(p)

    chosen: list[Path] = []
    for canonical, paths in by_canonical.items():
        if len(paths) == 1:
            chosen.append(paths[0])
            continue

        hashes = {_file_hash(p) for p in paths}
        if len(hashes) == 1:
            # copias idénticas -> nos quedamos con cualquiera
            chosen.append(paths[0])
        else:
            # contenido distinto bajo el mismo mes -> nos quedamos con la
            # más reciente y avisamos, para que el usuario revise
            newest = max(paths, key=lambda p: p.stat().st_mtime)
            print(
                f"[data_manager] AVISO: '{canonical}' tiene copias con "
                f"contenido DISTINTO. Se usó la más reciente: {newest.name}. "
                f"Revisa manualmente: {[p.name for p in paths]}"
            )
            chosen.append(newest)

    return sorted(chosen)


def _load_single_month_zip(zip_path: Path) -> pd.DataFrame:
    with zipfile.ZipFile(zip_path) as zf:
        csv_names = [n for n in zf.namelist() if n.lower().endswith(".csv")]
        if len(csv_names) != 1:
            raise ValueError(
                f"Se esperaba exactamente 1 CSV dentro de {zip_path.name}, "
                f"se encontraron {len(csv_names)}: {csv_names}"
            )
        with zf.open(csv_names[0]) as f:
            df = pd.read_csv(f, header=None, names=KLINES_COLUMNS)
    return df


def load_raw_folder(raw_folder: str | Path) -> pd.DataFrame:
    """
    Carga todos los ZIPs mensuales de una carpeta, deduplica, concatena
    y devuelve un DataFrame ordenado por tiempo con índice datetime UTC.
    """
    raw_folder = Path(raw_folder)
    month_files = discover_month_files(raw_folder)
    if not month_files:
        raise FileNotFoundError(f"No se encontraron .zip en {raw_folder}")

    frames = [_load_single_month_zip(p) for p in month_files]
    df = pd.concat(frames, ignore_index=True)

    # timestamps vienen en microsegundos
    df["open_time"] = pd.to_datetime(df["open_time"], unit="us", utc=True)
    df["close_time"] = pd.to_datetime(df["close_time"], unit="us", utc=True)

    df = df.set_index("open_time").sort_index()
    return df


def clean_dataset(df: pd.DataFrame) -> tuple[pd.DataFrame, ValidationReport]:
    """
    Elimina timestamps duplicados y detecta huecos en la serie de 15m.
    Devuelve el dataframe limpio + un reporte de validación.
    """
    before = len(df)
    df = df[~df.index.duplicated(keep="first")]
    dup_dropped = before - len(df)

    expected_delta = pd.Timedelta(minutes=TIMEFRAME_MINUTES)
    deltas = df.index.to_series().diff()
    gap_mask = deltas > expected_delta
    gaps = [
        (df.index[i - 1], df.index[i])
        for i in range(1, len(df))
        if gap_mask.iloc[i]
    ]

    report = ValidationReport(
        total_rows=len(df),
        start=df.index.min(),
        end=df.index.max(),
        duplicated_timestamps_dropped=dup_dropped,
        gaps=gaps,
    )
    return df, report


def build_master_dataset(raw_folder: str | Path) -> tuple[pd.DataFrame, ValidationReport]:
    """Pipeline completo: ZIPs -> DataFrame limpio + reporte."""
    df = load_raw_folder(raw_folder)
    df, report = clean_dataset(df)
    return df, report


def export_parquet(df: pd.DataFrame, out_path: str | Path) -> None:
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out_path)
