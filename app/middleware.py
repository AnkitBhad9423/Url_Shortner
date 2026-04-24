# app/middleware.py

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from app.database import get_redis
import time


class IPBlacklistMiddleware(BaseHTTPMiddleware):
    """
    Runs before every request.
    Blocks IPs that are in the Redis blacklist.
    """
    async def dispatch(self, request: Request, call_next):
        redis = get_redis()
        ip = request.client.host

        if redis:
            try:
                blocked = await redis.get(f"blacklist:ip:{ip}")
                if blocked:
                    return JSONResponse(
                        status_code=403,
                        content={"detail": f"Your IP has been blocked. Reason: {blocked}"}
                    )
            except Exception:
                pass  # if Redis fails, don't block legitimate users

        return await call_next(request)


class SlidingWindowRateLimiter(BaseHTTPMiddleware):
    """
    Sliding window rate limiter using Redis sorted sets.

    How it works:
    - Each IP has a sorted set in Redis
    - Score = timestamp of each request
    - On each request:
        1. Remove all entries older than the window
        2. Count remaining entries
        3. If count >= limit → block (429)
        4. Otherwise → add current timestamp → allow

    Why sliding window over fixed window:
    - Fixed window: 100 req allowed in minute 1:00–2:00
      User sends 100 at 1:59 and 100 at 2:00 → 200 req in 2 seconds ❌
    - Sliding window: always looks at last 60 seconds → no burst exploit ✅
    """

    def __init__(self, app, requests_per_window: int = 20, window_seconds: int = 60):
        super().__init__(app)
        self.requests_per_window = requests_per_window
        self.window_seconds = window_seconds

    async def dispatch(self, request: Request, call_next):
        # skip rate limiting for docs and health
        if request.url.path in ("/docs", "/openapi.json", "/health", "/redoc"):
            return await call_next(request)

        redis = get_redis()
        if not redis:
            return await call_next(request)  # if Redis down, don't block users

        ip = request.client.host
        key = f"ratelimit:{ip}"
        now = time.time()
        window_start = now - self.window_seconds

        try:
            pipe = redis.pipeline()
            # remove requests older than window
            await pipe.zremrangebyscore(key, 0, window_start)
            # count requests in current window
            await pipe.zcard(key)
            # add current request
            await pipe.zadd(key, {str(now): now})
            # set key expiry
            await pipe.expire(key, self.window_seconds)
            results = await pipe.execute()

            request_count = results[1]  # zcard result

            if request_count >= self.requests_per_window:
                return JSONResponse(
                    status_code=429,
                    content={
                        "detail": f"Rate limit exceeded. Max {self.requests_per_window} requests per {self.window_seconds} seconds.",
                        "retry_after": self.window_seconds
                    }
                )
        except Exception as e:
            print(f"⚠️ Rate limiter error: {e}")
            # if rate limiter fails, allow request through

        return await call_next(request)