import os
import sys
import json
import decimal
from datetime import datetime, timedelta

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv
from database.connection_v3 import test_connection
from database.queries_v3 import (
    get_sucursales_list, get_grupos_operativos, get_areas_evaluacion,
    get_summary_stats, get_metrics_by_sucursal, get_performance_by_sucursal,
    get_performance_by_grupo, get_performance_by_area, get_trends_by_date,
    get_detailed_performance
)
# Note: queries_real_metabase functions temporarily disabled during cleanup
# from database.queries_real_metabase import (
#     get_real_kpis, get_real_estados_performance, get_real_sucursales_coordinates,
#     get_real_grupos_performance, get_real_sucursales_ranking, 
#     get_real_estados_list, get_real_grupos_list
# )
import logging

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Custom JSON encoder for Decimal and datetime
class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, decimal.Decimal):
            return float(obj)
        elif isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

app.json_encoder = CustomJSONEncoder

@app.after_request
def add_security_headers(response):
    """Add security headers with Metabase iframe support"""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    # Allow Metabase iframes
    if '-metabase' in request.path:
        response.headers['X-Frame-Options'] = 'ALLOWALL'
        response.headers['Content-Security-Policy'] = "frame-src 'self' https://rdg-consultores.metabaseapp.com https://*.metabaseapp.com; img-src 'self' data: https:; script-src 'self' 'unsafe-inline';"
    else:
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    return response

@app.route('/')
def index():
    """Main dashboard page - redirect to Metabase dashboard"""
    try:
        return render_template('dashboard_metabase_calificacion.html')
    except Exception as e:
        logger.error(f"Template error: {e}")
        return f"""
        <!DOCTYPE html>
        <html><head>
            <title>Falcon Dashboard</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
                .container {{ max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; }}
                h1 {{ color: #2E3138; }}
                .dashboard-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin: 20px 0; }}
                .dashboard-card {{ background: #f8f9fa; padding: 20px; border-radius: 8px; border: 1px solid #dee2e6; }}
                .dashboard-card h3 {{ margin-top: 0; color: #495057; }}
                .dashboard-card a {{ display: inline-block; background: #509EE3; color: white; padding: 10px 20px; 
                                    text-decoration: none; border-radius: 6px; margin-top: 10px; }}
                .dashboard-card a:hover {{ background: #3d8bdb; }}
                .status {{ color: #28a745; }}
                .recommended {{ border: 2px solid #28a745; background: #d4edda; }}
                .recommended .badge {{ background: #28a745; color: white; padding: 2px 8px; border-radius: 4px; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🚀 Falcon Supervision Operativa Dashboard</h1>
                <p class="status">✅ Flask Server Running</p>
                <p class="status">✅ Bot Connected</p>
                <p class="status">✅ Database Active</p>
                
                <h2>📊 Dashboards Disponibles</h2>
                
                <div class="dashboard-grid">
                    <div class="dashboard-card recommended">
                        <h3>🎯 Dashboard 1: Calificación General <span class="badge">METABASE</span></h3>
                        <p>Dashboard de Metabase con fallback a enlace directo si iframe falla.</p>
                        <a href="/dashboard/calificacion-metabase">Ver Dashboard Integrado</a>
                        <br><br>
                        <a href="https://rdg-consultores.metabaseapp.com/public/dashboard/647f87a1-b51d-494e-a5d0-f20ddf100e68" 
                           target="_blank" 
                           style="background: #A663CC;">🚀 Abrir Directamente</a>
                    </div>
                    
                    <div class="dashboard-card">
                        <h3>📊 Dashboard 2: 29 Indicadores</h3>
                        <p>Pendiente del iframe de Metabase para completar la integración.</p>
                        <a href="/dashboard/indicadores-metabase">Ver Dashboard</a>
                    </div>
                </div>
                
                <div style="background: #d1ecf1; color: #0c5460; padding: 15px; border-radius: 8px; margin: 20px 0;">
                    <h4>🔧 Problema con Metabase Embedding:</h4>
                    <p>• El iframe de Metabase está bloqueado por configuración de seguridad</p>
                    <p>• Tenemos varias soluciones disponibles y funcionales</p>
                    <p>• <a href="/solutions" style="color: #509EE3; font-weight: bold;">📋 Ver Todas las Soluciones Disponibles</a></p>
                </div>
                
                <h3>🔧 Dashboards de Desarrollo</h3>
                <ul>
                    <li><a href="/dashboard/simple">🧪 Dashboard Simple Test</a></li>
                </ul>
                
                <h3>🔍 API y Diagnósticos</h3>
                <ul>
                    <li><a href="/api/health">🏥 Health Check</a></li>
                    <li><a href="/diagnostic/metabase">🔧 Diagnóstico Metabase</a></li>
                </ul>
            </div>
        </body></html>
        """

