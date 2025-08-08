"""
Advanced caching system with Redis and fallback strategies.
Provides intelligent caching for database queries, API responses, and session data.
"""

import os
import redis
import json
import hashlib
import logging
import pickle
from typing import Any, Optional, Dict, List, Union, Callable
from functools import wraps
from datetime import datetime, timedelta, timezone
from contextlib import contextmanager

logger = logging.getLogger(__name__)

class CacheConfig:
    """Cache configuration settings"""
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    DEFAULT_TTL = 300  # 5 minutes
    LONG_TTL = 3600    # 1 hour
    SHORT_TTL = 60     # 1 minute
    
    # Cache TTL by data type
    TTL_CONFIG = {
        'kpis': 300,           # 5 minutes
        'analytics': 600,      # 10 minutes  
        'geo_data': 900,       # 15 minutes
        'user_sessions': 1800, # 30 minutes
        'api_responses': 300,  # 5 minutes
        'database_queries': 180, # 3 minutes
        'static_data': 3600    # 1 hour
    }
    
    # Cache prefixes for organization
    PREFIXES = {
        'query': 'q',
        'api': 'api', 
        'session': 'sess',
        'user': 'user',
        'analytics': 'analytics',
        'geo': 'geo',
        'kpi': 'kpi'
    }

class MemoryCache:
    """In-memory fallback cache when Redis is unavailable"""
    
    def __init__(self, max_size: int = 1000):
        self.cache = {}
        self.access_times = {}
        self.max_size = max_size
    
    def get(self, key: str) -> Optional[Any]:
        """Get value with TTL check"""
        if key not in self.cache:
            return None
        
        value, expires_at = self.cache[key]
        
        # Check if expired
        if expires_at and datetime.now(timezone.utc) > expires_at:
            self.delete(key)
            return None
        
        # Update access time for LRU
        self.access_times[key] = datetime.now(timezone.utc)
        return value
    
    def set(self, key: str, value: Any, ttl: int = None):
        """Set value with optional TTL"""
        # Cleanup if at max size
        if len(self.cache) >= self.max_size:
            self._evict_lru()
        
        expires_at = None
        if ttl:
            expires_at = datetime.now(timezone.utc) + timedelta(seconds=ttl)
        
        self.cache[key] = (value, expires_at)
        self.access_times[key] = datetime.now(timezone.utc)
    
    def delete(self, key: str):
        """Delete key from cache"""
        self.cache.pop(key, None)
        self.access_times.pop(key, None)
    
    def clear(self):
        """Clear all cache"""
        self.cache.clear()
        self.access_times.clear()
    
    def _evict_lru(self):
        """Evict least recently used item"""
        if not self.access_times:
            return
        
        lru_key = min(self.access_times, key=self.access_times.get)
        self.delete(lru_key)

