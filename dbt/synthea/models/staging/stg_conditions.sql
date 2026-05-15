with source as (
    select * from {{ source('synthea', 'conditions') }}
)

select
    id,
    patient_id,
    code,
    display,
    onset_date,
    abatement_date,
    clinical_status,
    code = '82423001' as is_chronic_pain
from source
