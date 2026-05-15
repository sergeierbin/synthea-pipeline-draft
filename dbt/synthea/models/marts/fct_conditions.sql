with conditions as (
    select * from {{ ref('stg_conditions') }}
),

patients as (
    select * from {{ ref('stg_patients') }}
)

select
    c.id              as condition_id,
    c.patient_id,
    c.code,
    c.display,
    c.onset_date,
    c.abatement_date,
    c.clinical_status,
    c.is_chronic_pain,
    p.age,
    p.gender,
    p.city,
    p.state,
    p.country
from conditions c
inner join patients p on p.id = c.patient_id