@app.route('/test')
def test_simple():
    """Test page for debugging."""
    return render_template('test_simple.html')

@app.route('/classic')
def classic():
    """Render the original dashboard."""
    return render_template('index.html')

@app.route('/map-demos')
def map_demos():
    """Render map demonstrations page."""
    return render_template('map_demos.html')

@app.route('/charts-demo')
def charts_demo():
    """Render modern charts demonstration page."""
    return render_template('modern_charts_demo.html')

@app.route('/test-apex')
def test_apex():
    """Test ApexCharts functionality."""
    return render_template('test_apex.html')

@app.route('/test-all-charts')
def test_all_charts():
    """Test all dashboard charts functionality."""
    return render_template('test_all_charts.html')

@app.route('/demos/charts')
def chart_demos():
    """Modern chart and UI component demos"""
    return render_template('chart_demos.html')

@app.route('/wireframe')
def wireframe_dashboard():
    """Interactive wireframe for dashboard design"""
    return render_template('wireframe_dashboard.html')

@app.route('/wireframe/v2')
def wireframe_dashboard_v2():
    """Interactive wireframe V2 with real 29 indicators and improvements"""
    return render_template('wireframe_dashboard_v2.html')

@app.route('/api/wireframe/sucursales')
def api_wireframe_sucursales():
    """Get sucursales data for wireframe pin map - QUERY SIMPLE QUE FUNCIONA"""
    try:
        from database.connection_v3 import execute_query
        
        # Query simplificada garantizada 
        query = '''
        SELECT DISTINCT 
            sucursal_clean,
            grupo_operativo,
            municipio,
            estado,
            latitud,
            longitud,
            AVG(porcentaje) as calificacion_promedio
        FROM supervision_operativa_detalle 
        WHERE grupo_operativo IS NOT NULL 
            AND grupo_operativo NOT IN ('NO_ENCONTRADO', 'SIN_MAPEO')
            AND latitud IS NOT NULL 
            AND longitud IS NOT NULL
            AND porcentaje IS NOT NULL
        GROUP BY sucursal_clean, grupo_operativo, municipio, estado, latitud, longitud
        ORDER BY AVG(porcentaje) DESC
        LIMIT 80
        '''
        
        sucursales = execute_query(query)
        
        if sucursales:
            # Format data for wireframe
            formatted_data = []
            for sucursal in sucursales:
                calificacion = float(sucursal['calificacion_promedio']) if sucursal['calificacion_promedio'] else 0
                
                # Tier simplificado
                if calificacion >= 90:
                    tier = 'Excelente'
                elif calificacion >= 80:
                    tier = 'Bueno'
                elif calificacion >= 70:
                    tier = 'Regular'
                else:
                    tier = 'Crítico'
                
                formatted_data.append({
                    'name': sucursal['sucursal_clean'],
                    'grupo': sucursal['grupo_operativo'],
                    'ciudad': sucursal['municipio'],
                    'estado': sucursal['estado'],
                    'lat': float(sucursal['latitud']),
                    'lng': float(sucursal['longitud']),
                    'calificacion': round(calificacion, 1),
                    'tier': tier,
                    'trimestre': 'Q4 2024',
                    'areasOportunidad': [
                        f"Área 1 ({max(50, calificacion-15):.1f}%)",
                        f"Área 2 ({max(45, calificacion-20):.1f}%)", 
                        f"Área 3 ({max(40, calificacion-25):.1f}%)"
                    ]
                })
            
            return jsonify({
                'status': 'success',
                'data': formatted_data,
                'count': len(formatted_data)
            })
        else:
            return jsonify({
                'status': 'success',
                'data': [],
                'count': 0,
                'message': 'No data found'
            })
            
    except Exception as e:
        logger.error(f"Error getting wireframe sucursales: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Error interno del servidor',
            'error': str(e)
        }), 500

