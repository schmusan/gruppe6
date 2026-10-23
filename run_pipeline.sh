#!/usr/bin/env bash
# Führt die ganze Pipeline aus: Ingestion -> Parquet -> dbt (Modelle + Tests).
# Aufruf aus dem Repo-Root:  ./run_pipeline.sh
# Bricht beim ersten Fehler ab (set -e), damit kein Schritt auf alten Daten läuft.
set -euo pipefail
cd "$(dirname "$0")"

echo "== 1/3 Ingestion: NOAA-Rohdaten laden (idempotent)"
uv run python ingest/noaa.py

echo "== 2/3 Storage: Rohtext nach Parquet"
uv run python ingest/to_parquet.py

echo "== 3/3 Transformation: dbt build (Modelle + Tests)"
uv run --directory dbt dbt build --profiles-dir .

echo "Fertig. Analyse öffnen mit: uv run marimo edit notebooks/02_trends_hypothesen.py"
