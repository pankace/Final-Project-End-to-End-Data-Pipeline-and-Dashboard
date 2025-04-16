import json
from google.cloud import bigquery

class PriceProcessor:
    def __init__(self, bq_client):
        self.bq_client = bq_client
        self.dataset = "mt5_trading"
        self.table = "price_updates"

    def validate_price_data(self, data):
        required_fields = ['timestamp', 'symbol', 'bid', 'ask', 'spread']
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")

    def transform_price_data(self, data):
        return {
            "timestamp": data['timestamp'],
            "symbol": data['symbol'],
            "bid": data['bid'],
            "ask": data['ask'],
            "spread": data['spread']
        }

    def process_price_update(self, price_data):
        self.validate_price_data(price_data)
        transformed_data = self.transform_price_data(price_data)
        table_id = f"{self.bq_client.project}.{self.dataset}.{self.table}"
        errors = self.bq_client.insert_rows_json(table_id, [transformed_data])
        
        if errors:
            raise Exception(f"Errors inserting data: {errors}")
        
        return "Price data inserted successfully"