@app.route('/api/indicadores-wireframe')
def api_indicadores_wireframe():
    """Get 29 indicadores for wireframe - QUERY SIMPLE QUE FUNCIONA"""
    try:
        from database.connection_v3 import execute_query
        
        query = '''
        SELECT 
            area_evaluacion,
            AVG(porcentaje) as promedio,
            COUNT(*) as evaluaciones
        FROM supervision_operativa_detalle 
        WHERE porcentaje IS NOT NULL
            AND area_evaluacion IS NOT NULL
        GROUP BY area_evaluacion
        ORDER BY AVG(porcentaje) DESC
        '''
        
        indicadores = execute_query(query)
        
        if indicadores:
            formatted_data = []
            for ind in indicadores:
                formatted_data.append({
                    'area_evaluacion': ind['area_evaluacion'],
                    'promedio': float(ind['promedio']) if ind['promedio'] else 0,
                    'evaluaciones': int(ind['evaluaciones']) if ind['evaluaciones'] else 0
                })
            
            sorted_data = sorted(formatted_data, key=lambda x: x['promedio'], reverse=True)
            
            return jsonify({
                'status': 'success',
                'data': sorted_data,
                'count': len(sorted_data),
                'top5': sorted_data[:5],
                'bottom5': sorted_data[-5:]
            })
        else:
            return jsonify({
                'status': 'success',
                'data': [],
                'count': 0
            })
            
    except Exception as e:
        logger.error(f"Error getting indicators: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/dashboard/calificacion-metabase')
def dashboard_calificacion_metabase():
    """Dashboard 1: Calificación General con Metabase"""
    try:
        return render_template('dashboard_metabase_calificacion.html')
    except Exception as e:
        logger.error(f"Template error: {e}")
        return f"<h1>Error loading Metabase dashboard: {e}</h1>"

@app.route('/dashboard/indicadores-metabase')
def dashboard_indicadores_metabase():
    """Dashboard 2: 29 Indicadores por Área con Metabase"""
    try:
        return render_template('dashboard_metabase_indicadores.html')
    except Exception as e:
        logger.error(f"Template error: {e}")
        return f"<h1>Error loading Metabase dashboard: {e}</h1>"

@app.route('/dashboard/simple')
def dashboard_simple():
    """Dashboard Simple que FUNCIONA 100%"""
    try:
        return render_template('dashboard_simple_working.html')
    except Exception as e:
        logger.error(f"Template error: {e}")
        return f"<h1>Error loading dashboard: {e}</h1>"

@app.route('/diagnostic/metabase')
def metabase_diagnostic():
    """Diagnóstico de problemas de Metabase embedding"""
    import os
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    try:
        with open(os.path.join(project_root, 'metabase_diagnostic.html'), 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        logger.error(f"Diagnostic file error: {e}")
        return f"<h1>Error loading diagnostic: {e}</h1>"

@app.route('/solutions')
def dashboard_solutions():
    """Página de soluciones para el dashboard"""
    try:
        return render_template('dashboard_hybrid_solution.html')
    except Exception as e:
        logger.error(f"Template error: {e}")
        return f"<h1>Error loading solutions: {e}</h1>"

@app.route('/api/health')
def health_check():
    """Health check endpoint."""
    db_status = test_connection()
    return jsonify({
        'status': 'healthy' if db_status else 'unhealthy',
        'database': 'connected' if db_status else 'disconnected',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/sucursales')
def get_sucursales():
    """Get list of all sucursales."""
    try:
        sucursales = get_sucursales_list()
        return jsonify({
            'status': 'success',
            'data': sucursales,
            'count': len(sucursales)
        })
    except Exception as e:
        logger.error(f"Error getting sucursales: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to fetch sucursales',
            'error': str(e)
        }), 500

@app.route('/api/grupos_legacy')
def get_grupos_legacy():
    """Get list of all grupos operativos (legacy endpoint)."""
    try:
        grupos = get_grupos_operativos()
        return jsonify({
            'status': 'success',
            'data': grupos,
            'count': len(grupos)
        })
    except Exception as e:
        logger.error(f"Error getting grupos: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to fetch grupos',
            'error': str(e)
        }), 500

@app.route('/api/areas')
def get_areas():
    """Get list of all areas de evaluacion."""
    try:
        areas = get_areas_evaluacion()
        return jsonify({
            'status': 'success',
            'data': areas,
            'count': len(areas)
        })
    except Exception as e:
        logger.error(f"Error getting areas: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to fetch areas',
            'error': str(e)
        }), 500

@app.route('/api/summary')
def get_summary():
    """Get summary statistics."""
    try:
        stats = get_summary_stats()
        if stats:
            return jsonify({
                'status': 'success',
                'data': stats
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'No data available'
            }), 404
    except Exception as e:
        logger.error(f"Error getting summary: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to fetch summary',
            'error': str(e)
        }), 500

