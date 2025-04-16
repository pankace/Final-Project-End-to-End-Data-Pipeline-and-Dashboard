#import functions_framework
#import base64
#import json
#import logging
#import os
#from google.cloud import bigquery
#
## Configure logging
#logging.basicConfig(level=logging.INFO)
#logger = logging.getLogger(__name__)
#
## Import processors directly (no src prefix)
#from connectors.bigquery_client import BigQueryClient
#from processors.price_processor import process_price_update
#from processors.trade_processor import process_trade_update
#
## Initialize BigQuery client with environment variables
#project_id = os.environ.get('PROJECT_ID')
#dataset_id = os.environ.get('BQ_DATASET', 'mt5_trading')
#
#logger.info(f"Initializing BigQuery client with project={project_id}, dataset={dataset_id}")
#bq_client = BigQueryClient(project_id=project_id, dataset_id=dataset_id)
#
#@functions_framework.cloud_event
#def pubsub_function(cloud_event):
#    """Cloud Function triggered by Pub/Sub"""
#    try:
#        logger.info(f"Received Pub/Sub event: {cloud_event.id}")
#        
#        # Decode the Pub/Sub message
#        pubsub_message = base64.b64decode(cloud_event.data["message"]["data"]).decode("utf-8")
#        data = json.loads(pubsub_message)
#        
#        data_type = data.get('type')
#        logger.info(f"Processing {data_type} message")
#        
#        if data_type == 'price_update':
#            result = process_price_update(data, bq_client)
#            
#        elif data_type == 'trade_update':
#            result = process_trade_update(data, bq_client)
#            
#        else:
#            logger.error(f"Unknown data type: {data_type}")
#            return f"Unknown data type: {data_type}"
#        
#        logger.info(f"Message processed successfully: {result}")
#        return result
#        
#    except Exception as e:
#        logger.error(f"Error processing message: {e}", exc_info=True)
#        return f"Error: {str(e)}"

import functions_framework
import base64
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@functions_framework.cloud_event
def pubsub_function(cloud_event):
    """Cloud Function triggered by Pub/Sub"""
    logger.info(f"Event ID: {cloud_event.id}")
    
    # Simple response to verify function is working
    # We'll expand this once we confirm deployment
    return "PubSub function triggered successfully!"