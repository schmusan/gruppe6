# Polar-Wetter: Erwärmt sich die Arktis schneller als die Antarktis?

Projektarbeit Data Engineering HS26, ZHAW SML, **Gruppe 6**: Basil Härri, Sandro Schmuki, Kanita Willner.

Wir vergleichen die Temperaturentwicklung an drei Observatorien der NOAA. Utqiaġvik (Alaska) und Summit (Grönland) liegen in der Arktis, der Südpol in der Antarktis. Grundlage sind stündliche Messwerte seit den 1970er-Jahren.

## Abgabe Projektarbeit Teil 1 (LN1)

Abgegeben wird der Branch [`abgabe`](https://github.com/schmusan/gruppe6/tree/abgabe). Er bleibt nach dem 27.10.2026 unverändert, weitergearbeitet wird auf `main`.

| Bestandteil | Ort |
| --- | --- |
| Kommentierter Code | `ingest/` (Ingestion, Parquet, Benchmark), `dbt/` (Transformation und Tests), `notebooks/02_trends_hypothesen.py` (Analyse) |
| Daten | `data/raw/noaa/` (124 NOAA-Rohdateien, 73 MB, mit Manifest), `data/parquet/` (Parquet pro Station) |
| Präsentation | `praesentation/` (Folien als PDF und PPTX) |
| Storage-Evaluation | `docs/storage_evaluation.md` |

Die Rohdaten sind öffentlich: NOAA Global Monitoring Laboratory, Meteorologie-Messungen der Observatorien Utqiaġvik (BRW), Summit (SUM) und Südpol (SPO), heruntergeladen am 23.10.2026 von https://gml.noaa.gov/aftp/data/meteorology/in-situ/.

## Einsatz von KI

Für Inhalt und Gestaltung haben wir Claude Opus 5.5 (Anthropic) verwendet.

## Schnellstart

Voraussetzung: [uv](https://docs.astral.sh/uv/) ist installiert.

```bash
uv sync               # Python und alle Pakete aus uv.lock installieren
./run_pipeline.sh     # Ingestion -> Parquet -> dbt build (Modelle + Tests)
uv run marimo edit notebooks/02_trends_hypothesen.py   # Analyse öffnen
```

Die Parquet-Dateien liegen im Repo. Wer nur die Transformation braucht, kann direkt `uv run --directory dbt dbt build --profiles-dir .` ausführen, ohne die Rohdaten neu zu laden.

## Lebenszyklus und Code

| Phase | Was | Wo |
| --- | --- | --- |
| Generation | Stündliche Messungen der NOAA-Observatorien BRW, SUM, SPO | NOAA GML |
| Ingestion | Download pro Station und Jahr, idempotent, Retry, Manifest mit SHA-256 und Download-Datum | `ingest/noaa.py` |
| Storage | Rohtext unverändert, dazu Parquet (zstd, partitioniert nach Station), Analyse in DuckDB | `ingest/to_parquet.py`, `docs/storage_evaluation.md` |
| Transformation | Fehlcodes → NULL, Plausibilität, Duplikate, Datenabdeckung, Monats-, Jahres- und Saisonmittel, Anomalien, 19 dbt-Tests | `dbt/models/` |
| Analyse | Trends und Hypothesentests H1–H3 | `notebooks/02_trends_hypothesen.py` |
| Serving | Teil 2: interaktives Dashboard mit Trends pro Station und Jahreszeit | folgt |

```
data/raw/noaa/{site}/      NOAA-Rohtext (versioniert, ca. 73 MB), Manifest in data/raw/noaa/_manifest.csv
data/parquet/noaa_hourly/  Parquet pro Station (versioniert, ca. 7 MB)
polar.duckdb               DuckDB-Datenbank, wird von dbt erzeugt (nicht versioniert)
  raw.stations             Seed: Stammdaten der Stationen
  staging.stg_noaa_hourly  bereinigte Stundenwerte, Grain Station × Stunde
  marts.mart_monthly_temp  Monatsmittel + Datenabdeckung
  marts.mart_annual_temp   Jahresmittel + Anomalie
  marts.mart_seasonal_temp Saisonmittel, nach Hemisphäre benannt
```

## Datenentscheidungen

- **Fehlcodes:** Jedes NOAA-Feld hat einen eigenen Code für fehlende Werte (-999, -999.9, -9, -999.90, -99). In den Daten steht bei der Windgeschwindigkeit zusätzlich -99.9, obwohl das README -999.9 nennt. Wir behandeln darum jeden negativen Wind als fehlend.
- **Plausibilität:** Temperaturen ausserhalb von -90 bis +30 °C, Feuchte ausserhalb 0–100 % und Windrichtungen ausserhalb 0–360° werden NULL. In den aktuellen Daten betraf das keine Temperatur.
- **Datenabdeckung:** Ein Monat zählt nur mit mindestens 80 % gültigen Stunden, ein Jahr nur mit 12 gültigen Monaten. So verzerren lückenhafte Monate die Mittelwerte nicht. Die Schwelle ist in `dbt/dbt_project.yml` einstellbar (`min_month_coverage`).
- **Jahresmittel:** Mittel der 12 Monatsmittel, damit jeder Monat gleich zählt.
- **Referenzperiode für Anomalien:** 2009–2025, der gemeinsame Zeitraum aller drei Stationen.
- **Jahreszeiten:** meteorologisch (Dez–Feb, Mär–Mai, Jun–Aug, Sep–Nov). Am Südpol ist Dez–Feb Sommer, das Modell benennt die Saisons nach Hemisphäre.
- **Zeit:** alle Zeitstempel in UTC, wie geliefert.

## Abdeckung (Stand Download 23.10.2026)

| Station | Dateien | vollständige Jahre | erstes / letztes vollständiges Jahr | Mittel |
| --- | --- | --- | --- | --- |
| BRW Utqiaġvik | 1973–2026 | 34 | 1978 / 2025 | -10.9 °C |
| SPO Südpol | 1975–2026 (1976 fehlt) | 43 | 1978 / 2025 | -48.8 °C |
| SUM Summit | 2008–2026 | 14 | 2009 / 2024 | -28.5 °C |

## Erste Ergebnisse (Transformation Teil 1)

| Hypothese | Ergebnis |
| --- | --- |
| H1: positiver Trend in Utqiaġvik | bestätigt: +0.95 °C pro Jahrzehnt, p < 0.001 (Mann-Kendall p < 0.001) |
| H2: Arktis erwärmt sich schneller als der Südpol | bestätigt für BRW: Steigung um 0.67 °C pro Jahrzehnt höher, p = 0.001. Für SUM noch nicht signifikant, die Reihe ist zu kurz. |
| H3: Winter in Utqiaġvik erwärmt sich stärker als der Sommer | bestätigt: +0.49 °C pro Jahrzehnt Differenz, p = 0.044. Am stärksten erwärmt sich aber der Herbst mit +1.60 °C pro Jahrzehnt. |

Der Südpol zeigt +0.24 °C pro Jahrzehnt (OLS p = 0.045). Der robuste Mann-Kendall-Test ist mit p = 0.079 aber nicht signifikant.

**Limitationen:** drei Punktstationen, unterschiedliche Lagen (Küste gegenüber Eisschild), Lücken in Utqiaġvik, Autokorrelation der Jahre (die OLS-p-Werte sind eher zu optimistisch), keine Korrektur möglicher Instrumentenwechsel.

## Zitierung der Daten

> This research utilizes 2 m temperature meteorological data collected by NOAA GML at the observatories in Utqiaġvik/Barrow (BRW), Summit (SUM) and South Pole (SPO), covering the period from 1973-01-01 to 2026-10, downloaded on 2026-10-23. Source: NOAA GML Meteorology Data, https://gml.noaa.gov/aftp/data/meteorology/in-situ/

Das genaue Download-Datum jeder Datei steht in `data/raw/noaa/_manifest.csv`.

## Zusammenarbeit

- Jede Person arbeitet auf einem eigenen Branch und merged nach `main`.
- Vor jedem Push: `./run_pipeline.sh` muss grün durchlaufen.
- Abgabe: `main` wird in den Abgabe-Branch übernommen (LN1: 27.10.2026, 23:59).
