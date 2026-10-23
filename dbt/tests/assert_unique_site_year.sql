-- Grain-Test: eine Zeile pro Station und Jahr.
select site_code, year, count(*) as n
from {{ ref('mart_annual_temp') }}
group by all
having count(*) > 1
