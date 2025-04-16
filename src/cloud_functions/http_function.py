import json
from flask import Request
from google.cloud import bigquery
import os

# Import processors as functions (not classes)
from connectors.bigquery_client import BigQueryClient 
from processors.price_processor import process_price_update
from processors.trade_processor import process_trade_update
from config.settings import BQ_DATASET_ID

# Initialize the BigQuery client
project_id = os.environ.get('PROJECT_ID')
dataset_id = os.environ.get('BQ_DATASET', 'mt5_trading')
bq_client = BigQueryClient(project_id=project_id, dataset_id=dataset_id)

def process_mt5_data(request):
    """Cloud Function to process MT5 WebSocket data and insert into BigQuery"""
    request_json = request.get_json(silent=True)
    
    if not request_json:
        return 'No JSON data received', 400
    
    data_type = request_json.get('type')
    
    if data_type == 'price_update':
        response = process_price_update(request_json, bq_client)
        
    elif data_type == 'trade_update':
        response = process_trade_update(request_json, bq_client)
        
    else:
        return f"Unknown data type: {data_type}", 400
    
    return response