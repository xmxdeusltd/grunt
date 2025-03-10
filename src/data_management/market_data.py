from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import logging
import json

from src.config.types import Config
from .database import DatabaseManager
from .state import StateManager

logger = logging.getLogger(__name__)


class MarketDataManager:
    def __init__(
        self,
        db_manager: DatabaseManager,
        state_manager: StateManager,
        config: Config
    ):
        self.db = db_manager
        self.state = state_manager
        self.config = config

    async def process_trade(self, trade: Dict[str, Any]) -> None:
        """Process and store a new trade"""
        try:
            # Store trade in database
            await self.db.execute_query(
                """
                INSERT INTO trades (symbol, price, size, timestamp, side)
                VALUES ($1, $2, $3, $4, $5)
                """,
                trade["symbol"],
                trade["price"],
                trade["size"],
                trade["timestamp"],
                trade["side"]
            )

            # Update latest market data in Redis
            self.state.update_market_data(trade["symbol"], {
                "last_price": trade["price"],
                "last_size": trade["size"],
                "last_trade_time": trade["timestamp"],
                "updated_at": datetime.utcnow().isoformat()
            })

        except Exception as e:
            logger.error(f"Failed to process trade: {str(e)}")
            raise

    async def process_candle(self, candle: Dict[str, Any]) -> None:
        """Process and store a new candle"""
        try:
            # Store candle in database
            await self.db.execute_query(
                """
                INSERT INTO candles (
                    symbol, timestamp, open, high, low, close, volume
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                """,
                candle["symbol"],
                candle["timestamp"],
                candle["open"],
                candle["high"],
                candle["low"],
                candle["close"],
                candle["volume"]
            )

            # Update latest candle in Redis
            self.state.set_state(
                f"market:{candle['symbol']}:candle:{candle['interval']}",
                candle,
                ttl=300
            )

        except Exception as e:
            logger.error(f"Failed to process candle: {str(e)}")
            raise

    async def get_candles(
        self,
        symbol: str,
        interval: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get historical candles"""
        try:
            query = """
                SELECT *
                FROM candles
                WHERE symbol = $1
                AND timestamp >= $2
                AND timestamp <= $3
                ORDER BY timestamp DESC
                LIMIT $4
            """

            end_time = end_time or datetime.utcnow()
            start_time = start_time or (end_time - timedelta(days=1))

            return await self.db.fetch_query(
                query,
                symbol,
                start_time,
                end_time,
                limit
            )

        except Exception as e:
            logger.error(f"Failed to get candles: {str(e)}")
            raise

    async def get_trades(
        self,
        symbol: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get historical trades"""
        try:
            query = """
                SELECT *
                FROM trades
                WHERE symbol = $1
                AND timestamp >= $2
                AND timestamp <= $3
                ORDER BY timestamp DESC
                LIMIT $4
            """

            end_time = end_time or datetime.utcnow()
            start_time = start_time or (end_time - timedelta(hours=1))

            return await self.db.fetch_query(
                query,
                symbol,
                start_time,
                end_time,
                limit
            )

        except Exception as e:
            logger.error(f"Failed to get trades: {str(e)}")
            raise

    async def get_latest_price(self, symbol: str) -> Optional[float]:
        """Get latest price for a symbol"""
        try:
            # Try to get from Redis first
            market_data = self.state.get_market_data(symbol)
            if market_data and "last_price" in market_data:
                return float(market_data["last_price"])

            # Fallback to database
            query = """
                SELECT price
                FROM trades
                WHERE symbol = $1
                ORDER BY timestamp DESC
                LIMIT 1
            """
            result = await self.db.fetch_query(query, symbol)
            return float(result[0]["price"]) if result else None

        except Exception as e:
            logger.error(f"Failed to get latest price: {str(e)}")
            raise
