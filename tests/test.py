import asyncio
import json
import websockets
import logging
import time
from datetime import datetime
import csv
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

class MT5WebSocketClient:
    def __init__(self, server_url="ws://34.126.166.132:8765", symbols=None, 
                 save_data=True, data_dir="price_data", save_trades=True, 
                 trades_dir="trade_data"):
        """
        Initialize MT5 WebSocket Client
        
        Args:
            server_url: The WebSocket URL of the MT5 server
            symbols: List of symbols to subscribe to
            save_data: Whether to save received price data to CSV files
            data_dir: Directory to save price data
            save_trades: Whether to save trade data to CSV files
            trades_dir: Directory to save trade data
        """
        self.server_url = server_url
        self.symbols = symbols or ["EURUSD", "GBPUSD", "USDTHB"]
        self.save_data = save_data
        self.data_dir = data_dir
        self.save_trades = save_trades
        self.trades_dir = trades_dir
        self.is_running = False
        self.reconnect_delay = 5  # seconds
        self.max_reconnect_delay = 60  # maximum delay between reconnection attempts
        self.csv_files = {}  # Dictionary to store open CSV file handlers
        self.trade_files = {}  # Dictionary to store open trade file handlers
        
        # Create directories if they don't exist
        if self.save_data and not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
            
        if self.save_trades and not os.path.exists(self.trades_dir):
            os.makedirs(self.trades_dir)
            
    def _get_csv_writer(self, symbol):
        """Get or create a CSV writer for a symbol"""
        if symbol not in self.csv_files:
            # Generate filename with date
            today = datetime.now().strftime("%Y%m%d")
            filename = os.path.join(self.data_dir, f"{symbol}_{today}.csv")
            
            # Check if file exists to determine if we need to write headers
            file_exists = os.path.isfile(filename)
            
            # Open file and create CSV writer
            file = open(filename, 'a', newline='')
            writer = csv.writer(file)
            
            # Write header if new file
            if not file_exists:
                writer.writerow(['timestamp', 'symbol', 'bid', 'ask', 'spread'])
                
            self.csv_files[symbol] = {
                'file': file,
                'writer': writer
            }
            
        return self.csv_files[symbol]['writer']
        
    def _get_trades_writer(self, file_type="trades"):
        """Get or create a CSV writer for trade or transaction data"""
        if file_type not in self.trade_files:
            # Generate filename with date
            today = datetime.now().strftime("%Y%m%d")
            filename = os.path.join(self.trades_dir, f"{file_type}_{today}.csv")
            
            # Check if file exists to determine if we need to write headers
            file_exists = os.path.isfile(filename)
            
            # Open file and create CSV writer
            file = open(filename, 'a', newline='')
            writer = csv.writer(file)
            
            # Write header if new file
            if not file_exists:
                if file_type == "trades":
                    writer.writerow([
                        'timestamp', 'trade_id', 'type', 'symbol', 
                        'volume', 'price', 'profit', 'sl', 'tp'
                    ])
                else:  # transactions
                    writer.writerow([
                        'timestamp', 'transaction_id', 'type', 'symbol', 
                        'volume', 'price', 'commission', 'swap', 'profit'
                    ])
                
            self.trade_files[file_type] = {
                'file': file,
                'writer': writer
            }
            
        return self.trade_files[file_type]['writer']

    def save_price_data(self, symbol, bid, ask, spread, timestamp):
        """Save price data to CSV file"""
        # Skip if the client is not running or not saving data
        if not self.save_data or not self.is_running:
            return
            
        try:
            writer = self._get_csv_writer(symbol)
            writer.writerow([timestamp, symbol, bid, ask, spread])
            self.csv_files[symbol]['file'].flush()  # Ensure data is written immediately
        except Exception as e:
            logger.error(f"Error saving price data: {e}")
            
    def save_trade_data(self, trade_data, file_type="trades"):
        """Save trade data to CSV file with improved synchronization"""
        # Skip if the client is not running or not saving trade data
        if not self.save_trades or not self.is_running:
            return
            
        try:
            writer = self._get_trades_writer(file_type)
            
            if file_type == "trades":
                # Make sure we have a timestamp
                timestamp = trade_data.get('timestamp', datetime.now().isoformat())
                
                writer.writerow([
                    timestamp,
                    trade_data.get('trade_id'),
                    trade_data.get('type'),
                    trade_data.get('symbol'),
                    trade_data.get('volume'),
                    trade_data.get('price'),
                    trade_data.get('profit'),
                    trade_data.get('sl'),
                    trade_data.get('tp')
                ])
            else:  # transactions
                # Make sure we have a timestamp
                timestamp = trade_data.get('timestamp', datetime.now().isoformat())
                
                writer.writerow([
                    timestamp,
                    trade_data.get('transaction_id'),
                    trade_data.get('type'),
                    trade_data.get('symbol'),
                    trade_data.get('volume'),
                    trade_data.get('price'),
                    trade_data.get('commission'),
                    trade_data.get('swap'),
                    trade_data.get('profit')
                ])
                
            # Ensure data is written immediately
            self.trade_files[file_type]['file'].flush()
            # On Windows, fsync to make sure data is committed to disk
            os.fsync(self.trade_files[file_type]['file'].fileno())
            
            # Log the successful write
            if file_type == "trades":
                logger.debug(f"Saved trade {trade_data.get('trade_id')} for {trade_data.get('symbol')}")
            else:
                logger.debug(f"Saved transaction {trade_data.get('transaction_id')} for {trade_data.get('symbol')}")
                
        except Exception as e:
            logger.error(f"Error saving trade data: {e}", exc_info=True)

    def process_price_update(self, symbol, bid, ask, spread, timestamp):
        """Process the received price update"""
        # Skip processing if client is stopping
        if not self.is_running:
            return
            
        # Display the data
        print(f"Symbol: {symbol}")
        print(f"Bid: {bid}")
        print(f"Ask: {ask}")
        print(f"Spread: {spread}")
        print(f"Timestamp: {timestamp}")
        print("-----------------------------------")
        
        # Save to CSV if enabled
        if self.save_data:
            self.save_price_data(symbol, bid, ask, spread, timestamp)
    # Add these improvements to the relevant sections of your code
    async def connect(self):
        """Connect to the MT5 WebSocket server with automatic reconnection"""
        self.is_running = True
        current_delay = self.reconnect_delay

        # Track the last seen trade ID to request missed trades on reconnect
        last_trade_id = 0
        last_transaction_id = 0

        while self.is_running:
            try:
                logger.info(f"Connecting to MT5 WebSocket server at {self.server_url}")
                async with websockets.connect(self.server_url) as ws:
                    # Reset reconnection delay on successful connection
                    current_delay = self.reconnect_delay

                    logger.info("Connected successfully")

                    # Subscribe to symbols and trade updates
                    subscription = {
                        "type": "subscription",
                        "action": "subscribe",
                        "symbols": self.symbols,
                        "include_trades": True,
                        "last_trade_id": last_trade_id,         # Add these to request missed trades
                        "last_transaction_id": last_transaction_id
                    }

                    await ws.send(json.dumps(subscription))
                    logger.info(f"Subscription request sent for symbols: {self.symbols} with trade updates")

                    # Process incoming messages
                    while self.is_running:
                        try:
                            message = await ws.recv()

                            # Check again if client is still running after receiving message
                            if not self.is_running:
                                break

                            data = json.loads(message)

                            # Log raw message for debugging
                            msg_type = data.get("type", "unknown")
                            logger.info(f"Received message of type: {msg_type}")

                            # Process the data based on message type
                            if data.get("type") == "price_update":
                                symbol = data.get("symbol")
                                bid = data.get("bid")
                                ask = data.get("ask")
                                spread = data.get("spread")
                                timestamp = data.get("timestamp")

                                # Process the price data
                                self.process_price_update(symbol, bid, ask, spread, timestamp)

                            elif data.get("type") == "trade_update":
                                # Log entire trade update for debugging
                                logger.info(f"Trade update received: {data}")

                                # Update last seen trade IDs for reconnection
                                if data.get('update_type') == 'position' and data.get('trade_id'):
                                    last_trade_id = max(last_trade_id, int(data.get('trade_id')))
                                elif data.get('update_type') == 'transaction' and data.get('transaction_id'):
                                    last_transaction_id = max(last_transaction_id, int(data.get('transaction_id')))

                                # Process trade data
                                self.process_trade_update(data)

                            elif data.get("type") == "subscription_confirmation":
                                logger.info(f"Successfully subscribed to {data.get('symbols')}")
                                if data.get('trades_included'):
                                    logger.info("Trade updates included in subscription")

                            elif data.get("type") == "error":
                                logger.error(f"Server error: {data.get('message')}")

                            # Send heartbeat/ping every 30 seconds to keep connection alive
                            if time.time() % 30 < 1:
                                await ws.send(json.dumps({"type": "ping"}))

                        except asyncio.CancelledError:
                            # Handle cancellation
                            break
                        except json.JSONDecodeError as e:
                            logger.error(f"Error decoding JSON: {e} - Raw message: {message[:100]}...")
                        except Exception as e:
                            logger.error(f"Error processing message: {e}", exc_info=True)

            except websockets.exceptions.ConnectionClosed as e:
                if self.is_running:
                    logger.error(f"WebSocket connection closed: {e}")
            except Exception as e:
                if self.is_running:
                    logger.error(f"Error connecting to MT5 server: {e}")

            if not self.is_running:
                break

            # Implement exponential backoff for reconnection attempts
            logger.info(f"Reconnecting in {current_delay} seconds...")
            await asyncio.sleep(current_delay)

            # Increase delay for next attempt, up to maximum
            current_delay = min(current_delay * 1.5, self.max_reconnect_delay)
    def process_trade_update(self, trade_data):
        """Process the received trade update"""
        # Skip processing if client is stopping
        if not self.is_running:
            return

        trade_type = trade_data.get('update_type', 'unknown')

        # Add a unique identifier field based on the type
        if trade_type == "position":
            # Use the trade_id as the unique identifier
            trade_id = trade_data.get('trade_id')
            # Add direction to make these stand out in logs
            direction = trade_data.get('type', '')
            logger.info(f"Processing {direction} position {trade_id} on {trade_data.get('symbol')}")
        elif trade_type == "transaction":
            # Use transaction_id as the unique identifier
            transaction_id = trade_data.get('transaction_id')
            # Add direction to make these stand out in logs
            direction = trade_data.get('type', '')
            logger.info(f"Processing {direction} transaction {transaction_id} on {trade_data.get('symbol')}")
        else:
            logger.warning(f"Unknown trade update type: {trade_type}")

        # Enhanced logging of trade data
        if 'profit' in trade_data:
            logger.info(f"Trade profit: {trade_data['profit']}")

        # Display the data
        print(f"\n--- NEW TRADE {trade_type.upper()} ---")
        for key, value in trade_data.items():
            if key != 'type':  # Skip the message type
                print(f"{key}: {value}")
        print("-----------------------------------")

        # Save to CSV if enabled
        if self.save_trades:
            if trade_type == "position":
                self.save_trade_data(trade_data, "trades")
            elif trade_type == "transaction":
                self.save_trade_data(trade_data, "transactions")
            else:
                logger.warning(f"Unknown trade update type: {trade_type}")
                # Try to save it anyway
                self.save_trade_data(trade_data, "unknown_trades")
    def stop(self):
        """Stop the WebSocket client"""
        logger.info("Stopping client...")
        # Set is_running to False first to prevent further processing
        self.is_running = False
        
        # Close any open CSV files
        self.close_files()

    def close_files(self):
        """Close all open CSV files"""
        # Close price data files
        for symbol, file_data in self.csv_files.items():
            try:
                file_data['file'].close()
                logger.info(f"Closed price data file for {symbol}")
            except Exception as e:
                logger.error(f"Error closing price file for {symbol}: {e}")
        self.csv_files = {}
        
        # Close trade data files
        for file_type, file_data in self.trade_files.items():
            try:
                file_data['file'].close()
                logger.info(f"Closed {file_type} data file")
            except Exception as e:
                logger.error(f"Error closing {file_type} file: {e}")
        self.trade_files = {}

