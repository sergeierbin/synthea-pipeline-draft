#!/usr/bin/env bash
set -euo pipefail

COMPOSE_FILE="docker/docker-compose.yml"
TABLES_SQL="scripts/create_tables.sql"
FHIR_SRC="synthea/output/fhir"
FHIR_DST="./output/fhir"
DBT_DIR="dbt/synthea"

PG_HOST="localhost"
PG_PORT="5432"
PG_DB="synthea"
PG_USER="postgres"
export PGPASSWORD="postgres"

fail() {
    echo "FAILED: $1" >&2
    exit 1
}

run_step() {
    local name="$1"
    shift
    echo "--- $name ---"
    "$@" || fail "$name"
}

# 1. Start services
run_step "docker-compose up" \
    docker compose -f "$COMPOSE_FILE" up -d

echo "Waiting 30 seconds for services to be ready..."
sleep 30

# 2. Create tables
run_step "create tables" \
    psql -h "$PG_HOST" -p "$PG_PORT" -U "$PG_USER" -d "$PG_DB" -f "$TABLES_SQL"

# 3. Copy sample FHIR files
run_step "copy FHIR samples" bash -c "
    mkdir -p '$FHIR_DST'
    files=(\$(find '$FHIR_SRC' -maxdepth 1 -name '*.json' \
        ! -iname '*hospital*' ! -iname '*practitioner*' \
        | head -5))
    if [[ \${#files[@]} -eq 0 ]]; then
        echo 'No FHIR JSON files found in $FHIR_SRC' >&2
        exit 1
    fi
    cp \"\${files[@]}\" '$FHIR_DST/'
    echo \"Copied \${#files[@]} file(s) to $FHIR_DST\"
"

# 4. Load FHIR data
run_step "load_fhir.py" \
    python3 scripts/load_fhir.py

# 5. dbt run
run_step "dbt run" bash -c "
    cd '$DBT_DIR' && dbt run --profiles-dir .
"

# 6. dbt test
run_step "dbt test" bash -c "
    cd '$DBT_DIR' && dbt test --profiles-dir .
"

echo ""
echo "Pipeline OK"
