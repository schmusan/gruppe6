"""Ingestion: stündliche Meteorologie-Daten der NOAA-GML-Observatorien.

Zweck
    Lädt pro Station und Jahr die Datei
    ``met_{site}_insitu_1_obop_hour_{year}.txt`` aus dem öffentlichen
    NOAA-GML-Archiv und legt sie unverändert in ``data/raw/noaa/{site}/`` ab.

Grain der Rohdaten
    Eine Zeile = eine Station × eine Stunde (UTC).

Eigenschaften
    * idempotent: Bereits vorhandene, vollständige Jahre werden übersprungen.
      Das laufende Jahr (noch unvollständig) wird immer neu geladen.
    * robust: Retry mit exponentiellem Backoff bei Netzwerkfehlern und 5xx.
    * nachvollziehbar: Jeder Download landet mit Zeitstempel, Grösse und
      SHA-256 in ``data/raw/noaa/_manifest.csv``. Das Download-Datum wird für
      die Zitierung verlangt (siehe NOAA-README, Abschnitt 2).

Quelle
    NOAA Global Monitoring Laboratory, Meteorology Data,
    https://gml.noaa.gov/aftp/data/meteorology/in-situ/
    Formatbeschreibung: https://gml.noaa.gov/aftp/data/meteorology/in-situ/sum/README

Aufruf
    uv run python ingest/noaa.py                  # alle Stationen, alle Jahre
    uv run python ingest/noaa.py --sites brw spo  # nur ausgewählte Stationen
    uv run python ingest/noaa.py --years 2000 2025
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import logging
import re
import sys
import time
from pathlib import Path

import requests

BASE_URL = "https://gml.noaa.gov/aftp/data/meteorology/in-situ"
SITES = ("brw", "sum", "spo")  # Utqiagvik (Alaska), Summit (Grönland), Südpol
FILE_RE = re.compile(r"met_(?P<site>[a-z]{3})_insitu_1_obop_hour_(?P<year>\d{4})\.txt")

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw" / "noaa"
MANIFEST = RAW_DIR / "_manifest.csv"
MANIFEST_FIELDS = ["site", "year", "file", "url", "bytes", "lines", "sha256", "downloaded_at_utc"]

log = logging.getLogger("ingest.noaa")


def get_with_retry(session: requests.Session, url: str, attempts: int = 4) -> requests.Response:
    """GET mit Retry. Wartet 2, 4, 8 Sekunden zwischen den Versuchen."""
    for attempt in range(1, attempts + 1):
        try:
            resp = session.get(url, timeout=60)
            if resp.status_code < 500:
                resp.raise_for_status()
                return resp
            log.warning("HTTP %s für %s (Versuch %d/%d)", resp.status_code, url, attempt, attempts)
        except requests.RequestException as exc:  # Netzwerkfehler, Timeout, 4xx
            if isinstance(exc, requests.HTTPError) and exc.response is not None and exc.response.status_code < 500:
                raise  # 404 o. ä.: kein Retry, die Datei existiert nicht
            log.warning("Fehler bei %s: %s (Versuch %d/%d)", url, exc, attempt, attempts)
        if attempt < attempts:
            time.sleep(2**attempt)
    raise RuntimeError(f"Download nach {attempts} Versuchen fehlgeschlagen: {url}")


def list_available_years(session: requests.Session, site: str) -> list[int]:
    """Liest das Verzeichnis-Listing der Station und gibt die verfügbaren Jahre zurück."""
    resp = get_with_retry(session, f"{BASE_URL}/{site}/")
    years = {int(m["year"]) for m in FILE_RE.finditer(resp.text) if m["site"] == site}
    return sorted(years)


def load_manifest() -> dict[tuple[str, int], dict]:
    if not MANIFEST.exists():
        return {}
    with MANIFEST.open(newline="") as fh:
        return {(r["site"], int(r["year"])): r for r in csv.DictReader(fh)}


def save_manifest(rows: dict[tuple[str, int], dict]) -> None:
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    with MANIFEST.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=MANIFEST_FIELDS)
        writer.writeheader()
        for key in sorted(rows):
            writer.writerow(rows[key])


def ingest(sites: list[str], year_from: int | None, year_to: int | None) -> None:
    manifest = load_manifest()
    current_year = dt.datetime.now(dt.timezone.utc).year
    session = requests.Session()
    session.headers["User-Agent"] = "ZHAW-DAENG-Gruppe6/1.0 (Studienprojekt)"

    loaded = skipped = 0
    for site in sites:
        years = list_available_years(session, site)
        years = [y for y in years if (year_from is None or y >= year_from) and (year_to is None or y <= year_to)]
        log.info("%s: %d Jahre verfügbar (%s–%s)", site.upper(), len(years), years[0] if years else "-", years[-1] if years else "-")

        for year in years:
            name = f"met_{site}_insitu_1_obop_hour_{year}.txt"
            target = RAW_DIR / site / name
            # Idempotenz: abgeschlossene Jahre, die schon im Manifest stehen und
            # deren Datei noch den gleichen Hash hat, werden nicht erneut geladen.
            entry = manifest.get((site, year))
            if year < current_year and entry and target.exists():
                if hashlib.sha256(target.read_bytes()).hexdigest() == entry["sha256"]:
                    skipped += 1
                    continue
                log.warning("%s: Hash stimmt nicht mehr, lade neu", name)

            url = f"{BASE_URL}/{site}/{name}"
            content = get_with_retry(session, url).content
            target.parent.mkdir(parents=True, exist_ok=True)
            tmp = target.with_suffix(".part")
            tmp.write_bytes(content)  # erst vollständig schreiben, dann umbenennen
            tmp.replace(target)

            manifest[(site, year)] = {
                "site": site,
                "year": year,
                "file": str(target.relative_to(ROOT)),
                "url": url,
                "bytes": len(content),
                "lines": content.count(b"\n"),
                "sha256": hashlib.sha256(content).hexdigest(),
                "downloaded_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
            }
            save_manifest(manifest)  # nach jeder Datei, damit ein Abbruch nichts verliert
            loaded += 1
            log.info("geladen: %s (%d Zeilen)", name, manifest[(site, year)]["lines"])

    log.info("fertig: %d geladen, %d übersprungen", loaded, skipped)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--sites", nargs="+", default=list(SITES), choices=SITES)
    parser.add_argument("--years", nargs=2, type=int, metavar=("VON", "BIS"))
    args = parser.parse_args(argv)

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[logging.StreamHandler(sys.stdout), logging.FileHandler(RAW_DIR / "_ingest.log")],
    )
    year_from, year_to = args.years if args.years else (None, None)
    ingest(args.sites, year_from, year_to)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
