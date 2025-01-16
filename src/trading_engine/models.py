from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class OrderStatus(Enum):
    PENDING = "pending"
    FILLED = "filled"
    FAILED = "failed"
    CANCELLED = "cancelled"


class OrderType(Enum):
    MARKET = "market"
    LIMIT = "limit"


class PositionStatus(Enum):
    OPEN = "open"
    CLOSED = "closed"
    CLOSING = "closing"  # When stop loss is triggered but not yet closed


@dataclass
class Order:
    order_id: str
    symbol: str
    side: str  # 'buy' or 'sell'
    size: float
    price: Optional[float]
    type: OrderType
    status: OrderStatus
    timestamp: datetime
    filled_price: Optional[float] = None
    filled_size: Optional[float] = None
    filled_timestamp: Optional[datetime] = None
    metadata: Dict[str, Any] = None
    error: Optional[str] = None


@dataclass
class Position:
    position_id: str
    symbol: str
    side: str
    size: float
    entry_price: float
    current_price: float
    status: PositionStatus
    unrealized_pnl: float
    realized_pnl: float
    entry_time: datetime
    last_update_time: datetime
    stop_loss: Optional[float] = None
    metadata: Dict[str, Any] = None


@dataclass
class Trade:
    trade_id: str
    order_id: str
    position_id: Optional[str]
    symbol: str
    side: str
    size: float
    price: float
    timestamp: datetime
    fee: float
    metadata: Dict[str, Any] = None
