"""
Global error handlers for Flask application.
"""

import logging
import traceback
from typing import Tuple, Any
from datetime import datetime, timezone

from flask import Flask, request, jsonify, g
from werkzeug.exceptions import HTTPException
from marshmallow import ValidationError
from psycopg import Error as PostgresError

from .exceptions import (
    BaseAPIException, ValidationException, AuthenticationException,
    DatabaseException, CacheException, ErrorSeverity, error_collector
)
from auth.security import audit_logger

logger = logging.getLogger(__name__)

class ErrorHandlerManager:
    """Centralized error handling for the Flask application"""
    
    def __init__(self, app: Flask = None):
        self.app = app
        if app:
            self.init_app(app)
    
    def init_app(self, app: Flask):
        """Initialize error handlers with Flask app"""
        self.app = app
        
        # Register error handlers
        app.errorhandler(BaseAPIException)(self.handle_api_exception)
        app.errorhandler(ValidationError)(self.handle_validation_error)
        app.errorhandler(PostgresError)(self.handle_database_error)
        app.errorhandler(HTTPException)(self.handle_http_exception)
        app.errorhandler(Exception)(self.handle_generic_exception)
        
        # Add before/after request handlers for error context
        app.before_request(self.before_request_handler)
        app.after_request(self.after_request_handler)
        app.teardown_request(self.teardown_request_handler)
        
        logger.info("Error handlers initialized")
    
    def before_request_handler(self):
        """Set up error handling context before each request"""
        g.start_time = datetime.now(timezone.utc)
        g.request_errors = []
        
        # Generate request ID for tracing
        import uuid
        g.request_id = str(uuid.uuid4())[:8]
    
    def after_request_handler(self, response):
        """Process response and log request completion"""
        try:
            duration = (datetime.now(timezone.utc) - getattr(g, 'start_time', datetime.now(timezone.utc))).total_seconds()
            
            # Log slow requests
            if duration > 2.0:  # Requests taking more than 2 seconds
                logger.warning(f"Slow request: {request.method} {request.path} took {duration:.3f}s")
            
            # Add request ID to response headers
            response.headers['X-Request-ID'] = getattr(g, 'request_id', 'unknown')
            response.headers['X-Response-Time'] = f"{duration:.3f}s"
            
            return response
            
        except Exception as e:
            logger.error(f"Error in after_request_handler: {e}")
            return response
    
    def teardown_request_handler(self, exception):
        """Clean up after request processing"""
        if exception:
            logger.error(f"Request teardown with exception: {exception}")
    
    def handle_api_exception(self, error: BaseAPIException) -> Tuple[Any, int]:
        """Handle custom API exceptions"""
        try:
            # Record error for monitoring
            error_collector.record_error(error, {
                'request_path': request.path,
                'request_method': request.method,
                'user_id': getattr(request, 'user_id', None),
                'request_id': getattr(g, 'request_id', None)
            })
            
            # Log security events for security-related errors
            if error.status_code in [401, 403]:
                audit_logger.log_security_event(
                    event_type='security_error',
                    details={
                        'error_code': error.error_code,
                        'path': request.path,
                        'user_id': getattr(request, 'user_id', 'anonymous'),
                        'ip_address': request.remote_addr
                    },
                    severity='WARNING'
                )
            
            # Determine log level based on severity
            severity = ErrorSeverity.get_severity_by_status_code(error.status_code)
            log_level = {
                ErrorSeverity.LOW: logging.INFO,
                ErrorSeverity.MEDIUM: logging.WARNING,
                ErrorSeverity.HIGH: logging.ERROR,
                ErrorSeverity.CRITICAL: logging.CRITICAL
            }.get(severity, logging.ERROR)
            
            logger.log(log_level, f"API Exception: {error.error_code} - {error.message}")
            
            return jsonify(error.to_dict()), error.status_code
            
        except Exception as e:
            logger.error(f"Error in API exception handler: {e}")
            return self._generic_error_response(), 500
    
    def handle_validation_error(self, error: ValidationError) -> Tuple[Any, int]:
        """Handle Marshmallow validation errors"""
        try:
            validation_exception = ValidationException(
                message="Input validation failed",
                field_errors=error.messages
            )
            
            return self.handle_api_exception(validation_exception)
            
        except Exception as e:
            logger.error(f"Error in validation error handler: {e}")
            return self._generic_error_response(), 400
    
    def handle_database_error(self, error: PostgresError) -> Tuple[Any, int]:
        """Handle PostgreSQL database errors"""
        try:
            # Map PostgreSQL error codes to user-friendly messages
            error_messages = {
                '08000': 'Database connection failed',
                '08003': 'Database connection does not exist',
                '08006': 'Database connection failure',
                '53300': 'Database connection limit exceeded',
                '40001': 'Database transaction conflict, please retry',
                '23505': 'Data already exists',
                '23503': 'Referenced data not found',
                '42P01': 'Database table not found'
            }
            
            sqlstate = getattr(error, 'sqlstate', None)
            user_message = error_messages.get(sqlstate, 'Database operation failed')
            
            database_exception = DatabaseException(
                message=user_message,
                operation=f"{request.method} {request.path}",
                cause=error
            )
            
            return self.handle_api_exception(database_exception)
            
        except Exception as e:
            logger.error(f"Error in database error handler: {e}")
            return self._generic_error_response(), 503
    
    def handle_http_exception(self, error: HTTPException) -> Tuple[Any, int]:
        """Handle standard HTTP exceptions"""
        try:
            # Map common HTTP errors to our exception format
            error_messages = {
                400: 'Bad request',
                401: 'Authentication required',
                403: 'Access forbidden',
                404: 'Resource not found',
                405: 'Method not allowed',
                406: 'Not acceptable',
                408: 'Request timeout',
                409: 'Conflict',
                410: 'Resource no longer available',
                413: 'Request too large',
                414: 'URI too long',
                415: 'Unsupported media type',
                422: 'Unprocessable entity',
                429: 'Too many requests',
                500: 'Internal server error',
                501: 'Not implemented',
                502: 'Bad gateway',
                503: 'Service unavailable',
                504: 'Gateway timeout'
            }
            
            message = error_messages.get(error.code, error.description or 'HTTP error')
            
            response_data = {
                'error': message,
                'error_code': f'HTTP_{error.code}',
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'request_id': getattr(g, 'request_id', None)
            }
            
            # Add retry information for rate limiting
            if error.code == 429:
                response_data['retry_after'] = 60
            
            logger.warning(f"HTTP Exception: {error.code} - {message}")
            
            return jsonify(response_data), error.code
            
        except Exception as e:
            logger.error(f"Error in HTTP exception handler: {e}")
            return self._generic_error_response(), error.code or 500
    
    def handle_generic_exception(self, error: Exception) -> Tuple[Any, int]:
        """Handle unexpected exceptions"""
        try:
            # Log full traceback for debugging
            logger.error(f"Unhandled exception: {str(error)}", exc_info=True)
            
            # Don't expose internal error details in production
            import os
            debug_mode = os.getenv('DEBUG', 'false').lower() == 'true'
            
            if debug_mode:
                error_details = {
                    'type': type(error).__name__,
                    'message': str(error),
                    'traceback': traceback.format_exc()
                }
            else:
                error_details = None
            
            response_data = {
                'error': 'An unexpected error occurred',
                'error_code': 'INTERNAL_SERVER_ERROR',
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'request_id': getattr(g, 'request_id', None)
            }
            
            if error_details:
                response_data['debug_info'] = error_details
            
            # Record for monitoring
            from .exceptions import BaseAPIException
            generic_exception = BaseAPIException(
                message='Internal server error',
                status_code=500,
                error_code='INTERNAL_SERVER_ERROR',
                cause=error
            )
            
            error_collector.record_error(generic_exception, {
                'request_path': request.path,
                'request_method': request.method,
                'user_id': getattr(request, 'user_id', None),
                'request_id': getattr(g, 'request_id', None),
                'exception_type': type(error).__name__
            })
            
            # Send alert for critical errors
            self._send_critical_error_alert(error)
            
            return jsonify(response_data), 500
            
        except Exception as handler_error:
            logger.critical(f"Error in generic exception handler: {handler_error}")
            return self._fallback_error_response(), 500
    
    def _generic_error_response(self) -> dict:
        """Generate generic error response"""
        return {
            'error': 'An error occurred while processing your request',
            'error_code': 'PROCESSING_ERROR',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'request_id': getattr(g, 'request_id', None)
        }
    
    def _fallback_error_response(self) -> dict:
        """Fallback error response when all else fails"""
        return {
            'error': 'System error',
            'error_code': 'SYSTEM_ERROR',
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
    
    def _send_critical_error_alert(self, error: Exception):
        """Send alert for critical errors (placeholder implementation)"""
        try:
            # In production, integrate with alerting system (Slack, PagerDuty, etc.)
            logger.critical(f"CRITICAL ERROR ALERT: {type(error).__name__}: {str(error)}")
            
            # Example: Send to monitoring service
            # monitoring_service.send_alert({
            #     'severity': 'critical',
            #     'message': str(error),
            #     'service': 'falcon-miniapp-bot',
            #     'timestamp': datetime.now(timezone.utc).isoformat()
            # })
            
        except Exception as alert_error:
            logger.error(f"Failed to send critical error alert: {alert_error}")

class HealthCheckErrorHandler:
    """Specialized error handling for health check endpoints"""
    
    @staticmethod
    def handle_health_check_error(error: Exception, component: str) -> dict:
        """Handle errors in health check endpoints"""
        logger.error(f"Health check error for {component}: {error}")
        
        return {
            'status': 'unhealthy',
            'component': component,
            'error': str(error),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }

class AsyncErrorHandler:
    """Error handling for background tasks and async operations"""
    
    @staticmethod
    def handle_background_task_error(task_name: str, error: Exception):
        """Handle errors in background tasks"""
        logger.error(f"Background task '{task_name}' failed: {error}", exc_info=True)
        
        # Record for monitoring
        from .exceptions import BaseAPIException
        task_exception = BaseAPIException(
            message=f"Background task failed: {task_name}",
            status_code=500,
            error_code='BACKGROUND_TASK_ERROR',
            details={'task_name': task_name},
            cause=error
        )
        
        error_collector.record_error(task_exception, {
            'task_name': task_name,
            'error_type': type(error).__name__
        })
    
    @staticmethod
    def handle_cache_operation_error(operation: str, error: Exception):
        """Handle cache operation errors"""
        logger.warning(f"Cache operation '{operation}' failed: {error}")
        
        from .exceptions import CacheException
        cache_exception = CacheException(
            message=f"Cache operation failed: {operation}",
            operation=operation,
            cause=error
        )
        
        error_collector.record_error(cache_exception, {
            'operation': operation,
            'fallback_used': True
        })

# Context manager for error handling in specific operations
class ErrorHandlingContext:
    """Context manager for operation-specific error handling"""
    
    def __init__(self, operation_name: str, fallback_func=None):
        self.operation_name = operation_name
        self.fallback_func = fallback_func
        self.start_time = None
    
    def __enter__(self):
        self.start_time = datetime.now(timezone.utc)
        logger.debug(f"Starting operation: {self.operation_name}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = (datetime.now(timezone.utc) - self.start_time).total_seconds()
        
        if exc_type is None:
            logger.debug(f"Operation completed: {self.operation_name} ({duration:.3f}s)")
            return False
        
        logger.error(f"Operation failed: {self.operation_name} ({duration:.3f}s) - {exc_val}")
        
        # Try fallback if available
        if self.fallback_func and not isinstance(exc_val, BaseAPIException):
            try:
                logger.info(f"Attempting fallback for {self.operation_name}")
                fallback_result = self.fallback_func()
                logger.info(f"Fallback successful for {self.operation_name}")
                return True  # Suppress the original exception
            except Exception as fallback_error:
                logger.error(f"Fallback failed for {self.operation_name}: {fallback_error}")
        
        return False  # Don't suppress the exception

# Global error handler manager instance
error_handler_manager = ErrorHandlerManager()

# Utility functions for error handling
def safe_execute(func, fallback=None, operation_name=None):
    """Safely execute a function with optional fallback"""
    try:
        return func()
    except Exception as e:
        operation = operation_name or func.__name__
        logger.error(f"Safe execute failed for {operation}: {e}")
        
        if fallback:
            try:
                logger.info(f"Using fallback for {operation}")
                return fallback()
            except Exception as fallback_error:
                logger.error(f"Fallback failed for {operation}: {fallback_error}")
        
        # Re-raise as appropriate exception type
        if isinstance(e, BaseAPIException):
            raise
        else:
            raise BaseAPIException(
                message=f"Operation failed: {operation}",
                error_code='OPERATION_FAILED',
                cause=e
            )

def handle_database_operation(operation_func, operation_name: str = None):
    """Handle database operations with proper error handling"""
    try:
        return operation_func()
    except PostgresError as e:
        raise DatabaseException(
            message="Database operation failed",
            operation=operation_name or operation_func.__name__,
            cause=e
        )
    except Exception as e:
        raise DatabaseException(
            message="Unexpected database error",
            operation=operation_name or operation_func.__name__,
            cause=e
        )