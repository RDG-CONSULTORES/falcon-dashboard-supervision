"""
Authentication API endpoints.
"""

import logging
from flask import Blueprint, request, jsonify
from marshmallow import Schema, fields, ValidationError

from auth.security import (
    AuthenticationService, TelegramAuth, validate_input,
    TelegramAuthSchema, audit_logger, require_auth
)
from middleware.security_middleware import strict_rate_limit

logger = logging.getLogger(__name__)
auth_bp = Blueprint('auth', __name__, url_prefix='/api/v1/auth')

class LoginSchema(Schema):
    """Schema for login request validation"""
    username = fields.Str(required=True, validate=lambda x: len(x.strip()) > 0)
    password = fields.Str(required=True, validate=lambda x: len(x.strip()) > 0)

class RefreshTokenSchema(Schema):
    """Schema for refresh token request"""
    refresh_token = fields.Str(required=True)

@auth_bp.route('/telegram', methods=['POST'])
@strict_rate_limit
@validate_input(TelegramAuthSchema)
def telegram_auth():
    """
    Authenticate user via Telegram WebApp data.
    
    Expected payload:
    {
        "id": 123456789,
        "first_name": "John",
        "username": "john_doe",
        "photo_url": "https://...",
        "auth_date": 1641234567,
        "hash": "abcd1234..."
    }
    """
    try:
        auth_data = request.validated_data
        
        # Verify Telegram authentication data
        if not TelegramAuth.verify_telegram_data(auth_data.copy()):
            audit_logger.log_authentication(
                user_id=f"tg_{auth_data.get('id')}",
                success=False,
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent', '')
            )
            
            return jsonify({
                'error': 'Invalid Telegram authentication data',
                'error_code': 'INVALID_TELEGRAM_AUTH'
            }), 401
        
        # Create authenticated session
        tokens = TelegramAuth.create_telegram_session(auth_data)
        
        audit_logger.log_authentication(
            user_id=f"tg_{auth_data.get('id')}",
            success=True,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent', '')
        )
        
        return jsonify({
            'success': True,
            'user': {
                'id': f"tg_{auth_data.get('id')}",
                'telegram_id': auth_data.get('id'),
                'first_name': auth_data.get('first_name'),
                'username': auth_data.get('username')
            },
            'tokens': tokens
        })
        
    except Exception as e:
        logger.error(f"Telegram authentication error: {e}")
        return jsonify({
            'error': 'Authentication failed',
            'error_code': 'AUTH_ERROR'
        }), 500

@auth_bp.route('/refresh', methods=['POST'])
@strict_rate_limit
@validate_input(RefreshTokenSchema)
def refresh_token():
    """
    Refresh access token using refresh token.
    
    Expected payload:
    {
        "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
    }
    """
    try:
        refresh_token = request.validated_data['refresh_token']
        
        # Generate new tokens
        new_tokens = AuthenticationService.refresh_access_token(refresh_token)
        
        if not new_tokens:
            return jsonify({
                'error': 'Invalid or expired refresh token',
                'error_code': 'INVALID_REFRESH_TOKEN'
            }), 401
        
        return jsonify({
            'success': True,
            'tokens': new_tokens
        })
        
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        return jsonify({
            'error': 'Token refresh failed',
            'error_code': 'REFRESH_ERROR'
        }), 500

@auth_bp.route('/logout', methods=['POST'])
@require_auth
def logout():
    """
    Logout user (invalidate tokens).
    Note: JWT tokens are stateless, so we would need a blacklist
    implementation for true logout. For now, this is a placeholder.
    """
    try:
        user_id = request.user_id
        
        audit_logger.log_security_event(
            event_type='logout',
            details={'user_id': user_id},
            severity='INFO'
        )
        
        return jsonify({
            'success': True,
            'message': 'Logged out successfully'
        })
        
    except Exception as e:
        logger.error(f"Logout error: {e}")
        return jsonify({
            'error': 'Logout failed',
            'error_code': 'LOGOUT_ERROR'
        }), 500

@auth_bp.route('/verify', methods=['GET'])
@require_auth
def verify_token():
    """
    Verify current token and get user info.
    """
    try:
        return jsonify({
            'success': True,
            'valid': True,
            'user': {
                'id': request.user_id,
                'data': request.user_data
            }
        })
        
    except Exception as e:
        logger.error(f"Token verification error: {e}")
        return jsonify({
            'error': 'Token verification failed',
            'error_code': 'VERIFY_ERROR'
        }), 500

@auth_bp.route('/me', methods=['GET'])
@require_auth
def get_user_profile():
    """
    Get current user profile information.
    """
    try:
        user_data = request.user_data
        
        return jsonify({
            'success': True,
            'user': {
                'id': request.user_id,
                'telegram_id': user_data.get('telegram_id'),
                'first_name': user_data.get('first_name'),
                'username': user_data.get('username'),
                'auth_method': user_data.get('auth_method'),
                'authenticated_at': user_data.get('iat')
            }
        })
        
    except Exception as e:
        logger.error(f"Get user profile error: {e}")
        return jsonify({
            'error': 'Failed to get user profile',
            'error_code': 'PROFILE_ERROR'
        }), 500

# Error handlers for auth blueprint
@auth_bp.errorhandler(ValidationError)
def handle_validation_error(error):
    """Handle validation errors"""
    return jsonify({
        'error': 'Invalid input data',
        'details': error.messages,
        'error_code': 'VALIDATION_ERROR'
    }), 400

@auth_bp.errorhandler(429)
def handle_rate_limit(error):
    """Handle rate limit errors"""
    return jsonify({
        'error': 'Too many authentication attempts',
        'message': 'Please wait before trying again',
        'error_code': 'RATE_LIMIT_EXCEEDED',
        'retry_after': 60
    }), 429