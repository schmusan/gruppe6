-- Grain-Test: eine Zeile pro Station und Monat.
select site_code, year, month, count(*) as n
from {{ ref('mart_monthly_temp') }}
group by all
having count(*) > 1
