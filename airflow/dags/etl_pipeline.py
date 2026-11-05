from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator

def run_ge_validation():
    import sys
    sys.path.append('/opt/airflow/great_expectations')
    from run_ge_validation import main
    main()

default_args = {
    'owner': 'data-engineering',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    'etl_pipeline',
    default_args=default_args,
    description='Daily ETL for e-commerce data warehouse',
    schedule_interval='0 2 * * *',  # Daily at 2 AM UTC
    start_date=datetime(2024, 1, 1),
    catchup=False,
    max_active_runs=1,
    tags=['ecommerce', 'data-warehouse', 'dbt', 'great-expectations'],
) as dag:

    # Task 1: Load raw data via Python ingestion
    load_data = BashOperator(
        task_id='load_data',
        bash_command='cd /opt/airflow && python ingest/load_data.py',
        env={
            'POSTGRES_HOST': 'postgres',
            'POSTGRES_PORT': '5432',
            'POSTGRES_DB': 'reviews',
            'POSTGRES_USER': 'review_app',
            'POSTGRES_PASSWORD': '{{ var.value.postgres_password }}',
        },
    )

    # Task 2: Run Great Expectations validation
    ge_validation = PythonOperator(
        task_id='ge_validation',
        python_callable=run_ge_validation,
    )

    # Task 3: Run dbt deps
    dbt_deps = BashOperator(
        task_id='dbt_deps',
        bash_command='cd /opt/airflow && dbt deps',
    )

    # Task 4: Run dbt build
    dbt_build = BashOperator(
        task_id='dbt_build',
        bash_command='cd /opt/airflow && dbt build',
        env={
            'POSTGRES_PASSWORD': '{{ var.value.postgres_password }}',
        },
    )

    # Task 5: Generate dbt docs
    dbt_docs = BashOperator(
        task_id='dbt_docs',
        bash_command='cd /opt/airflow && dbt docs generate',
        env={
            'POSTGRES_PASSWORD': '{{ var.value.postgres_password }}',
        },
    )

    # Dependencies
    load_data >> ge_validation >> dbt_deps >> dbt_build >> dbt_docs