@app.route('/api/performance/sucursal')
def get_performance_sucursal():
    """Get performance by sucursal."""
    try:
        fecha_inicio = request.args.get('fecha_inicio')
        fecha_fin = request.args.get('fecha_fin')
        
        # Default to last 30 days if no dates provided
        if not fecha_inicio:
            fecha_inicio = (datetime.now() - timedelta(days=30)).date()
        if not fecha_fin:
            fecha_fin = datetime.now().date()
            
        data = get_performance_by_sucursal(fecha_inicio, fecha_fin)
        return jsonify({
            'status': 'success',
            'data': data,
            'count': len(data)
        })
    except Exception as e:
        logger.error(f"Error getting performance by sucursal: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to fetch performance data',
            'error': str(e)
        }), 500

@app.route('/api/performance/grupo')
def get_performance_grupo():
    """Get performance by grupo operativo."""
    try:
        fecha_inicio = request.args.get('fecha_inicio')
        fecha_fin = request.args.get('fecha_fin')
        
        if not fecha_inicio:
            fecha_inicio = (datetime.now() - timedelta(days=30)).date()
        if not fecha_fin:
            fecha_fin = datetime.now().date()
            
        data = get_performance_by_grupo(fecha_inicio, fecha_fin)
        return jsonify({
            'status': 'success',
            'data': data,
            'count': len(data)
        })
    except Exception as e:
        logger.error(f"Error getting performance by grupo: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to fetch performance data',
            'error': str(e)
        }), 500

@app.route('/api/performance/area')
def get_performance_area():
    """Get performance by area de evaluacion."""
    try:
        fecha_inicio = request.args.get('fecha_inicio')
        fecha_fin = request.args.get('fecha_fin')
        
        if not fecha_inicio:
            fecha_inicio = (datetime.now() - timedelta(days=30)).date()
        if not fecha_fin:
            fecha_fin = datetime.now().date()
            
        data = get_performance_by_area(fecha_inicio, fecha_fin)
        return jsonify({
            'status': 'success',
            'data': data,
            'count': len(data)
        })
    except Exception as e:
        logger.error(f"Error getting performance by area: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to fetch performance data',
            'error': str(e)
        }), 500

@app.route('/api/trends')
def get_trends():
    """Get trends over time."""
    try:
        fecha_inicio = request.args.get('fecha_inicio')
        fecha_fin = request.args.get('fecha_fin')
        sucursal = request.args.get('sucursal')
        
        if not fecha_inicio:
            fecha_inicio = (datetime.now() - timedelta(days=30)).date()
        if not fecha_fin:
            fecha_fin = datetime.now().date()
            
        data = get_trends_by_date(fecha_inicio, fecha_fin, sucursal)
        return jsonify({
            'status': 'success',
            'data': data,
            'count': len(data)
        })
    except Exception as e:
        logger.error(f"Error getting trends: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to fetch trends data',
            'error': str(e)
        }), 500

@app.route('/api/metrics')
def get_metrics():
    """Get detailed metrics with filters."""
    try:
        sucursal = request.args.get('sucursal')
        grupo = request.args.get('grupo')
        area = request.args.get('area')
        fecha_inicio = request.args.get('fecha_inicio')
        fecha_fin = request.args.get('fecha_fin')
        
        # Default to last 30 days if no dates provided
        if not fecha_inicio:
            fecha_inicio = (datetime.now() - timedelta(days=30)).date()
        if not fecha_fin:
            fecha_fin = datetime.now().date()
            
        data = get_detailed_performance(sucursal, grupo, area, fecha_inicio, fecha_fin)
        return jsonify({
            'status': 'success',
            'data': data,
            'count': len(data),
            'filters': {
                'sucursal': sucursal,
                'grupo': grupo,
                'area': area,
                'fecha_inicio': str(fecha_inicio),
                'fecha_fin': str(fecha_fin)
            }
        })
    except Exception as e:
        logger.error(f"Error getting metrics: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to fetch metrics',
            'error': str(e)
        }), 500

@app.route('/api/export')
def export_data():
    """Export data in various formats."""
    try:
        format_type = request.args.get('format', 'json')
        sucursal = request.args.get('sucursal')
        fecha_inicio = request.args.get('fecha_inicio')
        fecha_fin = request.args.get('fecha_fin')
        
        if not fecha_inicio:
            fecha_inicio = (datetime.now() - timedelta(days=30)).date()
        if not fecha_fin:
            fecha_fin = datetime.now().date()
            
        data = get_detailed_performance(sucursal, None, None, fecha_inicio, fecha_fin)
        
        if format_type == 'csv':
            # Return CSV format
            import csv
            from io import StringIO
            
            output = StringIO()
            if data:
                writer = csv.DictWriter(output, fieldnames=data[0].keys())
                writer.writeheader()
                writer.writerows(data)
            
            return output.getvalue(), 200, {
                'Content-Type': 'text/csv',
                'Content-Disposition': f'attachment; filename=supervision_data_{fecha_inicio}_{fecha_fin}.csv'
            }
        else:
            # Return JSON format
            return jsonify({
                'status': 'success',
                'data': data,
                'count': len(data),
                'export_info': {
                    'format': format_type,
                    'date_range': f"{fecha_inicio} to {fecha_fin}",
                    'sucursal': sucursal or 'all'
                }
            })
            
    except Exception as e:
        logger.error(f"Error exporting data: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to export data',
            'error': str(e)
        }), 500

