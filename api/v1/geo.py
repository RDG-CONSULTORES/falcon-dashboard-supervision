"""
Geospatial API endpoints for maps, coordinates, and location-based analytics.
"""

import logging
from flask import Blueprint, request, jsonify
from marshmallow import Schema, fields

from auth.security import optional_auth, validate_input, APIQuerySchema
from cache.cache_manager import cached_api_response
from database.optimization import optimized_queries
from middleware.security_middleware import rate_limit_by_user

logger = logging.getLogger(__name__)
geo_bp = Blueprint('geo', __name__, url_prefix='/api/v1/geo')

class GeoQuerySchema(APIQuerySchema):
    """Extended schema for geospatial queries"""
    include_coords = fields.Bool(missing=True)
    map_type = fields.Str(
        validate=lambda x: x in ['choropleth', 'markers', 'heatmap'],
        missing='markers'
    )

@geo_bp.route('/coordinates', methods=['GET'])
@optional_auth
@rate_limit_by_user("15 per minute")
@validate_input(GeoQuerySchema)
@cached_api_response(ttl=600, cache_type='geo_data')
def get_coordinates():
    """
    Get branch coordinates with performance data for mapping.
    
    Query parameters:
    - quarter: Q1, Q2, Q3, Q4, or ALL (default: ALL)
    - year: Year filter (default: 2025)
    - estado: State filter (optional)
    - limit: Number of results (default: 20, max: 1000)
    - include_coords: Include latitude/longitude (default: true)
    - map_type: Type of map visualization (default: markers)
    
    Returns coordinate data optimized for map visualization.
    """
    try:
        params = request.validated_data
        
        # Get coordinate data using optimized queries
        coord_data = optimized_queries.get_optimized_coordinates(
            quarter=params['quarter'],
            year=params['year'],
            estado=params.get('estado'),
            limit=params['limit']
        )
        
        if not coord_data:
            return jsonify({
                'success': True,
                'data': [],
                'message': 'No coordinate data found for the specified filters'
            })
        
        # Process data for map visualization
        processed_data = []
        for item in coord_data:
            processed_item = {
                'sucursal': item['sucursal_clean'],
                'estado': item['estado'],
                'municipio': item['municipio'],
                'promedio_porcentaje': item['promedio_porcentaje'],
                'total_supervisiones': item.get('total_supervisiones', 1)
            }
            
            # Add coordinates if requested
            if params['include_coords']:
                processed_item.update({
                    'latitud': float(item['latitud']) if item['latitud'] else None,
                    'longitud': float(item['longitud']) if item['longitud'] else None
                })
            
            # Add performance category for visualization
            score = item['promedio_porcentaje'] or 0
            if score >= 95:
                category = 'excelente'
                color = '#0d47a1'
            elif score >= 85:
                category = 'muy_bueno'
                color = '#1976d2'
            elif score >= 75:
                category = 'bueno'
                color = '#42a5f5'
            else:
                category = 'regular'
                color = '#90caf9'
            
            processed_item.update({
                'categoria_performance': category,
                'color_mapa': color
            })
            
            processed_data.append(processed_item)
        
        return jsonify({
            'success': True,
            'data': processed_data,
            'metadata': {
                'total_points': len(processed_data),
                'map_type': params['map_type'],
                'filters_applied': {
                    'quarter': params['quarter'],
                    'year': params['year'],
                    'estado': params.get('estado')
                }
            }
        })
        
    except Exception as e:
        logger.error(f"Coordinates endpoint error: {e}")
        return jsonify({
            'error': 'Failed to fetch coordinate data',
            'error_code': 'COORDINATES_ERROR'
        }), 500

