-- Mart: Jahresmittel der 2-m-Temperatur und Anomalie pro Station.
--
-- Grain: eine Zeile = eine Station × ein Kalenderjahr.
--
-- Regeln:
--   * Das Jahresmittel ist der Durchschnitt der 12 Monatsmittel. So zählt jeder
--     Monat gleich, auch wenn einzelne Stunden fehlen.
--   * Ein Jahr ist nur vollständig (is_complete), wenn alle 12 Monate gültig
--     sind. Für unvollständige Jahre bleibt das Jahresmittel leer.
--   * Anomalie = Jahresmittel minus Mittel der Station über die Referenzperiode
--     var('reference_start_year')–var('reference_end_year').

with monthly as (

    select * from {{ ref('mart_monthly_temp') }}

),

annual as (

    select
        site_code,
        any_value(station_name)                       as station_name,
        any_value(region)                             as region,
        any_value(hemisphere)                         as hemisphere,
        year,
        count(*) filter (where is_valid)              as n_valid_months,
        avg(t2m_mean_c) filter (where is_valid)       as t2m_mean_valid_months_c
    from monthly
    group by site_code, year

),

flagged as (

    select
        *,
        n_valid_months = 12                           as is_complete,
        case when n_valid_months = 12 then t2m_mean_valid_months_c end as t2m_annual_c
    from annual

),

reference as (

    select site_code, avg(t2m_annual_c) as t2m_reference_c
    from flagged
    where year between {{ var('reference_start_year') }} and {{ var('reference_end_year') }}
      and is_complete
    group by site_code

)

select
    f.site_code,
    f.station_name,
    f.region,
    f.hemisphere,
    f.year,
    f.n_valid_months,
    f.is_complete,
    round(f.t2m_annual_c, 3)                          as t2m_annual_c,
    round(r.t2m_reference_c, 3)                       as t2m_reference_c,
    round(f.t2m_annual_c - r.t2m_reference_c, 3)      as t2m_anomaly_c
from flagged f
left join reference r using (site_code)
