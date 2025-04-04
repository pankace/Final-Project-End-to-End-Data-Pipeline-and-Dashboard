import asyncio
import os
import logging
import signal
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
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

# Global variable to hold our client
client = None
client_thread = None
is_running = False

# Simple HTTP request handler to satisfy Cloud Run
class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        status_message = "MT5 WebSocket client is running" if is_running else "MT5 WebSocket client is starting..."
        self.send_response(200)
        self.send_header('Content-Type', 'text/plain')
        self.end_headers()
        self.wfile.write(status_message.encode())
        logger.info(f"Received HTTP request, client status: {status_message}")

def start_http_server():
    port = int(os.environ.get('PORT', 8080))
    server_address = ('', port)
    httpd = HTTPServer(server_address, SimpleHTTPRequestHandler)
    logger.info(f'Starting HTTP server on port {port}')
    httpd.serve_forever()

async def websocket_client_loop():
    global client, is_running
    
    # Initialize storage handler
    if STORAGE_TYPE == "gcs":
        storage_handler = StorageHandler(
            storage_type='gcs', 
            bucket_name=GCS_BUCKET_NAME
        )
    else:
        storage_handler = StorageHandler(
            storage_type='bigquery', 
            dataset_id=BQ_DATASET_ID,
            table_id=BQ_TABLE_ID
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
        if client:
            client.stop()
        
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Run the client
    is_running = True
    await client.connect()
    is_running = False

def main():
    # Start HTTP server in a separate thread
    http_thread = threading.Thread(target=start_http_server, daemon=True)
    http_thread.start()
    
    # Start WebSocket client in the main thread
    asyncio.run(websocket_client_loop())

if __name__ == "__main__":
    main()