import json
from flask import Request
from connectors.bigquery_client import BigQueryClient
from processors.price_processor import PriceProcessor
from processors.trade_processor import TradeProcessor

# Initialize the BigQuery client
bq_client = BigQueryClient()

def process_mt5_data(request: Request):
    """Cloud Function to process MT5 WebSocket data and insert into BigQuery
    
    Args:
        request (flask.Request): The request object
    Returns:
        The response text, or any set of values that can be turned into a
        Response object using `make_response`
    """
    request_json = request.get_json(silent=True)
    
    if not request_json:
        return 'No JSON data received', 400
    
    data_type = request_json.get('type')
    
    if data_type == 'price_update':
        processor = PriceProcessor(bq_client)
        response = processor.process_price_update(request_json)
        
    elif data_type == 'trade_update':
        processor = TradeProcessor(bq_client)
        response = processor.process_trade_update(request_json)
        
    else:
        return f"Unknown data type: {data_type}", 400
    
    return response