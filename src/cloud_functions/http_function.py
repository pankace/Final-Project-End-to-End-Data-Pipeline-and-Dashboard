import functions_framework
import logging
import os
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import directly (no src prefix)
from connectors.bigquery_client import BigQueryClient
from processors.price_processor import process_price_update
from processors.trade_processor import process_trade_update
from config.settings import BQ_DATASET_ID

# Initialize BigQuery client with environment variables
project_id = os.environ.get('PROJECT_ID')
dataset_id = os.environ.get('BQ_DATASET', 'mt5_trading')
logger.info(f"Initializing with project={project_id}, dataset={dataset_id}")
bq_client = BigQueryClient(project_id=project_id, dataset_id=dataset_id)

@functions_framework.http
def process_mt5_data(request):
    """Entry point for HTTP Cloud Function"""
    logger.info("Received request")
    request_json = request.get_json(silent=True)
    
    if not request_json:
        logger.error("No JSON data received")
        return 'No JSON data received', 400
    
    data_type = request_json.get('type')
    logger.info(f"Processing {data_type} data")
    
    if data_type == 'price_update':
        return process_price_update(request_json, bq_client)
    elif data_type == 'trade_update':
        return process_trade_update(request_json, bq_client)
    else:
        logger.error(f"Unknown data type: {data_type}")
        return f"Unknown data type: {data_type}", 400