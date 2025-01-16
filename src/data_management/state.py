from typing import Dict, Any, Optional
import aioredis
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class StateManager:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.redis: Optional[aioredis.Redis] = None

    async def initialize(self):
        """Initialize Redis connection"""
        try:
            self.redis = await aioredis.create_redis_pool(
                f'redis://{self.config["host"]}:{self.config["port"]}',
                db=self.config.get("db", 0),
                password=self.config.get("password"),
                maxsize=self.config.get("max_connections", 10)
            )
            logger.info("Redis connection initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Redis: {str(e)}")
            raise

    async def get_state(self, key: str) -> Optional[Dict[str, Any]]:
        """Get state data from Redis"""
        if not self.redis:
            raise RuntimeError("Redis not initialized")

        try:
            data = await self.redis.get(key)
            return json.loads(data) if data else None
        except Exception as e:
            logger.error(f"Failed to get state for key {key}: {str(e)}")
            raise

    async def set_state(self, key: str, value: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """Set state data in Redis"""
        if not self.redis:
            raise RuntimeError("Redis not initialized")

        try:
            serialized_value = json.dumps(value)
            if ttl:
                await self.redis.setex(key, ttl, serialized_value)
            else:
                await self.redis.set(key, serialized_value)
            return True
        except Exception as e:
            logger.error(f"Failed to set state for key {key}: {str(e)}")
            raise

    async def delete_state(self, key: str) -> bool:
        """Delete state data from Redis"""
        if not self.redis:
            raise RuntimeError("Redis not initialized")

        try:
            return await self.redis.delete(key) > 0
        except Exception as e:
            logger.error(f"Failed to delete state for key {key}: {str(e)}")
            raise

    async def get_strategy_state(self, strategy_id: str) -> Optional[Dict[str, Any]]:
        """Get strategy state"""
        key = f"strategy:{strategy_id}:state"
        return await self.get_state(key)

    async def update_strategy_state(self, strategy_id: str, state: Dict[str, Any]) -> bool:
        """Update strategy state"""
        key = f"strategy:{strategy_id}:state"
        return await self.set_state(key, state)

    async def get_position_state(self, position_id: str) -> Optional[Dict[str, Any]]:
        """Get position state"""
        key = f"position:{position_id}:state"
        return await self.get_state(key)

    async def update_position_state(self, position_id: str, state: Dict[str, Any]) -> bool:
        """Update position state"""
        key = f"position:{position_id}:state"
        return await self.set_state(key, state)

    async def get_market_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get latest market data"""
        key = f"market:{symbol}:latest"
        return await self.get_state(key)

    async def update_market_data(self, symbol: str, data: Dict[str, Any]) -> bool:
        """Update latest market data"""
        key = f"market:{symbol}:latest"
        # Market data typically needs a short TTL
        return await self.set_state(key, data, ttl=self.config.get("market_data_ttl", 60))

    async def get_custom_data(self, data_type: str, symbol: str) -> Optional[Dict[str, Any]]:
        """Get custom data"""
        key = f"custom:{data_type}:{symbol}"
        return await self.get_state(key)

    async def update_custom_data(
        self,
        data_type: str,
        symbol: str,
        data: Dict[str, Any],
        ttl: Optional[int] = None
    ) -> bool:
        """Update custom data"""
        key = f"custom:{data_type}:{symbol}"
        return await self.set_state(key, data, ttl=ttl)

    async def close(self):
        """Close Redis connection"""
        if self.redis:
            self.redis.close()
            await self.redis.wait_closed()
            logger.info("Redis connection closed")
