"""
Analytics API endpoints for KPIs, performance metrics, and business intelligence.
"""

import logging
from datetime import datetime
from flask import Blueprint, request, jsonify
from marshmallow import Schema, fields

from auth.security import require_auth, optional_auth, validate_input, APIQuerySchema
from cache.cache_manager import cached_api_response
from database.optimization import optimized_queries
from middleware.security_middleware import rate_limit_by_user

logger = logging.getLogger(__name__)
analytics_bp = Blueprint('analytics', __name__, url_prefix='/api/v1/analytics')

class TrendQuerySchema(APIQuerySchema):
    """Extended schema for trend queries"""
    days = fields.Int(validate=lambda x: 1 <= x <= 365, missing=30)

class RankingQuerySchema(APIQuerySchema):
    """Schema for ranking queries"""
    ranking_type = fields.Str(
        validate=lambda x: x in ['sucursales', 'estados', 'grupos'],
        missing='sucursales'
    )
    order = fields.Str(
        validate=lambda x: x in ['asc', 'desc'],
        missing='desc'
    )

@analytics_bp.route('/kpis', methods=['GET'])
@optional_auth
@rate_limit_by_user("30 per minute")
@validate_input(APIQuerySchema)
@cached_api_response(ttl=300, cache_type='kpis')
def get_kpis():
    """
    Get Key Performance Indicators with optional filtering.
    
    Query parameters:
    - quarter: Q1, Q2, Q3, Q4, or ALL (default: ALL)
    - year: Year filter (default: 2025)
    - estado: State filter (optional)
    - grupo: Operational group filter (optional)
    
    Returns aggregated KPI data including averages, counts, and trends.
    """
    try:
        params = request.validated_data
        
        # Get KPI data using direct query (fallback if optimized fails)
        try:
            kpi_data = optimized_queries.get_optimized_kpis(
                quarter=params['quarter'],
                year=params['year'],
                estado=params.get('estado'),
                grupo=params.get('grupo')
            )
        except Exception as e:
            logger.warning(f"Optimized query failed, using direct query: {e}")
            # Direct query fallback
            from database.connection_v3 import execute_query
            
            base_query = """
                SELECT 
                    ROUND(AVG(CAST(porcentaje AS NUMERIC)), 2) as promedio,
                    COUNT(DISTINCT submission_id) as supervisiones,
                    COUNT(DISTINCT sucursal_clean) as sucursales,
                    COUNT(DISTINCT estado) as estados,
                    ROUND(MIN(CAST(porcentaje AS NUMERIC)), 2) as minimo,
                    ROUND(MAX(CAST(porcentaje AS NUMERIC)), 2) as maximo,
                    ROUND(STDDEV(CAST(porcentaje AS NUMERIC)), 2) as desviacion_estandar
                FROM supervision_operativa_detalle 
                WHERE porcentaje IS NOT NULL 
                  AND fecha_supervision IS NOT NULL
            """
            
            query_params = []
            conditions = []
            
            if params['quarter'] != 'ALL':
                conditions.append("EXTRACT(QUARTER FROM fecha_supervision) = %s")
                query_params.append(int(params['quarter'][1]))
            
            if params['year']:
                conditions.append("EXTRACT(YEAR FROM fecha_supervision) = %s")
                query_params.append(params['year'])
                
            if params.get('estado'):
                conditions.append("estado = %s")
                query_params.append(params['estado'])
                
            if params.get('grupo'):
                conditions.append("grupo_operativo = %s")
                query_params.append(params['grupo'])
            
            if conditions:
                base_query += " AND " + " AND ".join(conditions)
            
            kpi_data = execute_query(base_query, query_params)
        
        if not kpi_data:
            return jsonify({
                'success': True,
                'data': None,
                'message': 'No data found for the specified filters'
            })
        
        # Handle different response types from execute_query
        if isinstance(kpi_data, list) and len(kpi_data) > 0:
            result = kpi_data[0]
        elif isinstance(kpi_data, dict):
            result = kpi_data
        else:
            # If it's an unexpected type, return empty data
            return jsonify({
                'success': True,
                'data': {
                    'promedio_general': None,
                    'total_supervisiones': None,
                    'total_sucursales': None,
                    'total_estados': 0,
                    'valor_minimo': None,
                    'valor_maximo': None,
                    'desviacion_estandar': None,
                    'meta_objetivo': 84.54,
                    'cumplimiento_meta': 0,
                    'tendencia': 'sin_datos',
                    'filtros_aplicados': {
                        'quarter': params['quarter'],
                        'year': params['year'],
                        'estado': params.get('estado'),
                        'grupo': params.get('grupo')
                    }
                },
                'message': 'Data format not recognized'
            })
        
        # Calculate additional metrics
        meta_objetivo = 84.54  # Target percentage
        promedio = result.get('promedio', 0) or 0
        cumplimiento_meta = (promedio / meta_objetivo * 100) if promedio else 0
        
        # Determine trend (this would normally compare with previous period)
        tendencia = "estable"  # Placeholder
        
        response_data = {
            'promedio_general': promedio,
            'total_supervisiones': result.get('supervisiones', 0) or 0,
            'total_sucursales': result.get('sucursales', 0) or 0,
            'total_estados': result.get('estados', 0) or 0,
            'valor_minimo': result.get('minimo'),
            'valor_maximo': result.get('maximo'),
            'desviacion_estandar': result.get('desviacion_estandar'),
            'meta_objetivo': meta_objetivo,
            'cumplimiento_meta': round(cumplimiento_meta, 2),
            'tendencia': tendencia,
            'filtros_aplicados': {
                'quarter': params['quarter'],
                'year': params['year'],
                'estado': params.get('estado'),
                'grupo': params.get('grupo')
            }
        }
        
        return jsonify({
            'success': True,
            'data': response_data
        })
        
    except Exception as e:
        logger.error(f"KPI endpoint error: {e}")
        return jsonify({
            'error': 'Failed to fetch KPI data',
            'error_code': 'KPI_ERROR'
        }), 500

