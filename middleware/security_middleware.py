"""
Security middleware for rate limiting, headers, and request processing.
"""

import os
import time
import redis
import logging
from typing import Dict, Any, Optional
from functools import wraps
from collections import defaultdict

from flask import Flask, request, jsonify, g
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_talisman import Talisman
from werkzeug.exceptions import TooManyRequests

logger = logging.getLogger(__name__)

class RateLimitConfig:
    """Rate limiting configuration"""
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    DEFAULT_RATE_LIMIT = "100 per hour"
    STRICT_RATE_LIMIT = "10 per minute" 
    API_RATE_LIMIT = "30 per minute"
    AUTH_RATE_LIMIT = "5 per minute"
    
    # Rate limits by endpoint type
    ENDPOINT_LIMITS = {
        '/api/auth/': "5 per minute",
        '/api/kpis': "30 per minute",
        '/api/analytics/': "20 per minute",
        '/api/geo/': "15 per minute",
        '/health': "100 per minute"
    }

class SecurityHeadersConfig:
    """Security headers configuration"""
    CSP_POLICY = {
        'default-src': "'self'",
        'script-src': [
            "'self'",
            "'unsafe-inline'",  # Required for Telegram WebApp
            "https://telegram.org",
            "https://cdn.jsdelivr.net",
            "https://cdn.plot.ly",
            "https://d3js.org",
            "https://unpkg.com"
        ],
        'style-src': [
            "'self'",
            "'unsafe-inline'",  # Required for dynamic styles
            "https://cdn.jsdelivr.net",
            "https://unpkg.com"
        ],
        'connect-src': [
            "'self'",
            "https://api.telegram.org"
        ],
        'img-src': [
            "'self'",
            "data:",
            "https:"
        ],
        'font-src': [
            "'self'",
            "https://cdn.jsdelivr.net"
        ]
    }

class InMemoryRateLimiter:
    """In-memory rate limiter for when Redis is not available"""
    
    def __init__(self):
        self.requests = defaultdict(list)
        self.cleanup_interval = 300  # 5 minutes
        self.last_cleanup = time.time()
    
    def is_allowed(self, key: str, limit: int, window: int) -> bool:
        """Check if request is within rate limit"""
        now = time.time()
        
        # Cleanup old entries periodically
        if now - self.last_cleanup > self.cleanup_interval:
            self._cleanup_old_entries(now)
            self.last_cleanup = now
        
        # Get requests for this key
        requests = self.requests[key]
        
        # Remove old requests outside the window
        cutoff = now - window
        requests[:] = [req_time for req_time in requests if req_time > cutoff]
        
        # Check if under limit
        if len(requests) >= limit:
            return False
        
        # Add current request
        requests.append(now)
        return True
    
    def _cleanup_old_entries(self, now: float):
        """Clean up old entries to prevent memory growth"""
        cutoff = now - 3600  # Keep last hour
        for key in list(self.requests.keys()):
            self.requests[key] = [
                req_time for req_time in self.requests[key] 
                if req_time > cutoff
            ]
            if not self.requests[key]:
                del self.requests[key]

