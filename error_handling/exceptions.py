"""
Custom exception classes and error handling utilities.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class BaseAPIException(Exception):
    """Base exception class for API errors"""
    
    def __init__(self, message: str, status_code: int = 500, error_code: str = None, 
                 details: Dict[str, Any] = None, cause: Exception = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_code = error_code or self.__class__.__name__.upper()
        self.details = details or {}
        self.cause = cause
        self.timestamp = datetime.now(timezone.utc)
        
        # Log the exception
        if cause:
            logger.error(f"{self.error_code}: {message}", exc_info=cause)
        else:
            logger.error(f"{self.error_code}: {message}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for JSON response"""
        result = {
            'error': self.message,
            'error_code': self.error_code,
            'timestamp': self.timestamp.isoformat()
        }
        
        if self.details:
            result['details'] = self.details
            
        return result

class ValidationException(BaseAPIException):
    """Raised when input validation fails"""
    
    def __init__(self, message: str = "Invalid input data", field_errors: Dict[str, Any] = None):
        super().__init__(
            message=message,
            status_code=400,
            error_code='VALIDATION_ERROR',
            details={'field_errors': field_errors} if field_errors else None
        )

class AuthenticationException(BaseAPIException):
    """Raised when authentication fails"""
    
    def __init__(self, message: str = "Authentication required"):
        super().__init__(
            message=message,
            status_code=401,
            error_code='AUTHENTICATION_ERROR'
        )

class AuthorizationException(BaseAPIException):
    """Raised when authorization fails"""
    
    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(
            message=message,
            status_code=403,
            error_code='AUTHORIZATION_ERROR'
        )

class ResourceNotFoundException(BaseAPIException):
    """Raised when a requested resource is not found"""
    
    def __init__(self, resource: str = "Resource", resource_id: str = None):
        message = f"{resource} not found"
        if resource_id:
            message += f": {resource_id}"
        
        super().__init__(
            message=message,
            status_code=404,
            error_code='RESOURCE_NOT_FOUND',
            details={'resource_type': resource, 'resource_id': resource_id}
        )

class RateLimitException(BaseAPIException):
    """Raised when rate limit is exceeded"""
    
    def __init__(self, message: str = "Rate limit exceeded", retry_after: int = 60):
        super().__init__(
            message=message,
            status_code=429,
            error_code='RATE_LIMIT_EXCEEDED',
            details={'retry_after': retry_after}
        )

class DatabaseException(BaseAPIException):
    """Raised when database operations fail"""
    
    def __init__(self, message: str = "Database operation failed", operation: str = None, cause: Exception = None):
        super().__init__(
            message=message,
            status_code=503,
            error_code='DATABASE_ERROR',
            details={'operation': operation} if operation else None,
            cause=cause
        )

class CacheException(BaseAPIException):
    """Raised when cache operations fail"""
    
    def __init__(self, message: str = "Cache operation failed", operation: str = None, cause: Exception = None):
        super().__init__(
            message=message,
            status_code=503,
            error_code='CACHE_ERROR',
            details={'operation': operation} if operation else None,
            cause=cause
        )

class ExternalServiceException(BaseAPIException):
    """Raised when external service calls fail"""
    
    def __init__(self, service: str, message: str = "External service unavailable", cause: Exception = None):
        super().__init__(
            message=f"{service}: {message}",
            status_code=503,
            error_code='EXTERNAL_SERVICE_ERROR',
            details={'service': service},
            cause=cause
        )

class ConfigurationException(BaseAPIException):
    """Raised when configuration is invalid or missing"""
    
    def __init__(self, message: str = "Configuration error", config_key: str = None):
        super().__init__(
            message=message,
            status_code=500,
            error_code='CONFIGURATION_ERROR',
            details={'config_key': config_key} if config_key else None
        )

class BusinessLogicException(BaseAPIException):
    """Raised when business logic validation fails"""
    
    def __init__(self, message: str, rule: str = None):
        super().__init__(
            message=message,
            status_code=422,
            error_code='BUSINESS_LOGIC_ERROR',
            details={'rule': rule} if rule else None
        )

class SecurityException(BaseAPIException):
    """Raised when security violations are detected"""
    
    def __init__(self, message: str = "Security violation detected", violation_type: str = None):
        super().__init__(
            message=message,
            status_code=403,
            error_code='SECURITY_VIOLATION',
            details={'violation_type': violation_type} if violation_type else None
        )

class MaintenanceException(BaseAPIException):
    """Raised when system is under maintenance"""
    
    def __init__(self, message: str = "System under maintenance", estimated_duration: int = None):
        super().__init__(
            message=message,
            status_code=503,
            error_code='MAINTENANCE_MODE',
            details={'estimated_duration_minutes': estimated_duration} if estimated_duration else None
        )

class QuotaExceededException(BaseAPIException):
    """Raised when usage quota is exceeded"""
    
    def __init__(self, quota_type: str, limit: int, current: int):
        message = f"{quota_type} quota exceeded: {current}/{limit}"
        super().__init__(
            message=message,
            status_code=429,
            error_code='QUOTA_EXCEEDED',
            details={
                'quota_type': quota_type,
                'limit': limit,
                'current': current
            }
        )

