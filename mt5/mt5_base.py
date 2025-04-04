import os
import logging
from typing import Optional, Dict, Generator, Any
from contextlib import contextmanager
from dataclasses import dataclass
from dotenv import load_dotenv
import MetaTrader5 as mt5

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass
class SymbolPrice:
    """Data class to store symbol price information"""

    bid: float
    ask: float

    @property
    def spread(self) -> float:
        return self.ask - self.bid


class MT5Base:
    """Base class for MT5 connection management"""

    def __init__(
        self,
        user: Optional[int] = None,
        password: Optional[str] = None,
        server: Optional[str] = None,
        path: Optional[str] = None,
    ):
        load_dotenv()
        self.user = user or int(os.getenv("login", 0))
        self.password = password or os.getenv("password")
        self.server = server or os.getenv("server")
        self.path = path or os.getenv("MT5_PATH")
        self.is_connected = False
        self._validate_credentials()

    def _validate_credentials(self) -> None:
        """Validate that all required credentials are present"""
        missing = [
            k
            for k, v in {
                "login": self.user,
                "password": self.password,
                "server": self.server,
                "MT5_PATH": self.path,
            }.items()
            if not v
        ]

        if missing:
            raise ValueError(f"Missing required credentials: {', '.join(missing)}")

    def login(self) -> bool:
        """Establish connection to MT5 terminal"""
        if self.is_connected:
            return True

        try:
            if not mt5.initialize(self.path):
                logger.error(f"MT5 initialization failed: {mt5.last_error()}")
                return False

            if not mt5.login(self.user, password=self.password, server=self.server):
                logger.error(f"Login failed: {mt5.last_error()}")
                return False

            self.is_connected = True
            logger.info("Successfully connected to MT5")
            return True
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            return False

    @contextmanager
    def connection(self) -> Generator[Optional["MT5Base"], None, None]:
        """Context manager for MT5 connection with proper resource cleanup"""
        if not self.login():
            yield None
        else:
            try:
                yield self
            finally:
                mt5.shutdown()
                self.is_connected = False

    def get_symbol_info(self, symbol: str) -> Dict[str, Any]:
        """Get information about a symbol"""
        with self.connection() as client:
            if not client:
                return {}

            info = mt5.symbol_info(symbol)
            if not info:
                logger.error(f"Failed to get symbol info for {symbol}")
                return {}

            return info._asdict()

    def get_account_info(self) -> Optional[Dict[str, Any]]:
        """Get account information"""
        with self.connection() as client:
            if not client:
                return None
            info = mt5.account_info()
            return info._asdict() if info else None