class CacheManager:
    """Advanced Redis-based caching with intelligent fallback"""
    
    def __init__(self):
        self.redis_client = None
        self.memory_cache = MemoryCache()
        self.stats = {
            'hits': 0,
            'misses': 0,
            'errors': 0,
            'redis_available': False
        }
        
        self._init_redis()
    
    def _init_redis(self):
        """Initialize Redis connection with error handling"""
        try:
            self.redis_client = redis.from_url(
                CacheConfig.REDIS_URL,
                decode_responses=False,  # Use binary for pickle support
                socket_connect_timeout=2,
                socket_timeout=2,
                retry_on_timeout=True,
                health_check_interval=30
            )
            
            # Test connection
            self.redis_client.ping()
            self.stats['redis_available'] = True
            logger.info("Redis cache connection established")
            
        except Exception as e:
            logger.warning(f"Redis not available, using memory cache: {e}")
            self.redis_client = None
            self.stats['redis_available'] = False
    
    def generate_cache_key(self, prefix: str, **kwargs) -> str:
        """Generate consistent cache keys"""
        # Sort kwargs for consistent keys
        key_data = json.dumps(kwargs, sort_keys=True, default=str)
        key_hash = hashlib.md5(key_data.encode()).hexdigest()
        
        prefix_short = CacheConfig.PREFIXES.get(prefix, prefix[:3])
        return f"{prefix_short}:{key_hash}"
    
    def get(self, key: str) -> Optional[Any]:
        """Get cached value with fallback strategy"""
        try:
            # Try Redis first
            if self.redis_client:
                value = self.redis_client.get(key)
                if value is not None:
                    self.stats['hits'] += 1
                    try:
                        return pickle.loads(value)
                    except (pickle.PickleError, TypeError):
                        # Fallback to JSON decode
                        return json.loads(value.decode('utf-8'))
                else:
                    self.stats['misses'] += 1
            
            # Fallback to memory cache
            value = self.memory_cache.get(key)
            if value is not None:
                self.stats['hits'] += 1
                return value
            
            self.stats['misses'] += 1
            return None
            
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            self.stats['errors'] += 1
            return None
    
    def set(self, key: str, value: Any, ttl: int = None, cache_type: str = 'default'):
        """Set cached value with intelligent TTL"""
        ttl = ttl or CacheConfig.TTL_CONFIG.get(cache_type, CacheConfig.DEFAULT_TTL)
        
        try:
            # Try Redis first
            if self.redis_client:
                try:
                    serialized_value = pickle.dumps(value)
                except (pickle.PickleError, TypeError):
                    # Fallback to JSON
                    serialized_value = json.dumps(value, default=str).encode('utf-8')
                
                self.redis_client.setex(key, ttl, serialized_value)
                logger.debug(f"Cached in Redis: {key} (TTL: {ttl}s)")
            
            # Also cache in memory for faster access
            self.memory_cache.set(key, value, ttl)
            
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            self.stats['errors'] += 1
            # Always try memory cache as fallback
            self.memory_cache.set(key, value, ttl)
    
    def delete(self, key: str):
        """Delete cached value"""
        try:
            if self.redis_client:
                self.redis_client.delete(key)
            self.memory_cache.delete(key)
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
    
    def clear_pattern(self, pattern: str):
        """Clear cache keys matching pattern"""
        try:
            if self.redis_client:
                keys = self.redis_client.keys(pattern)
                if keys:
                    self.redis_client.delete(*keys)
                    logger.info(f"Cleared {len(keys)} cache keys matching: {pattern}")
        except Exception as e:
            logger.error(f"Cache clear pattern error: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_requests = self.stats['hits'] + self.stats['misses']
        hit_rate = (self.stats['hits'] / total_requests * 100) if total_requests > 0 else 0
        
        stats = {
            **self.stats,
            'hit_rate': round(hit_rate, 2),
            'total_requests': total_requests
        }
        
        # Add Redis info if available
        if self.redis_client:
            try:
                redis_info = self.redis_client.info('memory')
                stats['redis_memory_used'] = redis_info.get('used_memory_human', 'N/A')
                stats['redis_keys'] = self.redis_client.dbsize()
            except Exception:
                pass
        
        return stats
    
    def warm_cache(self, warmup_functions: List[Callable]):
        """Warm cache with commonly accessed data"""
        logger.info("Starting cache warmup...")
        
        for func in warmup_functions:
            try:
                func()
                logger.debug(f"Cache warmed by: {func.__name__}")
            except Exception as e:
                logger.error(f"Cache warmup error in {func.__name__}: {e}")
        
        logger.info("Cache warmup completed")
    
    @contextmanager
    def batch_operations(self):
        """Context manager for batch cache operations"""
        if self.redis_client:
            pipe = self.redis_client.pipeline()
            try:
                yield pipe
                pipe.execute()
            except Exception as e:
                logger.error(f"Batch cache operations error: {e}")
        else:
            yield None

# Global cache manager instance
cache_manager = CacheManager()

# Caching decorators
def cached_query(ttl: int = None, cache_type: str = 'database_queries', key_prefix: str = 'query'):
    """Decorator for caching database query results"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = cache_manager.generate_cache_key(
                key_prefix,
                func_name=func.__name__,
                args=args,
                kwargs=kwargs
            )
            
            # Try to get from cache
            cached_result = cache_manager.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for {func.__name__}")
                return cached_result
            
            # Execute function and cache result
            logger.debug(f"Cache miss for {func.__name__}, executing query")
            result = func(*args, **kwargs)
            
            if result is not None:
                cache_manager.set(cache_key, result, ttl, cache_type)
            
            return result
        return wrapper
    return decorator

def cached_api_response(ttl: int = None, cache_type: str = 'api_responses'):
    """Decorator for caching API responses"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Include request args in cache key
            from flask import request
            
            cache_key = cache_manager.generate_cache_key(
                'api',
                endpoint=request.endpoint,
                args=dict(request.args),
                user_id=getattr(request, 'user_id', None)
            )
            
            # Try cache first
            cached_response = cache_manager.get(cache_key)
            if cached_response is not None:
                return cached_response
            
            # Execute and cache
            response = func(*args, **kwargs)
            if response and isinstance(response, (dict, list)):
                cache_manager.set(cache_key, response, ttl, cache_type)
            
            return response
        return wrapper
    return decorator

def invalidate_cache_on_update(cache_patterns: List[str]):
    """Decorator to invalidate cache after data updates"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            
            # Invalidate related cache patterns
            for pattern in cache_patterns:
                cache_manager.clear_pattern(pattern)
                logger.debug(f"Invalidated cache pattern: {pattern}")
            
            return result
        return wrapper
    return decorator

# Cache warming functions
def warm_kpi_cache():
    """Warm cache with common KPI queries"""
    from database.queries_v3 import get_summary_stats
    
    try:
        # Warm cache for current quarter
        get_summary_stats()
        logger.debug("KPI cache warmed")
    except Exception as e:
        logger.error(f"KPI cache warm error: {e}")

def warm_geo_cache():
    """Warm cache with geographic data"""
    # This would call geographic query functions
    logger.debug("Geo cache warming skipped (functions not available)")

def warm_analytics_cache():
    """Warm cache with analytics data"""
    # This would call analytics functions
    logger.debug("Analytics cache warming skipped (functions not available)")

# Register warmup functions
CACHE_WARMUP_FUNCTIONS = [
    warm_kpi_cache,
    warm_geo_cache,
    warm_analytics_cache
]

# Cache monitoring
class CacheMonitoring:
    """Monitor cache performance and health"""
    
    def __init__(self, cache_manager: CacheManager):
        self.cache_manager = cache_manager
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get cache health status"""
        stats = self.cache_manager.get_stats()
        
        # Determine health based on metrics
        health = "healthy"
        issues = []
        
        if not stats['redis_available']:
            health = "degraded"
            issues.append("Redis unavailable, using memory cache")
        
        if stats['hit_rate'] < 50:
            health = "degraded" if health == "healthy" else "unhealthy"
            issues.append(f"Low cache hit rate: {stats['hit_rate']}%")
        
        if stats['errors'] > stats['total_requests'] * 0.1:
            health = "unhealthy"
            issues.append("High error rate in cache operations")
        
        return {
            'status': health,
            'stats': stats,
            'issues': issues,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
    
    def optimize_cache(self):
        """Perform cache optimization"""
        if self.cache_manager.redis_client:
            try:
                # Get memory info
                info = self.cache_manager.redis_client.info('memory')
                memory_usage = info.get('used_memory', 0)
                max_memory = info.get('maxmemory', 0)
                
                # If memory usage is high, clear some cache
                if max_memory > 0 and memory_usage > max_memory * 0.8:
                    logger.warning("High Redis memory usage, clearing old cache")
                    # Clear oldest entries (implementation depends on Redis version)
            except Exception as e:
                logger.error(f"Cache optimization error: {e}")

# Global cache monitoring instance
cache_monitoring = CacheMonitoring(cache_manager)