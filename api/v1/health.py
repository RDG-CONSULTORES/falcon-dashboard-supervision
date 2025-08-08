"""
Health check and monitoring endpoints.
"""

import os
import logging
import psutil
from datetime import datetime, timezone
from flask import Blueprint, jsonify

from database.connection_v3 import test_connection
from cache.cache_manager import cache_manager, cache_monitoring
from middleware.security_middleware import security_middleware

logger = logging.getLogger(__name__)
health_bp = Blueprint('health', __name__, url_prefix='/api/v1/health')

@health_bp.route('/', methods=['GET'])
def health_check():
    """
    Basic health check endpoint.
    
    Returns basic system status for load balancers and monitoring.
    """
    try:
        # Basic database connectivity test
        db_healthy = test_connection()
        
        # Check cache status
        cache_status = cache_monitoring.get_health_status()
        
        # Determine overall health
        overall_status = "healthy"
        if not db_healthy:
            overall_status = "unhealthy"
        elif cache_status['status'] != "healthy":
            overall_status = "degraded"
        
        response = {
            'status': overall_status,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'version': '1.0.0',
            'components': {
                'database': 'healthy' if db_healthy else 'unhealthy',
                'cache': cache_status['status']
            }
        }
        
        status_code = 200 if overall_status == "healthy" else 503
        
        return jsonify(response), status_code
        
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return jsonify({
            'status': 'unhealthy',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'error': 'Health check failed'
        }), 503

@health_bp.route('/detailed', methods=['GET'])
def detailed_health():
    """
    Detailed health check with comprehensive system information.
    
    Returns detailed status of all system components.
    """
    try:
        # Database health
        db_healthy = test_connection()
        db_response_time = None
        
        if db_healthy:
            start_time = datetime.now()
            try:
                from database.connection_v3 import execute_query
                execute_query("SELECT 1;")
                db_response_time = (datetime.now() - start_time).total_seconds() * 1000
            except Exception:
                db_response_time = None
        
        # Cache health
        cache_status = cache_monitoring.get_health_status()
        
        # System metrics
        system_metrics = {
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_percent': psutil.disk_usage('/').percent,
            'load_average': os.getloadavg() if hasattr(os, 'getloadavg') else None
        }
        
        # Application metrics
        app_metrics = {
            'uptime_seconds': (datetime.now() - datetime.fromtimestamp(psutil.Process().create_time())).total_seconds(),
            'process_memory_mb': psutil.Process().memory_info().rss / 1024 / 1024,
            'open_files': len(psutil.Process().open_files()),
            'connections': len(psutil.Process().connections())
        }
        
        # Determine overall health
        overall_status = "healthy"
        issues = []
        
        if not db_healthy:
            overall_status = "unhealthy"
            issues.append("Database connection failed")
        elif db_response_time and db_response_time > 1000:  # >1 second
            overall_status = "degraded"
            issues.append(f"Database slow response: {db_response_time:.0f}ms")
        
        if cache_status['status'] != "healthy":
            if overall_status == "healthy":
                overall_status = "degraded"
            issues.extend(cache_status.get('issues', []))
        
        if system_metrics['memory_percent'] > 90:
            if overall_status == "healthy":
                overall_status = "degraded"
            issues.append(f"High memory usage: {system_metrics['memory_percent']:.1f}%")
        
        if system_metrics['cpu_percent'] > 90:
            if overall_status == "healthy":
                overall_status = "degraded"
            issues.append(f"High CPU usage: {system_metrics['cpu_percent']:.1f}%")
        
        response = {
            'status': overall_status,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'version': '1.0.0',
            'issues': issues,
            'components': {
                'database': {
                    'status': 'healthy' if db_healthy else 'unhealthy',
                    'response_time_ms': db_response_time
                },
                'cache': cache_status,
                'system': {
                    'status': 'healthy' if system_metrics['memory_percent'] < 90 and system_metrics['cpu_percent'] < 90 else 'degraded',
                    'metrics': system_metrics
                },
                'application': {
                    'status': 'healthy',
                    'metrics': app_metrics
                }
            }
        }
        
        status_code = 200 if overall_status == "healthy" else 503
        
        return jsonify(response), status_code
        
    except Exception as e:
        logger.error(f"Detailed health check error: {e}")
        return jsonify({
            'status': 'unhealthy',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'error': f'Detailed health check failed: {str(e)}'
        }), 503

