with source as (
    select * from {{ source('synthea', 'patients') }}
)

select
    id,
    birth_date,
    gender,
    city,
    state,
    country,
    date_part('year', age(current_date, birth_date))::integer as age
from source
