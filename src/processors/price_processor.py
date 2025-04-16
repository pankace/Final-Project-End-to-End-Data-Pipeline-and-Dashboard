import logging
import os

# Import settings correctly (no src. prefix)
from config.settings import BQ_PRICES_TABLE

logger = logging.getLogger(__name__)

def process_price_update(data, bq_client):
    """Process price update data from MT5"""
    try:
        # Validate required fields
        required_fields = ["timestamp", "symbol", "bid", "ask"]
        for field in required_fields:
            if field not in data:
                logger.error(f"Missing required field: {field}")
                return f"Missing required field: {field}"
        
        # Calculate spread if not provided
        if "spread" not in data:
            data["spread"] = data["ask"] - data["bid"]
        
        # Create row for BigQuery
        row = {
            "timestamp": data["timestamp"],
            "symbol": data["symbol"],
            "bid": data["bid"],
            "ask": data["ask"],
            "spread": data["spread"]
        }
        
        # Insert data into BigQuery
        errors = bq_client.insert_rows(BQ_PRICES_TABLE, [row])
        
        if errors:
            logger.error(f"Error inserting price data: {errors}")
            return f"Error inserting data: {errors}"
        
        logger.info(f"Successfully inserted price data for {data['symbol']}")
        return "Data inserted successfully"
        
    except Exception as e:
        logger.error(f"Error processing price update: {e}")
        return f"Error: {str(e)}"