@health_bp.route('/database', methods=['GET'])
def database_health():
    """
    Database-specific health check.
    
    Returns detailed database connection and performance information.
    """
    try:
        start_time = datetime.now()
        
        # Test basic connectivity
        db_connected = test_connection()
        
        if not db_connected:
            return jsonify({
                'status': 'unhealthy',
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'error': 'Database connection failed'
            }), 503
        
        # Test query performance
        from database.connection_v3 import execute_query
        
        # Simple query test
        test_result = execute_query("SELECT NOW() as current_time, version() as db_version;")
        response_time = (datetime.now() - start_time).total_seconds() * 1000
        
        # Connection pool info (if available)
        pool_info = {}
        try:
            from database.connection_v3 import connection_pool
            if connection_pool:
                pool_info = {
                    'pool_size': connection_pool.max_size,
                    'available_connections': connection_pool.get_stats().get('pool_available', 'unknown'),
                    'pool_hits': connection_pool.get_stats().get('pool_hits', 'unknown')
                }
        except Exception:
            pool_info = {'error': 'Pool info unavailable'}
        
        # Determine status based on response time
        if response_time < 100:
            status = 'excellent'
        elif response_time < 500:
            status = 'good'
        elif response_time < 1000:
            status = 'degraded'
        else:
            status = 'poor'
        
        response = {
            'status': status,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'database': {
                'connected': True,
                'response_time_ms': round(response_time, 2),
                'server_time': test_result[0]['current_time'].isoformat() if test_result else None,
                'version': test_result[0]['db_version'] if test_result else None,
                'pool_info': pool_info
            }
        }
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Database health check error: {e}")
        return jsonify({
            'status': 'unhealthy',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'error': f'Database health check failed: {str(e)}'
        }), 503

@health_bp.route('/cache', methods=['GET'])
def cache_health():
    """
    Cache-specific health check.
    
    Returns detailed cache performance and status information.
    """
    try:
        cache_status = cache_monitoring.get_health_status()
        cache_stats = cache_manager.get_stats()
        
        response = {
            'status': cache_status['status'],
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'cache': {
                'redis_available': cache_stats['redis_available'],
                'hit_rate': cache_stats['hit_rate'],
                'total_requests': cache_stats['total_requests'],
                'hits': cache_stats['hits'],
                'misses': cache_stats['misses'],
                'errors': cache_stats['errors'],
                'redis_memory_used': cache_stats.get('redis_memory_used', 'N/A'),
                'redis_keys': cache_stats.get('redis_keys', 'N/A')
            },
            'issues': cache_status.get('issues', [])
        }
        
        status_code = 200 if cache_status['status'] == 'healthy' else 503
        
        return jsonify(response), status_code
        
    except Exception as e:
        logger.error(f"Cache health check error: {e}")
        return jsonify({
            'status': 'unhealthy',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'error': f'Cache health check failed: {str(e)}'
        }), 503

@health_bp.route('/readiness', methods=['GET'])
def readiness_check():
    """
    Kubernetes readiness probe endpoint.
    
    Returns whether the application is ready to serve traffic.
    """
    try:
        # Check critical dependencies
        db_ready = test_connection()
        
        if not db_ready:
            return jsonify({
                'ready': False,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'reason': 'Database not ready'
            }), 503
        
        return jsonify({
            'ready': True,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'components_ready': {
                'database': True,
                'cache': cache_manager.stats['redis_available']
            }
        })
        
    except Exception as e:
        logger.error(f"Readiness check error: {e}")
        return jsonify({
            'ready': False,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'error': str(e)
        }), 503

@health_bp.route('/liveness', methods=['GET'])
def liveness_check():
    """
    Kubernetes liveness probe endpoint.
    
    Returns whether the application is alive and should be restarted if not.
    """
    try:
        # Simple liveness check - just return OK if we can process the request
        return jsonify({
            'alive': True,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'uptime_seconds': (datetime.now() - datetime.fromtimestamp(psutil.Process().create_time())).total_seconds()
        })
        
    except Exception as e:
        logger.error(f"Liveness check error: {e}")
        return jsonify({
            'alive': False,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'error': str(e)
        }), 503

@health_bp.route('/metrics', methods=['GET'])
def metrics():
    """
    Prometheus-style metrics endpoint.
    
    Returns metrics in a format compatible with monitoring systems.
    """
    try:
        # Get various metrics
        cache_stats = cache_manager.get_stats()
        system_metrics = {
            'cpu_percent': psutil.cpu_percent(),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_percent': psutil.disk_usage('/').percent
        }
        
        # Format as Prometheus metrics
        metrics_text = f"""# HELP app_cache_hit_rate Cache hit rate percentage
# TYPE app_cache_hit_rate gauge
app_cache_hit_rate {cache_stats['hit_rate']}

# HELP app_cache_requests_total Total cache requests
# TYPE app_cache_requests_total counter
app_cache_requests_total {cache_stats['total_requests']}

# HELP app_system_cpu_percent CPU usage percentage
# TYPE app_system_cpu_percent gauge
app_system_cpu_percent {system_metrics['cpu_percent']}

# HELP app_system_memory_percent Memory usage percentage
# TYPE app_system_memory_percent gauge
app_system_memory_percent {system_metrics['memory_percent']}

# HELP app_system_disk_percent Disk usage percentage
# TYPE app_system_disk_percent gauge
app_system_disk_percent {system_metrics['disk_percent']}

# HELP app_database_connected Database connection status
# TYPE app_database_connected gauge
app_database_connected {1 if test_connection() else 0}

# HELP app_redis_available Redis availability status
# TYPE app_redis_available gauge
app_redis_available {1 if cache_stats['redis_available'] else 0}
"""
        
        from flask import Response
        return Response(metrics_text, mimetype='text/plain')
        
    except Exception as e:
        logger.error(f"Metrics endpoint error: {e}")
        return jsonify({
            'error': f'Metrics collection failed: {str(e)}'
        }), 500