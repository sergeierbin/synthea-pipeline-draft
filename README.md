# Synthea Data Pipeline

An end-to-end data pipeline that generates synthetic patient data, loads it into PostgreSQL, transforms it with dbt, and visualizes it in Apache Superset.

## Architecture

```
Synthea (FHIR) → Python Loader → PostgreSQL → dbt → Apache Superset
```

### Components

1. **Synthea** — Generates realistic synthetic patient records in FHIR (Fast Healthcare Interoperability Resources) JSON format. No real patient data is used.

2. **Python Loader** (`scripts/`) — Reads FHIR bundles output by Synthea, parses relevant resources (Patient, Encounter, Condition, Observation, etc.), and bulk-inserts raw records into a PostgreSQL staging schema.

3. **PostgreSQL** — Central data store. Raw FHIR data lands in a `raw` schema; dbt writes to `staging` and `marts` schemas.

4. **dbt** (`dbt/synthea/`) — Transforms raw FHIR JSON into clean, analytics-ready tables:
   - `models/staging/` — Typed, deduplicated views over raw tables (one model per FHIR resource)
   - `models/marts/` — Business-level aggregations (e.g., patient demographics, encounter summaries, condition prevalence)

5. **Apache Superset** — Connects to the PostgreSQL marts schema to power dashboards and ad-hoc SQL exploration.

6. **Apache Airflow** (`airflow/dags/`) — Orchestrates the full pipeline: triggers Synthea, runs the Python loader, and executes `dbt run` on a schedule.

7. **Docker** (`docker/`) — Compose configuration to spin up PostgreSQL, Airflow, and Superset locally.

## Folder Structure

```
synthea-pipeline/
├── airflow/
│   └── dags/               # Airflow DAG definitions
├── dbt/
│   └── synthea/
│       └── models/
│           ├── staging/    # Typed models over raw FHIR tables
│           └── marts/      # Analytics-ready aggregated models
├── docker/                 # Docker Compose and service configs
├── scripts/                # Python FHIR loader and utilities
└── README.md
```

## Getting Started

### Prerequisites

- Docker and Docker Compose
- Java 11+ (required by Synthea)
- Python 3.10+

### 1. Generate Synthetic Data

```bash
# Clone and run Synthea
git clone https://github.com/synthetichealth/synthea.git
cd synthea
./run_synthea -p 1000   # Generate 1000 patients
```

### 2. Start Infrastructure

```bash
docker compose -f docker/docker-compose.yml up -d
```

This starts PostgreSQL, Airflow, and Superset.

### 3. Load FHIR Data

```bash
pip install -r scripts/requirements.txt
python scripts/load_fhir.py --input /path/to/synthea/output/fhir
```

### 4. Run dbt Transformations

```bash
cd dbt/synthea
dbt deps
dbt run
dbt test
```

### 5. View Dashboards

Open Superset at `http://localhost:8088` and connect it to the PostgreSQL `marts` schema.

## Data Flow Detail

```
Synthea output/fhir/
  └── *.json (FHIR Bundles)
        │
        ▼
scripts/load_fhir.py
  └── Parses resources → inserts into PostgreSQL raw schema
        │
        ▼
PostgreSQL: raw schema
  └── raw.patient, raw.encounter, raw.condition, raw.observation, ...
        │
        ▼
dbt staging models
  └── staging.stg_patients, stg_encounters, stg_conditions, ...
        │
        ▼
dbt mart models
  └── marts.patient_summary, encounter_metrics, condition_prevalence, ...
        │
        ▼
Apache Superset dashboards
```

## License

This project uses synthetic data only. No real patient information is processed or stored.
