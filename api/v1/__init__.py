"""
API v1 module initialization with RESTful endpoints.
"""

from .auth import auth_bp
from .analytics import analytics_bp
from .geo import geo_bp
from .health import health_bp
from .admin import admin_bp

__all__ = [
    'auth_bp',
    'analytics_bp', 
    'geo_bp',
    'health_bp',
    'admin_bp'
]