@analytics_bp.route('/performance/states', methods=['GET'])
@optional_auth
@rate_limit_by_user("20 per minute")
@validate_input(APIQuerySchema)
@cached_api_response(ttl=600, cache_type='analytics')
def get_states_performance():
    """
    Get performance metrics grouped by states.
    
    Returns performance data for each state including averages and rankings.
    """
    try:
        params = request.validated_data
        
        # Query for state performance
        query = """
            SELECT 
                estado,
                ROUND(AVG(CAST(porcentaje AS NUMERIC)), 2) as promedio,
                COUNT(*) as total_supervisiones,
                COUNT(DISTINCT sucursal_clean) as total_sucursales,
                ROUND(MIN(CAST(porcentaje AS NUMERIC)), 2) as minimo,
                ROUND(MAX(CAST(porcentaje AS NUMERIC)), 2) as maximo
            FROM supervision_operativa_detalle
            WHERE porcentaje IS NOT NULL AND fecha_supervision IS NOT NULL
        """
        
        query_params = []
        
        if params['quarter'] != 'ALL':
            query += " AND EXTRACT(QUARTER FROM fecha_supervision) = %s"
            query_params.append(int(params['quarter'][1]))
        
        if params['year']:
            query += " AND EXTRACT(YEAR FROM fecha_supervision) = %s"
            query_params.append(params['year'])
        
        if params.get('grupo'):
            query += " AND grupo_operativo = %s"
            query_params.append(params['grupo'])
        
        query += """
            GROUP BY estado
            ORDER BY promedio DESC
            LIMIT %s OFFSET %s;
        """
        query_params.extend([params['limit'], params['offset']])
        
        from database.connection_v3 import execute_query
        results = execute_query(query, query_params)
        
        return jsonify({
            'success': True,
            'data': results,
            'pagination': {
                'limit': params['limit'],
                'offset': params['offset'],
                'total': len(results)
            }
        })
        
    except Exception as e:
        logger.error(f"States performance endpoint error: {e}")
        return jsonify({
            'error': 'Failed to fetch states performance data',
            'error_code': 'STATES_PERFORMANCE_ERROR'
        }), 500

