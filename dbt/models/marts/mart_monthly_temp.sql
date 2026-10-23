-- Mart: Monatswerte der 2-m-Temperatur pro Station.
--
-- Grain: eine Zeile = eine Station × ein Kalendermonat (UTC).
--
-- Datenabdeckung: Ein Monat ist nur "gültig", wenn mindestens
-- var('min_month_coverage') der Stunden einen gültigen Temperaturwert haben.
-- Sonst würde z. B. ein Monat mit Messungen nur in der ersten Woche den
-- Monatsmittelwert verzerren (in der Polarnacht kühlt es laufend ab).

with hourly as (

    select * from {{ ref('stg_noaa_hourly') }}

),

monthly as (

    select
        site_code,
        year,
        month,
        count(*)                                     as n_rows,
        count(temp_2m_c)                             as n_valid_hours,
        day(last_day(make_date(year, month, 1))) * 24 as n_expected_hours,
        avg(temp_2m_c)                               as t2m_mean_c,
        min(temp_2m_c)                               as t2m_min_c,
        max(temp_2m_c)                               as t2m_max_c
    from hourly
    group by site_code, year, month

)

select
    m.site_code,
    s.station_name,
    s.region,
    s.hemisphere,
    m.year,
    m.month,
    make_date(m.year, m.month, 1)                    as month_start,
    m.n_rows,
    m.n_valid_hours,
    m.n_expected_hours,
    round(m.n_valid_hours / m.n_expected_hours, 4)  as coverage,
    m.n_valid_hours >= {{ var('min_month_coverage') }} * m.n_expected_hours as is_valid,
    round(m.t2m_mean_c, 3)                           as t2m_mean_c,
    m.t2m_min_c,
    m.t2m_max_c
from monthly m
left join {{ ref('stations') }} s using (site_code)
