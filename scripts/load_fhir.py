import json
import os
import glob
import psycopg2
from psycopg2.extras import execute_values

FHIR_DIR = "./output/fhir"

CONN_PARAMS = dict(
    host="localhost",
    dbname="synthea",
    user="postgres",
    password="postgres",
)

SKIP_KEYWORDS = ("hospital", "practitioner")


def parse_patient(resource):
    address = (resource.get("address") or [{}])[0]
    return (
        resource.get("id"),
        resource.get("birthDate"),
        (resource.get("gender") or "").lower() or None,
        address.get("city"),
        address.get("state"),
        address.get("country"),
    )


def parse_condition(resource):
    coding = ((resource.get("code") or {}).get("coding") or [{}])[0]
    onset = resource.get("onsetDateTime") or resource.get("onsetPeriod", {}).get("start")
    abatement = resource.get("abatementDateTime") or resource.get("abatementPeriod", {}).get("start")
    return (
        resource.get("id"),
        resource.get("subject", {}).get("reference", "").removeprefix("urn:uuid:"),
        coding.get("code"),
        coding.get("display"),
        onset[:10] if onset else None,
        abatement[:10] if abatement else None,
        (resource.get("clinicalStatus") or {}).get("coding", [{}])[0].get("code"),
    )


def parse_medication_request(resource):
    coding = ((resource.get("medicationCodeableConcept") or {}).get("coding") or [{}])[0]
    return (
        resource.get("id"),
        resource.get("subject", {}).get("reference", "").removeprefix("urn:uuid:"),
        coding.get("code"),
        coding.get("display"),
        resource.get("authoredOn", "")[:10] or None,
        resource.get("status"),
    )


def parse_observation(resource):
    coding = ((resource.get("code") or {}).get("coding") or [{}])[0]
    effective = resource.get("effectiveDateTime") or resource.get("effectivePeriod", {}).get("start")
    value_quantity = resource.get("valueQuantity") or {}
    return (
        resource.get("id"),
        resource.get("subject", {}).get("reference", "").removeprefix("urn:uuid:"),
        coding.get("code"),
        coding.get("display"),
        value_quantity.get("value"),
        value_quantity.get("unit"),
        effective[:10] if effective else None,
    )


PARSERS = {
    "Patient": parse_patient,
    "Condition": parse_condition,
    "MedicationRequest": parse_medication_request,
    "Observation": parse_observation,
}

INSERT_SQL = {
    "Patient": """
        INSERT INTO patients (id, birth_date, gender, city, state, country)
        VALUES %s
        ON CONFLICT DO NOTHING
    """,
    "Condition": """
        INSERT INTO conditions (id, patient_id, code, display, onset_date, abatement_date, clinical_status)
        VALUES %s
        ON CONFLICT DO NOTHING
    """,
    "MedicationRequest": """
        INSERT INTO medications (id, patient_id, code, display, authored_on, status)
        VALUES %s
        ON CONFLICT DO NOTHING
    """,
    "Observation": """
        INSERT INTO observations (id, patient_id, code, display, value, unit, effective_date)
        VALUES %s
        ON CONFLICT DO NOTHING
    """,
}


def load_bundle(path):
    with open(path) as f:
        bundle = json.load(f)

    rows = {rt: [] for rt in PARSERS}
    for entry in bundle.get("entry") or []:
        resource = entry.get("resource") or {}
        rt = resource.get("resourceType")
        if rt in PARSERS:
            rows[rt].append(PARSERS[rt](resource))
    return rows


def insert_rows(cur, resource_type, rows):
    if not rows:
        return
    execute_values(cur, INSERT_SQL[resource_type].strip(), rows)


def main():
    pattern = os.path.join(FHIR_DIR, "*.json")
    all_files = sorted(glob.glob(pattern))
    files = [
        f for f in all_files
        if not any(kw in os.path.basename(f).lower() for kw in SKIP_KEYWORDS)
    ]

    print(f"Found {len(all_files)} JSON files, processing {len(files)} (skipped {len(all_files) - len(files)})")

    conn = psycopg2.connect(**CONN_PARAMS)
    try:
        cur = conn.cursor()
        totals = {rt: 0 for rt in PARSERS}

        for i, path in enumerate(files, 1):
            rows = load_bundle(path)
            for rt, data in rows.items():
                insert_rows(cur, rt, data)
                totals[rt] += len(data)
            conn.commit()

            if i % 10 == 0 or i == len(files):
                print(f"[{i}/{len(files)}] {os.path.basename(path)}")

        print("\nDone.")
        for rt, count in totals.items():
            print(f"  {rt}: {count} records inserted")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
