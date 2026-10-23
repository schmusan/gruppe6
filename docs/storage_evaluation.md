# Storage-Evaluation

**Entscheid:** Die Rohdaten bleiben als Original-Textdateien erhalten und werden zusätzlich nach Parquet konvertiert, partitioniert nach Station. Abgefragt und transformiert wird mit DuckDB, die Modelle baut dbt.

## Gemessen auf unseren Daten

Gemessen mit `ingest/benchmark_storage.py`. Die Abfrage berechnet das Jahresmittel der 2-m-Temperatur pro Station über alle 1.08 Mio. Stundenzeilen, als Median aus 5 Läufen.

| Format | Grösse | Abfragezeit mit DuckDB |
| --- | --- | --- |
| NOAA-Rohtext (124 Dateien) | 75.3 MB | 1'540 ms |
| Parquet, zstd, nach Station partitioniert | 6.7 MB | 16 ms |
| **Faktor** | **11× kleiner** | **96× schneller** |

Die Werte stammen aus dem Lauf vom 23.10.2026 im Cloud-Arbeitsbereich und schwanken je nach Rechner. Das Verhältnis bleibt aber ähnlich.

## Vergleich der Optionen

| Kriterium | Textdateien | DuckDB + Parquet | PostgreSQL | TimescaleDB | MongoDB |
| --- | --- | --- | --- | --- | --- |
| Abfragetempo für Aggregationen | langsam, jedes Mal parsen | sehr schnell, spaltenbasiert | gut | sehr gut für Zeitreihen | mittel |
| Betriebsaufwand | keiner | keiner, kein Server | Server bzw. Docker | Server bzw. Docker | Server bzw. Docker |
| Passt zur Datenstruktur | ja, aber kein Schema | ja, tabellarisch mit Typen | ja | ja, Zeitreihen | schlecht, die Daten sind streng tabellarisch |
| Skalierbarkeit | schlecht | gut bis in den zweistelligen GB-Bereich auf einem Laptop, Partitionen pro Station | gut | sehr gut | gut |
| Zusammenarbeit im Team | Dateien versionierbar | Parquet-Dateien versionierbar, die DB wird neu gebaut | gemeinsamer Server nötig | gemeinsamer Server nötig | gemeinsamer Server nötig |
| Kosten | keine | keine | keine bei Eigenbetrieb | keine bei Eigenbetrieb | keine bei Eigenbetrieb |

## Begründung

- **Datenmenge:** Rund 1 Mio. Zeilen. Eine Server-Datenbank wäre zusätzlicher Betriebsaufwand ohne Nutzen.
- **Zugriffsmuster:** Wir aggregieren über Stunden zu Monaten und Jahren. Spaltenbasierte Formate lesen dafür nur die benötigten Spalten.
- **Skalierbarkeit:** NOAA bietet auch Minutenwerte, das wären etwa 60-mal mehr Zeilen. Dazu kommen weitere Stationen (AMRDC, Svalbard). Jede neue Station ist eine neue Partition, bestehende Dateien bleiben unverändert. Erst bei einem Vielfachen davon oder bei vielen gleichzeitigen Nutzenden wäre ein Server (TimescaleDB) oder ein Objektspeicher mit Abfrage-Engine sinnvoll.
- **Reproduzierbarkeit:** `polar.duckdb` wird von `dbt build` jederzeit aus den Parquet-Dateien neu erzeugt. Darum wird nur Parquet versioniert, nicht die Datenbank.