@analytics_bp.route('/performance/branches', methods=['GET'])
@optional_auth
@rate_limit_by_user("20 per minute")
@validate_input(APIQuerySchema)
@cached_api_response(ttl=300, cache_type='analytics')
def get_branches_performance():
    """
    Get performance metrics grouped by branches (sucursales).
    """
    try:
        params = request.validated_data
        
        query = """
            SELECT 
                sucursal_clean,
                estado,
                grupo_operativo,
                ROUND(AVG(CAST(porcentaje AS NUMERIC)), 2) as promedio,
                COUNT(*) as total_supervisiones,
                ROUND(MIN(CAST(porcentaje AS NUMERIC)), 2) as minimo,
                ROUND(MAX(CAST(porcentaje AS NUMERIC)), 2) as maximo,
                MAX(fecha_supervision) as ultima_supervision
            FROM supervision_operativa_detalle
            WHERE porcentaje IS NOT NULL AND fecha_supervision IS NOT NULL
        """
        
        query_params = []
        
        if params['quarter'] != 'ALL':
            query += " AND EXTRACT(QUARTER FROM fecha_supervision) = %s"
            query_params.append(int(params['quarter'][1]))
        
        if params['year']:
            query += " AND EXTRACT(YEAR FROM fecha_supervision) = %s"
            query_params.append(params['year'])
        
        if params.get('estado'):
            query += " AND estado = %s"
            query_params.append(params['estado'])
            
        if params.get('grupo'):
            query += " AND grupo_operativo = %s"
            query_params.append(params['grupo'])
        
        query += """
            GROUP BY sucursal_clean, estado, grupo_operativo
            ORDER BY promedio DESC
            LIMIT %s OFFSET %s;
        """
        query_params.extend([params['limit'], params['offset']])
        
        from database.connection_v3 import execute_query
        results = execute_query(query, query_params)
        
        return jsonify({
            'success': True,
            'data': results,
            'pagination': {
                'limit': params['limit'],
                'offset': params['offset']
            }
        })
        
    except Exception as e:
        logger.error(f"Branches performance endpoint error: {e}")
        return jsonify({
            'error': 'Failed to fetch branches performance data',
            'error_code': 'BRANCHES_PERFORMANCE_ERROR'
        }), 500

@analytics_bp.route('/performance/groups', methods=['GET'])
@optional_auth
@rate_limit_by_user("20 per minute") 
@validate_input(APIQuerySchema)
@cached_api_response(ttl=600, cache_type='analytics')
def get_groups_performance():
    """
    Get performance metrics grouped by operational groups.
    """
    try:
        params = request.validated_data
        
        query = """
            SELECT 
                grupo_operativo,
                ROUND(AVG(CAST(porcentaje AS NUMERIC)), 2) as promedio,
                COUNT(*) as total_supervisiones,
                COUNT(DISTINCT sucursal_clean) as total_sucursales,
                COUNT(DISTINCT estado) as estados_presentes,
                ROUND(MIN(CAST(porcentaje AS NUMERIC)), 2) as minimo,
                ROUND(MAX(CAST(porcentaje AS NUMERIC)), 2) as maximo
            FROM supervision_operativa_detalle
            WHERE porcentaje IS NOT NULL 
              AND fecha_supervision IS NOT NULL
              AND grupo_operativo IS NOT NULL
        """
        
        query_params = []
        
        if params['quarter'] != 'ALL':
            query += " AND EXTRACT(QUARTER FROM fecha_supervision) = %s"
            query_params.append(int(params['quarter'][1]))
        
        if params['year']:
            query += " AND EXTRACT(YEAR FROM fecha_supervision) = %s"
            query_params.append(params['year'])
        
        if params.get('estado'):
            query += " AND estado = %s"
            query_params.append(params['estado'])
        
        query += """
            GROUP BY grupo_operativo
            ORDER BY promedio DESC
            LIMIT %s OFFSET %s;
        """
        query_params.extend([params['limit'], params['offset']])
        
        from database.connection_v3 import execute_query
        results = execute_query(query, query_params)
        
        return jsonify({
            'success': True,
            'data': results,
            'pagination': {
                'limit': params['limit'],
                'offset': params['offset']
            }
        })
        
    except Exception as e:
        logger.error(f"Groups performance endpoint error: {e}")
        return jsonify({
            'error': 'Failed to fetch groups performance data',
            'error_code': 'GROUPS_PERFORMANCE_ERROR'
        }), 500

