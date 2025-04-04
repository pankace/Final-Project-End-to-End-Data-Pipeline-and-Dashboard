import asyncio
import json
import logging
import websockets
import argparse
import os
from datetime import datetime
from typing import Dict, List, Set
import time
import threading
from dotenv import load_dotenv
import asyncio
import json
import logging
import websockets
import argparse
import os
from datetime import datetime
from typing import Dict, List, Set
import time
import threading
from dotenv import load_dotenv

# Fix the .env file loading by specifying the exact path
current_dir = os.path.dirname(os.path.abspath(__file__))
dotenv_path = os.path.join(current_dir, '.env')
load_dotenv(dotenv_path=dotenv_path)

# Import your MT5 classes
from mt5_base import MT5Base, SymbolPrice
from mt5_trading import MT5Trading
# Import your MT5 classes
from mt5_base import MT5Base, SymbolPrice
from mt5_trading import MT5Trading

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    filename="mt5_websocket_server.log",
    filemode="a"
)
logger = logging.getLogger(__name__)

# Add console handler for real-time monitoring
console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console.setFormatter(formatter)
logger.addHandler(console)

class MT5WebSocketServer:
    def __init__(self, host: str = "0.0.0.0", port: int = 8765, update_interval: int = 1):
        """
        Initialize the MT5 WebSocket Server
        
        Args:
            host: Host address to bind the server to (0.0.0.0 allows external connections)
            port: Port number for the WebSocket server
            update_interval: Time in seconds between price updates
        """
        self.host = host
        self.port = port
        self.update_interval = update_interval
        
        # Load environment variables for MT5 credentials
        load_dotenv()
        
        # Initialize MT5 client with credentials from environment variables
        self.mt5_client = MT5Trading(
            user=int(os.getenv("MT5_USER")),
            password=os.getenv("MT5_PASSWORD"),
            server=os.getenv("MT5_SERVER"), 
            path=os.getenv("MT5_PATH")
        )
        
        self.connected_clients: Set = set()
        self.watched_symbols: Dict[str, Set] = {}
        self.running = False
        self.price_update_task = None

    async def register_client(self, websocket):
        """Register a new client connection"""
        self.connected_clients.add(websocket)
        logger.info(f"Client connected. Total clients: {len(self.connected_clients)}")
        
    async def unregister_client(self, websocket):
        """Unregister a client connection"""
        self.connected_clients.remove(websocket)
        
        # Remove client from all watched symbols
        for symbol in list(self.watched_symbols.keys()):
            if websocket in self.watched_symbols[symbol]:
                self.watched_symbols[symbol].remove(websocket)
                
            # Clean up empty symbol subscriptions
            if not self.watched_symbols[symbol]:
                del self.watched_symbols[symbol]
                
        logger.info(f"Client disconnected. Total clients: {len(self.connected_clients)}")

    async def handle_subscription(self, websocket, message: Dict):
        """Handle subscription requests from clients"""
        action = message.get("action")
        symbols = message.get("symbols", [])
        
        if not symbols or not isinstance(symbols, list):
            await websocket.send(json.dumps({
                "type": "error",
                "message": "Invalid symbols format. Expected a list."
            }))
            return
            
        if action == "subscribe":
            # Add client to each symbol's subscription list
            for symbol in symbols:
                if symbol not in self.watched_symbols:
                    self.watched_symbols[symbol] = set()
                self.watched_symbols[symbol].add(websocket)
                
            logger.info(f"Client subscribed to: {symbols}. Total watched symbols: {len(self.watched_symbols)}")
            
            # Send confirmation
            await websocket.send(json.dumps({
                "type": "subscription_confirmation",
                "symbols": symbols,
                "message": "Successfully subscribed"
            }))
            
        elif action == "unsubscribe":
            # Remove client from each symbol's subscription list
            for symbol in symbols:
                if symbol in self.watched_symbols and websocket in self.watched_symbols[symbol]:
                    self.watched_symbols[symbol].remove(websocket)
                    
                    # Clean up empty symbol subscriptions
                    if not self.watched_symbols[symbol]:
                        del self.watched_symbols[symbol]
            
            logger.info(f"Client unsubscribed from: {symbols}. Total watched symbols: {len(self.watched_symbols)}")
            
            # Send confirmation
            await websocket.send(json.dumps({
                "type": "unsubscription_confirmation",
                "symbols": symbols,
                "message": "Successfully unsubscribed"
            }))
        
        else:
            await websocket.send(json.dumps({
                "type": "error",
                "message": f"Unknown action: {action}"
            }))

    async def handle_client(self, websocket):
        """Handle client WebSocket connections"""
        await self.register_client(websocket)
        
        try:
            async for message in websocket:
                try:
                    data = json.loads(message)
                    message_type = data.get("type", "")
                    
                    if message_type == "subscription":
                        await self.handle_subscription(websocket, data)
                    elif message_type == "ping":
                        await websocket.send(json.dumps({"type": "pong", "time": datetime.now().isoformat()}))
                    else:
                        logger.warning(f"Unknown message type: {message_type}")
                        await websocket.send(json.dumps({
                            "type": "error",
                            "message": f"Unknown message type: {message_type}"
                        }))
                        
                except json.JSONDecodeError:
                    logger.warning("Received invalid JSON")
                    await websocket.send(json.dumps({
                        "type": "error",
                        "message": "Invalid JSON format"
                    }))
                    
        except websockets.exceptions.ConnectionClosed:
            logger.info("Connection closed")
        finally:
            await self.unregister_client(websocket)

    async def update_prices(self):
        """Fetch and broadcast price updates to subscribed clients"""
        while self.running:
            if not self.watched_symbols:
                await asyncio.sleep(self.update_interval)
                continue
                
            try:
                # Get all symbols that have at least one subscriber
                symbols_to_fetch = list(self.watched_symbols.keys())
                
                # Fetch prices from MT5
                prices = self.mt5_client.get_prices(symbols_to_fetch)
                
                timestamp = datetime.now().isoformat()
                
                # Send updates to each client based on their subscriptions
                for symbol, price_data in prices.items():
                    if symbol in self.watched_symbols:
                        price_update = {
                            "type": "price_update",
                            "symbol": symbol,
                            "bid": price_data.bid,
                            "ask": price_data.ask,
                            "spread": price_data.spread,
                            "timestamp": timestamp
                        }
                        
                        message = json.dumps(price_update)
                        
                        # Send to all clients subscribed to this symbol
                        for client in list(self.watched_symbols[symbol]):
                            try:
                                await client.send(message)
                            except Exception as e:
                                logger.error(f"Error sending to client: {e}")
                                # Client will be removed during next message handling
                
            except Exception as e:
                logger.error(f"Error updating prices: {e}")
                
            await asyncio.sleep(self.update_interval)

    async def start_server(self):
        """Start the WebSocket server"""
        self.running = True
        
        # Start price update task
        self.price_update_task = asyncio.create_task(self.update_prices())
        
        async with websockets.serve(self.handle_client, self.host, self.port):
            logger.info(f"MT5 WebSocket server started on {self.host}:{self.port}")
            await asyncio.Future()  # Run forever

    def stop_server(self):
        """Stop the WebSocket server"""
        self.running = False
        if self.price_update_task:
            self.price_update_task.cancel()
        logger.info("MT5 WebSocket server stopped")

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="MT5 WebSocket Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host address to bind to")
    parser.add_argument("--port", type=int, default=8765, help="Port to listen on")
    parser.add_argument("--interval", type=float, default=1.0, 
                        help="Price update interval in seconds")
    return parser.parse_args()

