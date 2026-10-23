"""Trends und Hypothesentests H1–H3 (Transformation Teil 1, erste Auswertung).

Öffnen:   uv run marimo edit notebooks/02_trends_hypothesen.py
Als App:  uv run marimo run notebooks/02_trends_hypothesen.py

Voraussetzung: `uv run --directory dbt dbt build --profiles-dir .` ist gelaufen,
damit `polar.duckdb` die Marts enthält.
"""

import marimo

__generated_with = "0.25.2"
app = marimo.App(width="medium")


@app.cell
def _():
    import duckdb
    import marimo as mo
    import matplotlib.pyplot as plt
    import pandas as pd
    import pymannkendall as mk
    import statsmodels.formula.api as smf
    from pathlib import Path

    return Path, duckdb, mk, mo, pd, plt, smf


@app.cell
def _(mo):
    mo.md("""
    # Erwärmt sich die Arktis schneller als die Antarktis?

    Datengrundlage: stündliche 2-m-Temperatur der NOAA-Observatorien
    **Utqiaġvik (BRW)**, **Summit (SUM)** und **Südpol (SPO)**, bereinigt und
    aggregiert in dbt (`marts.mart_annual_temp`, `marts.mart_seasonal_temp`).

    Ein Jahr zählt nur, wenn alle 12 Monate mindestens 80 % gültige Stunden
    haben. Trends werden in °C pro Jahrzehnt angegeben, Signifikanzniveau 5 %.
    """)
    return


@app.cell
def _(Path, duckdb, mo):
    # Datenbank liegt im Repo-Root, unabhängig davon, von wo das Notebook startet.
    db_path = Path(mo.notebook_dir()).parent / "polar.duckdb"
    con = duckdb.connect(str(db_path), read_only=True)

    annual = con.sql(
        "select site_code, year, n_valid_months, is_complete, t2m_annual_c, t2m_anomaly_c "
        "from marts.mart_annual_temp order by site_code, year"
    ).df()
    seasonal = con.sql(
        "select site_code, season_year, season_name, t2m_season_c "
        "from marts.mart_seasonal_temp where is_complete"
    ).df()
    complete = annual[annual.is_complete].copy()
    return annual, complete, seasonal


@app.cell
def _(annual, mo, plt):
    # Datenabdeckung: Wie viele gültige Monate hat jede Station pro Jahr?
    _fig, _ax = plt.subplots(figsize=(10, 2.6))
    _sites = ["BRW", "SUM", "SPO"]
    for _i, _site in enumerate(_sites):
        _g = annual[annual.site_code == _site]
        _ax.scatter(
            _g.year, [_i] * len(_g), c=_g.n_valid_months, cmap="Blues",
            vmin=0, vmax=12, marker="s", s=60, edgecolors="none",
        )
    _ax.set_yticks(range(len(_sites)), _sites)
    _ax.set_title("Gültige Monate pro Jahr (dunkel = 12, vollständig)")
    _ax.spines[["top", "right"]].set_visible(False)
    _fig.tight_layout()
    mo.vstack([mo.md("## Datenabdeckung"), _fig])
    return


@app.cell
def _(complete, mo, plt, smf):
    # Zeitreihe der Anomalien mit linearem Trend pro Station
    _fig, _ax = plt.subplots(figsize=(10, 4))
    _colors = {"BRW": "#1f77b4", "SUM": "#2ca02c", "SPO": "#d62728"}
    for _site, _g in complete.groupby("site_code"):
        _m = smf.ols("t2m_anomaly_c ~ year", _g).fit()
        _ax.plot(_g.year, _g.t2m_anomaly_c, "o", ms=4, color=_colors[_site], alpha=0.6)
        _ax.plot(
            _g.year, _m.predict(_g), color=_colors[_site],
            label=f"{_site}: {_m.params['year'] * 10:+.2f} °C pro Jahrzehnt",
        )
    _ax.axhline(0, color="grey", lw=0.8)
    _ax.set_ylabel("Anomalie zur Referenz 2009–2025 (°C)")
    _ax.legend(frameon=False)
    _ax.spines[["top", "right"]].set_visible(False)
    _fig.tight_layout()
    mo.vstack([mo.md("## Jahresmittel als Anomalie"), _fig])
    return


@app.cell
def _(complete, mk, mo, pd, smf):
    # H1 / FF1: Trend pro Station, parametrisch (OLS) und robust (Mann-Kendall, Sen)
    _rows = []
    for _site, _g in complete.groupby("site_code"):
        _g = _g.sort_values("year")
        _ols = smf.ols("t2m_annual_c ~ year", _g).fit()
        _mk = mk.original_test(_g.t2m_annual_c)
        _rows.append({
            "Station": _site,
            "Jahre (vollständig)": len(_g),
            "Zeitraum": f"{_g.year.min()}–{_g.year.max()}",
            "OLS °C/Jz": round(_ols.params["year"] * 10, 2),
            "OLS p": round(_ols.pvalues["year"], 4),
            "Sen °C/Jz": round(_mk.slope * 10, 2),
            "Mann-Kendall p": round(_mk.p, 4),
        })
    h1 = pd.DataFrame(_rows)
    mo.vstack([
        mo.md("## H1: Positiver Trend in Utqiaġvik\nTrend der Jahresmittel pro Station."),
        mo.ui.table(h1, selection=None),
    ])
    return


