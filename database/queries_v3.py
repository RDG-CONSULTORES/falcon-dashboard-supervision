from datetime import datetime, timedelta
from database.connection_v3 import execute_query
import logging

logger = logging.getLogger(__name__)

def get_sucursales_list():
    """Get list of all unique sucursales."""
    query = """
        SELECT DISTINCT sucursal_clean 
        FROM supervision_operativa_detalle 
        WHERE sucursal_clean IS NOT NULL 
        ORDER BY sucursal_clean;
    """
    
    results = execute_query(query)
    if results:
        return [row['sucursal_clean'] for row in results]
    return []

def get_grupos_operativos():
    """Get list of all unique grupos operativos."""
    query = """
        SELECT DISTINCT grupo_operativo 
        FROM supervision_operativa_detalle 
        WHERE grupo_operativo IS NOT NULL 
        ORDER BY grupo_operativo;
    """
    
    results = execute_query(query)
    if results:
        return [row['grupo_operativo'] for row in results]
    return []

def get_areas_evaluacion():
    """Get list of all unique areas de evaluacion."""
    query = """
        SELECT DISTINCT area_evaluacion 
        FROM supervision_operativa_detalle 
        WHERE area_evaluacion IS NOT NULL 
        ORDER BY area_evaluacion;
    """
    
    results = execute_query(query)
    if results:
        return [row['area_evaluacion'] for row in results]
    return []

def get_summary_stats():
    """Get general summary statistics."""
    query = """
        SELECT 
            COUNT(DISTINCT sucursal_clean) as total_sucursales,
            COUNT(*) as total_evaluaciones,
            AVG(porcentaje) as promedio_general,
            MIN(fecha_supervision) as fecha_inicio,
            MAX(fecha_supervision) as fecha_fin
        FROM supervision_operativa_detalle
        WHERE porcentaje IS NOT NULL;
    """
    
    results = execute_query(query)
    if results and len(results) > 0:
        stats = results[0]
        
        # Get top sucursales
        top_query = """
            SELECT 
                sucursal_clean as sucursal,
                AVG(porcentaje) as promedio
            FROM supervision_operativa_detalle
            WHERE porcentaje IS NOT NULL
            GROUP BY sucursal_clean
            ORDER BY promedio DESC
            LIMIT 5;
        """
        
        top_results = execute_query(top_query)
        if top_results:
            stats['top_sucursales'] = top_results
        
        return stats
    return None

def get_metrics_by_sucursal(sucursal=None, fecha_inicio=None, fecha_fin=None):
    """Get metrics filtered by sucursal and date range."""
    where_conditions = ["porcentaje IS NOT NULL"]
    params = []
    
    if sucursal:
        where_conditions.append("sucursal_clean = %s")
        params.append(sucursal)
    
    if fecha_inicio:
        where_conditions.append("fecha_supervision >= %s")
        params.append(fecha_inicio)
    
    if fecha_fin:
        where_conditions.append("fecha_supervision <= %s")
        params.append(fecha_fin)
    
    query = f"""
        SELECT 
            submission_id,
            sucursal_clean,
            grupo_operativo,
            area_evaluacion,
            fecha_supervision,
            porcentaje
        FROM supervision_operativa_detalle
        WHERE {' AND '.join(where_conditions)}
        ORDER BY fecha_supervision DESC, sucursal_clean
        LIMIT 1000;
    """
    
    results = execute_query(query, params)
    if results:
        return results
    return []

def get_performance_by_sucursal(fecha_inicio=None, fecha_fin=None):
    """Get average performance by sucursal."""
    where_conditions = ["porcentaje IS NOT NULL"]
    params = []
    
    if fecha_inicio:
        where_conditions.append("fecha_supervision >= %s")
        params.append(fecha_inicio)
    
    if fecha_fin:
        where_conditions.append("fecha_supervision <= %s")
        params.append(fecha_fin)
    
    query = f"""
        SELECT 
            sucursal_clean,
            AVG(porcentaje) as promedio,
            COUNT(*) as total_evaluaciones,
            MAX(porcentaje) as max_porcentaje,
            MIN(porcentaje) as min_porcentaje
        FROM supervision_operativa_detalle
        WHERE {' AND '.join(where_conditions)}
        GROUP BY sucursal_clean
        ORDER BY promedio DESC;
    """
    
    results = execute_query(query, params)
    if results:
        return results
    return []

