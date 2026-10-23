-- Datenabdeckung muss zwischen 0 und 1 liegen. Ein Wert über 1 hiesse,
-- dass Stunden doppelt gezählt werden.
select * from {{ ref('mart_monthly_temp') }}
where coverage < 0 or coverage > 1