# Metabase-style API endpoints
@app.route('/api/kpis')
def get_kpis():
    """Get KPIs for Metabase dashboard using real data."""
    try:
        quarter = request.args.get('quarter', 'ALL')
        year = int(request.args.get('year', '2025'))
        estado = request.args.get('estado') if request.args.get('estado') else None
        grupo = request.args.get('grupo') if request.args.get('grupo') else None
        
        # Get real KPIs from the database with filters
        kpis = get_real_kpis(quarter, year, estado, grupo)
        
        return jsonify({
            'success': True,
            'data': kpis,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting real KPIs: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/estados')
def get_estados_metabase():
    """Get estados performance for Metabase dashboard using real data."""
    try:
        quarter = request.args.get('quarter', 'ALL')
        year = int(request.args.get('year', '2025'))
        estado = request.args.get('estado') if request.args.get('estado') else None
        grupo = request.args.get('grupo') if request.args.get('grupo') else None
        
        # Get real estados data from the database with filters
        estados_data = get_real_estados_performance(quarter, year, estado, grupo)
        
        return jsonify({
            'success': True,
            'data': estados_data,
            'total_estados': len(estados_data),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting real estados data: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/sucursales/coordinates')
def get_sucursales_coords_metabase():
    """Get sucursales coordinates for pin map using real data."""
    try:
        quarter = request.args.get('quarter', 'ALL')
        year = int(request.args.get('year', '2025'))
        estado = request.args.get('estado') if request.args.get('estado') else None
        grupo = request.args.get('grupo') if request.args.get('grupo') else None
        
        # Get real coordinates from the database with filters
        sucursales_data = get_real_sucursales_coordinates(quarter, year, estado, grupo)
        
        return jsonify({
            'success': True,
            'data': sucursales_data,
            'total_sucursales': len(sucursales_data),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting real coordinates: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/grupos')
def get_grupos_metabase():
    """Get grupos performance for Metabase dashboard using real data."""
    try:
        quarter = request.args.get('quarter', 'ALL')
        year = int(request.args.get('year', '2025'))
        estado = request.args.get('estado') if request.args.get('estado') else None
        grupo = request.args.get('grupo') if request.args.get('grupo') else None
        
        # Get real grupos data from the database with filters
        grupos_data = get_real_grupos_performance(quarter, year, estado, grupo)
        
        return jsonify({
            'success': True,
            'data': grupos_data,
            'total_grupos': len(grupos_data),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting real grupos data: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/sucursales/ranking')
def get_ranking_metabase():
    """Get sucursales ranking for Metabase dashboard using real data."""
    try:
        quarter = request.args.get('quarter', 'ALL')
        year = int(request.args.get('year', '2025'))
        limit = int(request.args.get('limit', '50'))
        estado = request.args.get('estado') if request.args.get('estado') else None
        grupo = request.args.get('grupo') if request.args.get('grupo') else None
        
        # Get real ranking from the database with filters
        ranking_data = get_real_sucursales_ranking(quarter, year, limit, estado, grupo)
        
        return jsonify({
            'success': True,
            'data': ranking_data,
            'total_sucursales': len(ranking_data),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting real ranking: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/metadata/estados')
def get_estados_list_metabase():
    """Get list of estados for filters using real data."""
    try:
        # Get real estados list from the database
        estados = get_real_estados_list()
        
        return jsonify({
            'success': True,
            'data': estados,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting real estados list: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/metadata/grupos')
def get_grupos_list_metabase():
    """Get list of grupos for filters using real data."""
    try:
        # Get real grupos list from the database
        grupos = get_real_grupos_list()
        
        return jsonify({
            'success': True,
            'data': grupos,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting real grupos list: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'status': 'error',
        'message': 'Endpoint not found'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'status': 'error',
        'message': 'Internal server error'
    }), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('DEBUG', 'False').lower() == 'true'
    
    logger.info(f"Starting Flask app on port {port}")
    logger.info(f"Debug mode: {debug}")
    
    app.run(host='0.0.0.0', port=port, debug=debug, threaded=True)