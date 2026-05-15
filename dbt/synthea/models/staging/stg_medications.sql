with source as (
    select * from {{ source('synthea', 'medications') }}
)

select
    id,
    patient_id,
    coalesce(code, 'unknown')    as code,
    coalesce(display, 'unknown') as display,
    authored_on,
    coalesce(status, 'unknown')  as status
from source
