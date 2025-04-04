import os
import csv
from google.cloud import storage
from google.cloud import bigquery


def save_to_csv(data, filename):
    """Save data to a CSV file
    
    Args:
        data (list): Row data to write [timestamp, symbol, bid, ask, spread]
        filename (str): Path to the CSV file
    """
    # Ensure the directory exists
    os.makedirs(os.path.dirname(filename), exist_ok=True)

    with open(filename, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(data)


def save_to_gcs(data, bucket_name, destination_blob_name):
    """Save data to Google Cloud Storage
    
    Args:
        data (str): CSV formatted string to upload
        bucket_name (str): GCS bucket name
        destination_blob_name (str): Path within the bucket
    """
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)

    blob.upload_from_string(data, content_type='text/csv')


def save_to_bigquery(data, dataset_id, table_id):
    """Save data to Google BigQuery
    
    Args:
        data (dict): Data record to insert
        dataset_id (str): BigQuery dataset ID
        table_id (str): BigQuery table ID
    """
    client = bigquery.Client()
    table_ref = client.dataset(dataset_id).table(table_id)
    
    # Define table schema if creating a new table
    schema = [
        bigquery.SchemaField("timestamp", "TIMESTAMP"),
        bigquery.SchemaField("symbol", "STRING"),
        bigquery.SchemaField("bid", "FLOAT"),
        bigquery.SchemaField("ask", "FLOAT"),
        bigquery.SchemaField("spread", "FLOAT"),
    ]
    
    # Create table if it doesn't exist
    try:
        client.get_table(table_ref)
    except Exception:
        table = bigquery.Table(table_ref, schema=schema)
        table.time_partitioning = bigquery.TimePartitioning(
            type_=bigquery.TimePartitioningType.DAY,
            field="timestamp"  # Partition by timestamp
        )
        client.create_table(table)
    
    # Insert data
    rows_to_insert = [data]
    errors = client.insert_rows_json(table_ref, rows_to_insert)
    
    if errors:
        raise Exception(f"BigQuery insert errors: {errors}")