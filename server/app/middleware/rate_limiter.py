"""Rate limiting middleware (Redis-based, sliding window algorithm)."""

from typing import Optional, Tuple
import time
import logging
from redis import Redis
from redis.exceptions import RedisError
from config import settings
from core.exceptions import RateLimitExceededError

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Redis-based rate limiter using sliding window algorithm.
    
    More accurate than fixed window:
    - Fixed window: resets at exact times (boundary condition problems)
    - Sliding window: uses timestamps for precise rate limiting
    """
    

    def __init__(self, redis_client: Redis, enabled: bool = True):
        """
        Initialize rate limiter.
        
        Args:
            redis_client: Redis connection
            enabled: Enable/disable rate limiting
        """
        self.redis = redis_client
        self.enabled = enabled
        self.requests_per_minute = settings.RATE_LIMIT_REQUESTS
        self.window_seconds = settings.RATE_LIMIT_WINDOW_SECONDS
    
    async def check_rate_limit(
        self,
        key: str,
        limit: Optional[int] = None,
        window: Optional[int] = None
    ) -> Tuple[bool, Optional[int]]:
        """
        Check if request is within rate limit using sliding window.
        
        Args:
            key: Unique identifier (user_id, IP, etc)
            limit: Custom limit (overrides default)
            window: Custom window in seconds (overrides default)
        
        Returns:
            Tuple of (allowed: bool, retry_after: Optional[int])
            
        Raises:
            RateLimitExceededError: If limit exceeded
        """
        
        if not self.enabled:
            return True, None
        
        limit = limit or self.requests_per_minute
        window = window or self.window_seconds
        
        try:
            # Current timestamp
            now = time.time()
            window_start = now - window
            
            # Redis key for sliding window
            redis_key = f"rate_limit:{key}"
            
            # Remove old timestamps outside window
            self.redis.zremrangebyscore(redis_key, 0, window_start)
            
            # Count requests in current window
            current_count = self.redis.zcard(redis_key)
            
            if current_count >= limit:
                # Calculate retry_after: oldest timestamp + window
                oldest = self.redis.zrange(redis_key, 0, 0, withscores=True)
                if oldest:
                    oldest_timestamp = oldest[0][1]
                    retry_after = int((oldest_timestamp + window) - now) + 1
                else:
                    retry_after = window
                
                logger.warning(f"Rate limit exceeded for {key}: {current_count}/{limit}")
                raise RateLimitExceededError(
                    message=f"Rate limit exceeded: {current_count}/{limit} requests",
                    retry_after=retry_after
                )
            
            # Add current request timestamp
            self.redis.zadd(redis_key, {str(now): now})
            
            # Set expiration on key (window + 1 second buffer)
            self.redis.expire(redis_key, window + 1)
            
            return True, None
        
        except RateLimitExceededError:
            raise
        except RedisError as e:
            logger.error(f"Rate limiter Redis error: {str(e)}")
            # Fail open: allow request if Redis is down
            return True, None
        except Exception as e:
            logger.error(f"Rate limiter unexpected error: {str(e)}")
            return True, None
    
    def get_remaining(self, key: str, limit: Optional[int] = None) -> int:
        """Get remaining requests for a key."""
        if not self.enabled:
            return limit or self.requests_per_minute
        
        try:
            limit = limit or self.requests_per_minute
            redis_key = f"rate_limit:{key}"
            current_count = self.redis.zcard(redis_key)
            return max(0, limit - current_count)
        except RedisError:
            return limit or self.requests_per_minute
    
    def reset(self, key: str) -> bool:
        """Reset rate limit for a key."""
        try:
            redis_key = f"rate_limit:{key}"
            self.redis.delete(redis_key)
            logger.info(f"Rate limit reset for {key}")
            return True
        except RedisError as e:
            logger.error(f"Failed to reset rate limit: {str(e)}")
            return False


class IPRateLimiter:
    """Rate limiter by IP address."""
    
    def __init__(self, redis_client: Redis):
        self.limiter = RateLimiter(redis_client, settings.RATE_LIMIT_ENABLED)
    
    async def check(self, client_ip: str) -> Tuple[bool, Optional[int]]:
        """Check rate limit for IP."""
        key = f"ip:{client_ip}"
        return await self.limiter.check_rate_limit(key)


class UserRateLimiter:
    """Rate limiter by user ID."""
    
    def __init__(self, redis_client: Redis):
        self.limiter = RateLimiter(redis_client, settings.RATE_LIMIT_ENABLED)
    
    async def check(self, user_id: str, limit: int = 100) -> Tuple[bool, Optional[int]]:
        """Check rate limit for user."""
        key = f"user:{user_id}"
        return await self.limiter.check_rate_limit(key, limit=limit)


class EndpointRateLimiter:
    """Rate limiter by endpoint."""
    
    def __init__(self, redis_client: Redis):
        self.limiter = RateLimiter(redis_client, settings.RATE_LIMIT_ENABLED)
    
    async def check(self, endpoint: str, client_ip: str, limit: int = 60) -> Tuple[bool, Optional[int]]:
        """Check rate limit for specific endpoint + IP combo."""
        key = f"endpoint:{endpoint}:{client_ip}"
        return await self.limiter.check_rate_limit(key, limit=limit, window=60)
