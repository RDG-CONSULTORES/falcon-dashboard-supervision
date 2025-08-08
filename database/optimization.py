"""
Database optimization module with indexes, materialized views, and query optimization.
"""

import os
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

from .connection_v3 import execute_query
from cache.cache_manager import cached_query, cache_manager

logger = logging.getLogger(__name__)

class DatabaseOptimizer:
    """Database optimization utilities"""
    
    # Critical indexes for performance improvement
    CRITICAL_INDEXES = [
        {
            'name': 'idx_supervision_porcentaje_fecha',
            'table': 'supervision_operativa_detalle',
            'columns': ['porcentaje', 'fecha_supervision'],
            'where': 'porcentaje IS NOT NULL AND fecha_supervision IS NOT NULL',
            'description': 'Primary performance index for KPI queries'
        },
        {
            'name': 'idx_supervision_sucursal_fecha',
            'table': 'supervision_operativa_detalle', 
            'columns': ['sucursal_clean', 'fecha_supervision'],
            'where': None,
            'description': 'Index for branch-specific queries'
        },
        {
            'name': 'idx_supervision_estado_grupo',
            'table': 'supervision_operativa_detalle',
            'columns': ['estado', 'grupo_operativo'],
            'where': None,
            'description': 'Index for state and group filtering'
        },
        {
            'name': 'idx_supervision_quarter',
            'table': 'supervision_operativa_detalle',
            'columns': ['(EXTRACT(QUARTER FROM fecha_supervision))'],
            'where': None,
            'description': 'Index for quarter-based filtering'
        },
        {
            'name': 'idx_supervision_geo',
            'table': 'supervision_operativa_detalle',
            'columns': ['(ll_to_earth(latitud, longitud))'],
            'where': 'latitud IS NOT NULL AND longitud IS NOT NULL',
            'description': 'Geospatial index for map queries',
            'type': 'GIST'
        },
        {
            'name': 'idx_supervision_complex_filter',
            'table': 'supervision_operativa_detalle',
            'columns': ['estado', 'grupo_operativo', 'area_evaluacion', 'fecha_supervision'],
            'where': 'porcentaje IS NOT NULL',
            'description': 'Composite index for complex filtering'
        }
    ]
    
    # Materialized views for performance
    MATERIALIZED_VIEWS = [
        {
            'name': 'mv_kpi_summary',
            'query': """
                SELECT 
                    EXTRACT(QUARTER FROM fecha_supervision) as quarter,
                    EXTRACT(YEAR FROM fecha_supervision) as year,
                    estado,
                    grupo_operativo,
                    COUNT(*) as total_supervisiones,
                    AVG(CAST(porcentaje AS NUMERIC)) as promedio,
                    COUNT(DISTINCT sucursal_clean) as total_sucursales,
                    MIN(CAST(porcentaje AS NUMERIC)) as minimo,
                    MAX(CAST(porcentaje AS NUMERIC)) as maximo,
                    STDDEV(CAST(porcentaje AS NUMERIC)) as desviacion_estandar
                FROM supervision_operativa_detalle
                WHERE porcentaje IS NOT NULL 
                  AND fecha_supervision IS NOT NULL
                GROUP BY quarter, year, estado, grupo_operativo
            """,
            'unique_index': ['quarter', 'year', 'estado', 'grupo_operativo'],
            'description': 'Pre-aggregated KPI data for fast queries'
        },
        {
            'name': 'mv_geo_summary',
            'query': """
                SELECT DISTINCT ON (sucursal_clean)
                    sucursal_clean,
                    estado,
                    municipio,
                    latitud,
                    longitud,
                    AVG(CAST(porcentaje AS NUMERIC)) OVER (PARTITION BY sucursal_clean) as promedio_porcentaje,
                    COUNT(*) OVER (PARTITION BY sucursal_clean) as total_supervisiones,
                    MAX(fecha_supervision) OVER (PARTITION BY sucursal_clean) as ultima_supervision
                FROM supervision_operativa_detalle
                WHERE latitud IS NOT NULL 
                  AND longitud IS NOT NULL 
                  AND porcentaje IS NOT NULL
                ORDER BY sucursal_clean, fecha_supervision DESC
            """,
            'unique_index': ['sucursal_clean'],
            'description': 'Geographic data with performance metrics'
        }
    ]
    
    def create_indexes(self) -> Dict[str, Any]:
        """Create all critical indexes"""
        results = {
            'created': [],
            'skipped': [],
            'errors': []
        }
        
        logger.info("Starting database index creation...")
        
        for index_config in self.CRITICAL_INDEXES:
            try:
                if self._index_exists(index_config['name']):
                    results['skipped'].append(index_config['name'])
                    logger.info(f"Index {index_config['name']} already exists")
                    continue
                
                success = self._create_index(index_config)
                if success:
                    results['created'].append(index_config['name'])
                    logger.info(f"Created index: {index_config['name']}")
                else:
                    results['errors'].append(index_config['name'])
                
            except Exception as e:
                logger.error(f"Error creating index {index_config['name']}: {e}")
                results['errors'].append(index_config['name'])
        
        logger.info(f"Index creation completed: {len(results['created'])} created, {len(results['skipped'])} skipped, {len(results['errors'])} errors")
        return results
    
    def _index_exists(self, index_name: str) -> bool:
        """Check if index exists"""
        query = """
            SELECT EXISTS (
                SELECT 1 FROM pg_indexes 
                WHERE indexname = %s
            );
        """
        result = execute_query(query, [index_name])
        return result[0]['exists'] if result else False
    
    def _create_index(self, index_config: Dict[str, Any]) -> bool:
        """Create a single index"""
        try:
            # Build CREATE INDEX statement
            index_type = index_config.get('type', 'BTREE')
            columns_str = ', '.join(index_config['columns'])
            
            sql = f"CREATE INDEX CONCURRENTLY {index_config['name']} ON {index_config['table']}"
            
            if index_type != 'BTREE':
                sql += f" USING {index_type}"
            
            sql += f" ({columns_str})"
            
            if index_config.get('where'):
                sql += f" WHERE {index_config['where']}"
            
            sql += ";"
            
            logger.debug(f"Creating index with SQL: {sql}")
            execute_query(sql)
            return True
            
        except Exception as e:
            logger.error(f"Failed to create index {index_config['name']}: {e}")
            return False
    
    def create_materialized_views(self) -> Dict[str, Any]:
        """Create materialized views for performance"""
        results = {
            'created': [],
            'skipped': [],
            'errors': []
        }
        
        logger.info("Starting materialized view creation...")
        
        for view_config in self.MATERIALIZED_VIEWS:
            try:
                if self._materialized_view_exists(view_config['name']):
                    results['skipped'].append(view_config['name'])
                    logger.info(f"Materialized view {view_config['name']} already exists")
                    continue
                
                success = self._create_materialized_view(view_config)
                if success:
                    results['created'].append(view_config['name'])
                    logger.info(f"Created materialized view: {view_config['name']}")
                else:
                    results['errors'].append(view_config['name'])
                
            except Exception as e:
                logger.error(f"Error creating materialized view {view_config['name']}: {e}")
                results['errors'].append(view_config['name'])
        
        return results
    
    def _materialized_view_exists(self, view_name: str) -> bool:
        """Check if materialized view exists"""
        query = """
            SELECT EXISTS (
                SELECT 1 FROM pg_matviews 
                WHERE matviewname = %s
            );
        """
        result = execute_query(query, [view_name])
        return result[0]['exists'] if result else False
    
    def _create_materialized_view(self, view_config: Dict[str, Any]) -> bool:
        """Create a materialized view"""
        try:
            # Create materialized view
            sql = f"CREATE MATERIALIZED VIEW {view_config['name']} AS {view_config['query']};"
            execute_query(sql)
            
            # Create unique index if specified
            if view_config.get('unique_index'):
                columns = ', '.join(view_config['unique_index'])
                index_sql = f"CREATE UNIQUE INDEX ON {view_config['name']} ({columns});"
                execute_query(index_sql)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to create materialized view {view_config['name']}: {e}")
            return False
    
    def refresh_materialized_views(self) -> Dict[str, Any]:
        """Refresh all materialized views"""
        results = {
            'refreshed': [],
            'errors': []
        }
        
        logger.info("Refreshing materialized views...")
        
        for view_config in self.MATERIALIZED_VIEWS:
            try:
                if self._materialized_view_exists(view_config['name']):
                    sql = f"REFRESH MATERIALIZED VIEW CONCURRENTLY {view_config['name']};"
                    execute_query(sql)
                    results['refreshed'].append(view_config['name'])
                    logger.info(f"Refreshed materialized view: {view_config['name']}")
            except Exception as e:
                logger.error(f"Error refreshing materialized view {view_config['name']}: {e}")
                results['errors'].append(view_config['name'])
        
        return results
    
    def analyze_table_stats(self, table_name: str = 'supervision_operativa_detalle') -> Dict[str, Any]:
        """Analyze table statistics for optimization"""
        try:
            # Get table size and statistics
            stats_query = """
                SELECT 
                    schemaname,
                    tablename,
                    attname,
                    n_distinct,
                    correlation
                FROM pg_stats 
                WHERE tablename = %s
                ORDER BY attname;
            """
            
            size_query = """
                SELECT 
                    pg_size_pretty(pg_total_relation_size(%s)) as total_size,
                    pg_size_pretty(pg_relation_size(%s)) as table_size,
                    (SELECT count(*) FROM {}) as row_count
            """.format(table_name)
            
            stats = execute_query(stats_query, [table_name])
            size_info = execute_query(size_query, [table_name, table_name])
            
            return {
                'table_name': table_name,
                'size_info': size_info[0] if size_info else {},
                'column_stats': stats,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error analyzing table stats: {e}")
            return {}
    
    def vacuum_analyze(self, table_name: str = 'supervision_operativa_detalle'):
        """Run VACUUM ANALYZE for better query planning"""
        try:
            sql = f"VACUUM ANALYZE {table_name};"
            execute_query(sql)
            logger.info(f"VACUUM ANALYZE completed for {table_name}")
        except Exception as e:
            logger.error(f"VACUUM ANALYZE error: {e}")

class OptimizedQueries:
    """Optimized database query implementations"""
    
    @cached_query(ttl=300, cache_type='kpis')
    def get_optimized_kpis(self, quarter='ALL', year=2025, estado=None, grupo=None):
        """Optimized KPI calculation using materialized views when possible"""
        
        # Try to use materialized view first
        if self._can_use_materialized_view(quarter, year, estado, grupo):
            return self._get_kpis_from_materialized_view(quarter, year, estado, grupo)
        
        # Fallback to optimized direct query
        return self._get_kpis_direct_query(quarter, year, estado, grupo)
    
    def _can_use_materialized_view(self, quarter, year, estado, grupo) -> bool:
        """Check if we can use materialized view for this query"""
        # For now, use materialized view for simple aggregations
        return quarter != 'ALL' and year and not (estado and grupo)
    
    def _get_kpis_from_materialized_view(self, quarter, year, estado, grupo):
        """Get KPIs from materialized view"""
        base_query = """
            SELECT 
                ROUND(AVG(promedio), 2) as promedio,
                SUM(total_supervisiones) as supervisiones,
                SUM(total_sucursales) as sucursales,
                COUNT(DISTINCT estado) as estados,
                ROUND(MIN(minimo), 2) as minimo,
                ROUND(MAX(maximo), 2) as maximo
            FROM mv_kpi_summary
            WHERE 1=1
        """
        
        params = []
        conditions = []
        
        if quarter != 'ALL':
            conditions.append("quarter = %s")
            params.append(int(quarter[1]))
        
        if year:
            conditions.append("year = %s")
            params.append(year)
            
        if estado:
            conditions.append("estado = %s")
            params.append(estado)
            
        if grupo:
            conditions.append("grupo_operativo = %s")
            params.append(grupo)
        
        if conditions:
            base_query += " AND " + " AND ".join(conditions)
        
        return execute_query(base_query, params)
    
    def _get_kpis_direct_query(self, quarter, year, estado, grupo):
        """Get KPIs with optimized direct query"""
        
        # Use CTE for better performance
        base_query = """
            WITH filtered_data AS (
                SELECT 
                    CAST(porcentaje AS NUMERIC) as porcentaje_num,
                    submission_id,
                    sucursal_clean,
                    estado,
                    fecha_supervision
                FROM supervision_operativa_detalle 
                WHERE porcentaje IS NOT NULL 
                  AND fecha_supervision IS NOT NULL
        """
        
        params = []
        conditions = []
        
        if quarter != 'ALL':
            conditions.append("EXTRACT(QUARTER FROM fecha_supervision) = %s")
            params.append(int(quarter[1]))
        
        if year:
            conditions.append("EXTRACT(YEAR FROM fecha_supervision) = %s")
            params.append(year)
            
        if estado:
            conditions.append("estado = %s")
            params.append(estado)
            
        if grupo:
            conditions.append("grupo_operativo = %s")
            params.append(grupo)
        
        if conditions:
            base_query += " AND " + " AND ".join(conditions)
        
        # Optimized aggregation query
        final_query = base_query + """
            )
            SELECT 
                ROUND(AVG(porcentaje_num), 2) as promedio,
                COUNT(DISTINCT submission_id) as supervisiones,
                COUNT(DISTINCT sucursal_clean) as sucursales,
                COUNT(DISTINCT estado) as estados,
                ROUND(MIN(porcentaje_num), 2) as minimo,
                ROUND(MAX(porcentaje_num), 2) as maximo,
                ROUND(STDDEV(porcentaje_num), 2) as desviacion_estandar
            FROM filtered_data;
        """
        
        return execute_query(final_query, params)
    
    @cached_query(ttl=600, cache_type='geo_data')
    def get_optimized_coordinates(self, quarter='ALL', year=2025, estado=None, limit=20):
        """Optimized geospatial query using materialized view when possible"""
        
        # Try materialized view first for simple queries
        if not estado and quarter == 'ALL':
            query = """
                SELECT 
                    sucursal_clean,
                    estado,
                    municipio,
                    latitud,
                    longitud,
                    ROUND(promedio_porcentaje, 2) as promedio_porcentaje,
                    total_supervisiones
                FROM mv_geo_summary
                ORDER BY promedio_porcentaje DESC
                LIMIT %s;
            """
            return execute_query(query, [limit])
        
        # Use optimized direct query for complex filters
        query = """
            SELECT DISTINCT ON (s.sucursal_clean)
                s.sucursal_clean,
                s.estado,
                s.municipio,
                s.latitud,
                s.longitud,
                ROUND(AVG(CAST(s.porcentaje AS NUMERIC)), 2) as promedio_porcentaje,
                COUNT(*) as total_supervisiones
            FROM supervision_operativa_detalle s
            WHERE s.latitud IS NOT NULL 
              AND s.longitud IS NOT NULL 
              AND s.porcentaje IS NOT NULL
        """
        
        params = []
        
        if quarter != 'ALL':
            query += " AND EXTRACT(QUARTER FROM s.fecha_supervision) = %s"
            params.append(int(quarter[1]))
        
        if year:
            query += " AND EXTRACT(YEAR FROM s.fecha_supervision) = %s"
            params.append(year)
            
        if estado:
            query += " AND s.estado = %s"
            params.append(estado)
        
        query += """
            GROUP BY s.sucursal_clean, s.estado, s.municipio, s.latitud, s.longitud
            ORDER BY s.sucursal_clean, promedio_porcentaje DESC
            LIMIT %s;
        """
        params.append(limit)
        
        return execute_query(query, params)
    
    @cached_query(ttl=300, cache_type='analytics')
    def get_performance_trends(self, days=30, estado=None, grupo=None):
        """Get performance trends with optimized query"""
        query = """
            SELECT 
                DATE(fecha_supervision) as fecha,
                ROUND(AVG(CAST(porcentaje AS NUMERIC)), 2) as promedio_diario,
                COUNT(*) as supervisiones_diarias,
                COUNT(DISTINCT sucursal_clean) as sucursales_evaluadas
            FROM supervision_operativa_detalle
            WHERE fecha_supervision >= CURRENT_DATE - INTERVAL '%s days'
              AND porcentaje IS NOT NULL
        """
        
        params = [days]
        
        if estado:
            query += " AND estado = %s"
            params.append(estado)
            
        if grupo:
            query += " AND grupo_operativo = %s"
            params.append(grupo)
        
        query += """
            GROUP BY DATE(fecha_supervision)
            ORDER BY fecha DESC;
        """
        
        return execute_query(query, params)

# Background tasks for database maintenance
class DatabaseMaintenanceTasks:
    """Background tasks for database optimization"""
    
    def __init__(self):
        self.optimizer = DatabaseOptimizer()
        self.optimized_queries = OptimizedQueries()
    
    def daily_maintenance(self):
        """Daily database maintenance tasks"""
        logger.info("Starting daily database maintenance...")
        
        try:
            # Refresh materialized views
            self.optimizer.refresh_materialized_views()
            
            # Update statistics
            self.optimizer.vacuum_analyze()
            
            # Clear old cache entries
            cache_manager.clear_pattern("query:*")
            
            logger.info("Daily maintenance completed successfully")
            
        except Exception as e:
            logger.error(f"Daily maintenance error: {e}")
    
    def weekly_optimization(self):
        """Weekly optimization tasks"""
        logger.info("Starting weekly database optimization...")
        
        try:
            # Analyze table statistics
            stats = self.optimizer.analyze_table_stats()
            logger.info(f"Table statistics: {stats}")
            
            # Check for missing indexes
            # (Implementation would analyze query patterns and suggest new indexes)
            
            logger.info("Weekly optimization completed")
            
        except Exception as e:
            logger.error(f"Weekly optimization error: {e}")

# Global instances
db_optimizer = DatabaseOptimizer()
optimized_queries = OptimizedQueries()
maintenance_tasks = DatabaseMaintenanceTasks()