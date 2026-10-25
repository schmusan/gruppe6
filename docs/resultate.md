# Resultate und Interpretation



*Kanita Willner Â· DatenqualitÃ¤t und Resultate*



## Datenbereinigung



Ohne die Bereinigung wÃ¼rden Fehlcodes wie âˆ’999.9 Â°C als echte

Temperaturen zÃ¤hlen und die Mittelwerte verzerren. Insgesamt wurden

66'256 Temperaturstunden leer gesetzt, davon fast 44'000 in UtqiaÄ¡vik.



Beim Wind steht in der NOAA-Dokumentation âˆ’999.9 als Fehlcode, in den

Daten aber âˆ’99.9. Wir behandeln deshalb jeden negativen Wind als

fehlend und verlassen uns nicht blind auf die Dokumentation.



Die DuplikatsprÃ¼fung fand null Treffer; das zeigt, dass die

NOAA-Daten an dieser Stelle sauber sind.



## Temperaturtrends (H1, H2)



UtqiaÄ¡vik erwÃ¤rmt sich um +0.95 Â°C pro Jahrzehnt (p < 0.001), damit

ist H1 bestÃ¤tigt.



Die +0.67 bedeuten, dass sich UtqiaÄ¡vik pro Jahrzehnt um 0.67 Â°C

schneller erwÃ¤rmt als der SÃ¼dpol (p = 0.001). Damit ist H2 fÃ¼r

UtqiaÄ¡vik bestÃ¤tigt.



Der Trend am SÃ¼dpol ist klein (+0.24 Â°C pro Jahrzehnt) und die Jahre

schwanken stark, deshalb ist er nur knapp signifikant. Die Regression

sagt p = 0.045, der robustere Mann-Kendall-Test aber p = 0.079, das

heisst, der strengere Test kann den Trend nicht bestÃ¤tigen. Weil sich

die beiden Tests widersprechen, sprechen wir am SÃ¼dpol nur von einem

schwachen Trend.



Summit zeigt sogar +1.13 Â°C pro Jahrzehnt, aber mit nur 14 vollen

Jahren ist das Ergebnis statistisch noch nicht belastbar.



## Saisonale Trends (H3)



In UtqiaÄ¡vik erwÃ¤rmen sich alle vier Jahreszeiten. Der Winter steigt

um 0.49 Â°C pro Jahrzehnt stÃ¤rker als der Sommer (p = 0.044), damit

ist H3 bestÃ¤tigt. Ãœberrascht hat uns der Herbst: Er steigt mit

+1.60 Â°C pro Jahrzehnt am stÃ¤rksten. Am SÃ¼dpol ist kein Saisontrend

robust.



### Warum erwÃ¤rmt sich der Herbst am stÃ¤rksten?



Im Sommer schmilzt mehr Meereis, und das offene, dunkle Wasser

speichert die SonnenwÃ¤rme. Dadurch friert das Nordpolarmeer im Herbst

spÃ¤ter zu. Solange das Wasser offen ist, gibt es die gespeicherte

WÃ¤rme an die Luft ab â€“ das erwÃ¤rmt den Herbst.



Beleg: Screen, J. A., \& Simmonds, I. (2010). Increasing fall-winter

energy loss from the Arctic Ocean and its role in Arctic temperature

amplification. *Geophysical Research Letters, 37*, L16707.

https://doi.org/10.1029/2010GL044136



## Beantwortung der Forschungsfragen



FF1: Die Jahresmittel sind gestiegen â€“ UtqiaÄ¡vik +0.95 Â°C pro

Jahrzehnt, SÃ¼dpol +0.24, Summit +1.13 (Reihe noch zu kurz).



FF2: Ja, die Arktis erwÃ¤rmt sich schneller: UtqiaÄ¡vik steigt 0.67 Â°C

pro Jahrzehnt schneller als der SÃ¼dpol (p = 0.001); fÃ¼r Summit ist

die Frage noch offen.



FF3: Am stÃ¤rksten erwÃ¤rmt sich der Herbst; der Winter steigt stÃ¤rker

als der Sommer (p = 0.044).



Fazit: Die Arktis erwÃ¤rmt sich deutlich schneller als der SÃ¼dpol,

belegt fÃ¼r UtqiaÄ¡vik.



## Limitationen



Drei Punktstationen in unterschiedlicher Lage stehen nicht fÃ¼r ganze

Pole, deshalb gilt unser Fazit streng genommen nur fÃ¼r UtqiaÄ¡vik.

LÃ¼cken in UtqiaÄ¡vik verkleinern die Stichprobe. Aufeinanderfolgende

Jahre hÃ¤ngen zusammen; weil die Regression aber unabhÃ¤ngige Jahre

annimmt, sind die p-Werte eher zu optimistisch. Instrumentenwechsel

haben wir nicht korrigiert, deshalb kÃ¶nnten SprÃ¼nge in der Messreihe

wie Klimatrends aussehen.


