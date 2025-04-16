import logging
from src.config.settings import BQ_DATASET_ID, BQ_POSITIONS_TABLE, BQ_TRANSACTIONS_TABLE

logger = logging.getLogger(__name__)

def process_trade_update(data, bq_client):
    """
    Process a trade update from MT5 and insert it into BigQuery.
    
    Args:
        data (dict): The trade update data
        bq_client: BigQuery client instance
    
    Returns:
        str: Status message
    """
    try:
        # Get update type
        update_type = data.get("update_type")
        
        if not update_type:
            logger.error("Missing update_type in trade data")
            return "Missing update_type in trade data"
            
        if update_type == "position":
            # Process position update
            table_id = f"{BQ_POSITIONS_TABLE}" 
            
            # Validate required fields
            required_fields = ["timestamp", "trade_id", "symbol", "type", "volume", "price", "profit"]
            for field in required_fields:
                if field not in data:
                    logger.error(f"Missing required field for position: {field}")
                    return f"Missing required field: {field}"
            
            # Create row for BigQuery
            row = {
                "timestamp": data["timestamp"],
                "trade_id": data["trade_id"],
                "symbol": data["symbol"],
                "type": data["type"],
                "volume": data["volume"],
                "price": data["price"],
                "profit": data["profit"],
                "sl": data.get("sl", 0.0),  # Optional fields
                "tp": data.get("tp", 0.0)
            }
            
        elif update_type == "transaction":
            # Process transaction update
            table_id = f"{BQ_TRANSACTIONS_TABLE}"
            
            # Validate required fields
            required_fields = ["timestamp", "transaction_id", "symbol", "type", "volume", "price", "profit"]
            for field in required_fields:
                if field not in data:
                    logger.error(f"Missing required field for transaction: {field}")
                    return f"Missing required field: {field}"
            
            # Create row for BigQuery
            row = {
                "timestamp": data["timestamp"],
                "transaction_id": data["transaction_id"],
                "symbol": data["symbol"],
                "type": data["type"],
                "volume": data["volume"],
                "price": data["price"],
                "commission": data.get("commission", 0.0),
                "swap": data.get("swap", 0.0),
                "profit": data["profit"]
            }
            
        else:
            logger.error(f"Unknown trade update type: {update_type}")
            return f"Unknown trade update type: {update_type}"
            
        # Insert data into BigQuery
        errors = bq_client.insert_rows(table_id, [row])
        
        if errors:
            logger.error(f"Error inserting trade data: {errors}")
            return f"Error inserting data: {errors}"
        
        logger.info(f"Successfully inserted {update_type} data")
        return "Trade data inserted successfully"
        
    except Exception as e:
        logger.error(f"Error processing trade update: {e}", exc_info=True)
        raise