import asyncio
import os
import logging
import signal
from websocket_client import MT5WebSocketClient
from storage_handler import StorageHandler

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Read configuration from environment variables with defaults
SERVER_URL = os.environ.get("MT5_SERVER_URL", "ws://34.87.87.53:8765")
SYMBOLS = os.environ.get("MT5_SYMBOLS", "XAUUSD").split(',')
STORAGE_TYPE = os.environ.get("STORAGE_TYPE", "gcs")  # gcs or bigquery
GCS_BUCKET_NAME = os.environ.get("GCS_BUCKET_NAME", "mt5-price-data")
BQ_DATASET_ID = os.environ.get("BQ_DATASET_ID", "mt5_data")
BQ_TABLE_ID = os.environ.get("BQ_TABLE_ID", "price_data")

async def main():
    # Initialize storage handler
    if STORAGE_TYPE == "gcs":
        storage_handler = StorageHandler(
            storage_type='gcs', 
            bucket_name=GCS_BUCKET_NAME
        )
    else:
        storage_handler = StorageHandler(
            storage_type='bigquery', 
            dataset_id=BQ_DATASET_ID
        )
    
    # Initialize client
    client = MT5WebSocketClient(
        server_url=SERVER_URL,
        symbols=SYMBOLS,
        storage_handler=storage_handler
    )
    
    # Setup signal handlers for graceful shutdown
    def signal_handler(sig, frame):
        logger.info("Received shutdown signal")
        client.stop()
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Run the client
    await client.connect()

def cloud_run_handler(request):
    """Entry point for Google Cloud Functions/Run"""
    asyncio.run(main())
    return "MT5 WebSocket service running"

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Service stopped by user")