from typing import Dict, Any, Optional
import redis
import json
import logging
from datetime import datetime

from src.config.types import RedisConfig

logger = logging.getLogger(__name__)


class StateManager:
    def __init__(self, config: RedisConfig):
        self.config = config
        self.redis: Optional[redis.Redis] = None

        # Initialize Redis connection
        try:
            self.redis = redis.Redis(
                host=self.config.host,
                port=self.config.port,
                db=self.config.db,
                password=self.config.password,
                max_connections=self.config.max_connections,
                decode_responses=True
            )
            logger.info("Redis connection initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Redis: {str(e)}")
            raise

    def get_state(self, key: str) -> Optional[Dict[str, Any]]:
        """Get state data from Redis"""
        if not self.redis:
            raise RuntimeError("Redis not initialized")

        try:
            data = self.redis.get(key)
            if data is None:
                return None
            return json.loads(str(data))
        except Exception as e:
            logger.error(f"Failed to get state for key {key}: {str(e)}")
            raise

    def set_state(self, key: str, value: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """Set state data in Redis"""
        if not self.redis:
            raise RuntimeError("Redis not initialized")

        try:
            serialized_value = json.dumps(value)
            if ttl:
                return bool(self.redis.setex(key, ttl, serialized_value))
            else:
                return bool(self.redis.set(key, serialized_value))
        except Exception as e:
            logger.error(f"Failed to set state for key {key}: {str(e)}")
            raise

    def delete_state(self, key: str) -> bool:
        """Delete state data from Redis"""
        if not self.redis:
            raise RuntimeError("Redis not initialized")

        try:
            return bool(self.redis.delete(key))
        except Exception as e:
            logger.error(f"Failed to delete state for key {key}: {str(e)}")
            raise

    def get_strategy_state(self, strategy_id: str) -> Optional[Dict[str, Any]]:
        """Get strategy state"""
        key = f"strategy:{strategy_id}:state"
        return self.get_state(key)

    def update_strategy_state(self, strategy_id: str, state: Dict[str, Any]) -> bool:
        """Update strategy state"""
        key = f"strategy:{strategy_id}:state"
        return self.set_state(key, state)

    def get_position_state(self, position_id: str) -> Optional[Dict[str, Any]]:
        """Get position state"""
        key = f"position:{position_id}:state"
        return self.get_state(key)

    def update_position_state(self, position_id: str, state: Dict[str, Any]) -> bool:
        """Update position state"""
        key = f"position:{position_id}:state"
        return self.set_state(key, state)

    def get_market_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get latest market data"""
        key = f"market:{symbol}:latest"
        return self.get_state(key)

    def update_market_data(self, symbol: str, data: Dict[str, Any]) -> bool:
        """Update latest market data"""
        key = f"market:{symbol}:latest"
        return self.set_state(key, data, ttl=60)

    def get_custom_data(self, data_type: str, symbol: str) -> Optional[Dict[str, Any]]:
        """Get custom data"""
        key = f"custom:{data_type}:{symbol}"
        return self.get_state(key)

    def update_custom_data(
        self,
        data_type: str,
        symbol: str,
        data: Dict[str, Any],
        ttl: Optional[int] = None
    ) -> bool:
        """Update custom data"""
        key = f"custom:{data_type}:{symbol}"
        return self.set_state(key, data, ttl=ttl)

    def close(self):
        """Close Redis connection"""
        if self.redis:
            self.redis.close()
            logger.info("Redis connection closed")
