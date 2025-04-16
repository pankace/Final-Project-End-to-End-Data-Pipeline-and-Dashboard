import pytest
from src.processors.price_processor import process_price_update
from src.processors.trade_processor import process_trade_update

def test_process_price_update(mocker):
    mock_request = {
        "timestamp": "2023-01-01T00:00:00Z",
        "symbol": "EURUSD",
        "bid": 1.1234,
        "ask": 1.1236,
        "spread": 2
    }
    
    mock_insert_rows_json = mocker.patch('src.connectors.bigquery_client.bq_client.insert_rows_json')
    
    response = process_price_update(mock_request)
    
    assert response == "Data inserted successfully"
    mock_insert_rows_json.assert_called_once()

def test_process_trade_update_position(mocker):
    mock_request = {
        "timestamp": "2023-01-01T00:00:00Z",
        "update_type": "position",
        "trade_id": "12345",
        "symbol": "EURUSD",
        "type": "buy",
        "volume": 1.0,
        "price": 1.1234,
        "profit": 10.0,
        "sl": 1.1200,
        "tp": 1.1300
    }
    
    mock_insert_rows_json = mocker.patch('src.connectors.bigquery_client.bq_client.insert_rows_json')
    
    response = process_trade_update(mock_request)
    
    assert response == "Data inserted successfully"
    mock_insert_rows_json.assert_called_once()

def test_process_trade_update_transaction(mocker):
    mock_request = {
        "timestamp": "2023-01-01T00:00:00Z",
        "update_type": "transaction",
        "transaction_id": "54321",
        "symbol": "EURUSD",
        "type": "buy",
        "volume": 1.0,
        "price": 1.1234,
        "commission": 0.5,
        "swap": 0.1,
        "profit": 10.0
    }
    
    mock_insert_rows_json = mocker.patch('src.connectors.bigquery_client.bq_client.insert_rows_json')
    
    response = process_trade_update(mock_request)
    
    assert response == "Data inserted successfully"
    mock_insert_rows_json.assert_called_once()