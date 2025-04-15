import json
import base64
from google.cloud import bigquery

# Initialize the BigQuery client
bq_client = bigquery.Client()

# Define BigQuery dataset and table names
BQ_DATASET = "mt5_trading"
BQ_POSITIONS_TABLE = "positions" 
BQ_TRANSACTIONS_TABLE = "transactions"
BQ_PRICES_TABLE = "price_updates"

def process_mt5_data(request):
    """Cloud Function to process MT5 WebSocket data and insert into BigQuery
    
    Args:
        request (flask.Request): The request object
    Returns:
        The response text, or any set of values that can be turned into a
        Response object using `make_response`
    """
    # For HTTP functions, request is a flask.Request object
    request_json = request.get_json(silent=True)
    
    if not request_json:
        return 'No JSON data received', 400
    
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
            errors = bq_client.insert_rows_json(table_id, [row])
        
        else:
            return f"Unknown trade update type: {update_type}", 400
            
    else:
        return f"Unknown data type: {data_type}", 400
    
    if errors:
        return f"Errors inserting data: {errors}", 500
    
    return "Data inserted successfully", 200


# For Pub/Sub triggered functions
def process_mt5_pubsub(event, context):
    """Cloud Function to process MT5 WebSocket data published to Pub/Sub
    
    Args:
        event (dict): The dictionary with data specific to this type of event.
                      The `data` field contains the PubsubMessage message.
        context (google.cloud.functions.Context): The Cloud Functions event
                                                  metadata.
    """
    pubsub_message = base64.b64decode(event['data']).decode('utf-8')
    data = json.loads(pubsub_message)
    
    # Process the data using the same logic as the HTTP function
    data_type = data.get('type')
    
    if data_type == 'price_update':
        # Process price update
        table_id = f"{bq_client.project}.{BQ_DATASET}.{BQ_PRICES_TABLE}"
        row = {
            "timestamp": data.get('timestamp'),
            "symbol": data.get('symbol'),
            "bid": data.get('bid'),
            "ask": data.get('ask'),
            "spread": data.get('spread')
        }
        errors = bq_client.insert_rows_json(table_id, [row])
        
    elif data_type == 'trade_update':
        # Process trade update
        update_type = data.get('update_type')
        
        if update_type == 'position':
            # Process position update
            table_id = f"{bq_client.project}.{BQ_DATASET}.{BQ_POSITIONS_TABLE}"
            row = {
                "timestamp": data.get('timestamp'),
                "trade_id": data.get('trade_id'),
                "symbol": data.get('symbol'),
                "type": data.get('type'),
                "volume": data.get('volume'),
                "price": data.get('price'),
                "profit": data.get('profit'),
                "sl": data.get('sl'),
                "tp": data.get('tp')
            }
            errors = bq_client.insert_rows_json(table_id, [row])
            
        elif update_type == 'transaction':
            # Process transaction update
            table_id = f"{bq_client.project}.{BQ_DATASET}.{BQ_TRANSACTIONS_TABLE}"
            row = {
                "timestamp": data.get('timestamp'),
                "transaction_id": data.get('transaction_id'),
                "symbol": data.get('symbol'),
                "type": data.get('type'), 
                "volume": data.get('volume'),
                "price": data.get('price'),
                "commission": data.get('commission'),
                "swap": data.get('swap'),
                "profit": data.get('profit')
            }
            errors = bq_client.insert_rows_json(table_id, [row])