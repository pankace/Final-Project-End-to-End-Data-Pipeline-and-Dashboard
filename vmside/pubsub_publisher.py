import asyncio
import json
import logging
import websockets
import argparse
import os
from google.cloud import pubsub_v1
from dotenv import load_dotenv
import time
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO, 
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

class MT5PubSubPublisher:
    """Connects to MT5 WebSocket server and publishes data to Google Cloud Pub/Sub"""
    
    def __init__(self, websocket_url, project_id, topic_name, symbols=None):
        """
        Initialize the publisher
        
        Args:
            websocket_url: URL of the MT5 WebSocket server
            project_id: Google Cloud project ID
            topic_name: Pub/Sub topic name
            symbols: List of symbols to subscribe to
        """
        self.websocket_url = websocket_url
        self.project_id = project_id
        self.topic_name = topic_name
        self.symbols = symbols or ["EURUSD", "GBPUSD", "USDJPY", "XAUUSD"]
        self.publisher = None
        self.topic_path = None
        self.running = False
        self.reconnect_delay = 5  # seconds
        
    def setup_publisher(self):
        """Set up the Pub/Sub publisher client"""
        try:
            self.publisher = pubsub_v1.PublisherClient()
            self.topic_path = self.publisher.topic_path(self.project_id, self.topic_name)
            logger.info(f"Pub/Sub publisher initialized for topic: {self.topic_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Pub/Sub publisher: {e}")
            return False
        
    async def publish_message(self, message):
        """Publish a message to Pub/Sub"""
        try:
            # Convert message to JSON string and encode as bytes
            data = json.dumps(message).encode("utf-8")
            
            # Publish the message
            future = self.publisher.publish(self.topic_path, data)
            
            # Log after successful publish
            msg_id = await asyncio.wrap_future(future)
            logger.info(f"Published message {msg_id} for {message.get('type')} - {message.get('symbol', '')}")
            return True
        except Exception as e:
            logger.error(f"Error publishing message: {e}")
            return False
        
    async def connect_and_publish(self):
        """Connect to MT5 WebSocket server and publish messages to Pub/Sub"""
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
                            
                            # Log message type for debugging
                            msg_type = data.get("type", "unknown")
                            
                            # Only publish price_update and trade_update messages
                            if msg_type in ["price_update", "trade_update"]:
                                await self.publish_message(data)
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
                
    def stop(self):
        """Stop the publisher"""
        logger.info("Stopping MT5 PubSub publisher...")
        self.running = False

async def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="MT5 WebSocket to Pub/Sub Publisher")
    parser.add_argument("--url", default="ws://localhost:8765", 
                       help="WebSocket URL of the MT5 server")
    parser.add_argument("--project", default=os.getenv("GOOGLE_CLOUD_PROJECT"),
                       help="Google Cloud project ID")
    parser.add_argument("--topic", default="mt5-trading-topic",
                       help="Pub/Sub topic name")
    parser.add_argument("--symbols", default="EURUSD,GBPUSD,USDJPY,XAUUSD",
                       help="Comma-separated list of symbols to subscribe to")
    
    args = parser.parse_args()
    
    # Convert symbols string to list
    symbols = args.symbols.split(",")
    
    # Create and start the publisher
    publisher = MT5PubSubPublisher(
        websocket_url=args.url,
        project_id=args.project,
        topic_name=args.topic,
        symbols=symbols
    )
    
    # Set up the Pub/Sub publisher
    if not publisher.setup_publisher():
        logger.error("Failed to set up Pub/Sub publisher. Exiting.")
        return
    
    try:
        # Register cleanup handler
        import signal
        def signal_handler(sig, frame):
            logger.info("Received shutdown signal")
            publisher.stop()
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Start the publisher
        logger.info(f"Starting MT5 PubSub publisher for symbols: {symbols}")
        await publisher.connect_and_publish()
        
    except KeyboardInterrupt:
        logger.info("Publisher stopped by user")
        publisher.stop()

if __name__ == "__main__":
    asyncio.run(main())