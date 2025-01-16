from typing import Dict, Any, List, Optional, Union
from pydantic import BaseModel, Field


class DatabaseConfig(BaseModel):
    host: str = Field(..., description="Database host address")
    port: int = Field(5432, description="PostgreSQL default port")
    user: str = Field(..., description="Database user")
    password: str = Field(..., description="Database password")
    database: str = Field(..., description="Database name")
    min_connections: int = Field(5, description="Minimum connection pool size")
    max_connections: int = Field(
        20, description="Maximum connection pool size")


class RedisConfig(BaseModel):
    host: str = Field(..., description="Redis host address")
    port: int = Field(6379, description="Redis default port")
    password: Optional[str] = Field(None, description="Redis password")
    db: int = Field(0, description="Redis database number")
    max_connections: int = Field(10, description="Maximum connections in pool")


class JupiterConfig(BaseModel):
    rpc_endpoint: str = Field(..., description="Solana RPC endpoint")
    auth_token: str = Field(...,
                            description="Jupiter API authentication token")
    max_price_impact: float = Field(
        0.01, description="Maximum allowed price impact")
    min_sol_balance: float = Field(
        0.1, description="Minimum SOL balance to maintain")


class ApiConfig(BaseModel):
    host: str = Field(..., description="API host")
    port: int = Field(..., description="API port")
    secret_key: str = Field(..., description="API authentication secret key")


class TradingConfig(BaseModel):
    max_position_size: float = Field(...,
                                     description="Maximum position size in USDC")
    min_position_size: float = Field(...,
                                     description="Minimum position size in USDC")
    max_positions_per_symbol: int = Field(
        ..., description="Maximum concurrent positions per symbol")
    default_stop_loss_percent: float = Field(...,
                                             description="Default stop loss percentage")
    risk_factor: float = Field(...,
                               description="Risk factor for position sizing")


class MACrossoverTemplate(BaseModel):
    fast_ma: int = Field(..., description="Fast moving average period")
    slow_ma: int = Field(..., description="Slow moving average period")
    min_volume: float = Field(..., description="Minimum 24h volume in USDC")
    risk_factor: float = Field(...,
                               description="Strategy-specific risk factor")


class VWAPTemplate(BaseModel):
    period: str = Field(..., description="VWAP calculation period")
    deviation: float = Field(..., description="Standard deviation bands")
    min_volume: float = Field(..., description="Minimum volume requirement")
    risk_factor: float = Field(...,
                               description="Strategy-specific risk factor")


class StrategyTemplates(BaseModel):
    ma_crossover: Dict[str, MACrossoverTemplate]
    vwap: Dict[str, VWAPTemplate]


class Config(BaseModel):
    database: DatabaseConfig
    redis: RedisConfig
    jupiter: JupiterConfig
    api: ApiConfig
    trading: TradingConfig
    # Will be loaded from templates
    strategy_templates: Optional[StrategyTemplates] = None
