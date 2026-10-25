\# Konzept und Daten



Autor: Basil Härri · Teil «Konzept und Daten», Kolloquium LN1, Data Engineering HS26



\## 1. Ausgangslage



Unser Projekt untersucht die Frage: Erwärmt sich die Arktis schneller als die Antarktis? Dafür analysieren wir über 1.08 Millionen Stundenmessungen von drei NOAA-Observatorien: Utqiaġvik in Alaska, Summit in Grönland und dem Südpol.



Wir erwarten Unterschiede, weil sich die geografischen Bedingungen unterscheiden: Die Arktis besteht hauptsächlich aus einem von Land umgebenen Meer, während die Antarktis ein eisbedeckter Kontinent ist. Diese unterschiedlichen Bedingungen beeinflussen die Wärmeaufnahme der beiden Polarregionen. Die Untersuchung ist relevant, weil die Temperaturentwicklung für Klimaprognosen und die Abschätzung von Meeresspiegelveränderungen wichtig ist.



\## 2. Forschungsfragen und Hypothesen



Wir untersuchen drei Forschungsfragen:



1\. Wie stark sind die Jahresmitteltemperaturen gestiegen? Unsere erste Hypothese lautet, dass Utqiaġvik einen signifikant positiven Temperaturtrend aufweist.

2\. Erwärmt sich die Arktis schneller als die Antarktis? Wir vermuten, dass der Temperaturtrend in Utqiaġvik steiler ist als am Südpol.

3\. In welcher Jahreszeit ist die Erwärmung am stärksten? Wir erwarten, dass sich der Winter in Utqiaġvik stärker erwärmt als der Sommer.



Eine Messstation repräsentiert nicht automatisch eine ganze Polarregion. Deshalb formulieren wir die zweite Hypothese konkret als Vergleich zwischen Utqiaġvik und dem Südpol. Aussagen über die gesamte Arktis oder Antarktis wären mit nur drei räumlich unterschiedlichen Stationen nicht ausreichend abgesichert.



\## 3. Vorgehen der Analyse: Monatsmittel, Jahresmittel, Anomalien



Wir wandeln die Stundenmessungen schrittweise in vergleichbare Kennzahlen um.



Warum Monatsmittel? Jeder Monat muss mindestens 80 % gültige Stunden enthalten. Anschliessend berechnen wir Jahresmittel nur aus zwölf gültigen Monatsmitteln. So vermeiden wir, dass Monate mit vielen Messungen stärker gewichtet werden als Monate mit wenigen gültigen Messungen.



Vereinfachtes Beispiel mit zwei Monaten: Der Februar hat ein Monatsmittel von −25 °C bei 50 % gültigen Stunden, der Juli eines von +5 °C bei 100 % gültigen Stunden.



\- Mittel über die gültigen Stunden: (0.5 · (−25) + 1 · 5) / 1.5 = −5 °C

\- Gleichgewichtetes Mittel der Monatsmittel: (−25 + 5) / 2 = −10 °C



Wenn im kalten Februar die Hälfte der Stunden fehlt, zählt dieser Monat beim Mittel über alle gültigen Stunden nur halb so stark wie der Juli. Das Jahresmittel verschiebt sich dadurch um 5 °C nach oben, obwohl sich das Klima nicht verändert hat. Eine Datenlücke könnte somit fälschlicherweise wie eine Erwärmung aussehen. Deshalb gewichten wir die Monatsmittel gleich und berücksichtigen nur vollständige Jahre.



Warum Anomalien? Die Anomaliebildung ist nicht notwendig, um die Steigung eines linearen Trends zu vergleichen, denn eine konstante Verschiebung der Temperaturwerte verändert die Steigung nicht. Anomalien ermöglichen jedoch, beide Stationen in einer gemeinsamen Grafik darzustellen: Der Wert null entspricht jeweils dem Mittel der Referenzperiode. Wir verwenden für alle Stationen dieselbe Referenzperiode von 2009 bis 2025, weil in diesem Zeitraum alle drei Stationen messen. Hätte jede Station eine eigene Referenzperiode, würde null unterschiedliche Klimazustände bezeichnen und die Kurven wären nicht direkt vergleichbar.



