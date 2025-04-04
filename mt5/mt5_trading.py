from typing import Dict, List, Union, Optional
from dataclasses import dataclass
import logging
from multiprocessing import Process, Queue, freeze_support
import MetaTrader5 as mt5
from .mt5_base import MT5Base, SymbolPrice

logger = logging.getLogger(__name__)


@dataclass
class Position:
    """Data class for position information"""

    volume: float
    type: int
    symbol: str
    profit: float
    ticket: int


class MT5Trading(MT5Base):
    """Trading operations for MT5"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        freeze_support()

    def _fetch_symbol_price(self, symbol: str, queue: Queue) -> None:
        """Worker process for fetching symbol prices"""
        try:
            if not mt5.initialize(self.path):
                queue.put((symbol, None))
                return

            ticker = mt5.symbol_info_tick(symbol)
            if ticker is None:
                queue.put((symbol, None))
            else:
                price = SymbolPrice(bid=ticker.bid, ask=ticker.ask)
                queue.put((symbol, price))
        finally:
            mt5.shutdown()

    def get_prices(self, symbols: List[str]) -> Dict[str, SymbolPrice]:
        """Fetch prices for multiple symbols concurrently using multiprocessing"""
        if not symbols:
            return {}

        queue = Queue()
        processes = [
            Process(target=self._fetch_symbol_price, args=(symbol, queue))
            for symbol in symbols
        ]
        active_processes = []

        try:
            # Start processes and keep track of started ones
            for p in processes:
                try:
                    p.start()
                    active_processes.append(p)
                except Exception as e:
                    logger.error(f"Failed to start process: {e}")

            results = {}
            # Only wait for successfully started processes
            for _ in range(len(active_processes)):
                try:
                    symbol, price_data = queue.get(timeout=10)  # Add timeout
                    if price_data is not None:
                        results[symbol] = price_data
                except Exception as e:
                    logger.error(f"Error getting queue data: {e}")

            return results
        finally:
            # Clean up only the processes that were successfully started
            for p in active_processes:
                try:
                    if p.is_alive():
                        p.terminate()
                    p.join()
                except Exception as e:
                    logger.error(f"Error cleaning up process: {e}")

    def get_position_summary(
        self, symbol: str = "USDTHB"
    ) -> Dict[str, Union[float, List[Position]]]:
        """Get summary of positions for a symbol"""
        with self.connection() as client:
            if not client:
                return {"net_volume": 0, "positions": []}

            positions = mt5.positions_get(symbol=symbol) or []
            position_objects = [
                Position(p.volume, p.type, p.symbol, p.profit, p.ticket)
                for p in positions
            ]

            net_volume = sum(
                p.volume if p.type == mt5.ORDER_TYPE_BUY else -p.volume
                for p in position_objects
            )

            return {"net_volume": round(net_volume, 2), "positions": position_objects}

    def place_order(
        self, symbol: str, order_type: int, volume: float, price: Optional[float] = None
    ) -> bool:
        """Place a trading order"""
        with self.connection() as client:
            if not client:
                return False

            tick = mt5.symbol_info_tick(symbol)
            if not tick:
                logger.error(f"Failed to get tick info for {symbol}")
                return False

            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": volume,
                "type": order_type,
                "price": price
                or (tick.ask if order_type == mt5.ORDER_TYPE_BUY else tick.bid),
                "deviation": 20,
                "magic": 234000,
                "comment": "python script order",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }

            result = mt5.order_send(request)
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                logger.error(f"Order failed: {result.comment}, Code: {result.retcode}")
                return False

            logger.info(f"Order placed: {symbol}, Volume: {volume}, Type: {order_type}")
            return True

    def _get_positions(self, symbol: str) -> tuple[List[dict], List[dict]]:
        """Helper method to get buy and sell positions"""
        positions = mt5.positions_get(symbol=symbol)
        if not positions:
            return [], []

        buy_positions = [p._asdict() for p in positions if p.type == 0]
        sell_positions = [p._asdict() for p in positions if p.type == 1]
        return buy_positions, sell_positions

    def close_positions_by_type(self, symbol: str = "USDTHB") -> bool:
        """Close matching buy/sell positions using a multi-pass strategy"""
        with self.connection() as client:
            if not client:
                return False

            positions_total = mt5.positions_total()
            if positions_total == 0:
                logger.info("No positions found")
                return True

            buy_positions, sell_positions = self._get_positions(symbol)
            if not buy_positions and not sell_positions:
                logger.error(f"Failed to get positions for {symbol}")
                return False

            total_buy_volume = sum(p["volume"] for p in buy_positions)
            total_sell_volume = sum(p["volume"] for p in sell_positions)

            logger.info(f"Total positions: {positions_total}")
            logger.info(
                f"Buy positions: {len(buy_positions)}, volume: {total_buy_volume}"
            )
            logger.info(
                f"Sell positions: {len(sell_positions)}, volume: {total_sell_volume}"
            )

            if total_buy_volume <= 0 or total_sell_volume <= 0:
                logger.info("No matching positions to close")
                return True

            # First attempt: Try CLOSE_BY
            logger.info("First pass: Attempting to close positions with CLOSE_BY")
            first_pass_result = self._close_matching_positions(
                buy_positions, sell_positions
            )

            # Check remaining positions
            remaining_buys, remaining_sells = self._get_positions(symbol)
            remaining_buy_volume = sum(p["volume"] for p in remaining_buys)
            remaining_sell_volume = sum(p["volume"] for p in remaining_sells)

            # Second pass if needed
            if remaining_buy_volume > 0 and remaining_sell_volume > 0:
                logger.info("Second pass: Attempting another round of CLOSE_BY")
                second_pass_result = self._close_matching_positions(
                    remaining_buys, remaining_sells
                )

                # Final check if positions still remain
                final_buys, final_sells = self._get_positions(symbol)
                final_buy_volume = sum(p["volume"] for p in final_buys)
                final_sell_volume = sum(p["volume"] for p in final_sells)

                # Third pass - fall back to manual closing if needed
                if final_buy_volume > 0 and final_sell_volume > 0:
                    logger.info("Third pass: Falling back to manual position closure")
                    return self._close_matching_positions_backup(
                        final_buys, final_sells
                    )

                return first_pass_result or second_pass_result

            return first_pass_result

    def _close_matching_positions(
        self, buy_positions: List[dict], sell_positions: List[dict]
    ) -> bool:
        """Simplified position closure - prioritize largest volumes first"""

        # Sort positions by volume (largest first)
        buy_positions = sorted(buy_positions, key=lambda p: p["volume"], reverse=True)
        sell_positions = sorted(sell_positions, key=lambda p: p["volume"], reverse=True)

        success = False

        # Try to close positions using CLOSE_BY
        for buy in buy_positions:
            if buy["volume"] <= 0:
                continue

            for sell in sell_positions:
                if sell["volume"] <= 0:
                    continue

                request = {
                    "action": mt5.TRADE_ACTION_CLOSE_BY,
                    "position": sell["ticket"],
                    "position_by": buy["ticket"],
                    "comment": "hedge close by",
                }

                result = mt5.order_send(request)
                if result.retcode == mt5.TRADE_RETCODE_DONE:
                    logger.info(
                        f"Closed positions: Buy {buy['ticket']} - Sell {sell['ticket']}"
                    )

                    # Update position status after closure
                    remaining_positions = mt5.positions_get(symbol=buy["symbol"])

                    # Reset volumes based on what's left open
                    buy_still_exists = False
                    sell_still_exists = False

                    for p in remaining_positions:
                        pos = p._asdict()
                        if pos["ticket"] == buy["ticket"]:
                            buy["volume"] = pos["volume"]
                            buy_still_exists = True
                        if pos["ticket"] == sell["ticket"]:
                            sell["volume"] = pos["volume"]
                            sell_still_exists = True

                    if not buy_still_exists:
                        buy["volume"] = 0
                    if not sell_still_exists:
                        sell["volume"] = 0

                    success = True

        return success

    def _close_matching_positions_backup(
        self, buy_positions: List[dict], sell_positions: List[dict]
    ) -> bool:
        """Helper method to close positions with available volume"""

        for buy in buy_positions:
            for sell in sell_positions:
                if buy["volume"] <= 0 or sell["volume"] <= 0:
                    continue

                # Determine volume to close
                volume_to_close = min(buy["volume"], sell["volume"])

                # Close the positions
                request = {
                    "action": mt5.TRADE_ACTION_DEAL,
                    "symbol": buy["symbol"],
                    "type": mt5.ORDER_TYPE_SELL,  # Close buy position
                    "position": buy["ticket"],
                    "volume": volume_to_close,
                    "magic": 234000,
                    "deviation": 20,
                    "comment": "hedge close",
                    "type_time": mt5.ORDER_TIME_GTC,
                    "type_filling": mt5.ORDER_FILLING_IOC,
                }

                result = mt5.order_send(request)
                if result.retcode != mt5.TRADE_RETCODE_DONE:
                    logger.error(
                        f"Failed to close buy position {buy['ticket']}: {result.comment}"
                    )
                    return False

                # Close corresponding sell position
                request = {
                    "action": mt5.TRADE_ACTION_DEAL,
                    "symbol": sell["symbol"],
                    "type": mt5.ORDER_TYPE_BUY,  # Close sell position
                    "position": sell["ticket"],
                    "volume": volume_to_close,
                    "magic": 234000,
                    "deviation": 20,
                    "comment": "hedge close",
                    "type_time": mt5.ORDER_TIME_GTC,
                    "type_filling": mt5.ORDER_FILLING_IOC,
                }

                result = mt5.order_send(request)
                if result.retcode != mt5.TRADE_RETCODE_DONE:
                    logger.error(
                        f"Failed to close sell position {sell['ticket']}: {result.comment}"
                    )
                    return False

                logger.info(
                    f"Closed positions: Buy {buy['ticket']} - Sell {sell['ticket']} with volume {volume_to_close}"
                )

                # Update remaining volumes
                buy["volume"] -= volume_to_close
                sell["volume"] -= volume_to_close

        return True
