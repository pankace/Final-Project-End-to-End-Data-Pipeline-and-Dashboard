import asyncio
import json
import logging
import websockets
import argparse
import os
import requests
from datetime import datetime
from dotenv import load_dotenv
import time
import backoff

# Configure logging
logging.basicConfig(
    level=logging.INFO, 
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

class MT5CloudFunctionClient:
    """Connects to MT5 WebSocket server and forwards data to Google Cloud Function"""
    
    def __init__(self, websocket_url, cloud_function_url, symbols=None, retry_max_attempts=5):
        """
        Initialize the client
        
        Args:
            websocket_url: URL of the MT5 WebSocket server
            cloud_function_url: URL of the Google Cloud Function endpoint
            symbols: List of symbols to subscribe to
            retry_max_attempts: Maximum number of retry attempts for HTTP requests
        """
        self.websocket_url = websocket_url
        self.cloud_function_url = cloud_function_url
        self.symbols = symbols or ["EURUSD", "GBPUSD", "USDJPY", "XAUUSD"]
        self.retry_max_attempts = retry_max_attempts
        self.running = False
        self.reconnect_delay = 5  # seconds
        self.session = requests.Session()
        self.stats = {
            "messages_received": 0,
            "messages_sent": 0,
            "errors": 0,
            "start_time": datetime.now()
        }
        
    @backoff.on_exception(
        backoff.expo,
        (requests.exceptions.RequestException),
        max_tries=5,
        giveup=lambda e: isinstance(e, requests.exceptions.HTTPError) and e.response.status_code < 500
    )
    async def send_to_cloud_function(self, message):
        """Send a message to the Cloud Function with retry logic"""
        try:
            # Convert message to JSON string
            headers = {'Content-Type': 'application/json'}
            
            # Use asyncio to run the HTTP request in a thread pool
            loop = asyncio.get_running_loop()
            response = await loop.run_in_executor(
                None, 
                lambda: self.session.post(
                    self.cloud_function_url, 
                    data=json.dumps(message), 
                    headers=headers,
                    timeout=10  # 10 second timeout
                )
            )
            
            response.raise_for_status()  # Raise exception for 4XX/5XX responses
            
            # Update stats on success
            self.stats["messages_sent"] += 1
            
            # Log periodically but not too often
            if self.stats["messages_sent"] % 100 == 0:
                logger.info(f"Successfully sent {self.stats['messages_sent']} messages to cloud function")
                
            return True
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error sending to cloud function: {e} - Status code: {e.response.status_code}")
            self.stats["errors"] += 1
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f"Error sending to cloud function: {e}")
            self.stats["errors"] += 1
            raise
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            self.stats["errors"] += 1
            return False
        
    async def connect_and_forward(self):
        """Connect to MT5 WebSocket server and forward messages to Cloud Function"""
        self.running = True
        
        while self.running:
            try:
                logger.info(f"Connecting to WebSocket server at {self.websocket_url}")
                async with websockets.connect(self.websocket_url) as websocket:
                    # Subscribe to symbols and trade updates
                    subscription = {
                        "type": "subscription",
                        "action": "subscribe",
                        "symbols": self.symbols,
                        "include_trades": True
                    }
                    await websocket.send(json.dumps(subscription))
                    logger.info(f"Subscription request sent for symbols: {self.symbols}")
                    
                    # Process incoming messages
                    while self.running:
                        try:
                            message = await websocket.recv()
                            data = json.loads(message)
                            
                            # Update stats
                            self.stats["messages_received"] += 1
                            
                            # Log message type for debugging
                            msg_type = data.get("type", "unknown")
                            
                            # Only forward price_update and trade_update messages to cloud function
                            if msg_type in ["price_update", "trade_update"]:
                                await self.send_to_cloud_function(data)
                            elif msg_type == "subscription_confirmation":
                                logger.info(f"Successfully subscribed to {data.get('symbols')}")
                            elif msg_type == "error":
                                logger.error(f"WebSocket server error: {data.get('message')}")
                                
                            # Send heartbeat to keep connection alive
                            if time.time() % 30 < 1:
                                await websocket.send(json.dumps({"type": "ping"}))
                                
                        except asyncio.CancelledError:
                            break
                        except json.JSONDecodeError:
                            logger.error("Received invalid JSON from WebSocket")
                        except Exception as e:
                            logger.error(f"Error processing WebSocket message: {e}")
                            break
                            
            except websockets.exceptions.ConnectionClosed:
                logger.warning("WebSocket connection closed")
            except Exception as e:
                logger.error(f"WebSocket connection error: {e}")
                
            if self.running:
                logger.info(f"Reconnecting in {self.reconnect_delay} seconds...")
                await asyncio.sleep(self.reconnect_delay)
                
    def print_stats(self):
        """Print statistics about processed messages"""
        runtime = datetime.now() - self.stats["start_time"]
        runtime_seconds = runtime.total_seconds()
        
        if runtime_seconds > 0:
            msgs_per_second = self.stats["messages_sent"] / runtime_seconds
        else:
            msgs_per_second = 0
            
        logger.info("=" * 40)
        logger.info("MT5 Cloud Function Client Statistics")
        logger.info("=" * 40)
        logger.info(f"Runtime: {runtime}")
        logger.info(f"Messages received: {self.stats['messages_received']}")
        logger.info(f"Messages sent: {self.stats['messages_sent']}")
        logger.info(f"Errors: {self.stats['errors']}")
        logger.info(f"Messages per second: {msgs_per_second:.2f}")
        logger.info("=" * 40)
                
    def stop(self):
        """Stop the client"""
        logger.info("Stopping MT5 Cloud Function client...")
        self.running = False
        self.print_stats()

async def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="MT5 WebSocket to Cloud Function Client")
    parser.add_argument("--ws-url", default=os.getenv("MT5_WS_URL", "ws://localhost:8765"), 
                       help="WebSocket URL of the MT5 server")
    parser.add_argument("--cf-url", default=os.getenv("CLOUD_FUNCTION_URL"),
                       help="URL of the deployed Cloud Function")
    parser.add_argument("--symbols", default=os.getenv("MT5_SYMBOLS", "EURUSD,GBPUSD,USDJPY,XAUUSD"),
                       help="Comma-separated list of symbols to subscribe to")
    
    args = parser.parse_args()
    
    if not args.cf_url:
        logger.error("Cloud Function URL is required. Set CLOUD_FUNCTION_URL environment variable or use --cf-url.")
        return
    
    # Convert symbols string to list
    symbols = args.symbols.split(",")
    
    # Create and start the client
    client = MT5CloudFunctionClient(
        websocket_url=args.ws_url,
        cloud_function_url=args.cf_url,
        symbols=symbols
    )
    
    try:
        # Register cleanup handler
        import signal
        def signal_handler(sig, frame):
            logger.info("Received shutdown signal")
            client.stop()
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Start the client
        logger.info(f"Starting MT5 Cloud Function client")
        logger.info(f"WebSocket URL: {args.ws_url}")
        logger.info(f"Cloud Function URL: {args.cf_url}")
        logger.info(f"Symbols: {symbols}")
        await client.connect_and_forward()
        
    except KeyboardInterrupt:
        logger.info("Client stopped by user")
        client.stop()

if __name__ == "__main__":
    asyncio.run(main())