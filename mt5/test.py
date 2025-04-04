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
    def __init__(self, server_url="ws://34.87.87.53:8765", symbols=None, 
                 save_data=True, data_dir="price_data"):
        """
        Initialize MT5 WebSocket Client
        
        Args:
            server_url: The WebSocket URL of the MT5 server
            symbols: List of symbols to subscribe to
            save_data: Whether to save received price data to CSV files
            data_dir: Directory to save price data
        """
        self.server_url = server_url
        self.symbols = symbols or ["EURUSD", "GBPUSD", "USDTHB"]
        self.save_data = save_data
        self.data_dir = data_dir
        self.is_running = False
        self.reconnect_delay = 5  # seconds
        self.max_reconnect_delay = 60  # maximum delay between reconnection attempts
        self.csv_files = {}  # Dictionary to store open CSV file handlers
        
        # Create data directory if it doesn't exist and we're saving data
        if self.save_data and not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
            
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

    async def connect(self):
        """Connect to the MT5 WebSocket server with automatic reconnection"""
        self.is_running = True
        current_delay = self.reconnect_delay
        
        while self.is_running:
            try:
                logger.info(f"Connecting to MT5 WebSocket server at {self.server_url}")
                async with websockets.connect(self.server_url) as ws:
                    # Reset reconnection delay on successful connection
                    current_delay = self.reconnect_delay
                    
                    logger.info("Connected successfully")
                    
                    # Subscribe to symbols
                    subscription = {
                        "type": "subscription",
                        "action": "subscribe",
                        "symbols": self.symbols
                    }
                    
                    await ws.send(json.dumps(subscription))
                    logger.info(f"Subscription request sent for symbols: {self.symbols}")
                    
                    # Process incoming messages
                    while self.is_running:
                        try:
                            message = await ws.recv()
                            
                            # Check again if client is still running after receiving message
                            if not self.is_running:
                                break
                                
                            data = json.loads(message)
                            
                            # Process the data based on message type
                            if data.get("type") == "price_update":
                                symbol = data.get("symbol")
                                bid = data.get("bid")
                                ask = data.get("ask")
                                spread = data.get("spread")
                                timestamp = data.get("timestamp")
                                
                                # Process the price data
                                self.process_price_update(symbol, bid, ask, spread, timestamp)
                                
                            elif data.get("type") == "subscription_confirmation":
                                logger.info(f"Successfully subscribed to {data.get('symbols')}")
                                
                            elif data.get("type") == "error":
                                logger.error(f"Server error: {data.get('message')}")
                        
                        except asyncio.CancelledError:
                            # Handle cancellation
                            break
            
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
    
    def stop(self):
        """Stop the WebSocket client"""
        logger.info("Stopping client...")
        # Set is_running to False first to prevent further processing
        self.is_running = False
        
        # Close any open CSV files
        self.close_files()

    def close_files(self):
        """Close all open CSV files"""
        for symbol, file_data in self.csv_files.items():
            try:
                file_data['file'].close()
                logger.info(f"Closed data file for {symbol}")
            except Exception as e:
                logger.error(f"Error closing file for {symbol}: {e}")
        self.csv_files = {}

async def main():
    """Main function to run the WebSocket client"""
    # Default server URL
    server_url = "ws://34.87.87.53:8765"
    
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
    
    # Create and start the client
    client = MT5WebSocketClient(
        server_url=server_url,
        symbols=symbols,
        save_data=True,
        data_dir="price_data"
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