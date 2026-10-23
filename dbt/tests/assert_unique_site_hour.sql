-- Grain-Test: Jede Station hat pro Stunde höchstens eine Zeile.
-- Schlägt fehl (liefert Zeilen), wenn die Deduplizierung in stg_noaa_hourly bricht.
select site_code, observed_at_utc, count(*) as n
from {{ ref('stg_noaa_hourly') }}
group by all
having count(*) > 1
