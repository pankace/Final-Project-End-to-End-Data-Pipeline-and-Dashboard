import os
import signal
import asyncio
import json
import websockets
from datetime import datetime
from dotenv import load_dotenv
from utils.logging import logger
from utils.storage import save_to_csv, save_to_gcs, save_to_bigquery

# Load environment variables
load_dotenv()

# Configuration from environment variables
MT5_SERVER_URL = os.getenv("MT5_SERVER_URL")
FOREX_SYMBOLS = os.getenv("FOREX_SYMBOLS", "EURUSD,GBPUSD,USDJPY").split(',')
CSV_FILE_PATH = os.getenv("CSV_FILE_PATH", "/tmp/forex_data")
GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME")
STORAGE_TYPE = os.getenv("STORAGE_TYPE", "csv").lower()  # 'csv', 'gcs', or 'bigquery'
BQ_DATASET_ID = os.getenv("BQ_DATASET_ID")
BQ_TABLE_ID = os.getenv("BQ_TABLE_ID", "forex_prices")

# Flag to control the running state
running = True

def handle_sigterm(sig, frame):
    """Handle termination signals gracefully"""
    global running
    logger.info("Received termination signal. Starting graceful shutdown...")
    running = False

# Register signal handlers
signal.signal(signal.SIGINT, handle_sigterm)
signal.signal(signal.SIGTERM, handle_sigterm)

async def subscribe_to_symbols(websocket):
    """Subscribe to forex symbols"""
    subscription_message = {
        "type": "subscription",
        "action": "subscribe",
        "symbols": FOREX_SYMBOLS
    }
    await websocket.send(json.dumps(subscription_message))
    logger.info(f"Subscribed to symbols: {FOREX_SYMBOLS}")

async def process_price_update(data):
    """Process and store price update data"""
    symbol = data.get("symbol")
    timestamp = data.get("timestamp")
    bid = data.get("bid")
    ask = data.get("ask")
    spread = data.get("spread", ask-bid)
    
    if STORAGE_TYPE == "csv":
        # Create date-based filename
        today = datetime.now().strftime("%Y-%m-%d")
        filename = f"{CSV_FILE_PATH}/{symbol}_{today}.csv"
        save_to_csv([timestamp, symbol, bid, ask, spread], filename)
        logger.debug(f"Saved {symbol} price data to CSV")
    
    elif STORAGE_TYPE == "gcs" and GCS_BUCKET_NAME:
        # Format as CSV string for GCS
        csv_data = f"{timestamp},{symbol},{bid},{ask},{spread}\n"
        # Use date-based path for organization
        destination_blob = f"forex_data/{symbol}/{datetime.now().strftime('%Y/%m/%d')}/{symbol}_{datetime.now().strftime('%H%M%S')}.csv"
        save_to_gcs(csv_data, GCS_BUCKET_NAME, destination_blob)
        logger.debug(f"Saved {symbol} price data to GCS bucket {GCS_BUCKET_NAME}")
    
    elif STORAGE_TYPE == "bigquery" and BQ_DATASET_ID:
        # Prepare data for BigQuery
        bq_record = {
            "timestamp": timestamp,
            "symbol": symbol,
            "bid": bid,
            "ask": ask,
            "spread": spread
        }
        save_to_bigquery(bq_record, BQ_DATASET_ID, f"{BQ_TABLE_ID}_{symbol.lower()}")
        logger.debug(f"Saved {symbol} price data to BigQuery {BQ_DATASET_ID}.{BQ_TABLE_ID}_{symbol.lower()}")

async def connect_to_mt5_server():
    """Connect to the MT5 WebSocket server and handle price updates"""
    global running
    reconnect_delay = 5  # Initial reconnect delay in seconds
    max_reconnect_delay = 60  # Maximum reconnect delay
    
    logger.info(f"Starting MT5 WebSocket client, connecting to {MT5_SERVER_URL}")
    logger.info(f"Using {STORAGE_TYPE} storage type")
    
    while running:
        try:
            async with websockets.connect(MT5_SERVER_URL) as websocket:
                # Reset reconnect delay on successful connection
                reconnect_delay = 5
                
                logger.info("Connected to MT5 WebSocket server")
                
                # Subscribe to symbols
                await subscribe_to_symbols(websocket)
                
                # Process messages while connection is active
                while running:
                    try:
                        # Use a timeout to allow checking the running flag
                        message = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                        data = json.loads(message)
                        
                        # Handle different types of messages
                        if data.get("type") == "price_update":
                            await process_price_update(data)
                        elif data.get("type") == "subscription_confirmation":
                            logger.info(f"Subscription confirmed for: {data.get('symbols')}")
                        elif data.get("type") == "error":
                            logger.error(f"Server error: {data.get('message')}")
                        else:
                            logger.debug(f"Received other message: {data}")
                            
                    except asyncio.TimeoutError:
                        # This allows checking the running flag periodically
                        continue
                    except websockets.exceptions.ConnectionClosed:
                        logger.warning("WebSocket connection closed")
                        break
                    except Exception as e:
                        logger.error(f"Error processing message: {str(e)}")
                        break
                
                # If we're stopping cleanly, send unsubscribe message
                if running is False:
                    try:
                        unsubscribe_message = {
                            "type": "subscription",
                            "action": "unsubscribe",
                            "symbols": FOREX_SYMBOLS
                        }
                        await websocket.send(json.dumps(unsubscribe_message))
                        logger.info("Unsubscribed from symbols")
                    except:
                        pass  # Ignore errors during shutdown
        
        except websockets.exceptions.ConnectionClosed as e:
            logger.error(f"WebSocket connection closed: {e}")
        except Exception as e:
            logger.error(f"Connection error: {str(e)}")
            
        # If we're supposed to keep running, attempt to reconnect
        if running:
            logger.info(f"Reconnecting in {reconnect_delay} seconds...")
            await asyncio.sleep(reconnect_delay)
            # Implement exponential backoff with maximum value
            reconnect_delay = min(reconnect_delay * 1.5, max_reconnect_delay)
        else:
            logger.info("Client is shutting down")

async def main():
    """Main entry point for the application"""
    try:
        # Create directory for CSV files if needed
        if STORAGE_TYPE == "csv":
            os.makedirs(CSV_FILE_PATH, exist_ok=True)
            
        # Validate required environment variables
        if STORAGE_TYPE == "gcs" and not GCS_BUCKET_NAME:
            logger.error("GCS_BUCKET_NAME is required when STORAGE_TYPE is 'gcs'")
            return
            
        if STORAGE_TYPE == "bigquery" and not BQ_DATASET_ID:
            logger.error("BQ_DATASET_ID is required when STORAGE_TYPE is 'bigquery'")
            return
            
        # Start the client
        await connect_to_mt5_server()
    except Exception as e:
        logger.error(f"Unhandled exception: {str(e)}")
    finally:
        logger.info("MT5 WebSocket client shutdown complete")

if __name__ == "__main__":
    asyncio.run(main())