from typing import Dict, Any, Optional, List
import logging
from datetime import datetime
import uuid
from .models import Order, OrderStatus, OrderType, Trade

logger = logging.getLogger(__name__)


class OrderManager:
    def __init__(self, state_manager: Any):
        self.state_manager = state_manager
        self.orders: Dict[str, Order] = {}
        self.trades: Dict[str, Trade] = {}

    async def create_order(
        self,
        symbol: str,
        side: str,
        size: float,
        order_type: OrderType,
        price: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Order:
        """Create a new order"""
        try:
            order_id = f"ord_{uuid.uuid4().hex[:8]}"
            timestamp = datetime.utcnow()

            order = Order(
                order_id=order_id,
                symbol=symbol,
                side=side,
                size=size,
                price=price,
                type=order_type,
                status=OrderStatus.PENDING,
                timestamp=timestamp,
                metadata=metadata or {}
            )

            # Store in memory
            self.orders[order_id] = order

            # Store in state
            await self._save_order_state(order)

            logger.info(f"Created order {order_id} for {symbol}")
            return order

        except Exception as e:
            logger.error(f"Error creating order: {str(e)}")
            raise

    async def update_order(
        self,
        order_id: str,
        status: OrderStatus,
        filled_price: Optional[float] = None,
        filled_size: Optional[float] = None,
        error: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Order:
        """Update order status and fill information"""
        try:
            order = await self.get_order(order_id)
            if not order:
                raise ValueError(f"Order not found: {order_id}")

            # Update order
            order.status = status
            if filled_price is not None:
                order.filled_price = filled_price
            if filled_size is not None:
                order.filled_size = filled_size
            if error is not None:
                order.error = error
            if metadata:
                order.metadata.update(metadata)

            if status == OrderStatus.FILLED:
                order.filled_timestamp = datetime.utcnow()

            # Save updated state
            await self._save_order_state(order)

            logger.info(f"Updated order {order_id} status to {status.value}")
            return order

        except Exception as e:
            logger.error(f"Error updating order: {str(e)}")
            raise

    async def create_trade(
        self,
        order_id: str,
        position_id: Optional[str],
        price: float,
        size: float,
        fee: float,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Trade:
        """Create a trade from an order fill"""
        try:
            order = await self.get_order(order_id)
            if not order:
                raise ValueError(f"Order not found: {order_id}")

            trade_id = f"trade_{uuid.uuid4().hex[:8]}"
            timestamp = datetime.utcnow()

            trade = Trade(
                trade_id=trade_id,
                order_id=order_id,
                position_id=position_id,
                symbol=order.symbol,
                side=order.side,
                size=size,
                price=price,
                timestamp=timestamp,
                fee=fee,
                metadata=metadata or {}
            )

            # Store in memory
            self.trades[trade_id] = trade

            # Store in state
            await self._save_trade_state(trade)

            logger.info(f"Created trade {trade_id} for order {order_id}")
            return trade

        except Exception as e:
            logger.error(f"Error creating trade: {str(e)}")
            raise

    async def get_order(self, order_id: str) -> Optional[Order]:
        """Get order by ID"""
        try:
            # Try memory first
            if order_id in self.orders:
                return self.orders[order_id]

            # Try state storage
            state = await self.state_manager.get_state(f"order:{order_id}")
            if state:
                # Convert string status back to enum
                state['status'] = OrderStatus(state['status'])
                state['type'] = OrderType(state['type'])
                order = Order(**state)
                self.orders[order_id] = order
                return order

            return None

        except Exception as e:
            logger.error(f"Error getting order: {str(e)}")
            raise

    async def get_trades(
        self,
        symbol: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[Trade]:
        """Get trades filtered by symbol and time range"""
        try:
            trades = list(self.trades.values())

            if symbol:
                trades = [t for t in trades if t.symbol == symbol]

            if start_time:
                trades = [t for t in trades if t.timestamp >= start_time]

            if end_time:
                trades = [t for t in trades if t.timestamp <= end_time]

            return sorted(trades, key=lambda x: x.timestamp)

        except Exception as e:
            logger.error(f"Error getting trades: {str(e)}")
            raise

    async def _save_order_state(self, order: Order) -> None:
        """Save order state"""
        try:
            # Update memory
            self.orders[order.order_id] = order

            # Update state storage
            state = {
                k: v for k, v in order.__dict__.items()
                if not k.startswith('_')
            }
            # Convert enums to strings
            state['status'] = order.status.value
            state['type'] = order.type.value

            await self.state_manager.set_state(
                f"order:{order.order_id}",
                state
            )

        except Exception as e:
            logger.error(f"Error saving order state: {str(e)}")
            raise

    async def _save_trade_state(self, trade: Trade) -> None:
        """Save trade state"""
        try:
            # Update memory
            self.trades[trade.trade_id] = trade

            # Update state storage
            state = {
                k: v for k, v in trade.__dict__.items()
                if not k.startswith('_')
            }

            await self.state_manager.set_state(
                f"trade:{trade.trade_id}",
                state
            )

        except Exception as e:
            logger.error(f"Error saving trade state: {str(e)}")
            raise