@app.cell
def _(complete, mo, smf):
    # H2: Ist der Trend in der Arktis steiler als am Südpol?
    # Modell auf Anomalien: anomaly ~ year * arctic. Der Interaktionsterm
    # year:arctic ist die Differenz der Steigungen. Nur gemeinsame Jahre.
    def compare(arctic_site: str):
        _d = complete[complete.site_code.isin([arctic_site, "SPO"])]
        _years = set(_d[_d.site_code == arctic_site].year) & set(_d[_d.site_code == "SPO"].year)
        _d = _d[_d.year.isin(_years)].assign(arctic=lambda x: (x.site_code == arctic_site).astype(int))
        _m = smf.ols("t2m_anomaly_c ~ year * arctic", _d).fit()
        return len(_years), _m.params["year:arctic"] * 10, _m.pvalues["year:arctic"]

    _n1, _diff1, _p1 = compare("BRW")
    _n2, _diff2, _p2 = compare("SUM")
    mo.md(
        f"""
        ## H2: Die Arktis erwärmt sich schneller als der Südpol

        | Vergleich | gemeinsame Jahre | Differenz der Steigung | p-Wert |
        | --- | --- | --- | --- |
        | BRW gegen SPO | {_n1} | {_diff1:+.2f} °C pro Jahrzehnt | {_p1:.4f} |
        | SUM gegen SPO | {_n2} | {_diff2:+.2f} °C pro Jahrzehnt | {_p2:.4f} |

        Summit misst erst seit 2008, darum ist der zweite Vergleich deutlich
        unsicherer.
        """
    )
    return


@app.cell
def _(mo, pd, plt, seasonal, smf):
    # H3: Saisontrends. Jahreszeiten sind nach Hemisphäre benannt
    # (am Südpol ist Dez–Feb Sommer).
    _rows = []
    for (_site, _season), _g in seasonal.groupby(["site_code", "season_name"]):
        _m = smf.ols("t2m_season_c ~ season_year", _g).fit()
        _rows.append({"Station": _site, "Saison": _season, "n": len(_g),
                      "°C/Jz": round(_m.params["season_year"] * 10, 2),
                      "p": round(_m.pvalues["season_year"], 4)})
    h3 = pd.DataFrame(_rows)

    _b = seasonal[(seasonal.site_code == "BRW") & seasonal.season_name.isin(["Winter", "Sommer"])]
    _b = _b.assign(winter=lambda x: (x.season_name == "Winter").astype(int))
    _m3 = smf.ols("t2m_season_c ~ season_year * winter", _b).fit()

    _order = ["Winter", "Frühling", "Sommer", "Herbst"]
    _fig, _ax = plt.subplots(figsize=(8, 3.2))
    _pivot = h3.pivot(index="Saison", columns="Station", values="°C/Jz").reindex(_order)
    _pivot[["BRW", "SPO"]].plot.bar(ax=_ax, rot=0, color=["#1f77b4", "#d62728"])
    _ax.axhline(0, color="grey", lw=0.8)
    _ax.set_ylabel("Trend (°C pro Jahrzehnt)")
    _ax.set_xlabel("")
    _ax.legend(frameon=False)
    _ax.spines[["top", "right"]].set_visible(False)
    _fig.tight_layout()

    mo.vstack([
        mo.md(
            "## H3: In Utqiaġvik erwärmt sich der Winter stärker als der Sommer\n"
            f"Differenz Winter minus Sommer: **{_m3.params['season_year:winter'] * 10:+.2f} °C pro Jahrzehnt**, "
            f"p = {_m3.pvalues['season_year:winter']:.4f}."
        ),
        _fig,
        mo.ui.table(h3, selection=None),
    ])
    return


@app.cell
def _(mo):
    mo.md("""
    ## Limitationen

    - Nur drei Punktstationen, keine Aussage über ganze Polargebiete.
    - Unterschiedliche Lagen: Utqiaġvik liegt an der Küste, Summit und
      der Südpol auf Eisschilden in grosser Höhe.
    - In Utqiaġvik fehlen viele Jahre (unter 80 % Abdeckung in einzelnen
      Monaten), das verkleinert die Stichprobe.
    - Lineare Regression nimmt unabhängige Jahre an. Jahre hängen aber
      zusammen (Autokorrelation), die p-Werte sind daher eher zu optimistisch.
      Der Mann-Kendall-Test dient als robuste Gegenprobe.
    - Mögliche Instrumentenwechsel sind nicht korrigiert (NOAA-README, Warnungen).
    """)
    return


if __name__ == "__main__":
    app.run()