Welche statistischen Verfahren? Wir bestimmen Trends mit einer linearen Regression und geben die Steigung in °C pro Jahrzehnt an. Zusätzlich verwenden wir den Mann-Kendall-Test mit Sen-Steigung als robuste Gegenprüfung. Für den direkten Vergleich zwischen Utqiaġvik und dem Südpol berücksichtigen wir nur die 32 gemeinsamen vollständigen Jahre.



\## 4. Data Engineering Lifecycle im Projekt



Unser Lifecycle orientiert sich an Reis und Housley (2022). Das Modell umfasst fünf Phasen und sechs unterstützende Undercurrents. Vier der sechs Undercurrents setzen wir konkret um: Datenmanagement, DataOps, Software Engineering und Orchestrierung.



| Phase          | Was passiert?                                           | Umsetzung im Repository                                                                              |

| -------------- | ------------------------------------------------------- | ---------------------------------------------------------------------------------------------------- |

| Generation     | NOAA-Stationen erzeugen Messdaten.                      | Externe Quelle: NOAA GML                                                                             |

| Ingestion      | Dateien werden automatisch heruntergeladen und geprüft. | `ingest/noaa.py`                                                                                     |

| Storage        | Rohdaten und verarbeitete Daten werden gespeichert.     | `data/raw/noaa/`, `ingest/to\_parquet.py`, `data/parquet/`, Bewertung in `docs/storage\_evaluation.md` |

| Transformation | Daten werden bereinigt, aggregiert und getestet.        | `dbt/models/` (Staging und Marts), `dbt/tests/` und `.yml`-Dateien                                   |

| Serving        | Ergebnisse werden für Nutzende bereitgestellt.          | Interaktives Dashboard in Teil 2                                                                     |



Das Manifest mit Hashes und Download-Datum unterstützt das Datenmanagement. dbt-Tests sichern DataOps, Git und `uv.lock` das Software Engineering und `run\_pipeline.sh` die Orchestrierung.



Serving kommt erst in Teil 2, weil wir zuerst eine reproduzierbare und geprüfte Datenbasis schaffen wollen. Ein Dashboard wäre wenig sinnvoll, solange Bereinigung, Transformation und Datenqualität nicht zuverlässig sichergestellt sind.



\## 5. Datenquelle NOAA



Die Daten stammen vom Global Monitoring Laboratory der NOAA. Die Dateien enthalten stündliche Messungen von Utqiaġvik ab 1973, Summit ab 2008 und dem Südpol ab 1975. Sie bestehen aus 14 Feldern pro Zeile, haben keine Kopfzeile und verwenden UTC-Zeitangaben.



Fehlende Werte sind durch spezielle Codes wie `-999.9`, `-99` oder `-9` gekennzeichnet. Werden diese nicht bereinigt, könnten sie als echte Messwerte in die Mittelwerte einfliessen. Beispielsweise würde `-999.9` als extrem tiefe Temperatur interpretiert und die Analyse massiv verfälschen. Deshalb setzen wir Fehlcodes auf fehlende Werte und prüfen Temperaturen zusätzlich auf Plausibilität: Zulässig sind Werte zwischen −90 und +30 °C.



Ein wichtiger Datenqualitätsfund betrifft die Windgeschwindigkeit: In den Daten tritt `-99.9` auf, während die NOAA-Dokumentation `-999.9` nennt. Deshalb behandeln wir negative Windwerte als fehlend, statt uns blind auf die Dokumentation zu verlassen.



Die Länge der Messreihen beeinflusst zudem, welche Aussagen statistisch möglich sind. Summit hat nur 14 vollständige Jahre, weshalb ein belastbarer Vergleich des Erwärmungstrends mit dem Südpol noch nicht möglich ist. Deshalb stützt sich unsere zweite Hypothese auf den Vergleich zwischen Utqiaġvik und dem Südpol.

