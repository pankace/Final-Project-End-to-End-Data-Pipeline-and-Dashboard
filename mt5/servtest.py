from pathlib import Path
import sys
import time

from mt5_trading import MT5Trading
import MetaTrader5 as mt5
import logging
import os
from dotenv import load_dotenv
from multiprocessing import freeze_support

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


def example_usage():
    try:
        # Initialize MT5Trading
        mt5_trader = MT5Trading(
            path=os.getenv("MT5_PATH"),
            user=int(os.getenv("MT5_USER")),
            password=os.getenv("MT5_PASSWORD"),
            server=os.getenv("MT5_SERVER"),
        )

        # Test connection first
        if not mt5.initialize(mt5_trader.path):
            logger.error("Failed to initialize MT5")
            return

        # Get account info to verify connection
        account_info = mt5_trader.get_account_info()
        if account_info:
            logger.info(f"Connected to account: {account_info.get('login')}")

        # Initialize previous prices dictionary
        symbols = ["USDTHB", "XAUUSD"]
        prev_prices = {symbol: None for symbol in symbols}

        while True:
            prices = mt5_trader.get_prices(symbols)

            # Check each symbol separately
            for symbol, price in prices.items():
                if (
                    prev_prices[symbol] is None
                    or price.bid != prev_prices[symbol].bid
                    or price.ask != prev_prices[symbol].ask
                ):
                    logger.info(f"{symbol} - Bid: {price.bid}, Ask: {price.ask}")
                    prev_prices[symbol] = price

            time.sleep(0.1)

    except Exception as e:
        logger.error(f"Error in example usage: {str(e)}")
    finally:
        mt5.shutdown()


if __name__ == "__main__":
    freeze_support()
    print("Example usage")
    example_usage()
