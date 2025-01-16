from typing import Dict, Any, Optional, List
import logging
from datetime import datetime
import uuid
from .models import Position, PositionStatus, Order, Trade

logger = logging.getLogger(__name__)


class PositionManager:
    def __init__(self, state_manager: Any):
        self.state_manager = state_manager
        self.positions: Dict[str, Position] = {}

    async def create_position(
        self,
        symbol: str,
        side: str,
        size: float,
        entry_price: float,
        stop_loss: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Position:
        """Create a new position"""
        try:
            position_id = f"pos_{uuid.uuid4().hex[:8]}"
            timestamp = datetime.utcnow()

            position = Position(
                position_id=position_id,
                symbol=symbol,
                side=side,
                size=size,
                entry_price=entry_price,
                current_price=entry_price,
                status=PositionStatus.OPEN,
                unrealized_pnl=0.0,
                realized_pnl=0.0,
                entry_time=timestamp,
                last_update_time=timestamp,
                stop_loss=stop_loss,
                metadata=metadata or {}
            )

            # Store in memory
            self.positions[position_id] = position

            # Store in state
            await self._save_position_state(position)

            logger.info(f"Created position {position_id} for {symbol}")
            return position

        except Exception as e:
            logger.error(f"Error creating position: {str(e)}")
            raise

    async def update_position(
        self,
        position_id: str,
        current_price: float,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Position:
        """Update position with current price and calculate PnL"""
        try:
            position = await self.get_position(position_id)
            if not position:
                raise ValueError(f"Position not found: {position_id}")

            # Update price and PnL
            position.current_price = current_price
            position.last_update_time = datetime.utcnow()

            # Calculate unrealized PnL
            price_diff = current_price - position.entry_price
            if position.side == "sell":
                price_diff = -price_diff
            position.unrealized_pnl = price_diff * position.size

            # Update metadata if provided
            if metadata:
                position.metadata.update(metadata)

            # Check stop loss
            if position.stop_loss and position.status == PositionStatus.OPEN:
                if (position.side == "buy" and current_price <= position.stop_loss) or \
                   (position.side == "sell" and current_price >= position.stop_loss):
                    position.status = PositionStatus.CLOSING
                    logger.info(
                        f"Stop loss triggered for position {position_id}")

            # Save updated state
            await self._save_position_state(position)

            return position

        except Exception as e:
            logger.error(f"Error updating position: {str(e)}")
            raise

    async def close_position(
        self,
        position_id: str,
        close_price: float,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Position:
        """Close a position"""
        try:
            position = await self.get_position(position_id)
            if not position:
                raise ValueError(f"Position not found: {position_id}")

            if position.status == PositionStatus.CLOSED:
                raise ValueError(f"Position already closed: {position_id}")

            # Calculate realized PnL
            price_diff = close_price - position.entry_price
            if position.side == "sell":
                price_diff = -price_diff
            position.realized_pnl = price_diff * position.size
            position.unrealized_pnl = 0
            position.current_price = close_price
            position.status = PositionStatus.CLOSED
            position.last_update_time = datetime.utcnow()

            if metadata:
                position.metadata.update(metadata)

            # Save updated state
            await self._save_position_state(position)

            logger.info(
                f"Closed position {position_id} with PnL {position.realized_pnl}")
            return position

        except Exception as e:
            logger.error(f"Error closing position: {str(e)}")
            raise

    async def get_position(self, position_id: str) -> Optional[Position]:
        """Get position by ID"""
        try:
            # Try memory first
            if position_id in self.positions:
                return self.positions[position_id]

            # Try state storage
            state = await self.state_manager.get_state(f"position:{position_id}")
            if state:
                position = Position(**state)
                self.positions[position_id] = position
                return position

            return None

        except Exception as e:
            logger.error(f"Error getting position: {str(e)}")
            raise

    async def get_open_positions(self, symbol: Optional[str] = None) -> List[Position]:
        """Get all open positions, optionally filtered by symbol"""
        try:
            open_positions = [
                pos for pos in self.positions.values()
                if pos.status in [PositionStatus.OPEN, PositionStatus.CLOSING]
                and (not symbol or pos.symbol == symbol)
            ]
            return open_positions

        except Exception as e:
            logger.error(f"Error getting open positions: {str(e)}")
            raise

    async def _save_position_state(self, position: Position) -> None:
        """Save position state"""
        try:
            # Update memory
            self.positions[position.position_id] = position

            # Update state storage
            state = {
                k: v for k, v in position.__dict__.items()
                if not k.startswith('_')
            }
            # Convert enums to strings
            state['status'] = position.status.value

            await self.state_manager.set_state(
                f"position:{position.position_id}",
                state
            )

        except Exception as e:
            logger.error(f"Error saving position state: {str(e)}")
            raise
