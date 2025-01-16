from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Signal:
    strategy_id: str
    symbol: str
    side: str  # 'buy' or 'sell'
    size: float
    price: Optional[float]
    timestamp: datetime
    metadata: Dict[str, Any]
    signal_type: str  # 'entry' or 'exit'
    confidence: float
    expiry: Optional[datetime] = None


@dataclass
class StrategyState:
    strategy_id: str
    symbol: str
    active: bool
    last_update: datetime
    position_size: float
    current_position: Optional[Dict[str, Any]]
    metadata: Dict[str, Any]


@dataclass
class DataPoint:
    data_type: str
    symbol: str
    timestamp: datetime
    value: Any
    metadata: Dict[str, Any]