async def main():
    """Main function to run the WebSocket client"""
    # Default server URL
    server_url = "ws://34.126.166.132:8765"
    
    # Ask for server URL if desired
    use_default = input(f"Use default server URL ({server_url})? (y/n): ").lower()
    if use_default != 'y':
        ip = input("Enter server IP address: ")
        port = input("Enter server port (default: 8765): ") or "8765"
        server_url = f"ws://{ip}:{port}"

    # Ask for symbols to subscribe to
    default_symbols = ["XAUUSD", "EURUSD", "GBPUSD", "USDTHB"]
    use_default_symbols = input(f"Use default symbols {default_symbols}? (y/n): ").lower()
    
    symbols = default_symbols
    if use_default_symbols != 'y':
        symbols_input = input("Enter symbols separated by commas: ")
        symbols = [s.strip() for s in symbols_input.split(',')]
    
    # Ask to include trade data
    include_trades = input("Would you like to receive trade updates? (y/n): ").lower() == 'y'
    
    # Create and start the client
    client = MT5WebSocketClient(
        server_url=server_url,
        symbols=symbols,
        save_data=True,
        data_dir="price_data",
        save_trades=include_trades,
        trades_dir="trade_data"
    )
    
    try:
        # Register cleanup handler
        import signal
        def signal_handler(sig, frame):
            logger.info("Received shutdown signal")
            client.stop()
        
        signal.signal(signal.SIGINT, signal_handler)
        
        # Run the client
        await client.connect()
    except KeyboardInterrupt:
        logger.info("Client stopped by user")
        client.stop()
    finally:
        # Ensure files are closed on exit
        client.close_files()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Client stopped by user")