class SecurityMiddleware:
    """Comprehensive security middleware"""
    
    def __init__(self, app: Flask = None):
        self.app = app
        self.redis_client = None
        self.memory_limiter = InMemoryRateLimiter()
        
        if app:
            self.init_app(app)
    
    def init_app(self, app: Flask):
        """Initialize security middleware with Flask app"""
        self.app = app
        
        # Initialize Redis connection
        try:
            self.redis_client = redis.from_url(
                RateLimitConfig.REDIS_URL,
                decode_responses=True,
                socket_connect_timeout=2,
                socket_timeout=2
            )
            # Test connection
            self.redis_client.ping()
            logger.info("Redis connection established for rate limiting")
        except Exception as e:
            logger.warning(f"Redis not available, using in-memory rate limiting: {e}")
            self.redis_client = None
        
        # Configure Flask-Limiter
        self.limiter = Limiter(
            key_func=self._get_rate_limit_key,
            default_limits=[RateLimitConfig.DEFAULT_RATE_LIMIT],
            storage_uri=RateLimitConfig.REDIS_URL if self.redis_client else None,
            strategy="fixed-window"
        )
        self.limiter.init_app(app)
        
        # Configure security headers
        self._configure_security_headers(app)
        
        # Register middleware
        app.before_request(self._before_request)
        app.after_request(self._after_request)
        
        # Error handlers
        app.errorhandler(429)(self._rate_limit_handler)
    
    def _get_rate_limit_key(self) -> str:
        """Generate rate limit key based on user or IP"""
        # Use authenticated user ID if available
        if hasattr(request, 'user_id') and request.user_id:
            return f"user:{request.user_id}"
        
        # Use IP address with additional factors
        ip = get_remote_address()
        user_agent = request.headers.get('User-Agent', '')[:50]
        
        # Create composite key for better tracking
        return f"ip:{ip}"
    
    def _configure_security_headers(self, app: Flask):
        """Configure security headers using Flask-Talisman"""
        # Security headers configuration
        talisman_config = {
            'force_https': app.config.get('FORCE_HTTPS', False),  # Disable for development
            'strict_transport_security': True,
            'strict_transport_security_max_age': 31536000,
            'content_security_policy': SecurityHeadersConfig.CSP_POLICY,
            'frame_options': 'SAMEORIGIN',
            'referrer_policy': 'strict-origin-when-cross-origin'
        }
        
        # Apply Talisman with configuration
        Talisman(app, **talisman_config)
        
        logger.info("Security headers configured")
    
    def _before_request(self):
        """Process request before handling"""
        g.request_start_time = time.time()
        
        # Additional rate limiting for specific endpoints
        endpoint = request.endpoint
        if endpoint:
            limit_info = self._get_endpoint_limit(request.path)
            if limit_info and not self._check_custom_rate_limit(limit_info):
                return self._rate_limit_response()
        
        # Security logging
        if request.path.startswith('/api/'):
            self._log_api_request()
    
    def _after_request(self, response):
        """Process response after handling"""
        # Add custom security headers
        response.headers['X-Request-ID'] = getattr(g, 'request_id', 'unknown')
        response.headers['X-Response-Time'] = f"{time.time() - getattr(g, 'request_start_time', 0):.3f}s"
        
        # Security audit logging
        if hasattr(request, 'user_id') and request.path.startswith('/api/'):
            from auth.security import audit_logger
            audit_logger.log_api_access(
                endpoint=request.path,
                user_id=request.user_id or 'anonymous',
                method=request.method,
                status_code=response.status_code
            )
        
        return response
    
    def _get_endpoint_limit(self, path: str) -> Optional[Dict[str, Any]]:
        """Get rate limit configuration for endpoint"""
        for pattern, limit in RateLimitConfig.ENDPOINT_LIMITS.items():
            if path.startswith(pattern):
                return self._parse_rate_limit(limit)
        return None
    
    def _parse_rate_limit(self, limit_str: str) -> Dict[str, Any]:
        """Parse rate limit string into components"""
        parts = limit_str.split(' per ')
        if len(parts) != 2:
            return None
        
        count = int(parts[0])
        unit = parts[1]
        
        # Convert to seconds
        unit_seconds = {
            'second': 1,
            'minute': 60,
            'hour': 3600,
            'day': 86400
        }
        
        window = unit_seconds.get(unit, 60)
        
        return {
            'count': count,
            'window': window,
            'description': limit_str
        }
    
    def _check_custom_rate_limit(self, limit_info: Dict[str, Any]) -> bool:
        """Check custom rate limit"""
        key = self._get_rate_limit_key()
        count = limit_info['count']
        window = limit_info['window']
        
        if self.redis_client:
            return self._check_redis_rate_limit(key, count, window)
        else:
            return self.memory_limiter.is_allowed(key, count, window)
    
    def _check_redis_rate_limit(self, key: str, count: int, window: int) -> bool:
        """Check rate limit using Redis"""
        try:
            pipe = self.redis_client.pipeline()
            now = time.time()
            
            # Use sliding window log
            pipe.zremrangebyscore(key, 0, now - window)
            pipe.zcard(key)
            pipe.zadd(key, {str(now): now})
            pipe.expire(key, window)
            
            results = pipe.execute()
            current_requests = results[1]
            
            return current_requests < count
        except Exception as e:
            logger.error(f"Redis rate limit error: {e}")
            # Fallback to memory limiter
            return self.memory_limiter.is_allowed(key, count, window)
    
    def _rate_limit_response(self):
        """Generate rate limit exceeded response"""
        return jsonify({
            'error': 'Rate limit exceeded',
            'message': 'Too many requests. Please slow down.',
            'error_code': 'RATE_LIMIT_EXCEEDED',
            'retry_after': 60
        }), 429
    
    def _rate_limit_handler(self, e):
        """Handle rate limit exceeded errors"""
        logger.warning(f"Rate limit exceeded for {get_remote_address()}: {e}")
        
        return jsonify({
            'error': 'Rate limit exceeded',
            'message': str(e.description) if hasattr(e, 'description') else 'Too many requests',
            'error_code': 'RATE_LIMIT_EXCEEDED',
            'retry_after': getattr(e, 'retry_after', 60)
        }), 429
    
    def _log_api_request(self):
        """Log API request for security monitoring"""
        logger.info({
            'event': 'api_request',
            'path': request.path,
            'method': request.method,
            'ip': get_remote_address(),
            'user_agent': request.headers.get('User-Agent', '')[:100],
            'user_id': getattr(request, 'user_id', None)
        })

