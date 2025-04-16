import os
import json
import functions_framework
from flask import jsonify
from google.cloud import bigquery

# Initialize BigQuery client
bq_client = bigquery.Client()

# Define BigQuery dataset and table names
BQ_DATASET = os.environ.get("BQ_DATASET", "mt5_trading")
BQ_POSITIONS_TABLE = os.environ.get("BQ_POSITIONS_TABLE", "positions")
BQ_TRANSACTIONS_TABLE = os.environ.get("BQ_TRANSACTIONS_TABLE", "transactions")
BQ_PRICES_TABLE = os.environ.get("BQ_PRICES_TABLE", "price_updates")

@functions_framework.http
def receive_message(request):
    """HTTP Cloud Function that receives MT5 data and inserts into BigQuery."""
    try:
        request_json = request.get_json(silent=True)
        
        if not request_json:
            return jsonify({'error': 'No JSON data provided'}), 400
        
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
                return jsonify({'error': f'Unknown trade update type: {update_type}'}), 400
        else:
            return jsonify({'error': f'Unknown data type: {data_type}'}), 400
            
        if errors:
            return jsonify({'error': f'Errors inserting data: {errors}'}), 500
            
        return jsonify({'success': True, 'message': 'Data inserted successfully'})
            
    except Exception as e:
        return jsonify({'error': f'Error processing request: {str(e)}'}), 500