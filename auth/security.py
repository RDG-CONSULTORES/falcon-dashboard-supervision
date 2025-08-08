"""
Security module for authentication, authorization, and validation.
Implements JWT authentication, input validation, and security middleware.
"""

import os
import jwt
import hashlib
import logging
from datetime import datetime, timedelta, timezone
from functools import wraps
from typing import Optional, Dict, Any

from flask import request, jsonify, current_app
from marshmallow import Schema, fields, validate, ValidationError
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

class SecurityConfig:
    """Centralized security configuration"""
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'dev-secret-key-change-in-production')
    JWT_ALGORITHM = 'HS256'
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS = 7
    API_KEY_HEADER = 'X-API-Key'
    TELEGRAM_BOT_TOKEN = os.getenv('BOT_TOKEN')
    RATE_LIMIT_DEFAULT = "100 per hour"
    RATE_LIMIT_STRICT = "10 per minute"

class AuthenticationService:
    """JWT-based authentication service"""
    
    @staticmethod
    def generate_tokens(user_id: str, user_data: Dict[str, Any] = None) -> Dict[str, str]:
        """Generate access and refresh tokens"""
        now = datetime.now(timezone.utc)
        user_data = user_data or {}
        
        # Access token payload
        access_payload = {
            'user_id': user_id,
            'exp': now + timedelta(minutes=SecurityConfig.JWT_ACCESS_TOKEN_EXPIRE_MINUTES),
            'iat': now,
            'type': 'access',
            **user_data
        }
        
        # Refresh token payload
        refresh_payload = {
            'user_id': user_id,
            'exp': now + timedelta(days=SecurityConfig.JWT_REFRESH_TOKEN_EXPIRE_DAYS),
            'iat': now,
            'type': 'refresh'
        }
        
        access_token = jwt.encode(
            access_payload,
            SecurityConfig.JWT_SECRET_KEY,
            algorithm=SecurityConfig.JWT_ALGORITHM
        )
        
        refresh_token = jwt.encode(
            refresh_payload,
            SecurityConfig.JWT_SECRET_KEY,
            algorithm=SecurityConfig.JWT_ALGORITHM
        )
        
        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'token_type': 'bearer',
            'expires_in': SecurityConfig.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
        }
    
    @staticmethod
    def verify_token(token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(
                token,
                SecurityConfig.JWT_SECRET_KEY,
                algorithms=[SecurityConfig.JWT_ALGORITHM]
            )
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("Token expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            return None
    
    @staticmethod
    def refresh_access_token(refresh_token: str) -> Optional[Dict[str, str]]:
        """Generate new access token from refresh token"""
        payload = AuthenticationService.verify_token(refresh_token)
        
        if not payload or payload.get('type') != 'refresh':
            return None
        
        user_id = payload.get('user_id')
        if not user_id:
            return None
        
        # Generate new access token
        return AuthenticationService.generate_tokens(user_id)

class TelegramAuth:
    """Telegram-specific authentication for bot integration"""
    
    @staticmethod
    def verify_telegram_data(auth_data: Dict[str, Any]) -> bool:
        """Verify Telegram WebApp authentication data"""
        if not SecurityConfig.TELEGRAM_BOT_TOKEN:
            logger.error("Telegram bot token not configured")
            return False
        
        # Extract hash from auth_data
        received_hash = auth_data.pop('hash', None)
        if not received_hash:
            return False
        
        # Create verification string
        data_check_arr = []
        for key, value in sorted(auth_data.items()):
            data_check_arr.append(f"{key}={value}")
        data_check_string = '\n'.join(data_check_arr)
        
        # Calculate expected hash
        secret_key = hashlib.sha256(SecurityConfig.TELEGRAM_BOT_TOKEN.encode()).digest()
        calculated_hash = hashlib.sha256(
            secret_key + data_check_string.encode()
        ).hexdigest()
        
        return calculated_hash == received_hash
    
    @staticmethod
    def create_telegram_session(telegram_user: Dict[str, Any]) -> Dict[str, str]:
        """Create authenticated session for Telegram user"""
        user_id = f"tg_{telegram_user.get('id')}"
        user_data = {
            'telegram_id': telegram_user.get('id'),
            'first_name': telegram_user.get('first_name'),
            'username': telegram_user.get('username'),
            'auth_method': 'telegram'
        }
        
        return AuthenticationService.generate_tokens(user_id, user_data)

# Authentication decorators
def require_auth(f):
    """Authentication decorator for API endpoints"""
    @wraps(f)
    def decorated(*args, **kwargs):
        # Check Authorization header
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({
                'error': 'Authentication required',
                'message': 'Please provide Authorization header',
                'error_code': 'AUTH_REQUIRED'
            }), 401
        
        # Extract token
        try:
            token_type, token = auth_header.split(' ', 1)
            if token_type.lower() != 'bearer':
                raise ValueError("Invalid token type")
        except ValueError:
            return jsonify({
                'error': 'Invalid authorization header',
                'message': 'Use format: Bearer <token>',
                'error_code': 'INVALID_AUTH_HEADER'
            }), 401
        
        # Verify token
        payload = AuthenticationService.verify_token(token)
        if not payload:
            return jsonify({
                'error': 'Invalid or expired token',
                'message': 'Please authenticate again',
                'error_code': 'TOKEN_INVALID'
            }), 401
        
        # Add user info to request
        request.user_id = payload.get('user_id')
        request.user_data = payload
        
        return f(*args, **kwargs)
    return decorated

def require_api_key(f):
    """API key authentication for bot integration"""
    @wraps(f)
    def decorated(*args, **kwargs):
        api_key = request.headers.get(SecurityConfig.API_KEY_HEADER)
        
        if not api_key:
            return jsonify({
                'error': 'API key required',
                'message': f'Please provide {SecurityConfig.API_KEY_HEADER} header',
                'error_code': 'API_KEY_REQUIRED'
            }), 401
        
        # Verify API key (for now, check against bot token hash)
        expected_key = hashlib.sha256(
            SecurityConfig.TELEGRAM_BOT_TOKEN.encode()
        ).hexdigest()[:32]
        
        if api_key != expected_key:
            return jsonify({
                'error': 'Invalid API key',
                'message': 'Provided API key is not valid',
                'error_code': 'INVALID_API_KEY'
            }), 401
        
        return f(*args, **kwargs)
    return decorated

def optional_auth(f):
    """Optional authentication - provides user info if authenticated"""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        
        if auth_header:
            try:
                token_type, token = auth_header.split(' ', 1)
                if token_type.lower() == 'bearer':
                    payload = AuthenticationService.verify_token(token)
                    if payload:
                        request.user_id = payload.get('user_id')
                        request.user_data = payload
            except ValueError:
                pass  # Invalid format, proceed without auth
        
        # Set defaults if not authenticated
        if not hasattr(request, 'user_id'):
            request.user_id = None
            request.user_data = None
        
        return f(*args, **kwargs)
    return decorated

# Input validation schemas
class APIQuerySchema(Schema):
    """Comprehensive input validation for API queries"""
    quarter = fields.Str(
        validate=validate.OneOf(['Q1', 'Q2', 'Q3', 'Q4', 'ALL']),
        missing='ALL',
        error_messages={'invalid_choice': 'Quarter must be Q1, Q2, Q3, Q4, or ALL'}
    )
    year = fields.Int(
        validate=validate.Range(min=2020, max=2030),
        missing=2025,
        error_messages={'invalid': 'Year must be between 2020 and 2030'}
    )
    estado = fields.Str(
        validate=validate.Length(max=100),
        missing=None,
        allow_none=True,
        error_messages={'invalid_length': 'Estado name too long (max 100 characters)'}
    )
    grupo = fields.Str(
        validate=validate.Length(max=100),
        missing=None,
        allow_none=True,
        error_messages={'invalid_length': 'Grupo name too long (max 100 characters)'}
    )
    limit = fields.Int(
        validate=validate.Range(min=1, max=1000),
        missing=20,
        error_messages={'invalid': 'Limit must be between 1 and 1000'}
    )
    offset = fields.Int(
        validate=validate.Range(min=0),
        missing=0,
        error_messages={'invalid': 'Offset must be 0 or greater'}
    )

class TelegramAuthSchema(Schema):
    """Validation for Telegram authentication data"""
    id = fields.Int(required=True)
    first_name = fields.Str(required=True, validate=validate.Length(max=100))
    username = fields.Str(missing=None, allow_none=True, validate=validate.Length(max=50))
    photo_url = fields.Str(missing=None, allow_none=True)
    auth_date = fields.Int(required=True)
    hash = fields.Str(required=True, validate=validate.Length(min=64, max=64))

def validate_input(schema_class):
    """Input validation decorator"""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            schema = schema_class()
            try:
                # Validate query parameters for GET requests
                if request.method == 'GET':
                    validated_data = schema.load(request.args)
                # Validate JSON body for POST/PUT requests
                else:
                    validated_data = schema.load(request.get_json() or {})
                
                request.validated_data = validated_data
            except ValidationError as err:
                logger.warning(f"Validation error: {err.messages}")
                return jsonify({
                    'error': 'Invalid input parameters',
                    'details': err.messages,
                    'error_code': 'VALIDATION_ERROR',
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }), 400
            
            return f(*args, **kwargs)
        return decorated
    return decorator

# Security utilities
class SecurityUtils:
    """Security utility functions"""
    
    @staticmethod
    def generate_api_key() -> str:
        """Generate secure API key"""
        import secrets
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using secure method"""
        import bcrypt
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    @staticmethod
    def verify_password(password: str, hashed: str) -> bool:
        """Verify password against hash"""
        import bcrypt
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    
    @staticmethod
    def sanitize_input(text: str) -> str:
        """Sanitize user input to prevent XSS"""
        import html
        return html.escape(text.strip())

# Audit logging
class AuditLogger:
    """Security audit logging"""
    
    def __init__(self):
        self.logger = logging.getLogger('audit')
        
    def log_authentication(self, user_id: str, success: bool, ip_address: str, user_agent: str):
        """Log authentication attempts"""
        self.logger.info({
            'event': 'authentication',
            'user_id': hashlib.sha256(user_id.encode()).hexdigest()[:16],  # Don't log raw user ID
            'success': success,
            'ip_address': hashlib.sha256(ip_address.encode()).hexdigest()[:16],  # Hash IP for privacy
            'user_agent': user_agent[:100],  # Limit length
            'timestamp': datetime.now(timezone.utc).isoformat()
        })
    
    def log_api_access(self, endpoint: str, user_id: str, method: str, status_code: int):
        """Log API access"""
        self.logger.info({
            'event': 'api_access',
            'endpoint': endpoint,
            'user_id': hashlib.sha256(user_id.encode()).hexdigest()[:16] if user_id else None,
            'method': method,
            'status_code': status_code,
            'timestamp': datetime.now(timezone.utc).isoformat()
        })
    
    def log_security_event(self, event_type: str, details: Dict[str, Any], severity: str = 'INFO'):
        """Log security events"""
        self.logger.log(
            getattr(logging, severity),
            {
                'event': 'security_event',
                'type': event_type,
                'details': details,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
        )

# Global audit logger instance
audit_logger = AuditLogger()