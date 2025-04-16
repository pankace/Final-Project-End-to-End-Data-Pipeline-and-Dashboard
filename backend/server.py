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
from datetime import timedelta , datetime
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
from mt5_code.mt5_base import MT5Base, SymbolPrice
from mt5_code.mt5_trading import MT5Trading
# Import your MT5 classes
from mt5_code.mt5_base import MT5Base, SymbolPrice
from mt5_code.mt5_trading import MT5Trading

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

# Add to the existing imports
import time
import MetaTrader5 as mt5
from collections import defaultdict

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
        
        self.connected_clients = set()
        self.watched_symbols = {}  # Symbol to set of WebSocket clients
        self.trade_subscribers = set()  # Clients subscribed to trade updates
        self.running = False
        self.price_update_task = None
        self.trade_update_task = None
        
        # Store last known positions to detect changes
        self.last_positions = {}
        self.last_history_positions = {}
        self.last_deals = set()
    # Store trade history for new clients requesting missed data
        self.trade_history = {}
        self.transaction_history = {}
        
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
                
        # Remove from trade subscribers
        if websocket in self.trade_subscribers:
            self.trade_subscribers.remove(websocket)
                
        logger.info(f"Client disconnected. Total clients: {len(self.connected_clients)}")

    async def handle_subscription(self, websocket, message):
        """Handle subscription requests from clients"""
        action = message.get("action")
        symbols = message.get("symbols", [])
        include_trades = message.get("include_trades", False)
        last_trade_id = message.get("last_trade_id", 0)
        last_transaction_id = message.get("last_transaction_id", 0)

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

            # Add to trade subscribers if requested
            if include_trades:
                self.trade_subscribers.add(websocket)

                # If client provides last trade/transaction IDs, send missed updates
                if last_trade_id > 0 or last_transaction_id > 0:
                    logger.info(f"Client requesting missed trades since trade_id: {last_trade_id}, transaction_id: {last_transaction_id}")
                    await self.send_missed_trades(websocket, last_trade_id, last_transaction_id)

            logger.info(f"Client subscribed to: {symbols}. Total watched symbols: {len(self.watched_symbols)}")

            # Send confirmation
            await websocket.send(json.dumps({
                "type": "subscription_confirmation",
                "symbols": symbols,
                "trades_included": include_trades,
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

            # Remove from trade subscribers if explicitly specified
            if message.get("unsubscribe_trades", False) and websocket in self.trade_subscribers:
                self.trade_subscribers.remove(websocket)

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


    async def send_missed_trades(self, websocket, last_trade_id, last_transaction_id):
        """Send missed trades to a newly connected client"""
        try:
            # Connect to MT5 to get history
            with self.mt5_client.connection() as client:
                if not client:
                    logger.error("Could not connect to MT5 to retrieve missed trades")
                    return

                # Get current open positions
                positions = mt5.positions_get() or []
                current_positions = {p.ticket: p._asdict() for p in positions}

                # Send all current positions that the client hasn't seen yet
                for ticket, position in current_positions.items():
                    if int(ticket) > last_trade_id:
                        timestamp = datetime.now().isoformat()
                        update = {
                            "type": "trade_update",
                            "update_type": "position",
                            "timestamp": timestamp,
                            "trade_id": ticket,
                            "symbol": position['symbol'],
                            "type": "buy" if position['type'] == mt5.ORDER_TYPE_BUY else "sell",
                            "volume": position['volume'],
                            "price": position['price_open'],
                            "profit": position['profit'],
                            "sl": position['sl'],
                            "tp": position['tp']
                        }

                        try:
                            await websocket.send(json.dumps(update))
                            logger.info(f"Sent missed position update for trade_id: {ticket}")
                        except Exception as e:
                            logger.error(f"Error sending missed trade update: {e}")

                # Get recent history for transactions
                from_date = datetime.now() - timedelta(days=7)  # Get last week's history
                history_deals = mt5.history_deals_get(from_date, datetime.now()) or []

                # Keep track of sent deals to avoid duplicates
                sent_deals = set()

                # Send closed positions that the client hasn't seen yet
                for deal in history_deals:
                    if deal.entry == mt5.DEAL_ENTRY_OUT and deal.ticket > last_transaction_id:
                        if deal.ticket in sent_deals:
                            continue
                        
                        sent_deals.add(deal.ticket)
                        deal_dict = deal._asdict()

                        # Prepare transaction update
                        timestamp = datetime.fromtimestamp(deal_dict['time']).isoformat()
                        update = {
                            "type": "trade_update",
                            "update_type": "transaction",
                            "timestamp": timestamp,
                            "transaction_id": deal_dict['ticket'],
                            "symbol": deal_dict['symbol'],
                            "type": "close_buy" if deal_dict['type'] == mt5.DEAL_TYPE_SELL else "close_sell",
                            "volume": deal_dict['volume'],
                            "price": deal_dict['price'],
                            "commission": deal_dict['commission'],
                            "swap": deal_dict['swap'],
                            "profit": deal_dict['profit']
                        }

                        try:
                            await websocket.send(json.dumps(update))
                            logger.info(f"Sent missed transaction update for transaction_id: {deal_dict['ticket']}")
                        except Exception as e:
                            logger.error(f"Error sending missed transaction update: {e}")

                logger.info(f"Finished sending missed trade updates")

        except Exception as e:
            logger.error(f"Error retrieving missed trades: {e}")

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
            
    async def update_trades(self):
        """Fetch and broadcast trade updates to subscribed clients"""
        logger.info("Starting trade update task")

        # Store trades by ID for efficient lookups and history tracking
        trade_history = {}
        transaction_history = {}

        while self.running:
            if not self.trade_subscribers:
                await asyncio.sleep(self.update_interval)
                continue

            try:
                # Get current positions from MT5
                with self.mt5_client.connection() as client:
                    if not client:
                        await asyncio.sleep(self.update_interval)
                        logger.warning("MT5 client not connected")
                        continue
                    
                    # Get current open positions
                    positions = mt5.positions_get() or []
                    current_positions = {p.ticket: p._asdict() for p in positions}

                    # Check for new or updated positions
                    for ticket, position in current_positions.items():
                        # New position or position was updated
                        if ticket not in self.last_positions or position['profit'] != self.last_positions[ticket]['profit']:
                            logger.info(f"Position updated: {ticket}")

                            # Prepare position update
                            timestamp = datetime.now().isoformat()
                            update = {
                                "type": "trade_update",
                                "update_type": "position",
                                "timestamp": timestamp,
                                "trade_id": ticket,
                                "symbol": position['symbol'],
                                "type": "buy" if position['type'] == mt5.ORDER_TYPE_BUY else "sell",
                                "volume": position['volume'],
                                "price": position['price_open'],
                                "profit": position['profit'],
                                "sl": position['sl'],
                                "tp": position['tp']
                            }

                            # Store in our trade history for future reference
                            trade_history[ticket] = update

                            # Send to all trade subscribers
                            message = json.dumps(update)
                            subscribers = list(self.trade_subscribers)  # Create copy to avoid modification during iteration
                            for client in subscribers:
                                try:
                                    await client.send(message)
                                except Exception as e:
                                    logger.error(f"Error sending trade update to client: {e}")

                    # Check for closed positions
                    closed_positions = set(self.last_positions.keys()) - set(current_positions.keys())
                    for ticket in closed_positions:
                        # Position was closed, get from history
                        from_date = datetime.now() - timedelta(hours=24)  # Get last 24 hours
                        history_orders = mt5.history_orders_get(from_date, datetime.now()) or []
                        history_deals = mt5.history_deals_get(from_date, datetime.now()) or []

                        # Find the closed position in history
                        for deal in history_deals:
                            if deal.position_id == ticket and deal.entry == mt5.DEAL_ENTRY_OUT:
                                # This is a closing deal for our position
                                deal_dict = deal._asdict()

                                # Skip if already processed
                                if deal.ticket in self.last_deals:
                                    continue

                                # Add to processed deals
                                self.last_deals.add(deal.ticket)

                                # Prepare transaction update
                                timestamp = datetime.fromtimestamp(deal_dict['time']).isoformat()
                                update = {
                                    "type": "trade_update",
                                    "update_type": "transaction",
                                    "timestamp": timestamp,
                                    "transaction_id": deal_dict['ticket'],
                                    "symbol": deal_dict['symbol'],
                                    "type": "close_buy" if deal_dict['type'] == mt5.DEAL_TYPE_SELL else "close_sell",
                                    "volume": deal_dict['volume'],
                                    "price": deal_dict['price'],
                                    "commission": deal_dict['commission'],
                                    "swap": deal_dict['swap'],
                                    "profit": deal_dict['profit']
                                }

                                # Store in our transaction history
                                transaction_history[deal_dict['ticket']] = update

                                # Send to all trade subscribers
                                message = json.dumps(update)
                                subscribers = list(self.trade_subscribers)  # Create copy to avoid modification during iteration
                                for client in subscribers:
                                    try:
                                        await client.send(message)
                                    except Exception as e:
                                        logger.error(f"Error sending trade update to client: {e}")

                    # Update last positions
                    self.last_positions = current_positions

                    # Store the most recent 1000 trades each for positions and transactions
                    if len(trade_history) > 1000:
                        # Keep the most recent entries
                        trade_history = {k: v for k, v in sorted(trade_history.items(), reverse=True)[:1000]}

                    if len(transaction_history) > 1000:
                        # Keep the most recent entries
                        transaction_history = {k: v for k, v in sorted(transaction_history.items(), reverse=True)[:1000]}

                    # Limit the size of the last deals set to prevent memory growth
                    if len(self.last_deals) > 1000:
                        # Keep only the most recent 500 deals
                        self.last_deals = set(sorted(list(self.last_deals))[-500:])

            except Exception as e:
                logger.error(f"Error updating trade data: {e}", exc_info=True)

            await asyncio.sleep(self.update_interval)
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
        
        # Start trade update task
        self.trade_update_task = asyncio.create_task(self.update_trades())
        
        async with websockets.serve(self.handle_client, self.host, self.port):
            logger.info(f"MT5 WebSocket server started on {self.host}:{self.port}")
            await asyncio.Future()  # Run forever

    def stop_server(self):
        """Stop the WebSocket server"""
        self.running = False
        if self.price_update_task:
            self.price_update_task.cancel()
        if self.trade_update_task:
            self.trade_update_task.cancel()
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