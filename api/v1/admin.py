"""
Administrative API endpoints for system management and maintenance.
"""

import logging
from datetime import datetime, timezone
from flask import Blueprint, request, jsonify

from auth.security import require_auth, validate_input
from database.optimization import db_optimizer, maintenance_tasks
from cache.cache_manager import cache_manager, CACHE_WARMUP_FUNCTIONS
from middleware.security_middleware import strict_rate_limit

logger = logging.getLogger(__name__)
admin_bp = Blueprint('admin', __name__, url_prefix='/api/v1/admin')

@admin_bp.route('/cache/clear', methods=['POST'])
@require_auth
@strict_rate_limit
def clear_cache():
    """
    Clear application cache.
    
    Requires authentication. Use with caution in production.
    """
    try:
        # Clear all cache
        cache_manager.memory_cache.clear()
        
        if cache_manager.redis_client:
            cache_manager.redis_client.flushdb()
        
        logger.info(f"Cache cleared by user: {request.user_id}")
        
        return jsonify({
            'success': True,
            'message': 'Cache cleared successfully',
            'timestamp': datetime.now(timezone.utc).isoformat()
        })
        
    except Exception as e:
        logger.error(f"Cache clear error: {e}")
        return jsonify({
            'error': 'Failed to clear cache',
            'error_code': 'CACHE_CLEAR_ERROR'
        }), 500

@admin_bp.route('/cache/warm', methods=['POST'])
@require_auth
@strict_rate_limit
def warm_cache():
    """
    Warm application cache with commonly accessed data.
    
    Executes cache warming functions to pre-populate frequently used data.
    """
    try:
        # Execute cache warming
        cache_manager.warm_cache(CACHE_WARMUP_FUNCTIONS)
        
        logger.info(f"Cache warming initiated by user: {request.user_id}")
        
        return jsonify({
            'success': True,
            'message': 'Cache warming completed',
            'functions_executed': len(CACHE_WARMUP_FUNCTIONS),
            'timestamp': datetime.now(timezone.utc).isoformat()
        })
        
    except Exception as e:
        logger.error(f"Cache warm error: {e}")
        return jsonify({
            'error': 'Failed to warm cache',
            'error_code': 'CACHE_WARM_ERROR'
        }), 500

@admin_bp.route('/database/optimize', methods=['POST'])
@require_auth
@strict_rate_limit
def optimize_database():
    """
    Run database optimization tasks.
    
    Creates indexes, materialized views, and runs maintenance tasks.
    """
    try:
        results = {
            'indexes': {'created': [], 'skipped': [], 'errors': []},
            'materialized_views': {'created': [], 'skipped': [], 'errors': []},
            'maintenance': {'completed': False, 'error': None}
        }
        
        # Create indexes
        try:
            index_results = db_optimizer.create_indexes()
            results['indexes'] = index_results
        except Exception as e:
            logger.error(f"Index creation error: {e}")
            results['indexes']['errors'] = [f"Index creation failed: {str(e)}"]
        
        # Create materialized views
        try:
            view_results = db_optimizer.create_materialized_views()
            results['materialized_views'] = view_results
        except Exception as e:
            logger.error(f"Materialized view creation error: {e}")
            results['materialized_views']['errors'] = [f"View creation failed: {str(e)}"]
        
        # Run maintenance
        try:
            maintenance_tasks.daily_maintenance()
            results['maintenance']['completed'] = True
        except Exception as e:
            logger.error(f"Maintenance error: {e}")
            results['maintenance']['error'] = str(e)
        
        logger.info(f"Database optimization initiated by user: {request.user_id}")
        
        return jsonify({
            'success': True,
            'message': 'Database optimization completed',
            'results': results,
            'timestamp': datetime.now(timezone.utc).isoformat()
        })
        
    except Exception as e:
        logger.error(f"Database optimization error: {e}")
        return jsonify({
            'error': 'Failed to optimize database',
            'error_code': 'DB_OPTIMIZE_ERROR'
        }), 500

@admin_bp.route('/database/stats', methods=['GET'])
@require_auth
def get_database_stats():
    """
    Get database statistics and analysis.
    
    Returns table statistics, size information, and performance metrics.
    """
    try:
        stats = db_optimizer.analyze_table_stats()
        
        return jsonify({
            'success': True,
            'data': stats,
            'timestamp': datetime.now(timezone.utc).isoformat()
        })
        
    except Exception as e:
        logger.error(f"Database stats error: {e}")
        return jsonify({
            'error': 'Failed to get database statistics',
            'error_code': 'DB_STATS_ERROR'
        }), 500

