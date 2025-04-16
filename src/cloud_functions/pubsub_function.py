import json
import base64
import logging
import functions_framework
from google.cloud import bigquery
from src.connectors.bigquery_client import BigQueryClient
from src.processors.price_processor import process_price_update
from src.processors.trade_processor import process_trade_update
from src.config.settings import BQ_PROJECT_ID, BQ_DATASET_ID

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize the BigQuery client
try:
    bq_client = BigQueryClient(project_id=BQ_PROJECT_ID, dataset_id=BQ_DATASET_ID)
    logger.info(f"BigQuery client initialized for project {BQ_PROJECT_ID}, dataset {BQ_DATASET_ID}")
except Exception as e:
    logger.critical(f"Failed to initialize BigQuery client: {e}")
    bq_client = None

@functions_framework.cloud_event
def pubsub_function(cloud_event):
    """Cloud Function triggered by Pub/Sub messages to process MT5 data.

    Args:
        cloud_event (CloudEvent): The Cloud Event containing the Pub/Sub message
    """
    # Check if BigQuery client was initialized successfully
    if bq_client is None:
        logger.error("BigQuery client is not available. Cannot process message.")
        raise RuntimeError("BigQuery client failed to initialize.")

    try:
        # Extract event information
        event_id = cloud_event.id
        timestamp = cloud_event.time
        logger.info(f"Processing message ID: {event_id}, Published: {timestamp}")

        # Decode the Pub/Sub message data
        pubsub_message = base64.b64decode(cloud_event.data["message"]["data"]).decode("utf-8")
        logger.debug(f"Received raw message data: {pubsub_message}")

        # Parse the JSON data
        try:
            data = json.loads(pubsub_message)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode JSON from message: {e}")
            return

        # Determine the type of data
        data_type = data.get('type')
        logger.info(f"Data type identified: {data_type}")

        # Route data to the appropriate processor
        if data_type == 'price_update':
            # Process price update using the dedicated processor
            result = process_price_update(data, bq_client)
            logger.info(f"Processed price update for symbol: {data.get('symbol')}")
            return result
            
        elif data_type == 'trade_update':
            # Process trade update using the dedicated processor
            update_type = data.get('update_type')
            result = process_trade_update(data, bq_client)
            
            # Log different identifiers based on update type
            if update_type == 'position':
                logger.info(f"Processed position update for trade ID: {data.get('trade_id')}")
            elif update_type == 'transaction':
                logger.info(f"Processed transaction update for transaction ID: {data.get('transaction_id')}")
            else:
                logger.warning(f"Unknown trade update type: {update_type}")
                
            return result
            
        else:
            logger.warning(f"Unknown data type: {data_type}")
            return f"Unknown data type: {data_type}"
            
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in Pub/Sub message: {e}")
        return
        
    except Exception as e:
        logger.error(f"Error processing message: {e}", exc_info=True)
        raise