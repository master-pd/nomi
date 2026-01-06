"""
Error Handler - Centralized error handling
"""

import sys
import traceback
import logging
from typing import Dict, Any, Optional, Callable
from datetime import datetime
import asyncio

class ErrorHandler:
    """Centralized error handling system"""
    
    def __init__(self):
        self.logger = logging.getLogger("nomi_errors")
        self.error_count = 0
        self.error_types = {}
        self.last_errors = []
        self.handlers = {}
        
    def setup_global_handler(self):
        """Setup global exception handler"""
        sys.excepthook = self._global_exception_handler
        
        # Setup asyncio exception handler
        loop = asyncio.get_event_loop()
        loop.set_exception_handler(self._async_exception_handler)
        
        self.logger.info("🛡️ Global error handler installed")
        
    def _global_exception_handler(self, exc_type, exc_value, exc_traceback):
        """Global exception handler"""
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
            
        self.logger.critical(
            "Uncaught exception",
            exc_info=(exc_type, exc_value, exc_traceback)
        )
        
        # Record error
        self.record_error(exc_type.__name__, str(exc_value), traceback.format_exc())
        
    def _async_exception_handler(self, loop, context):
        """Asyncio exception handler"""
        exception = context.get('exception')
        message = context.get('message', 'Unknown error')
        
        if exception:
            self.logger.error(f"Async error: {message}", exc_info=exception)
            self.record_error(
                exception.__class__.__name__,
                str(exception),
                traceback.format_exception(type(exception), exception, exception.__traceback__)
            )
        else:
            self.logger.error(f"Async error: {message}")
            self.record_error("AsyncError", message, "")
            
    def record_error(self, error_type: str, message: str, traceback_str: str):
        """
        Record an error
        
        Args:
            error_type: Type of error
            message: Error message
            traceback_str: Traceback string
        """
        self.error_count += 1
        
        # Update error types count
        if error_type not in self.error_types:
            self.error_types[error_type] = 0
        self.error_types[error_type] += 1
        
        # Store last errors
        error_record = {
            'timestamp': datetime.now().isoformat(),
            'type': error_type,
            'message': message,
            'traceback': traceback_str[:1000]  # Limit size
        }
        
        self.last_errors.append(error_record)
        
        # Keep only last 100 errors
        if len(self.last_errors) > 100:
            self.last_errors = self.last_errors[-100:]
            
        # Call registered handlers
        for handler in self.handlers.get(error_type, []):
            try:
                handler(error_record)
            except Exception as e:
                self.logger.error(f"Error in error handler: {e}")
                
    def register_handler(self, error_type: str, handler: Callable):
        """
        Register error handler
        
        Args:
            error_type: Error type to handle
            handler: Handler function
        """
        if error_type not in self.handlers:
            self.handlers[error_type] = []
        self.handlers[error_type].append(handler)
        self.logger.debug(f"Registered handler for error type: {error_type}")
        
    async def handle_async_error(self, coroutine, context: str = "", 
                               fallback_value=None):
        """
        Safely execute async function with error handling
        
        Args:
            coroutine: Async coroutine to execute
            context: Context for error logging
            fallback_value: Value to return on error
            
        Returns:
            Function result or fallback_value
        """
        try:
            return await coroutine
        except Exception as e:
            self.logger.error(f"Error in {context}: {e}")
            self.record_error(
                e.__class__.__name__,
                str(e),
                traceback.format_exc()
            )
            return fallback_value
            
    def handle_sync_error(self, func, context: str = "", 
                         fallback_value=None, *args, **kwargs):
        """
        Safely execute sync function with error handling
        
        Args:
            func: Function to execute
            context: Context for error logging
            fallback_value: Value to return on error
            *args, **kwargs: Function arguments
            
        Returns:
            Function result or fallback_value
        """
        try:
            return func(*args, **kwargs)
        except Exception as e:
            self.logger.error(f"Error in {context}: {e}")
            self.record_error(
                e.__class__.__name__,
                str(e),
                traceback.format_exc()
            )
            return fallback_value
            
    def get_error_stats(self) -> Dict[str, Any]:
        """Get error statistics"""
        return {
            'total_errors': self.error_count,
            'error_types': self.error_types,
            'recent_errors': len(self.last_errors),
            'most_common_error': max(self.error_types.items(), key=lambda x: x[1], default=("None", 0))
        }
        
    def get_last_errors(self, limit: int = 10) -> list:
        """Get last errors"""
        return self.last_errors[-limit:] if limit else self.last_errors.copy()
        
    def clear_errors(self):
        """Clear error records"""
        self.last_errors.clear()
        self.error_types.clear()
        self.error_count = 0
        self.logger.info("🧹 Cleared all error records")
        
    def create_error_response(self, error: Exception, user_friendly: bool = True) -> Dict[str, Any]:
        """
        Create error response for user
        
        Args:
            error: Exception object
            user_friendly: Whether to create user-friendly message
            
        Returns:
            Error response dict
        """
        error_type = error.__class__.__name__
        
        if user_friendly:
            # User-friendly messages
            messages = {
                'ConnectionError': '⚠️ সংযোগ সমস্যা হয়েছে। আবার চেষ্টা করুন।',
                'TimeoutError': '⏰ সময়সীমা শেষ হয়েছে। আবার চেষ্টা করুন।',
                'PermissionError': '🚫 এই কাজটি করার অনুমতি নেই।',
                'ValueError': '❌ ভুল ইনপুট। আবার চেষ্টা করুন।',
                'FileNotFoundError': '📁 ফাইল পাওয়া যায়নি।',
                'KeyError': '🔑 প্রয়োজনীয় তথ্য পাওয়া যায়নি।',
                'IndexError': '📊 তথ্যের সঠিক অবস্থান পাওয়া যায়নি।',
                'AttributeError': '⚙️ বৈশিষ্ট্য পাওয়া যায়নি।',
                'TypeError': '🔄 ভুল ধরনের তথ্য।',
                'RuntimeError': '⚡ সিস্টেম ত্রুটি হয়েছে।'
            }
            
            message = messages.get(error_type, '❌ একটি ত্রুটি হয়েছে। আবার চেষ্টা করুন।')
            
        else:
            message = str(error)
            
        return {
            'success': False,
            'error': True,
            'error_type': error_type,
            'message': message,
            'technical_message': str(error) if not user_friendly else None,
            'timestamp': datetime.now().isoformat()
        }
        
    def log_and_notify(self, error: Exception, context: str = "", 
                      notify_admins: bool = False):
        """
        Log error and optionally notify admins
        
        Args:
            error: Exception object
            context: Error context
            notify_admins: Whether to notify admins
        """
        # Log error
        self.logger.error(f"{context}: {error}", exc_info=error)
        
        # Record error
        self.record_error(
            error.__class__.__name__,
            str(error),
            traceback.format_exc()
        )
        
        # Notify admins if enabled
        if notify_admins:
            # TODO: Implement admin notification
            pass
            
    def is_critical_error(self, error: Exception) -> bool:
        """Check if error is critical"""
        critical_errors = [
            'MemoryError',
            'SystemExit',
            'KeyboardInterrupt',
            'GeneratorExit',
            'BaseException'
        ]
        
        return error.__class__.__name__ in critical_errors
        
    def should_restart_on_error(self, error: Exception) -> bool:
        """Determine if bot should restart on this error"""
        restart_errors = [
            'MemoryError',
            'SystemError',
            'RuntimeError'  # Some runtime errors
        ]
        
        return error.__class__.__name__ in restart_errors

# Global error handler instance
error_handler = ErrorHandler()

def handle_errors(func):
    """Decorator for error handling"""
    if asyncio.iscoroutinefunction(func):
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                error_handler.log_and_notify(e, f"Error in {func.__name__}")
                raise
        return async_wrapper
    else:
        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_handler.log_and_notify(e, f"Error in {func.__name__}")
                raise
        return sync_wrapper