-- Mart: Saisonmittel der 2-m-Temperatur pro Station (für H3).
--
-- Grain: eine Zeile = eine Station × eine meteorologische Jahreszeit eines Jahres.
--
-- Meteorologische Jahreszeiten: Dez–Feb, Mär–Mai, Jun–Aug, Sep–Nov.
-- Der Dezember zählt zur Saison des Folgejahres (Dez 2019 gehört zu Dez–Feb 2020).
-- Auf der Südhalbkugel sind die Jahreszeiten umgekehrt: Dez–Feb ist am Südpol
-- Sommer, Jun–Aug Winter. Darum wird die Bezeichnung über die Hemisphäre gesetzt.
-- Eine Saison zählt nur, wenn alle drei Monate gültig sind.

with monthly as (

    select * from {{ ref('mart_monthly_temp') }}

),

assigned as (

    select
        *,
        case when month = 12 then year + 1 else year end as season_year,
        case
            when month in (12, 1, 2) then 'DJF'
            when month in (3, 4, 5)  then 'MAM'
            when month in (6, 7, 8)  then 'JJA'
            else 'SON'
        end as season_code
    from monthly

),

seasonal as (

    select
        site_code,
        any_value(station_name)                 as station_name,
        any_value(region)                       as region,
        any_value(hemisphere)                   as hemisphere,
        season_year,
        season_code,
        count(*) filter (where is_valid)        as n_valid_months,
        avg(t2m_mean_c) filter (where is_valid) as t2m_mean_c
    from assigned
    group by site_code, season_year, season_code

)

select
    site_code,
    station_name,
    region,
    hemisphere,
    season_year,
    season_code,
    case
        when hemisphere = 'Nord' then
            case season_code when 'DJF' then 'Winter' when 'MAM' then 'Frühling'
                             when 'JJA' then 'Sommer' else 'Herbst' end
        else
            case season_code when 'DJF' then 'Sommer' when 'MAM' then 'Herbst'
                             when 'JJA' then 'Winter' else 'Frühling' end
    end                                         as season_name,
    n_valid_months,
    n_valid_months = 3                          as is_complete,
    case when n_valid_months = 3 then round(t2m_mean_c, 3) end as t2m_season_c
from seasonal
