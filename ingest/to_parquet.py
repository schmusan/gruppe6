"""Storage, Schritt 1: Rohtext der NOAA nach Parquet konvertieren.

Zweck
    Liest alle Dateien aus ``data/raw/noaa/{site}/`` und schreibt pro Station
    eine Parquet-Datei nach ``data/parquet/noaa_hourly/site={site}/``.
    Die Werte bleiben unverändert (auch die Fehlcodes wie -999.9). Bereinigt
    wird erst in dbt (staging), damit die Rohdaten jederzeit nachvollziehbar
    bleiben.

Grain
    Eine Zeile = eine Station × eine Stunde (UTC), wie in der Quelle.

Warum Parquet?
    Spaltenbasiert und komprimiert: deutlich kleiner als der Rohtext, und
    DuckDB liest nur die Spalten, die eine Abfrage braucht. Die
    Partitionierung nach Station erlaubt, weitere Stationen hinzuzufügen,
    ohne bestehende Dateien anzufassen (Skalierbarkeit).

Aufruf
    uv run python ingest/to_parquet.py
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw" / "noaa"
OUT_DIR = ROOT / "data" / "parquet" / "noaa_hourly"

# Feldreihenfolge laut NOAA-README, Abschnitt 5.3 (Felder 1–14)
COLUMNS = [
    "site_code", "year", "month", "day", "hour",
    "wind_dir_deg", "wind_speed_ms", "wind_steadiness",
    "pressure_hpa", "temp_2m_c", "temp_10m_c", "temp_top_c",
    "rel_humidity_pct", "precip_mm_h",
]
DTYPES = {
    "site_code": "string", "year": "int16", "month": "int8", "day": "int8", "hour": "int8",
    "wind_dir_deg": "int16", "wind_speed_ms": "float32", "wind_steadiness": "int16",
    "pressure_hpa": "float32", "temp_2m_c": "float32", "temp_10m_c": "float32",
    "temp_top_c": "float32", "rel_humidity_pct": "int16", "precip_mm_h": "int16",
}


def convert_site(site_dir: Path) -> pd.DataFrame:
    frames = []
    for path in sorted(site_dir.glob("met_*_hour_*.txt")):
        df = pd.read_csv(path, sep=r"\s+", header=None, names=COLUMNS, dtype=DTYPES, engine="c")
        # Lineage: Herkunftsdatei pro Zeile. Download-Datum und Hash stehen im
        # Manifest (data/raw/noaa/_manifest.csv), nicht hier: So bleibt die
        # Parquet-Datei bei unveränderten Daten byte-gleich, auch nach einem
        # erneuten Download, und erzeugt in git keine unnötigen Änderungen.
        df["source_file"] = path.name
        frames.append(df)
    return pd.concat(frames, ignore_index=True)


def main() -> int:
    for site_dir in sorted(p for p in RAW_DIR.iterdir() if p.is_dir()):
        df = convert_site(site_dir)
        target = OUT_DIR / f"site={site_dir.name}" / "data.parquet"
        target.parent.mkdir(parents=True, exist_ok=True)
        df.to_parquet(target, index=False, compression="zstd")
        print(f"{site_dir.name}: {len(df):>9,} Zeilen -> {target.relative_to(ROOT)} ({target.stat().st_size / 1e6:.1f} MB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
