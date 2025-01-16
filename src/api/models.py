from typing import Dict, Any, Optional, List, Union
from pydantic import BaseModel, Field
from datetime import datetime


class TradeRequest(BaseModel):
    symbol: str = Field(...,
                        description="Trading pair symbol (e.g., 'SOL-USDC')")
    side: str = Field(..., description="Trade side: 'buy' or 'sell'")
    size: float = Field(..., gt=0, description="Trade size")
    type: str = Field("market", description="Order type: 'market' or 'limit'")
    stop_loss: Optional[float] = Field(
        None, description="Optional stop loss price")
    metadata: Optional[Dict[str, Any]] = Field(
        None, description="Additional metadata")


class StrategyConfig(BaseModel):
    symbol: str = Field(..., description="Trading pair symbol")
    type: str = Field(..., description="Strategy type (e.g., 'ma_crossover')")
    template: Optional[str] = Field(
        "default", description="Strategy template name")
    parameters: Dict[str, Any] = Field(..., description="Strategy parameters")


class StrategyUpdate(BaseModel):
    active: Optional[bool] = Field(None, description="Strategy active status")
    parameters: Optional[Dict[str, Any]] = Field(
        None, description="Updated parameters")
    metadata: Optional[Dict[str, Any]] = Field(
        None, description="Additional metadata")


class TimeRange(BaseModel):
    start_time: Optional[datetime] = Field(
        None, description="Start time for data range")
    end_time: Optional[datetime] = Field(
        None, description="End time for data range")


class APIResponse(BaseModel):
    success: bool = Field(..., description="Operation success status")
    data: Optional[Union[Dict[str, Any], List[Any], Any]
                   ] = Field(None, description="Response data")
    error: Optional[str] = Field(None, description="Error message if any")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
