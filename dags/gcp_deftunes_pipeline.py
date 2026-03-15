"""
DefTunes GCP Data Pipeline — Airflow DAG
=========================================
Orchestrates the end-to-end data ingestion pipeline on Google Cloud Platform.

Pipeline Flow:
    GCS (NDJSON) → BigQuery Landing Zone → dbt Transformation → Serving Layer

Product Context:
    This DAG represents how the pipeline would run in production via Cloud Composer
    (managed Airflow). Each task is idempotent and can be re-run independently,
    which is critical for data reliability in a consumer-facing product.

Note:
    For local development, data loading is handled by load_to_bq.py directly.
    This DAG is the production-grade orchestration layer.
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.providers.google.cloud.transfers.gcs_to_bigquery import GCSToBigQueryOperator
from airflow.operators.empty import EmptyOperator
from airflow.operators.bash import BashOperator

# ──────────────────────────────────────────────────────────────────────────
# DAG CONFIGURATION
# ──────────────────────────────────────────────────────────────────────────
PROJECT_ID = "ai-data-product-work"
GCS_BUCKET = "ai-data-product-work-data-lake"
BQ_LANDING_DATASET = "deftunes_landing_zone"

default_args = {
    "owner": "data-engineering",
    "depends_on_past": False,
    "email_on_failure": True,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="deftunes_gcp_pipeline",
    default_args=default_args,
    description="DefTunes: Load raw data from GCS to BigQuery and transform via dbt",
    schedule_interval="@daily",
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["deftunes", "bigquery", "dbt"],
) as dag:

    start = EmptyOperator(task_id="start")

    # ──────────────────────────────────────────────────────────────────
    # LANDING ZONE INGESTION
    # Each task loads a raw NDJSON file from GCS into BigQuery.
    # All four tasks run in parallel — they have no dependencies on each other.
    # ──────────────────────────────────────────────────────────────────

    load_users = GCSToBigQueryOperator(
        task_id="load_users_to_bq",
        bucket=GCS_BUCKET,
        source_objects=["landing_zone/users.json"],
        destination_project_dataset_table=f"{PROJECT_ID}.{BQ_LANDING_DATASET}.raw_users",
        source_format="NEWLINE_DELIMITED_JSON",
        autodetect=True,
        write_disposition="WRITE_TRUNCATE",
    )

    load_songs = GCSToBigQueryOperator(
        task_id="load_songs_to_bq",
        bucket=GCS_BUCKET,
        source_objects=["landing_zone/songs.json"],
        destination_project_dataset_table=f"{PROJECT_ID}.{BQ_LANDING_DATASET}.raw_songs",
        source_format="NEWLINE_DELIMITED_JSON",
        autodetect=True,
        write_disposition="WRITE_TRUNCATE",
    )

    load_sessions = GCSToBigQueryOperator(
        task_id="load_sessions_to_bq",
        bucket=GCS_BUCKET,
        source_objects=["landing_zone/sessions.json"],
        destination_project_dataset_table=f"{PROJECT_ID}.{BQ_LANDING_DATASET}.raw_sessions",
        source_format="NEWLINE_DELIMITED_JSON",
        autodetect=True,
        write_disposition="WRITE_TRUNCATE",
    )

    load_feedback = GCSToBigQueryOperator(
        task_id="load_feedback_to_bq",
        bucket=GCS_BUCKET,
        source_objects=["landing_zone/user_song_feedback.json"],
        destination_project_dataset_table=f"{PROJECT_ID}.{BQ_LANDING_DATASET}.raw_user_feedback",
        source_format="NEWLINE_DELIMITED_JSON",
        autodetect=True,
        write_disposition="WRITE_TRUNCATE",
    )

    # ──────────────────────────────────────────────────────────────────
    # DATA CONTRACT VALIDATION
    # Uses the open-source datacontract CLI to enforce the ODCS YAML rules
    # against the newly loaded BigQuery tables. If this fails, the DAG halts.
    # ──────────────────────────────────────────────────────────────────
    validate_landing_data = BashOperator(
        task_id="validate_landing_data_contract",
        bash_command="datacontract test --server bigquery --contract ./odcs_contracts/landing_datacontract.yaml"
    )

    # Placeholder for dbt transformation step
    # In production, this would call `dbt run` via BashOperator or KubernetesPodOperator
    dbt_transform = EmptyOperator(task_id="dbt_transform_placeholder")

    # ──────────────────────────────────────────────────────────────────
    # SERVING CONTRACT VALIDATION
    # Validates the output of the dbt models against the serving contract.
    # ──────────────────────────────────────────────────────────────────
    validate_serving_data = BashOperator(
        task_id="validate_serving_data_contract",
        bash_command="datacontract test --server bigquery --contract ./odcs_contracts/serving_datacontract.yaml"
    )

    end = EmptyOperator(task_id="end")

    # ──────────────────────────────────────────────────────────────────
    # TASK DEPENDENCIES
    # All landing zone loads run in parallel.
    # When complete, validate the landing contract.
    # If validation passes, run dbt transforms.
    # If transforms succeed, validate the serving contract before finishing.
    # ──────────────────────────────────────────────────────────────────
    start >> [load_users, load_songs, load_sessions, load_feedback] >> validate_landing_data >> dbt_transform >> validate_serving_data >> end
