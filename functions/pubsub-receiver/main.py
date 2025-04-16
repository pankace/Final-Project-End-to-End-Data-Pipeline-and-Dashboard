import os
import json
import logging
import functions_framework
from flask import jsonify
from google.cloud import bigquery

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define BigQuery dataset and table names
BQ_DATASET = os.environ.get("BQ_DATASET", "mt5_trading")
BQ_POSITIONS_TABLE = os.environ.get("BQ_POSITIONS_TABLE", "positions")
BQ_TRANSACTIONS_TABLE = os.environ.get("BQ_TRANSACTIONS_TABLE", "transactions")
BQ_PRICES_TABLE = os.environ.get("BQ_PRICES_TABLE", "price_updates")

# Initialize BigQuery client - wrap in try/except to catch any initialization errors
try:
    bq_client = bigquery.Client()
    logger.info("BigQuery client initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize BigQuery client: {str(e)}")
    # Still create a variable to prevent errors, but we'll check it later
    bq_client = None

@functions_framework.http
def receive_message(request):
    """HTTP Cloud Function that receives MT5 data and inserts into BigQuery."""
    try:
        # Check if BigQuery client was initialized properly
        if not bq_client:
            logger.error("BigQuery client not available")
            return jsonify({'error': 'Internal server error - database connection failed'}), 500
            
        request_json = request.get_json(silent=True)
        
        if not request_json:
            logger.warning("No JSON data provided in request")
            return jsonify({'error': 'No JSON data provided'}), 400
        
        logger.info(f"Received data: {json.dumps(request_json)[:100]}...")
        
        data_type = request_json.get('type')
        
        if data_type == 'price_update':
            # Process price update
            table_id = f"{bq_client.project}.{BQ_DATASET}.{BQ_PRICES_TABLE}"
            row = {
                "timestamp": request_json.get('timestamp'),
                "symbol": request_json.get('symbol'),
                "bid": request_json.get('bid'),
                "ask": request_json.get('ask'),
                "spread": request_json.get('spread')
            }
            logger.info(f"Inserting price update for {row['symbol']}")
            errors = bq_client.insert_rows_json(table_id, [row])
            
        elif data_type == 'trade_update':
            # Process trade update
            update_type = request_json.get('update_type')
            
            if update_type == 'position':
                # Process position update
                table_id = f"{bq_client.project}.{BQ_DATASET}.{BQ_POSITIONS_TABLE}"
                row = {
                    "timestamp": request_json.get('timestamp'),
                    "trade_id": request_json.get('trade_id'),
                    "symbol": request_json.get('symbol'),
                    "type": request_json.get('type'),
                    "volume": request_json.get('volume'),
                    "price": request_json.get('price'),
                    "profit": request_json.get('profit'),
                    "sl": request_json.get('sl'),
                    "tp": request_json.get('tp')
                }
                logger.info(f"Inserting position update for trade_id {row['trade_id']}")
                errors = bq_client.insert_rows_json(table_id, [row])
                
            elif update_type == 'transaction':
                # Process transaction update
                table_id = f"{bq_client.project}.{BQ_DATASET}.{BQ_TRANSACTIONS_TABLE}"
                row = {
                    "timestamp": request_json.get('timestamp'),
                    "transaction_id": request_json.get('transaction_id'),
                    "symbol": request_json.get('symbol'),
                    "type": request_json.get('type'), 
                    "volume": request_json.get('volume'),
                    "price": request_json.get('price'),
                    "commission": request_json.get('commission'),
                    "swap": request_json.get('swap'),
                    "profit": request_json.get('profit')
                }
                logger.info(f"Inserting transaction update for transaction_id {row['transaction_id']}")
                errors = bq_client.insert_rows_json(table_id, [row])
            else:
                logger.warning(f"Unknown trade update type: {update_type}")
                return jsonify({'error': f'Unknown trade update type: {update_type}'}), 400
        else:
            logger.warning(f"Unknown data type: {data_type}")
            return jsonify({'error': f'Unknown data type: {data_type}'}), 400
            
        if errors:
            logger.error(f"Errors inserting data: {errors}")
            return jsonify({'error': f'Errors inserting data: {errors}'}), 500
            
        logger.info("Data inserted successfully")
        return jsonify({'success': True, 'message': 'Data inserted successfully'})
            
    except Exception as e:
        logger.exception(f"Error processing request: {str(e)}")
        return jsonify({'error': f'Error processing request: {str(e)}'}), 500