@geo_bp.route('/states', methods=['GET'])
@optional_auth
@rate_limit_by_user("20 per minute")
@validate_input(APIQuerySchema)
@cached_api_response(ttl=900, cache_type='geo_data')
def get_states_geo_data():
    """
    Get state-level geographic performance data for choropleth maps.
    
    Returns aggregated performance data by state for map visualization.
    """
    try:
        params = request.validated_data
        
        query = """
            SELECT 
                estado,
                ROUND(AVG(CAST(porcentaje AS NUMERIC)), 2) as promedio,
                COUNT(*) as total_supervisiones,
                COUNT(DISTINCT sucursal_clean) as total_sucursales,
                ROUND(MIN(CAST(porcentaje AS NUMERIC)), 2) as minimo,
                ROUND(MAX(CAST(porcentaje AS NUMERIC)), 2) as maximo,
                ROUND(STDDEV(CAST(porcentaje AS NUMERIC)), 2) as desviacion
            FROM supervision_operativa_detalle
            WHERE porcentaje IS NOT NULL 
              AND fecha_supervision IS NOT NULL
              AND estado IS NOT NULL
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
            ORDER BY promedio DESC;
        """
        
        from database.connection_v3 import execute_query
        results = execute_query(query, query_params)
        
        # Process for choropleth visualization
        processed_data = []
        for item in results:
            score = item['promedio'] or 0
            
            # Determine intensity for choropleth coloring
            if score >= 95:
                intensity = 1.0
                category = 'excelente'
            elif score >= 85:
                intensity = 0.75
                category = 'muy_bueno'
            elif score >= 75:
                intensity = 0.5
                category = 'bueno'
            elif score >= 70:
                intensity = 0.25
                category = 'regular'
            else:
                intensity = 0.1
                category = 'bajo'
            
            processed_data.append({
                'estado': item['estado'],
                'promedio': item['promedio'],
                'total_supervisiones': item['total_supervisiones'],
                'total_sucursales': item['total_sucursales'],
                'minimo': item['minimo'],
                'maximo': item['maximo'],
                'desviacion': item['desviacion'],
                'intensidad_mapa': intensity,
                'categoria_performance': category
            })
        
        return jsonify({
            'success': True,
            'data': processed_data,
            'metadata': {
                'total_states': len(processed_data),
                'visualization_type': 'choropleth',
                'filters_applied': {
                    'quarter': params['quarter'],
                    'year': params['year'],
                    'grupo': params.get('grupo')
                }
            }
        })
        
    except Exception as e:
        logger.error(f"States geo endpoint error: {e}")
        return jsonify({
            'error': 'Failed to fetch states geographic data',
            'error_code': 'STATES_GEO_ERROR'
        }), 500