def display_connection_info():
    """Display connection information for users to connect to the server"""
    import socket
    try:
        # Get local IP address
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        
        logger.info("\n" + "="*60)
        logger.info("CONNECTION INFORMATION FOR CLIENTS")
        logger.info("="*60)
        logger.info(f"Local WebSocket URL: ws://{local_ip}:8765")
        logger.info("Example Python client connection:")
        logger.info('    client = MT5WebSocketClient("ws://' + local_ip + ':8765")')
        logger.info("="*60 + "\n")
    except:
        logger.info("Could not determine local IP address")

if __name__ == "__main__":
    args = parse_arguments()
    
    logger.info("Starting MT5 WebSocket Server")
    logger.info(f"Configuration: host={args.host}, port={args.port}, interval={args.interval}")
    
    # Display connection information
    display_connection_info()
    
    # Check if required environment variables are set
    if not os.getenv("MT5_USER") or not os.getenv("MT5_PASSWORD") or not os.getenv("MT5_SERVER") or not os.getenv("MT5_PATH"):
        logger.error("Missing required MT5 credentials in environment variables.")
        logger.error("Please ensure MT5_USER, MT5_PASSWORD, MT5_SERVER, and MT5_PATH are set in .env file")
        exit(1)
    
    server = MT5WebSocketServer(
        host=args.host,
        port=args.port,
        update_interval=args.interval
    )
    
    try:
        asyncio.run(server.start_server())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    finally:
        server.stop_server()