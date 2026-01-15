"""
Utility functions for the YC Startup Scraper.
Includes rate limiting, retry logic, and logging configuration.
"""

import asyncio
import logging
import random
from functools import wraps
from typing import Any, Callable


def setup_logging(level: int = logging.INFO) -> logging.Logger:
    """Configure and return a logger for the scraper."""
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    return logging.getLogger("yc_scraper")


logger = setup_logging()


class RateLimiter:
    """
    Async rate limiter to control request frequency.
    Uses a semaphore to limit concurrent requests.
    """
    
    def __init__(self, requests_per_second: float = 5, max_concurrent: int = 10):
        self.delay = 1.0 / requests_per_second
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.last_request_time = 0
        self._lock = asyncio.Lock()
    
    async def acquire(self):
        """Wait for rate limit and semaphore before making a request."""
        await self.semaphore.acquire()
        async with self._lock:
            now = asyncio.get_event_loop().time()
            time_since_last = now - self.last_request_time
            if time_since_last < self.delay:
                await asyncio.sleep(self.delay - time_since_last)
            self.last_request_time = asyncio.get_event_loop().time()
    
    def release(self):
        """Release the semaphore after request completes."""
        self.semaphore.release()


async def retry_async(
    func: Callable,
    max_retries: int = 3,
    base_delay: float = 1.0,
    *args,
    **kwargs
) -> Any:
    """
    Retry an async function with exponential backoff.
    
    Args:
        func: Async function to retry
        max_retries: Maximum number of retry attempts
        base_delay: Base delay between retries (doubles each attempt)
        *args, **kwargs: Arguments to pass to the function
    
    Returns:
        Result of the function call
    
    Raises:
        Last exception if all retries fail
    """
    last_exception = None
    
    for attempt in range(max_retries + 1):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            last_exception = e
            if attempt < max_retries:
                delay = base_delay * (2 ** attempt) + random.uniform(0, 0.5)
                logger.warning(
                    f"Attempt {attempt + 1} failed: {e}. Retrying in {delay:.2f}s..."
                )
                await asyncio.sleep(delay)
            else:
                logger.error(f"All {max_retries + 1} attempts failed: {e}")
    
    raise last_exception
