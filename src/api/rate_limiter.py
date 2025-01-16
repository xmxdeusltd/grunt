from typing import Dict, Any, Optional
import logging
from datetime import datetime, timedelta
import asyncio
from fastapi import HTTPException

logger = logging.getLogger(__name__)


class RateLimiter:
    def __init__(self, redis_client: Any, config: Dict[str, Any]):
        self.redis = redis_client
        self.config = config
        self.limits = {
            "trade": {
                "requests": config["api"]["rate_limits"]["trade"]["requests"],
                "period": config["api"]["rate_limits"]["trade"]["period"]
            },
            "query": {
                "requests": config["api"]["rate_limits"]["query"]["requests"],
                "period": config["api"]["rate_limits"]["query"]["period"]
            }
        }

    async def check_rate_limit(
        self,
        key: str,
        limit_type: str,
        max_requests: Optional[int] = None,
        period: Optional[int] = None
    ) -> bool:
        """Check if request is within rate limit"""
        try:
            # Get limit settings
            limit_config = self.limits.get(limit_type, self.limits["query"])
            max_requests = max_requests or limit_config["requests"]
            period = period or limit_config["period"]

            # Get current count
            count_key = f"rate_limit:{limit_type}:{key}"
            count = await self.redis.get(count_key)

            if count is None:
                # First request
                await self.redis.setex(count_key, period, 1)
                return True

            count = int(count)
            if count >= max_requests:
                return False

            # Increment counter
            await self.redis.incr(count_key)
            return True

        except Exception as e:
            logger.error(f"Error checking rate limit: {str(e)}")
            # Allow request on error
            return True

    async def increment_counter(self, key: str, limit_type: str) -> None:
        """Increment rate limit counter"""
        try:
            count_key = f"rate_limit:{limit_type}:{key}"
            period = self.limits.get(
                limit_type, self.limits["query"])["period"]

            # Check if key exists
            exists = await self.redis.exists(count_key)
            if exists:
                await self.redis.incr(count_key)
            else:
                await self.redis.setex(count_key, period, 1)

        except Exception as e:
            logger.error(f"Error incrementing counter: {str(e)}")

    async def reset_counter(self, key: str, limit_type: str) -> None:
        """Reset rate limit counter"""
        try:
            count_key = f"rate_limit:{limit_type}:{key}"
            await self.redis.delete(count_key)

        except Exception as e:
            logger.error(f"Error resetting counter: {str(e)}")


class RateLimitMiddleware:
    def __init__(self, rate_limiter: RateLimiter):
        self.rate_limiter = rate_limiter

    async def __call__(self, request, call_next):
        """Rate limit middleware"""
        try:
            # Get client IP
            client_ip = request.client.host

            # Determine limit type based on path
            limit_type = "trade" if "/trade" in request.url.path else "query"

            # Check rate limit
            if not await self.rate_limiter.check_rate_limit(client_ip, limit_type):
                raise HTTPException(
                    status_code=429,
                    detail="Rate limit exceeded"
                )

            # Process request
            response = await call_next(request)

            # Increment counter on success
            await self.rate_limiter.increment_counter(client_ip, limit_type)

            return response

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error in rate limit middleware: {str(e)}")
            return await call_next(request)