def get_performance_by_grupo(fecha_inicio=None, fecha_fin=None):
    """Get average performance by grupo operativo."""
    where_conditions = ["porcentaje IS NOT NULL"]
    params = []
    
    if fecha_inicio:
        where_conditions.append("fecha_supervision >= %s")
        params.append(fecha_inicio)
    
    if fecha_fin:
        where_conditions.append("fecha_supervision <= %s")
        params.append(fecha_fin)
    
    query = f"""
        SELECT 
            grupo_operativo,
            AVG(porcentaje) as promedio,
            COUNT(*) as total_evaluaciones,
            COUNT(DISTINCT sucursal_clean) as total_sucursales
        FROM supervision_operativa_detalle
        WHERE {' AND '.join(where_conditions)}
        GROUP BY grupo_operativo
        ORDER BY promedio DESC;
    """
    
    results = execute_query(query, params)
    if results:
        return results
    return []

def get_performance_by_area(fecha_inicio=None, fecha_fin=None):
    """Get average performance by area de evaluacion."""
    where_conditions = ["porcentaje IS NOT NULL"]
    params = []
    
    if fecha_inicio:
        where_conditions.append("fecha_supervision >= %s")
        params.append(fecha_inicio)
    
    if fecha_fin:
        where_conditions.append("fecha_supervision <= %s")
        params.append(fecha_fin)
    
    query = f"""
        SELECT 
            area_evaluacion,
            AVG(porcentaje) as promedio,
            COUNT(*) as total_evaluaciones,
            COUNT(DISTINCT sucursal_clean) as total_sucursales
        FROM supervision_operativa_detalle
        WHERE {' AND '.join(where_conditions)}
        GROUP BY area_evaluacion
        ORDER BY promedio DESC;
    """
    
    results = execute_query(query, params)
    if results:
        return results
    return []

def get_trends_by_date(fecha_inicio=None, fecha_fin=None, sucursal=None):
    """Get trends over time."""
    where_conditions = ["porcentaje IS NOT NULL"]
    params = []
    
    if fecha_inicio:
        where_conditions.append("fecha_supervision >= %s")
        params.append(fecha_inicio)
    
    if fecha_fin:
        where_conditions.append("fecha_supervision <= %s")
        params.append(fecha_fin)
    
    if sucursal:
        where_conditions.append("sucursal_clean = %s")
        params.append(sucursal)
    
    query = f"""
        SELECT 
            fecha_supervision,
            AVG(porcentaje) as promedio_dia,
            COUNT(*) as evaluaciones_dia,
            COUNT(DISTINCT sucursal_clean) as sucursales_dia
        FROM supervision_operativa_detalle
        WHERE {' AND '.join(where_conditions)}
        GROUP BY fecha_supervision
        ORDER BY fecha_supervision;
    """
    
    results = execute_query(query, params)
    if results:
        return results
    return []

def get_detailed_performance(sucursal=None, grupo=None, area=None, fecha_inicio=None, fecha_fin=None):
    """Get detailed performance with all filters."""
    where_conditions = ["porcentaje IS NOT NULL"]
    params = []
    
    if sucursal:
        where_conditions.append("sucursal_clean = %s")
        params.append(sucursal)
    
    if grupo:
        where_conditions.append("grupo_operativo = %s")
        params.append(grupo)
    
    if area:
        where_conditions.append("area_evaluacion = %s")
        params.append(area)
    
    if fecha_inicio:
        where_conditions.append("fecha_supervision >= %s")
        params.append(fecha_inicio)
    
    if fecha_fin:
        where_conditions.append("fecha_supervision <= %s")
        params.append(fecha_fin)
    
    query = f"""
        SELECT 
            submission_id,
            sucursal_clean,
            grupo_operativo,
            area_evaluacion,
            fecha_supervision,
            porcentaje
        FROM supervision_operativa_detalle
        WHERE {' AND '.join(where_conditions)}
        ORDER BY fecha_supervision DESC, sucursal_clean, area_evaluacion
        LIMIT 1000;
    """
    
    results = execute_query(query, params)
    if results:
        return results
    return []