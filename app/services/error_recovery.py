"""
Comprehensive error recovery system for blockchain operations
Handles retries, fallbacks, and user-friendly error messages
"""
import logging
from typing import Dict, Optional, Any, Callable, Coroutine
from enum import Enum
from datetime import datetime, timedelta
from functools import wraps
import asyncio

logger = logging.getLogger(__name__)


class RecoveryStrategy(Enum):
    """Strategies for handling errors"""
    RETRY = "retry"                    # Retry with exponential backoff
    FALLBACK = "fallback"              # Use fallback value/function
    SKIP = "skip"                      # Skip this operation
    FAIL = "fail"                      # Propagate error


class ErrorRecoveryConfig:
    """Configuration for error recovery"""
    
    def __init__(
        self,
        strategy: RecoveryStrategy = RecoveryStrategy.RETRY,
        max_retries: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        backoff_multiplier: float = 2.0,
        fallback_value: Optional[Any] = None,
        fallback_func: Optional[Callable] = None,
        user_message: str = "Operation failed, please try again",
    ):
        """Initialize recovery config"""
        self.strategy = strategy
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.backoff_multiplier = backoff_multiplier
        self.fallback_value = fallback_value
        self.fallback_func = fallback_func
        self.user_message = user_message


class RecoveryContext:
    """Tracks recovery attempts for a single operation"""
    
    def __init__(self, operation_name: str, config: ErrorRecoveryConfig):
        """Initialize recovery context"""
        self.operation_name = operation_name
        self.config = config
        self.attempt = 0
        self.last_error: Optional[Exception] = None
        self.start_time = datetime.utcnow()
        self.errors: list = []
    
    def record_error(self, error: Exception) -> None:
        """Record an error attempt"""
        self.attempt += 1
        self.last_error = error
        self.errors.append({
            "attempt": self.attempt,
            "error": str(error),
            "timestamp": datetime.utcnow().isoformat()
        })
        logger.debug(f"[{self.operation_name}] Attempt {self.attempt} failed: {error}")
    
    def should_retry(self) -> bool:
        """Check if we should retry"""
        if self.config.strategy != RecoveryStrategy.RETRY:
            return False
        return self.attempt < self.config.max_retries
    
    def get_next_delay(self) -> float:
        """Calculate delay before next retry (exponential backoff)"""
        delay = self.config.initial_delay * (self.config.backoff_multiplier ** (self.attempt - 1))
        return min(delay, self.config.max_delay)
    
    def get_summary(self) -> Dict[str, Any]:
        """Get recovery attempt summary"""
        elapsed = (datetime.utcnow() - self.start_time).total_seconds()
        return {
            "operation": self.operation_name,
            "total_attempts": self.attempt,
            "strategy": self.config.strategy.value,
            "elapsed_seconds": elapsed,
            "errors": self.errors,
            "user_message": self.config.user_message
        }