@analytics_bp.route('/trends', methods=['GET'])
@optional_auth
@rate_limit_by_user("15 per minute")
@validate_input(TrendQuerySchema)
@cached_api_response(ttl=900, cache_type='analytics')
def get_performance_trends():
    """
    Get performance trends over time.
    
    Query parameters:
    - days: Number of days to look back (default: 30, max: 365)
    - estado: State filter (optional)
    - grupo: Group filter (optional)
    """
    try:
        params = request.validated_data
        
        trends = optimized_queries.get_performance_trends(
            days=params['days'],
            estado=params.get('estado'),
            grupo=params.get('grupo')
        )
        
        return jsonify({
            'success': True,
            'data': trends,
            'metadata': {
                'days_analyzed': params['days'],
                'filters': {
                    'estado': params.get('estado'),
                    'grupo': params.get('grupo')
                }
            }
        })
        
    except Exception as e:
        logger.error(f"Trends endpoint error: {e}")
        return jsonify({
            'error': 'Failed to fetch trend data',
            'error_code': 'TRENDS_ERROR'
        }), 500

@analytics_bp.route('/ranking', methods=['GET'])
@optional_auth
@rate_limit_by_user("15 per minute")
@validate_input(RankingQuerySchema)
@cached_api_response(ttl=600, cache_type='analytics')
def get_ranking():
    """
    Get performance rankings for different entity types.
    
    Query parameters:
    - ranking_type: 'sucursales', 'estados', or 'grupos' (default: sucursales)
    - order: 'asc' or 'desc' (default: desc)
    - limit: Number of results (default: 20, max: 1000)
    """
    try:
        params = request.validated_data
        ranking_type = params['ranking_type']
        order = params['order']
        
        # Build query based on ranking type
        if ranking_type == 'sucursales':
            entity_column = 'sucursal_clean'
            additional_columns = 'estado, grupo_operativo,'
        elif ranking_type == 'estados':
            entity_column = 'estado'
            additional_columns = ''
        else:  # grupos
            entity_column = 'grupo_operativo'
            additional_columns = ''
        
        query = f"""
            SELECT 
                {entity_column} as entidad,
                {additional_columns}
                ROUND(AVG(CAST(porcentaje AS NUMERIC)), 2) as promedio,
                COUNT(*) as total_supervisiones,
                COUNT(DISTINCT sucursal_clean) as sucursales_incluidas,
                ROUND(MIN(CAST(porcentaje AS NUMERIC)), 2) as minimo,
                ROUND(MAX(CAST(porcentaje AS NUMERIC)), 2) as maximo
            FROM supervision_operativa_detalle
            WHERE porcentaje IS NOT NULL 
              AND fecha_supervision IS NOT NULL
              AND {entity_column} IS NOT NULL
        """
        
        query_params = []
        
        if params['quarter'] != 'ALL':
            query += " AND EXTRACT(QUARTER FROM fecha_supervision) = %s"
            query_params.append(int(params['quarter'][1]))
        
        if params['year']:
            query += " AND EXTRACT(YEAR FROM fecha_supervision) = %s"
            query_params.append(params['year'])
        
        group_by_columns = entity_column
        if additional_columns:
            group_by_columns += ', ' + additional_columns.rstrip(',')
        
        order_direction = 'DESC' if order == 'desc' else 'ASC'
        
        query += f"""
            GROUP BY {group_by_columns}
            ORDER BY promedio {order_direction}
            LIMIT %s OFFSET %s;
        """
        query_params.extend([params['limit'], params['offset']])
        
        from database.connection_v3 import execute_query
        results = execute_query(query, query_params)
        
        return jsonify({
            'success': True,
            'data': results,
            'metadata': {
                'ranking_type': ranking_type,
                'order': order,
                'pagination': {
                    'limit': params['limit'],
                    'offset': params['offset']
                }
            }
        })
        
    except Exception as e:
        logger.error(f"Ranking endpoint error: {e}")
        return jsonify({
            'error': 'Failed to fetch ranking data',
            'error_code': 'RANKING_ERROR'
        }), 500