@geo_bp.route('/heatmap', methods=['GET'])
@optional_auth
@rate_limit_by_user("10 per minute")
@validate_input(GeoQuerySchema)
@cached_api_response(ttl=1200, cache_type='geo_data')
def get_heatmap_data():
    """
    Get data optimized for heatmap visualization.
    
    Returns coordinate points with intensity values for heatmap layers.
    """
    try:
        params = request.validated_data
        
        query = """
            SELECT 
                latitud,
                longitud,
                CAST(porcentaje AS NUMERIC) as porcentaje,
                sucursal_clean,
                estado,
                fecha_supervision
            FROM supervision_operativa_detalle
            WHERE latitud IS NOT NULL 
              AND longitud IS NOT NULL 
              AND porcentaje IS NOT NULL
              AND fecha_supervision IS NOT NULL
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
        
        # Limit for performance
        query += " LIMIT %s;"
        query_params.append(min(params['limit'], 5000))  # Max 5000 points for heatmap
        
        from database.connection_v3 import execute_query
        results = execute_query(query, query_params)
        
        # Process for heatmap
        heatmap_points = []
        for item in results:
            # Normalize intensity (0-1 based on percentage)
            intensity = (item['porcentaje'] or 0) / 100.0
            
            heatmap_points.append({
                'lat': float(item['latitud']),
                'lng': float(item['longitud']),
                'intensity': intensity,
                'value': item['porcentaje'],
                'sucursal': item['sucursal_clean'],
                'estado': item['estado']
            })
        
        return jsonify({
            'success': True,
            'data': heatmap_points,
            'metadata': {
                'total_points': len(heatmap_points),
                'visualization_type': 'heatmap',
                'intensity_range': {
                    'min': 0.0,
                    'max': 1.0
                },
                'filters_applied': {
                    'quarter': params['quarter'],
                    'year': params['year'],
                    'estado': params.get('estado'),
                    'grupo': params.get('grupo')
                }
            }
        })
        
    except Exception as e:
        logger.error(f"Heatmap endpoint error: {e}")
        return jsonify({
            'error': 'Failed to fetch heatmap data',
            'error_code': 'HEATMAP_ERROR'
        }), 500

@geo_bp.route('/bounds', methods=['GET'])
@optional_auth
@rate_limit_by_user("30 per minute")
@cached_api_response(ttl=3600, cache_type='geo_data')
def get_map_bounds():
    """
    Get geographic bounds for map initialization.
    
    Returns the bounding box coordinates for centering maps.
    """
    try:
        query = """
            SELECT 
                MIN(latitud) as min_lat,
                MAX(latitud) as max_lat,
                MIN(longitud) as min_lng,
                MAX(longitud) as max_lng,
                AVG(latitud) as center_lat,
                AVG(longitud) as center_lng,
                COUNT(*) as total_points
            FROM supervision_operativa_detalle
            WHERE latitud IS NOT NULL 
              AND longitud IS NOT NULL;
        """
        
        from database.connection_v3 import execute_query
        results = execute_query(query)
        
        if not results or not results[0]['total_points']:
            # Default bounds for Mexico
            bounds_data = {
                'bounds': {
                    'north': 32.72083,
                    'south': 14.53333,
                    'east': -86.81056,
                    'west': -118.40556
                },
                'center': {
                    'lat': 23.6345,
                    'lng': -102.5528
                },
                'zoom_level': 5,
                'total_points': 0
            }
        else:
            result = results[0]
            bounds_data = {
                'bounds': {
                    'north': float(result['max_lat']),
                    'south': float(result['min_lat']),
                    'east': float(result['max_lng']),
                    'west': float(result['min_lng'])
                },
                'center': {
                    'lat': float(result['center_lat']),
                    'lng': float(result['center_lng'])
                },
                'zoom_level': 6,
                'total_points': result['total_points']
            }
        
        return jsonify({
            'success': True,
            'data': bounds_data
        })
        
    except Exception as e:
        logger.error(f"Map bounds endpoint error: {e}")
        return jsonify({
            'error': 'Failed to fetch map bounds',
            'error_code': 'BOUNDS_ERROR'
        }), 500

@geo_bp.route('/clusters', methods=['GET'])
@optional_auth
@rate_limit_by_user("10 per minute")
@validate_input(GeoQuerySchema)
@cached_api_response(ttl=1800, cache_type='geo_data')
def get_performance_clusters():
    """
    Get performance clusters for advanced map visualization.
    
    Groups nearby branches with similar performance for cluster visualization.
    """
    try:
        params = request.validated_data
        
        # Simple clustering based on state and performance ranges
        query = """
            SELECT 
                estado,
                CASE 
                    WHEN AVG(CAST(porcentaje AS NUMERIC)) >= 95 THEN 'excelente'
                    WHEN AVG(CAST(porcentaje AS NUMERIC)) >= 85 THEN 'muy_bueno'
                    WHEN AVG(CAST(porcentaje AS NUMERIC)) >= 75 THEN 'bueno'
                    ELSE 'regular'
                END as cluster_performance,
                ROUND(AVG(CAST(porcentaje AS NUMERIC)), 2) as promedio_cluster,
                COUNT(*) as total_sucursales,
                AVG(latitud) as centro_lat,
                AVG(longitud) as centro_lng,
                ARRAY_AGG(sucursal_clean) as sucursales_incluidas
            FROM supervision_operativa_detalle
            WHERE latitud IS NOT NULL 
              AND longitud IS NOT NULL 
              AND porcentaje IS NOT NULL
              AND fecha_supervision IS NOT NULL
        """
        
        query_params = []
        
        if params['quarter'] != 'ALL':
            query += " AND EXTRACT(QUARTER FROM fecha_supervision) = %s"
            query_params.append(int(params['quarter'][1]))
        
        if params['year']:
            query += " AND EXTRACT(YEAR FROM fecha_supervision) = %s"
            query_params.append(params['year'])
        
        query += """
            GROUP BY estado
            HAVING COUNT(*) >= 3
            ORDER BY promedio_cluster DESC;
        """
        
        from database.connection_v3 import execute_query
        results = execute_query(query, query_params)
        
        # Process clusters
        clusters = []
        for item in results:
            cluster = {
                'id': f"cluster_{item['estado']}",
                'estado': item['estado'],
                'performance_level': item['cluster_performance'],
                'promedio': item['promedio_cluster'],
                'total_sucursales': item['total_sucursales'],
                'centro': {
                    'lat': float(item['centro_lat']),
                    'lng': float(item['centro_lng'])
                },
                'sucursales': item['sucursales_incluidas'][:10]  # Limit for response size
            }
            clusters.append(cluster)
        
        return jsonify({
            'success': True,
            'data': clusters,
            'metadata': {
                'total_clusters': len(clusters),
                'clustering_method': 'state_performance',
                'filters_applied': {
                    'quarter': params['quarter'],
                    'year': params['year']
                }
            }
        })
        
    except Exception as e:
        logger.error(f"Clusters endpoint error: {e}")
        return jsonify({
            'error': 'Failed to fetch performance clusters',
            'error_code': 'CLUSTERS_ERROR'
        }), 500