class ErrorRecoveryManager:
    """Manages error recovery for operations"""
    
    def __init__(self):
        """Initialize recovery manager"""
        self._contexts: Dict[str, RecoveryContext] = {}
        logger.info("ErrorRecoveryManager initialized")
    
    async def execute_with_recovery(
        self,
        operation_name: str,
        func: Callable,
        config: ErrorRecoveryConfig,
        *args,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute function with automatic error recovery
        
        Args:
            operation_name: Name of operation for logging
            func: Async function to execute
            config: Recovery configuration
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Result dict with success status and data/error
        """
        context = RecoveryContext(operation_name, config)
        self._contexts[operation_name] = context
        
        try:
            logger.info(f"Starting operation: {operation_name}")
            
            while True:
                try:
                    # Try to execute the function
                    result = await func(*args, **kwargs)
                    logger.info(f"Operation {operation_name} succeeded on attempt {context.attempt + 1}")
                    return {
                        "success": True,
                        "data": result,
                        "attempts": context.attempt + 1,
                        "strategy": config.strategy.value
                    }
                
                except Exception as e:
                    context.record_error(e)
                    
                    if context.should_retry():
                        delay = context.get_next_delay()
                        logger.warning(
                            f"Operation {operation_name} failed, retrying in {delay}s "
                            f"(attempt {context.attempt}/{config.max_retries})"
                        )
                        await asyncio.sleep(delay)
                        continue
                    else:
                        break
            
            # Max retries exceeded or strategy doesn't allow retry
            if config.strategy == RecoveryStrategy.FALLBACK:
                if config.fallback_func:
                    logger.info(f"Using fallback function for {operation_name}")
                    result = await config.fallback_func(*args, **kwargs) if asyncio.iscoroutinefunction(config.fallback_func) else config.fallback_func(*args, **kwargs)
                    return {
                        "success": True,
                        "data": result,
                        "attempts": context.attempt,
                        "strategy": "fallback_function",
                        "warning": "Used fallback logic"
                    }
                elif config.fallback_value is not None:
                    logger.info(f"Using fallback value for {operation_name}")
                    return {
                        "success": True,
                        "data": config.fallback_value,
                        "attempts": context.attempt,
                        "strategy": "fallback_value",
                        "warning": "Used fallback value"
                    }
            
            # Operation failed exhausted retry attempts
            error_summary = context.get_summary()
            logger.error(f"Operation {operation_name} failed after {context.attempt} attempts")
            
            return {
                "success": False,
                "error": str(context.last_error),
                "user_message": config.user_message,
                "attempts": context.attempt,
                "strategy": config.strategy.value,
                "details": error_summary
            }
        
        finally:
            # Cleanup
            if operation_name in self._contexts:
                del self._contexts[operation_name]
    
    async def execute_with_timeout(
        self,
        operation_name: str,
        func: Callable,
        timeout_seconds: float = 30,
        *args,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute function with timeout protection
        
        Args:
            operation_name: Name of operation
            func: Async function to execute
            timeout_seconds: Timeout in seconds
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Result dict with success status
        """
        try:
            logger.debug(f"Executing {operation_name} with {timeout_seconds}s timeout")
            result = await asyncio.wait_for(func(*args, **kwargs), timeout=timeout_seconds)
            return {
                "success": True,
                "data": result
            }
        except asyncio.TimeoutError:
            logger.error(f"Operation {operation_name} timed out after {timeout_seconds}s")
            return {
                "success": False,
                "error": f"Operation timed out after {timeout_seconds} seconds",
                "user_message": "Operation took too long, please try again"
            }
        except Exception as e:
            logger.error(f"Operation {operation_name} failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "user_message": "An unexpected error occurred"
            }


# Global recovery manager instance
_recovery_manager = ErrorRecoveryManager()


def get_recovery_manager() -> ErrorRecoveryManager:
    """Get the global error recovery manager"""
    return _recovery_manager


# Decorator for functions that need recovery
def with_recovery(config: ErrorRecoveryConfig = None):
    """Decorator for adding recovery to async functions"""
    if config is None:
        config = ErrorRecoveryConfig()
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            operation_name = f"{func.__module__}.{func.__name__}"
            return await get_recovery_manager().execute_with_recovery(
                operation_name,
                func,
                config,
                *args,
                **kwargs
            )
        return wrapper
    return decorator


# Common recovery configurations
BLOCKCHAIN_QUERY_RECOVERY = ErrorRecoveryConfig(
    strategy=RecoveryStrategy.RETRY,
    max_retries=5,
    initial_delay=2.0,
    max_delay=30.0,
    user_message="Failed to query blockchain, please try again"
)

TRANSACTION_VERIFICATION_RECOVERY = ErrorRecoveryConfig(
    strategy=RecoveryStrategy.RETRY,
    max_retries=3,
    initial_delay=1.0,
    max_delay=10.0,
    user_message="Failed to verify transaction, please try again"
)

API_CALL_RECOVERY = ErrorRecoveryConfig(
    strategy=RecoveryStrategy.RETRY,
    max_retries=3,
    initial_delay=1.0,
    max_delay=10.0,
    user_message="API call failed, please try again"
)

DATABASE_OPERATION_RECOVERY = ErrorRecoveryConfig(
    strategy=RecoveryStrategy.RETRY,
    max_retries=3,
    initial_delay=0.5,
    max_delay=5.0,
    user_message="Database operation failed, please try again"
)
