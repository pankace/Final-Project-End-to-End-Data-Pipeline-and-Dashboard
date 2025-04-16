import json
import base64
from google.cloud import bigquery
from src.connectors.bigquery_client import BigQueryClient
from src.processors.price_processor import process_price_update
from src.processors.trade_processor import process_trade_update

# Initialize the BigQuery client
bq_client = BigQueryClient()

def pubsub_function(event, context):
    """Cloud Function to process messages published to Pub/Sub.
    
    Args:
        event (dict): The dictionary with data specific to this type of event.
                      The `data` field contains the PubsubMessage message.
        context (google.cloud.functions.Context): The Cloud Functions event
                                                  metadata.
    """
    pubsub_message = base64.b64decode(event['data']).decode('utf-8')
    data = json.loads(pubsub_message)
    
    data_type = data.get('type')
    
    if data_type == 'price_update':
        process_price_update(data, bq_client)
        
    elif data_type == 'trade_update':
        process_trade_update(data, bq_client)
        
    else:
        raise ValueError(f"Unknown data type: {data_type}")