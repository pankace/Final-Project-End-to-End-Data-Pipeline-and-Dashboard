import logging
from src.config.settings import BQ_DATASET_ID, BQ_PRICES_TABLE

logger = logging.getLogger(__name__)

def process_price_update(data, bq_client):
    """
    Process a price update from MT5 and insert it into BigQuery.
    
    Args:
        data (dict): The price update data
        bq_client: BigQuery client instance
    
    Returns:
        str: Status message
    """
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
        table_id = f"{BQ_PRICES_TABLE}"
        row = {
            "timestamp": data["timestamp"],
            "symbol": data["symbol"],
            "bid": data["bid"],
            "ask": data["ask"],
            "spread": data["spread"]
        }
        
        # Insert data into BigQuery
        errors = bq_client.insert_rows(table_id, [row])
        
        if errors:
            logger.error(f"Error inserting price data: {errors}")
            return f"Error inserting data: {errors}"
        
        logger.info(f"Successfully inserted price data for {data['symbol']}")
        return "Price data inserted successfully"
        
    except Exception as e:
        logger.error(f"Error processing price update: {e}", exc_info=True)
        raise f"Error: {str(e)}"  