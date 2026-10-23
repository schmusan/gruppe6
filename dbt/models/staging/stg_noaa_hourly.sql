-- Staging: bereinigte Stundenwerte der NOAA-Observatorien.
--
-- Grain: eine Zeile = eine Station × eine Stunde (UTC). Der Test
-- `unique_site_hour` in _staging.yml sichert diesen Grain ab.
--
-- Bereinigung:
--   1. Fehlcodes -> NULL. Jedes Feld hat laut NOAA-README einen eigenen Code.
--      Abweichung zur Doku: Die Windgeschwindigkeit verwendet in den Daten auch
--      -99.9 statt -999.9, deshalb prüfen wir dort auf "< 0".
--   2. Plausibilität: physikalisch unmögliche Werte -> NULL (Grenzen unten).
--   3. Duplikate: Falls eine Stunde mehrfach vorkommt, bleibt die erste Zeile.

with source as (

    select * from {{ source('noaa', 'hourly') }}

),

typed as (

    select
        upper(site_code)                                        as site_code,
        make_timestamp(year, month, day, hour, 0, 0)            as observed_at_utc,
        year, month, day, hour,

        nullif(wind_dir_deg, -999)                              as wind_dir_deg,
        case when wind_speed_ms < 0 then null else wind_speed_ms end as wind_speed_ms,
        nullif(wind_steadiness, -9)                             as wind_steadiness,
        case when pressure_hpa <= -999 then null else pressure_hpa end as pressure_hpa,
        case when temp_2m_c  <= -999 then null else temp_2m_c  end as temp_2m_c,
        case when temp_10m_c <= -999 then null else temp_10m_c end as temp_10m_c,
        case when temp_top_c <= -999 then null else temp_top_c end as temp_top_c,
        nullif(rel_humidity_pct, -99)                           as rel_humidity_pct,
        nullif(precip_mm_h, -99)                                as precip_mm_h,

        source_file
    from source

),

plausible as (

    select
        * replace (
            -- Kältester je gemessener Wert auf der Erde liegt bei rund -89 °C,
            -- an keiner der drei Stationen sind über +30 °C realistisch.
            case when temp_2m_c  between -90 and 30 then temp_2m_c  end as temp_2m_c,
            case when temp_10m_c between -90 and 30 then temp_10m_c end as temp_10m_c,
            case when temp_top_c between -90 and 30 then temp_top_c end as temp_top_c,
            case when rel_humidity_pct between 0 and 100 then rel_humidity_pct end as rel_humidity_pct,
            case when wind_dir_deg between 0 and 360 then wind_dir_deg end as wind_dir_deg
        )
    from typed

),

deduplicated as (

    select *
    from plausible
    qualify row_number() over (partition by site_code, observed_at_utc order by source_file) = 1

)

select * from deduplicated
