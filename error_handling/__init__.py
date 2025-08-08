"""
Error handling module initialization.
"""

from .exceptions import (
    BaseAPIException,
    ValidationException,
    AuthenticationException,
    AuthorizationException,
    ResourceNotFoundException,
    RateLimitException,
    DatabaseException,
    CacheException,
    ExternalServiceException,
    ConfigurationException,
    BusinessLogicException,
    SecurityException,
    MaintenanceException,
    QuotaExceededException,
    ErrorSeverity,
    ErrorRecoveryStrategy,
    ErrorContext,
    ErrorCollector,
    error_collector
)

from .handlers import (
    ErrorHandlerManager,
    HealthCheckErrorHandler,
    AsyncErrorHandler,
    ErrorHandlingContext,
    error_handler_manager,
    safe_execute,
    handle_database_operation
)

__all__ = [
    # Custom exceptions
    'BaseAPIException',
    'ValidationException',
    'AuthenticationException', 
    'AuthorizationException',
    'ResourceNotFoundException',
    'RateLimitException',
    'DatabaseException',
    'CacheException',
    'ExternalServiceException',
    'ConfigurationException',
    'BusinessLogicException',
    'SecurityException',
    'MaintenanceException',
    'QuotaExceededException',
    
    # Error utilities
    'ErrorSeverity',
    'ErrorRecoveryStrategy',
    'ErrorContext',
    'ErrorCollector',
    'error_collector',
    
    # Error handlers
    'ErrorHandlerManager',
    'HealthCheckErrorHandler',
    'AsyncErrorHandler',
    'ErrorHandlingContext',
    'error_handler_manager',
    
    # Utility functions
    'safe_execute',
    'handle_database_operation'
]