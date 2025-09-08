"""
Intelligent retry manager for external API integrations
Handles retryable failures with exponential backoff
"""

import asyncio
import logging
from typing import Dict, List, Callable, Any
from enum import Enum

logger = logging.getLogger(__name__)

class RetryableError(Exception):
    """Exception for retryable errors"""
    pass

class RetryStrategy(Enum):
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    FIXED_DELAY = "fixed_delay"
    LINEAR_BACKOFF = "linear_backoff"

class RetryManager:
    """
    Intelligent retry manager with configurable strategies
    """

    def __init__(self,
                 max_retries: int = 3,
                 base_delay: float = 1.0,
                 max_delay: float = 10.0,
                 strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF):

        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.strategy = strategy

        # Define retryable conditions per service
        self.retryable_conditions = {
            "notion": [429, 500, 502, 503, 504, "TimeoutError"],
            "clickup": [429, 500, 502, 503, 504, "TimeoutError"],
            "slack": ["rate_limited", "timeout", 500, 502, 503],
            "task_creation": [429, 500, 502, 503, 504, "TimeoutError", "network_error"]
        }

    async def execute_with_retry(self,
                                func: Callable,
                                service_name: str,
                                *args,
                                **kwargs) -> Dict:
        """
        Execute function with intelligent retry logic
        """
        last_error = None

        for attempt in range(self.max_retries + 1):  # +1 for initial attempt
            try:
                logger.info(f"[{service_name}] Attempt {attempt + 1}/{self.max_retries + 1}")

                result = await func(*args, **kwargs)

                # Check if result indicates success
                if result.get("success"):
                    if attempt > 0:
                        logger.info(f"[{service_name}] Success after {attempt + 1} attempts")
                    # Add retry metadata to successful results
                    return {
                        "success": True,
                        "result": result,
                        "attempts_made": attempt + 1,
                        "retries_exhausted": False
                    }

                # Check if error is non-retryable - fail immediately
                if not self._is_retryable_error(result, service_name):
                    logger.error(f"[{service_name}] Non-retryable error, aborting: {result.get('error', 'Unknown error')}")
                    return {
                        "success": False,
                        "error": result.get("error", "Non-retryable error"),
                        "retries_exhausted": False,
                        "attempts_made": attempt + 1
                    }

                # Result indicates retryable failure
                last_error = result.get("error", "Unknown retryable error")
                logger.warning(f"[{service_name}] Attempt {attempt + 1} failed with retryable error: {last_error}")

            except Exception as e:
                last_error = str(e)
                logger.warning(f"[{service_name}] Attempt {attempt + 1} exception: {e}")

                # Check if exception is retryable
                error_result = {"success": False, "error": str(e), "exception": True}
                if not self._is_retryable_error(error_result, service_name):
                    logger.error(f"[{service_name}] Non-retryable exception, aborting: {e}")
                    return {
                        "success": False,
                        "error": f"Non-retryable error: {last_error}",
                        "retries_exhausted": False,
                        "attempts_made": attempt + 1
                    }

            # If not the last attempt, wait before retrying
            if attempt < self.max_retries:
                delay = self._calculate_delay(attempt)
                logger.info(f"[{service_name}] Retrying in {delay:.1f}s...")
                await asyncio.sleep(delay)

        # All attempts exhausted
        logger.error(f"[{service_name}] All {self.max_retries + 1} attempts failed. Last error: {last_error}")
        return {
            "success": False,
            "error": f"Max retries exceeded. Last error: {last_error}",
            "retries_exhausted": True,
            "attempts_made": self.max_retries + 1
        }

    def _is_retryable_error(self, result: Dict, service_name: str) -> bool:
        """Check if error is retryable for given service"""
        if result.get("success"):
            return False

        # Check explicit retryable flag
        if "retryable" in result:
            return result["retryable"]

        # Check service-specific retryable conditions
        retryable_codes = self.retryable_conditions.get(service_name, [])

        # Check status code
        status_code = result.get("status_code")
        if status_code in retryable_codes:
            return True

        # Check error code
        error_code = result.get("error_code")
        if error_code in retryable_codes:
            return True

        # Check error message patterns
        error_msg = result.get("error", "").lower()
        retryable_patterns = ["timeout", "rate limit", "server error", "network error", "connection", "temporary"]
        if any(pattern in error_msg for pattern in retryable_patterns):
            return True

        # Check for exceptions that are typically retryable
        if result.get("exception"):
            retryable_exceptions = ["TimeoutError", "ConnectionError", "HTTPError", "RequestException"]
            error_str = str(result.get("error", ""))
            if any(exc_type in error_str for exc_type in retryable_exceptions):
                return True

        return False

    def _calculate_delay(self, attempt: int) -> float:
        """Calculate delay based on retry strategy"""
        if self.strategy == RetryStrategy.EXPONENTIAL_BACKOFF:
            delay = self.base_delay * (2 ** attempt)
        elif self.strategy == RetryStrategy.LINEAR_BACKOFF:
            delay = self.base_delay * (attempt + 1)
        else:  # FIXED_DELAY
            delay = self.base_delay

        return min(delay, self.max_delay)

    def get_retry_statistics(self) -> Dict:
        """Get retry statistics for monitoring"""
        return {
            "max_retries": self.max_retries,
            "base_delay": self.base_delay,
            "max_delay": self.max_delay,
            "strategy": self.strategy.value,
            "retryable_conditions": self.retryable_conditions
        }

# Global retry manager instance
retry_manager = RetryManager()

# Convenience function for quick usage
async def retry_async_function(func: Callable, service_name: str = "generic",
                              max_retries: int = 3, *args, **kwargs) -> Dict:
    """
    Convenience function to retry any async function

    Usage:
        result = await retry_async_function(
            some_api_call,
            "my_service",
            arg1="value1"
        )
    """
    temp_retry_manager = RetryManager(max_retries=max_retries)
    return await temp_retry_manager.execute_with_retry(func, service_name, *args, **kwargs)
