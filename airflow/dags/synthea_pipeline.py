import sys
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator

sys.path.insert(0, "/opt/airflow/scripts")
from load_fhir import main as load_fhir_files

default_args = {
    "owner": "airflow",
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="synthea_pipeline",
    description="Generate synthetic FHIR data, load to PostgreSQL, and transform with dbt",
    schedule_interval="0 6 1 * *",
    start_date=datetime(2024, 1, 1),
    catchup=False,
    default_args=default_args,
    tags=["synthea", "fhir", "dbt"],
) as dag:

    generate_patients = BashOperator(
        task_id="generate_patients",
        bash_command=(
            "cd /opt/synthea && "
            "./run_synthea -i snapshot.json -u snapshot.json -t 30"
        ),
    )

    load_to_postgres = PythonOperator(
        task_id="load_to_postgres",
        python_callable=load_fhir_files,
    )

    dbt_run = BashOperator(
        task_id="dbt_run",
        bash_command=(
            "cd /opt/airflow/dbt/synthea && "
            "dbt run --profiles-dir ."
        ),
    )

    dbt_test = BashOperator(
        task_id="dbt_test",
        bash_command=(
            "cd /opt/airflow/dbt/synthea && "
            "dbt test --profiles-dir ."
        ),
    )

    generate_patients >> load_to_postgres >> dbt_run >> dbt_test
