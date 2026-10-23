"""Storage-Evaluation: misst dieselbe Abfrage auf Rohtext und auf Parquet.

Zweck
    Liefert belastbare Zahlen für den Storage-Entscheid (Folie Storage):
    Dateigrösse und Abfragezeit von DuckDB auf den NOAA-Rohdateien (Text)
    gegenüber den konvertierten Parquet-Dateien.

Abfrage
    Jahresmittel der 2-m-Temperatur pro Station, Fehlcode -999.9 ausgeschlossen.
    Jede Variante läuft 5-mal, berichtet wird der Median.

Aufruf
    uv run python ingest/benchmark_storage.py
"""

from __future__ import annotations

import statistics
import time
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
RAW_GLOB = str(ROOT / "data/raw/noaa/*/met_*_hour_*.txt")
PARQUET_GLOB = str(ROOT / "data/parquet/noaa_hourly/*/data.parquet")

QUERY_PARQUET = f"""
select site_code as site, year, avg(temp_2m_c) as t2m
from read_parquet('{PARQUET_GLOB}')
where temp_2m_c > -999
group by all
"""


def size_mb(pattern: str) -> float:
    return sum(p.stat().st_size for p in ROOT.glob(pattern)) / 1e6


def bench(con: duckdb.DuckDBPyConnection, sql: str, runs: int = 5) -> tuple[float, int]:
    times, rows = [], 0
    for _ in range(runs):
        t0 = time.perf_counter()
        rows = len(con.sql(sql).fetchall())
        times.append(time.perf_counter() - t0)
    return statistics.median(times), rows


def main() -> int:
    con = duckdb.connect()
    # Der Rohtext ist mit mehreren Leerzeichen ausgerichtet; DuckDB braucht dafür
    # eine Vorverarbeitung. Wir normalisieren deshalb in einer Ansicht.
    txt_sql = f"""
    with lines as (
        select string_split(regexp_replace(trim(column0), ' +', ' ', 'g'), ' ') as f
        from read_csv('{RAW_GLOB}', delim='\\x01', header=false, columns={{'column0':'VARCHAR'}})
    )
    select f[1] as site, cast(f[2] as int) as year, avg(cast(f[10] as double)) as t2m
    from lines where cast(f[10] as double) > -999
    group by all
    """
    t_txt, n_txt = bench(con, txt_sql)
    t_pq, n_pq = bench(con, QUERY_PARQUET)
    print(f"Rohtext : {size_mb('data/raw/noaa/*/*.txt'):6.1f} MB, Abfrage {t_txt * 1000:7.0f} ms, {n_txt} Ergebniszeilen")
    print(f"Parquet : {size_mb('data/parquet/noaa_hourly/*/*.parquet'):6.1f} MB, Abfrage {t_pq * 1000:7.0f} ms, {n_pq} Ergebniszeilen")
    print(f"Faktor  : {size_mb('data/raw/noaa/*/*.txt') / size_mb('data/parquet/noaa_hourly/*/*.parquet'):.1f}x kleiner, {t_txt / t_pq:.1f}x schneller")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
