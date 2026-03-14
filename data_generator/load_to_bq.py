"""
BigQuery Data Loader
====================
Loads NDJSON files from Google Cloud Storage (GCS) into BigQuery landing zone tables.
This is the ingestion step of the DefTunes data pipeline.

Pipeline Position:
    GCS (landing_zone/) → [THIS SCRIPT] → BigQuery (deftunes_landing_zone)

Product Context:
    The landing zone is our "single source of truth" for raw data. By loading
    directly from GCS with auto-schema detection, we minimize manual schema
    management while preserving the original data shape for auditability.

Usage:
    python load_to_bq.py
"""

from google.cloud import bigquery

# ──────────────────────────────────────────────────────────────────────────
# CONFIGURATION
# These values define the GCP project topology for the data pipeline.
# ──────────────────────────────────────────────────────────────────────────
PROJECT_ID = "ai-data-product-work"
GCS_BUCKET = "ai-data-product-work-data-lake"
BQ_LANDING_DATASET = "deftunes_landing_zone"


def load_gcs_json_to_bq(client, table_id, gcs_uri):
    """
    Loads a newline-delimited JSON file from GCS into a BigQuery table.
    
    Uses WRITE_TRUNCATE to ensure idempotent loads — re-running this script
    will replace (not append) the data, which is the safest pattern for
    landing zone tables that should always reflect the latest raw extract.
    """
    print(f"Loading {gcs_uri} into {table_id}...")
    
    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
        autodetect=True,
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
    )
    
    load_job = client.load_table_from_uri(gcs_uri, table_id, job_config=job_config)
    
    try:
        load_job.result()
        destination_table = client.get_table(table_id)
        print(f"✅ Loaded {destination_table.num_rows} rows into {table_id}.")
        return True
    except Exception as e:
        print(f"❌ Error loading {gcs_uri} to {table_id}:\n{e}")
        return False


if __name__ == "__main__":
    client = bigquery.Client(project=PROJECT_ID)

    # Ensure the landing zone dataset exists (create if first run)
    dataset_id = f"{PROJECT_ID}.{BQ_LANDING_DATASET}"
    dataset = bigquery.Dataset(dataset_id)
    dataset.location = "us-east1"
    try:
        client.get_dataset(dataset_id)
    except Exception:
        client.create_dataset(dataset, timeout=30)
        print(f"Created dataset {dataset_id}")

    # Map each raw table to its GCS source file
    # These table names match the ODCS data contract (landing_datacontract.yaml)
    files_to_load = [
        ("raw_users", "users.json"),
        ("raw_songs", "songs.json"),
        ("raw_sessions", "sessions.json"),
        ("raw_user_feedback", "user_song_feedback.json"),
    ]

    print("\n--- Starting BigQuery Ingestion ---")
    all_success = True
    for table_name, filename in files_to_load:
        bq_table = f"{dataset_id}.{table_name}"
        gcs_path = f"gs://{GCS_BUCKET}/landing_zone/{filename}"
        if not load_gcs_json_to_bq(client, bq_table, gcs_path):
            all_success = False

    if all_success:
        print("\n🎉 All datasets loaded into BigQuery landing zone!")
    else:
        print("\n⚠️ Some datasets failed. Check the output above.")
