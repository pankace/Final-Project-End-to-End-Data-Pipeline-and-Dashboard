import json
from google.cloud import bigquery

# Initialize the BigQuery client
bq_client = bigquery.Client()

# Define BigQuery dataset and table names
BQ_DATASET = "mt5_trading"
BQ_TRANSACTIONS_TABLE = "transactions"

def process_trade_update(request_json):
    """Process trade update data and insert into BigQuery.

    Args:
        request_json (dict): The JSON data received from the request.
    
    Returns:
        str: Success or error message.
    """
    update_type = request_json.get('update_type')
    
    if update_type == 'position':
        # Process position update
        table_id = f"{bq_client.project}.{BQ_DATASET}.{BQ_TRANSACTIONS_TABLE}"
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
    
    if errors:
        return f"Errors inserting data: {errors}", 500
    
    return "Trade data inserted successfully", 200