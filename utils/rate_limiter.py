import asyncio
import time
from collections import defaultdict

class GlobalRateLimiter:
    """Per-token token bucket to throttle requests."""
    def __init__(self, tokens, rate=50, capacity=50):
        self.buckets = {token: asyncio.Semaphore(capacity) for token in tokens}  # simplified

    async def acquire(self, token):
        await self.buckets[token].acquire()

    def release(self, token):
        self.buckets[token].release()
