-- Nach der Bereinigung darf kein NOAA-Fehlcode mehr in den Messwerten stehen.
select *
from {{ ref('stg_noaa_hourly') }}
where temp_2m_c <= -99 or temp_10m_c <= -99 or temp_top_c <= -99
   or pressure_hpa <= -99 or wind_speed_ms < 0 or wind_dir_deg < 0
   or rel_humidity_pct < 0 or precip_mm_h < 0