# Error severity levels
class ErrorSeverity:
    """Error severity levels for logging and alerting"""
    LOW = 'low'
    MEDIUM = 'medium'
    HIGH = 'high'
    CRITICAL = 'critical'
    
    @classmethod
    def get_severity_by_status_code(cls, status_code: int) -> str:
        """Get severity level based on HTTP status code"""
        if status_code < 400:
            return cls.LOW
        elif status_code < 500:
            return cls.MEDIUM
        elif status_code < 503:
            return cls.HIGH
        else:
            return cls.CRITICAL

# Error recovery strategies
class ErrorRecoveryStrategy:
    """Strategies for error recovery and fallback handling"""
    
    @staticmethod
    def with_fallback(primary_func, fallback_func, *args, **kwargs):
        """Execute primary function with fallback on failure"""
        try:
            return primary_func(*args, **kwargs)
        except Exception as e:
            logger.warning(f"Primary function failed, using fallback: {e}")
            return fallback_func(*args, **kwargs)
    
    @staticmethod
    def with_retry(func, max_attempts: int = 3, delay: float = 1.0, backoff: float = 2.0):
        """Execute function with exponential backoff retry"""
        import time
        
        last_exception = None
        current_delay = delay
        
        for attempt in range(max_attempts):
            try:
                return func()
            except Exception as e:
                last_exception = e
                if attempt < max_attempts - 1:
                    logger.warning(f"Attempt {attempt + 1} failed, retrying in {current_delay}s: {e}")
                    time.sleep(current_delay)
                    current_delay *= backoff
                else:
                    logger.error(f"All {max_attempts} attempts failed: {e}")
        
        if last_exception:
            raise last_exception
    
    @staticmethod
    def circuit_breaker(func, failure_threshold: int = 5, timeout: int = 60):
        """Implement circuit breaker pattern"""
        # This is a simplified implementation
        # In production, use a proper circuit breaker library
        if not hasattr(func, '_cb_failures'):
            func._cb_failures = 0
            func._cb_last_failure = 0
        
        import time
        current_time = time.time()
        
        # Check if circuit is open
        if func._cb_failures >= failure_threshold:
            if current_time - func._cb_last_failure < timeout:
                raise ExternalServiceException("Circuit breaker", "Service temporarily unavailable")
            else:
                # Reset circuit breaker
                func._cb_failures = 0
        
        try:
            result = func()
            func._cb_failures = 0  # Reset on success
            return result
        except Exception as e:
            func._cb_failures += 1
            func._cb_last_failure = current_time
            raise

# Error context manager
class ErrorContext:
    """Context manager for error handling with additional context"""
    
    def __init__(self, operation: str, user_id: str = None, request_id: str = None):
        self.operation = operation
        self.user_id = user_id
        self.request_id = request_id
        self.start_time = datetime.now(timezone.utc)
    
    def __enter__(self):
        logger.info(f"Starting operation: {self.operation}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = (datetime.now(timezone.utc) - self.start_time).total_seconds()
        
        if exc_type is None:
            logger.info(f"Operation completed successfully: {self.operation} ({duration:.3f}s)")
        else:
            logger.error(f"Operation failed: {self.operation} ({duration:.3f}s) - {exc_val}")
            
            # Add context to exception if it's our custom exception
            if isinstance(exc_val, BaseAPIException):
                exc_val.details.update({
                    'operation': self.operation,
                    'duration_seconds': duration,
                    'user_id': self.user_id,
                    'request_id': self.request_id
                })
        
        return False  # Don't suppress exceptions

# Error aggregation for monitoring
class ErrorCollector:
    """Collect and aggregate errors for monitoring and alerting"""
    
    def __init__(self):
        self.errors = []
        self.error_counts = {}
    
    def record_error(self, exception: BaseAPIException, context: Dict[str, Any] = None):
        """Record an error for aggregation"""
        error_record = {
            'timestamp': exception.timestamp,
            'error_code': exception.error_code,
            'message': exception.message,
            'status_code': exception.status_code,
            'severity': ErrorSeverity.get_severity_by_status_code(exception.status_code),
            'context': context or {}
        }
        
        self.errors.append(error_record)
        
        # Update counts
        key = f"{exception.error_code}:{exception.status_code}"
        self.error_counts[key] = self.error_counts.get(key, 0) + 1
    
    def get_error_summary(self, time_window: int = 3600) -> Dict[str, Any]:
        """Get error summary for the specified time window (seconds)"""
        from datetime import timedelta
        
        cutoff_time = datetime.now(timezone.utc) - timedelta(seconds=time_window)
        recent_errors = [
            error for error in self.errors 
            if error['timestamp'] > cutoff_time
        ]
        
        # Count by severity
        severity_counts = {}
        for error in recent_errors:
            severity = error['severity']
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        # Count by error code
        error_code_counts = {}
        for error in recent_errors:
            code = error['error_code']
            error_code_counts[code] = error_code_counts.get(code, 0) + 1
        
        return {
            'total_errors': len(recent_errors),
            'time_window_seconds': time_window,
            'severity_breakdown': severity_counts,
            'error_code_breakdown': error_code_counts,
            'error_rate': len(recent_errors) / (time_window / 60),  # errors per minute
            'timestamp': datetime.now(timezone.utc).isoformat()
        }

# Global error collector instance
error_collector = ErrorCollector()