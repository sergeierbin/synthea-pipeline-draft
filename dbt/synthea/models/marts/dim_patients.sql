with patients as (
    select * from {{ ref('stg_patients') }}
),

condition_counts as (
    select
        patient_id,
        count(*)                          as total_conditions,
        count(*) filter (
            where clinical_status = 'active'
        )                                 as active_conditions,
        bool_or(is_chronic_pain)          as has_chronic_pain
    from {{ ref('stg_conditions') }}
    group by patient_id
)

select
    p.id,
    p.birth_date,
    p.age,
    p.gender,
    p.city,
    p.state,
    p.country,
    coalesce(cc.total_conditions, 0)   as total_conditions,
    coalesce(cc.active_conditions, 0)  as active_conditions,
    coalesce(cc.has_chronic_pain, false) as has_chronic_pain
from patients p
left join condition_counts cc on cc.patient_id = p.id
