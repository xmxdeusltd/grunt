from typing import Dict, Any, Optional, Type, List
import logging
import asyncio
from datetime import datetime

from src.config.types import Config

from .trading_engine.engine import TradingEngine
from .strategy_engine.manager import StrategyManager
from .strategy_engine.base import BaseStrategy
from .strategy_engine.models import DataPoint
from .data_management import StateManager
from .clients import JupiterClient
from .config.loader import config as config_loader

logger = logging.getLogger(__name__)


class TradingSystem:
    def __init__(self, config: Config):
        self.config = config
        self.config_loader = config_loader
        self.state_manager = StateManager(config.redis)

        self.jupiter_client = JupiterClient(
            rpc_endpoint=config.jupiter.rpc_endpoint,
            auth_token=config.jupiter.auth_token
        )

        # Initialize engines
        self.trading_engine = TradingEngine(
            state_manager=self.state_manager,
            jupiter_client=self.jupiter_client,
            config=config
        )

        self.strategy_manager = StrategyManager(
            trading_engine=self.trading_engine,
            state_manager=self.state_manager,
            config=config
        )

        self._running = False
        self._data_queue: asyncio.Queue = asyncio.Queue()

    async def start(self) -> None:
        """Start the trading system"""
        try:
            if self._running:
                logger.warning("Trading system is already running")
                return

            self._running = True
            logger.info("Starting trading system")

            # Start data processing loop
            asyncio.create_task(self._process_data_loop())

        except Exception as e:
            logger.error(f"Error starting trading system: {str(e)}")
            raise

    async def stop(self) -> None:
        """Stop the trading system"""
        try:
            if not self._running:
                logger.warning("Trading system is not running")
                return

            self._running = False
            logger.info("Stopping trading system")

            # Close all positions
            await self._close_all_positions()

        except Exception as e:
            logger.error(f"Error stopping trading system: {str(e)}")
            raise

    async def add_strategy(
        self,
        strategy_id: str,
        strategy_class: Type[BaseStrategy],
        symbol: str,
        params: Dict[str, Any]
    ) -> None:
        """Add a new trading strategy"""
        try:
            await self.strategy_manager.add_strategy(
                strategy_id=strategy_id,
                strategy_class=strategy_class,
                symbol=symbol,
                params=params
            )
            logger.info(f"Added strategy: {strategy_id}")

        except Exception as e:
            logger.error(f"Error adding strategy: {str(e)}")
            raise

    async def get_strategies(self) -> Dict[str, Any]:
        """Get all strategies"""
        return await self.strategy_manager.get_strategy_summary()

    async def remove_strategy(self, strategy_id: str) -> None:
        """Remove a trading strategy"""
        try:
            await self.strategy_manager.remove_strategy(strategy_id)
            logger.info(f"Removed strategy: {strategy_id}")

        except Exception as e:
            logger.error(f"Error removing strategy: {str(e)}")
            raise

    async def process_market_data(
        self,
        symbol: str,
        data_type: str,
        value: float,
        timestamp: Optional[datetime] = None
    ) -> None:
        """Process new market data"""
        try:
            if not self._running:
                logger.warning(
                    "Trading system is not running, ignoring market data")
                return

            data_point = DataPoint(
                data_type=data_type,
                symbol=symbol,
                value=value,
                timestamp=timestamp or datetime.utcnow(),
                metadata={}
            )

            await self._data_queue.put(data_point)

        except Exception as e:
            logger.error(f"Error processing market data: {str(e)}")

    async def get_system_status(self) -> Dict[str, Any]:
        """Get current system status"""
        try:
            strategy_summary = await self.strategy_manager.get_strategy_summary()
            position_summary = await self.trading_engine.get_position_summary()

            return {
                "running": self._running,
                "timestamp": datetime.utcnow().isoformat(),
                "strategies": strategy_summary,
                "positions": position_summary
            }

        except Exception as e:
            logger.error(f"Error getting system status: {str(e)}")
            raise

    async def get_trade_history(
        self,
        symbol: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get trading history"""
        try:
            trades = await self.trading_engine.get_trade_history(
                symbol=symbol,
                start_time=start_time,
                end_time=end_time
            )

            return {
                "total_trades": len(trades),
                "trades": trades
            }

        except Exception as e:
            logger.error(f"Error getting trade history: {str(e)}")
            raise

    async def _process_data_loop(self) -> None:
        """Main data processing loop"""
        while self._running:
            try:
                # Get next data point from queue
                data_point = await self._data_queue.get()

                # Process data through strategy manager
                await self.strategy_manager.process_data(data_point)

                self._data_queue.task_done()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in data processing loop: {str(e)}")

    async def _close_all_positions(self) -> None:
        """Close all open positions"""
        try:
            position_summary = await self.trading_engine.get_position_summary()
            for position in position_summary["positions"]:
                try:
                    await self.trading_engine.close_position(
                        position_id=position["position_id"],
                        metadata={"reason": "system_shutdown"}
                    )
                except Exception as e:
                    logger.error(
                        f"Error closing position {position['position_id']}: {str(e)}")

        except Exception as e:
            logger.error(f"Error closing all positions: {str(e)}")
            raise