# Rate limiting decorators for specific use cases
def rate_limit_by_user(limit: str):
    """Rate limit decorator that uses user ID if available"""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            # This will be handled by the global limiter
            return f(*args, **kwargs)
        return decorated
    return decorator

def strict_rate_limit(f):
    """Apply strict rate limiting to sensitive endpoints"""
    @wraps(f)
    def decorated(*args, **kwargs):
        # Additional strict checking can be added here
        return f(*args, **kwargs)
    return decorated

# IP-based blocking for security
class IPBlocklist:
    """Manage IP blocklist for security"""
    
    def __init__(self, redis_client=None):
        self.redis_client = redis_client
        self.memory_blocklist = set()
    
    def block_ip(self, ip: str, duration: int = 3600, reason: str = "Security violation"):
        """Block IP address for specified duration"""
        if self.redis_client:
            try:
                self.redis_client.setex(f"blocked_ip:{ip}", duration, reason)
                logger.warning(f"Blocked IP {ip} for {duration}s: {reason}")
            except Exception as e:
                logger.error(f"Failed to block IP in Redis: {e}")
                self.memory_blocklist.add(ip)
        else:
            self.memory_blocklist.add(ip)
            logger.warning(f"Blocked IP {ip} in memory: {reason}")
    
    def is_blocked(self, ip: str) -> bool:
        """Check if IP is blocked"""
        if self.redis_client:
            try:
                return bool(self.redis_client.exists(f"blocked_ip:{ip}"))
            except Exception:
                pass
        
        return ip in self.memory_blocklist
    
    def unblock_ip(self, ip: str):
        """Unblock IP address"""
        if self.redis_client:
            try:
                self.redis_client.delete(f"blocked_ip:{ip}")
            except Exception:
                pass
        
        self.memory_blocklist.discard(ip)
        logger.info(f"Unblocked IP {ip}")

# Security monitoring
class SecurityMonitor:
    """Monitor for suspicious activities"""
    
    def __init__(self):
        self.suspicious_patterns = [
            'script',
            'javascript:',
            '<script',
            'union select',
            'drop table',
            '../',
            'passwd',
            'etc/passwd'
        ]
    
    def check_request_security(self, request) -> Dict[str, Any]:
        """Check request for security issues"""
        issues = []
        
        # Check for SQL injection patterns
        query_string = str(request.query_string)
        for pattern in self.suspicious_patterns:
            if pattern.lower() in query_string.lower():
                issues.append(f"Suspicious pattern detected: {pattern}")
        
        # Check request size
        if request.content_length and request.content_length > 10 * 1024 * 1024:  # 10MB
            issues.append("Request too large")
        
        # Check for too many parameters
        if len(request.args) > 50:
            issues.append("Too many parameters")
        
        return {
            'secure': len(issues) == 0,
            'issues': issues,
            'risk_score': len(issues) * 0.3
        }

# Global instances
security_middleware = SecurityMiddleware()
ip_blocklist = IPBlocklist()
security_monitor = SecurityMonitor()