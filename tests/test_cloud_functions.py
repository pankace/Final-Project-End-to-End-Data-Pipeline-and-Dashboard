import json
import pytest
from unittest.mock import patch
from src.cloud_functions.http_function import process_mt5_data
from src.cloud_functions.pubsub_function import process_mt5_pubsub

def test_process_mt5_data_price_update():
    request = {
        "type": "price_update",
        "timestamp": "2023-01-01T00:00:00Z",
        "symbol": "EURUSD",
        "bid": 1.1234,
        "ask": 1.1236,
        "spread": 0.0002
    }
    
    with patch('src.cloud_functions.http_function.bq_client.insert_rows_json') as mock_insert:
        response = process_mt5_data(request)
        assert response == "Data inserted successfully", "Expected successful insertion response"
        mock_insert.assert_called_once()

def test_process_mt5_data_trade_update_position():
    request = {
        "type": "trade_update",
        "update_type": "position",
        "timestamp": "2023-01-01T00:00:00Z",
        "trade_id": "12345",
        "symbol": "EURUSD",
        "type": "buy",
        "volume": 1.0,
        "price": 1.1234,
        "profit": 10.0,
        "sl": 1.1200,
        "tp": 1.1300
    }
    
    with patch('src.cloud_functions.http_function.bq_client.insert_rows_json') as mock_insert:
        response = process_mt5_data(request)
        assert response == "Data inserted successfully", "Expected successful insertion response"
        mock_insert.assert_called_once()

def test_process_mt5_data_trade_update_transaction():
    request = {
        "type": "trade_update",
        "update_type": "transaction",
        "timestamp": "2023-01-01T00:00:00Z",
        "transaction_id": "54321",
        "symbol": "EURUSD",
        "type": "sell",
        "volume": 0.5,
        "price": 1.1234,
        "commission": 0.5,
        "swap": 0.1,
        "profit": -5.0
    }
    
    with patch('src.cloud_functions.http_function.bq_client.insert_rows_json') as mock_insert:
        response = process_mt5_data(request)
        assert response == "Data inserted successfully", "Expected successful insertion response"
        mock_insert.assert_called_once()

def test_process_mt5_pubsub():
    event = {
        'data': base64.b64encode(json.dumps({
            "type": "price_update",
            "timestamp": "2023-01-01T00:00:00Z",
            "symbol": "EURUSD",
            "bid": 1.1234,
            "ask": 1.1236,
            "spread": 0.0002
        }).encode('utf-8')).decode('utf-8')
    }
    context = {}
    
    with patch('src.cloud_functions.pubsub_function.bq_client.insert_rows_json') as mock_insert:
        response = process_mt5_pubsub(event, context)
        assert response == "Data inserted successfully", "Expected successful insertion response"
        mock_insert.assert_called_once()