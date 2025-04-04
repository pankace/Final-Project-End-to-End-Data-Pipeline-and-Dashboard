from google.cloud import storage, bigquery
import json
import os

class StorageHandler:
    def __init__(self, storage_type='gcs', bucket_name=None, dataset_id=None):
        self.storage_type = storage_type
        self.bucket_name = bucket_name
        self.dataset_id = dataset_id
        
        if self.storage_type == 'gcs':
            self.client = storage.Client()
            if not self.bucket_name:
                raise ValueError("Bucket name must be provided for Google Cloud Storage.")
            self.bucket = self.client.bucket(self.bucket_name)
        elif self.storage_type == 'bigquery':
            self.client = bigquery.Client()
            if not self.dataset_id:
                raise ValueError("Dataset ID must be provided for BigQuery.")
        else:
            raise ValueError("Invalid storage type. Use 'gcs' for Google Cloud Storage or 'bigquery' for BigQuery.")

    def save_to_gcs(self, symbol, bid, ask, spread, timestamp):
        filename = f"{symbol}_{timestamp}.json"
        blob = self.bucket.blob(filename)
        data = {
            'symbol': symbol,
            'bid': bid,
            'ask': ask,
            'spread': spread,
            'timestamp': timestamp
        }
        blob.upload_from_string(json.dumps(data), content_type='application/json')
    
    def save_to_bigquery(self, symbol, bid, ask, spread, timestamp):
        table_id = f"{self.dataset_id}.{symbol}"
        rows_to_insert = [{
            'symbol': symbol,
            'bid': bid,
            'ask': ask,
            'spread': spread,
            'timestamp': timestamp
        }]
        errors = self.client.insert_rows_json(table_id, rows_to_insert)
        if errors:
            raise Exception(f"Failed to insert rows: {errors}")

    def save_data(self, symbol, bid, ask, spread, timestamp):
        if self.storage_type == 'gcs':
            self.save_to_gcs(symbol, bid, ask, spread, timestamp)
        elif self.storage_type == 'bigquery':
            self.save_to_bigquery(symbol, bid, ask, spread, timestamp)
        else:
            raise ValueError("Invalid storage type. Use 'gcs' for Google Cloud Storage or 'bigquery' for BigQuery.")