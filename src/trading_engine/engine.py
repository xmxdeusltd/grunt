from typing import Dict, Any, Optional, List
import logging
from datetime import datetime

from src.config.types import Config
from .models import Order, Trade, Position, OrderType, OrderStatus, PositionStatus
from .order_manager import OrderManager
from .position_manager import PositionManager

logger = logging.getLogger(__name__)


class TradingEngine:
    def __init__(
        self,
        state_manager: Any,
        jupiter_client: Any,  # Will be properly typed when implementing Jupiter integration
        config: Config
    ):
        self.state_manager = state_manager
        self.jupiter_client = jupiter_client
        self.config = config
        self.order_manager = OrderManager(state_manager)
        self.position_manager = PositionManager(state_manager)

    async def execute_market_order(
        self,
        symbol: str,
        side: str,
        size: float,
        stop_loss: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Order:
        """Execute a market order"""
        try:
            # Create order
            order = await self.order_manager.create_order(
                symbol=symbol,
                side=side,
                size=size,
                order_type=OrderType.MARKET,
                metadata=metadata
            )

            # Get quote from Jupiter
            quote = await self.jupiter_client.get_quote(
                input_token=symbol.split('-')[0],
                output_token=symbol.split('-')[1],
                amount=size,
                side=side
            )

            try:
                # Execute swap
                result = await self.jupiter_client.execute_swap(quote)

                # Create trade
                trade = await self.order_manager.create_trade(
                    order_id=order.order_id,
                    position_id=None,  # Will be updated after position creation
                    price=result["price"],
                    size=result["size"],
                    fee=result["fee"]
                )

                # Create position
                position = await self.position_manager.create_position(
                    symbol=symbol,
                    side=side,
                    size=trade.size,
                    entry_price=trade.price,
                    stop_loss=stop_loss,
                    metadata=metadata
                )

                # Update trade with position ID
                trade.position_id = position.position_id
                await self.order_manager._save_trade_state(trade)

                # Update order as filled
                await self.order_manager.update_order(
                    order_id=order.order_id,
                    status=OrderStatus.FILLED,
                    filled_price=trade.price,
                    filled_size=trade.size
                )

                logger.info(
                    f"Market order executed successfully: {order.order_id}")
                return order

            except Exception as e:
                # Update order as failed
                await self.order_manager.update_order(
                    order_id=order.order_id,
                    status=OrderStatus.FAILED,
                    error=str(e)
                )
                raise

        except Exception as e:
            logger.error(f"Error executing market order: {str(e)}")
            raise

    async def close_position(
        self,
        position_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Position:
        """Close a position"""
        try:
            position = await self.position_manager.get_position(position_id)
            if not position:
                raise ValueError(f"Position not found: {position_id}")

            if position.status == PositionStatus.CLOSED:
                raise ValueError(f"Position already closed: {position_id}")

            # Create closing order
            close_side = "sell" if position.side == "buy" else "buy"
            order = await self.order_manager.create_order(
                symbol=position.symbol,
                side=close_side,
                size=position.size,
                order_type=OrderType.MARKET,
                metadata=metadata
            )

            # Get quote from Jupiter
            quote = await self.jupiter_client.get_quote(
                input_token=position.symbol.split('-')[0],
                output_token=position.symbol.split('-')[1],
                amount=position.size,
                side=close_side
            )

            try:
                # Execute swap
                result = await self.jupiter_client.execute_swap(quote)

                # Create trade
                trade = await self.order_manager.create_trade(
                    order_id=order.order_id,
                    position_id=position_id,
                    price=result["price"],
                    size=result["size"],
                    fee=result["fee"]
                )

                # Update order as filled
                await self.order_manager.update_order(
                    order_id=order.order_id,
                    status=OrderStatus.FILLED,
                    filled_price=trade.price,
                    filled_size=trade.size
                )

                # Close position
                closed_position = await self.position_manager.close_position(
                    position_id=position_id,
                    close_price=trade.price,
                    metadata=metadata
                )

                logger.info(f"Position closed successfully: {position_id}")
                return closed_position

            except Exception as e:
                # Update order as failed
                await self.order_manager.update_order(
                    order_id=order.order_id,
                    status=OrderStatus.FAILED,
                    error=str(e)
                )
                raise

        except Exception as e:
            logger.error(f"Error closing position: {str(e)}")
            raise

    async def update_positions(self, symbol: str, current_price: float) -> None:
        """Update positions with current market price"""
        try:
            positions = await self.position_manager.get_open_positions(symbol)
            for position in positions:
                updated_position = await self.position_manager.update_position(
                    position_id=position.position_id,
                    current_price=current_price
                )

                # Check if stop loss was triggered
                if updated_position.status == PositionStatus.CLOSING:
                    try:
                        await self.close_position(
                            position_id=position.position_id,
                            metadata={"reason": "stop_loss"}
                        )
                    except Exception as e:
                        logger.error(f"Error executing stop loss: {str(e)}")

        except Exception as e:
            logger.error(f"Error updating positions: {str(e)}")
            raise

    async def get_position_summary(self) -> Dict[str, Any]:
        """Get summary of all positions"""
        try:
            positions = await self.position_manager.get_open_positions()

            total_pnl = 0.0
            position_count = len(positions)
            symbols = set()

            for position in positions:
                total_pnl += position.unrealized_pnl
                symbols.add(position.symbol)

            return {
                "total_positions": position_count,
                "total_pnl": total_pnl,
                "active_symbols": list(symbols),
                "positions": [
                    {
                        "position_id": p.position_id,
                        "symbol": p.symbol,
                        "side": p.side,
                        "size": p.size,
                        "entry_price": p.entry_price,
                        "current_price": p.current_price,
                        "unrealized_pnl": p.unrealized_pnl,
                        "stop_loss": p.stop_loss
                    }
                    for p in positions
                ]
            }

        except Exception as e:
            logger.error(f"Error getting position summary: {str(e)}")
            raise

    async def get_trade_history(
        self,
        symbol: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Get trade history"""
        try:
            trades = await self.order_manager.get_trades(
                symbol=symbol,
                start_time=start_time,
                end_time=end_time
            )

            return [
                {
                    "trade_id": t.trade_id,
                    "symbol": t.symbol,
                    "side": t.side,
                    "size": t.size,
                    "price": t.price,
                    "timestamp": t.timestamp,
                    "fee": t.fee,
                    "position_id": t.position_id
                }
                for t in trades
            ]

        except Exception as e:
            logger.error(f"Error getting trade history: {str(e)}")
            raise