@admin_bp.route('/system/info', methods=['GET'])
@require_auth
def get_system_info():
    """
    Get comprehensive system information.
    
    Returns application version, configuration, and runtime information.
    """
    try:
        import os
        import psutil
        
        system_info = {
            'application': {
                'version': '1.0.0',
                'environment': os.getenv('FLASK_ENV', 'production'),
                'debug_mode': os.getenv('DEBUG', 'false').lower() == 'true'
            },
            'system': {
                'python_version': f"{psutil.version_info}",
                'cpu_count': psutil.cpu_count(),
                'memory_total_gb': round(psutil.virtual_memory().total / (1024**3), 2),
                'disk_total_gb': round(psutil.disk_usage('/').total / (1024**3), 2)
            },
            'database': {
                'url_configured': bool(os.getenv('DATABASE_URL')),
                'connection_healthy': bool(db_optimizer._index_exists('dummy'))  # Simple connectivity test
            },
            'cache': {
                'redis_configured': bool(os.getenv('REDIS_URL')),
                'redis_available': cache_manager.stats['redis_available']
            },
            'security': {
                'jwt_configured': bool(os.getenv('JWT_SECRET_KEY')),
                'bot_token_configured': bool(os.getenv('BOT_TOKEN'))
            }
        }
        
        return jsonify({
            'success': True,
            'data': system_info,
            'timestamp': datetime.now(timezone.utc).isoformat()
        })
        
    except Exception as e:
        logger.error(f"System info error: {e}")
        return jsonify({
            'error': 'Failed to get system information',
            'error_code': 'SYSTEM_INFO_ERROR'
        }), 500

@admin_bp.route('/logs/recent', methods=['GET'])
@require_auth
def get_recent_logs():
    """
    Get recent application logs.
    
    Returns recent log entries for debugging and monitoring.
    """
    try:
        # This is a simplified implementation
        # In production, you'd integrate with your logging system
        
        import subprocess
        import os
        
        log_lines = []
        
        # Try to read from common log locations
        log_files = [
            '/var/log/app.log',
            './logs/app.log',
            './app.log'
        ]
        
        for log_file in log_files:
            if os.path.exists(log_file):
                try:
                    result = subprocess.run(['tail', '-50', log_file], 
                                          capture_output=True, text=True, timeout=5)
                    if result.returncode == 0:
                        log_lines = result.stdout.split('\n')
                        break
                except (subprocess.TimeoutExpired, subprocess.SubprocessError):
                    continue
        
        return jsonify({
            'success': True,
            'data': {
                'lines': log_lines[-50:],  # Last 50 lines
                'total_lines': len(log_lines),
                'source': 'application_logs'
            },
            'timestamp': datetime.now(timezone.utc).isoformat()
        })
        
    except Exception as e:
        logger.error(f"Recent logs error: {e}")
        return jsonify({
            'error': 'Failed to get recent logs',
            'error_code': 'LOGS_ERROR'
        }), 500

@admin_bp.route('/maintenance/run', methods=['POST'])
@require_auth
@strict_rate_limit
def run_maintenance():
    """
    Run system maintenance tasks.
    
    Executes daily maintenance routines including cache cleanup,
    database maintenance, and system optimization.
    """
    try:
        maintenance_results = {
            'database_maintenance': False,
            'cache_cleanup': False,
            'errors': []
        }
        
        # Run database maintenance
        try:
            maintenance_tasks.daily_maintenance()
            maintenance_results['database_maintenance'] = True
        except Exception as e:
            logger.error(f"Database maintenance error: {e}")
            maintenance_results['errors'].append(f"Database maintenance: {str(e)}")
        
        # Cache cleanup
        try:
            # Clear old cache entries
            cache_manager.clear_pattern("*:expired:*")
            maintenance_results['cache_cleanup'] = True
        except Exception as e:
            logger.error(f"Cache cleanup error: {e}")
            maintenance_results['errors'].append(f"Cache cleanup: {str(e)}")
        
        logger.info(f"System maintenance initiated by user: {request.user_id}")
        
        success = len(maintenance_results['errors']) == 0
        
        return jsonify({
            'success': success,
            'message': 'Maintenance tasks completed' if success else 'Maintenance completed with errors',
            'results': maintenance_results,
            'timestamp': datetime.now(timezone.utc).isoformat()
        })
        
    except Exception as e:
        logger.error(f"Maintenance error: {e}")
        return jsonify({
            'error': 'Failed to run maintenance tasks',
            'error_code': 'MAINTENANCE_ERROR'
        }), 500

# Error handlers for admin blueprint
@admin_bp.errorhandler(401)
def handle_unauthorized(error):
    """Handle unauthorized access to admin endpoints"""
    return jsonify({
        'error': 'Administrative access required',
        'message': 'This endpoint requires administrator authentication',
        'error_code': 'ADMIN_ACCESS_REQUIRED'
    }), 401

@admin_bp.errorhandler(429)
def handle_admin_rate_limit(error):
    """Handle rate limit errors for admin endpoints"""
    return jsonify({
        'error': 'Administrative action rate limit exceeded',
        'message': 'Too many administrative actions. Please wait before trying again.',
        'error_code': 'ADMIN_RATE_LIMIT_EXCEEDED',
        'retry_after': 300  # 5 minutes for admin actions
    }), 429