@analytics_bp.route('/summary', methods=['GET'])
@optional_auth
@rate_limit_by_user("30 per minute")
@validate_input(APIQuerySchema)
@cached_api_response(ttl=180, cache_type='analytics')
def get_analytics_summary():
    """
    Get comprehensive analytics summary combining multiple metrics.
    """
    try:
        params = request.validated_data
        
        # Get KPIs
        kpi_data = optimized_queries.get_optimized_kpis(
            quarter=params['quarter'],
            year=params['year'],
            estado=params.get('estado'),
            grupo=params.get('grupo')
        )
        
        # Get recent trends (last 7 days)
        trend_data = optimized_queries.get_performance_trends(
            days=7,
            estado=params.get('estado'),
            grupo=params.get('grupo')
        )
        
        summary = {
            'kpis': kpi_data[0] if kpi_data else None,
            'recent_trends': trend_data[:7] if trend_data else [],
            'filters_applied': {
                'quarter': params['quarter'],
                'year': params['year'],
                'estado': params.get('estado'),
                'grupo': params.get('grupo')
            },
            'generated_at': str(datetime.now())
        }
        
        return jsonify({
            'success': True,
            'data': summary
        })
        
    except Exception as e:
        logger.error(f"Analytics summary endpoint error: {e}")
        return jsonify({
            'error': 'Failed to fetch analytics summary',
            'error_code': 'SUMMARY_ERROR'
        }), 500

@analytics_bp.route('/metadata/estados', methods=['GET'])
@optional_auth
@rate_limit_by_user("60 per minute")
@cached_api_response(ttl=3600, cache_type='metadata')
def get_estados_metadata():
    """
    Get list of all available states for filtering.
    """
    try:
        query = """
            SELECT DISTINCT estado
            FROM supervision_operativa_detalle
            WHERE estado IS NOT NULL
              AND estado != ''
            ORDER BY estado;
        """
        
        from database.connection_v3 import execute_query
        results = execute_query(query)
        
        estados = [row['estado'] for row in results]
        
        return jsonify({
            'success': True,
            'data': estados,
            'metadata': {
                'total_estados': len(estados),
                'cache_ttl': 3600
            }
        })
        
    except Exception as e:
        logger.error(f"Estados metadata endpoint error: {e}")
        return jsonify({
            'error': 'Failed to fetch estados metadata',
            'error_code': 'ESTADOS_METADATA_ERROR'
        }), 500

@analytics_bp.route('/metadata/grupos', methods=['GET'])
@optional_auth
@rate_limit_by_user("60 per minute")
@cached_api_response(ttl=3600, cache_type='metadata')
def get_grupos_metadata():
    """
    Get list of all available operational groups for filtering.
    """
    try:
        query = """
            SELECT DISTINCT grupo_operativo
            FROM supervision_operativa_detalle
            WHERE grupo_operativo IS NOT NULL
              AND grupo_operativo != ''
            ORDER BY grupo_operativo;
        """
        
        from database.connection_v3 import execute_query
        results = execute_query(query)
        
        grupos = [row['grupo_operativo'] for row in results]
        
        return jsonify({
            'success': True,
            'data': grupos,
            'metadata': {
                'total_grupos': len(grupos),
                'cache_ttl': 3600
            }
        })
        
    except Exception as e:
        logger.error(f"Grupos metadata endpoint error: {e}")
        return jsonify({
            'error': 'Failed to fetch grupos metadata',
            'error_code': 'GRUPOS_METADATA_ERROR'
        }), 500

@analytics_bp.route('/metadata/areas', methods=['GET'])
@optional_auth
@rate_limit_by_user("60 per minute")
@cached_api_response(ttl=3600, cache_type='metadata')
def get_areas_metadata():
    """
    Get list of all available evaluation areas (29 indicators).
    """
    try:
        query = """
            SELECT DISTINCT area_evaluacion, COUNT(*) as total_evaluaciones
            FROM supervision_operativa_detalle
            WHERE area_evaluacion IS NOT NULL
              AND area_evaluacion != ''
            GROUP BY area_evaluacion
            ORDER BY area_evaluacion;
        """
        
        from database.connection_v3 import execute_query
        results = execute_query(query)
        
        return jsonify({
            'success': True,
            'data': results,
            'metadata': {
                'total_areas': len(results),
                'cache_ttl': 3600
            }
        })
        
    except Exception as e:
        logger.error(f"Areas metadata endpoint error: {e}")
        return jsonify({
            'error': 'Failed to fetch areas metadata',
            'error_code': 'AREAS_METADATA_ERROR'
        }), 500