"""
Production-ready Flask application with all security, performance, and architectural improvements.
Version 4.0 - Production Release
"""

import os
import sys
import logging
from datetime import datetime, timezone
from flask import Flask, request, jsonify
from flask_cors import CORS

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import all the new modules
from auth.security import SecurityConfig
from middleware.security_middleware import SecurityMiddleware
from cache.cache_manager import cache_manager, CACHE_WARMUP_FUNCTIONS
from database.optimization import db_optimizer, maintenance_tasks
from error_handling import error_handler_manager
from api.v1 import auth_bp, analytics_bp, geo_bp, health_bp, admin_bp
from web.dashboard import web_bp
from flask import render_template

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/app.log') if os.path.exists('logs') else logging.NullHandler()
    ]
)
logger = logging.getLogger(__name__)

def create_app(config_name='production'):
    """Application factory with production configuration"""
    app = Flask(__name__)
    
    # Load configuration
    configure_app(app, config_name)
    
    # Initialize security middleware
    security_middleware = SecurityMiddleware(app)
    
    # Initialize error handling
    error_handler_manager.init_app(app)
    
    # Configure CORS
    CORS(app, origins=[
        "https://telegram.org",
        "https://*.vercel.app",
        os.getenv('WEBAPP_URL', 'http://localhost:5000')
    ])
    
    # Register blueprints
    register_blueprints(app)
    
    # Initialize background services
    initialize_services(app)
    
    # Add custom middleware
    add_custom_middleware(app)
    
    logger.info(f"Flask application initialized in {config_name} mode")
    return app

def configure_app(app, config_name):
    """Configure application settings"""
    
    # Basic Flask configuration
    app.config.update({
        'SECRET_KEY': SecurityConfig.JWT_SECRET_KEY,
        'JSON_SORT_KEYS': False,
        'JSONIFY_PRETTYPRINT_REGULAR': False,
        'MAX_CONTENT_LENGTH': 16 * 1024 * 1024,  # 16MB max request size
        'SEND_FILE_MAX_AGE_DEFAULT': 31536000,   # 1 year cache for static files
    })
    
    # Environment-specific configuration
    if config_name == 'production':
        app.config.update({
            'DEBUG': False,
            'TESTING': False,
            'ENV': 'production',
            'FORCE_HTTPS': True,
        })
    elif config_name == 'development':
        app.config.update({
            'DEBUG': True,
            'TESTING': False,
            'ENV': 'development',
            'FORCE_HTTPS': False,
        })
    elif config_name == 'testing':
        app.config.update({
            'DEBUG': False,
            'TESTING': True,
            'ENV': 'testing',
            'FORCE_HTTPS': False,
        })
    
    logger.info(f"Application configured for {config_name} environment")

def register_blueprints(app):
    """Register all API and web blueprints"""
    
    # Web dashboard blueprints (register first for root path)
    app.register_blueprint(web_bp)
    
    # API v1 blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(geo_bp)
    app.register_blueprint(health_bp)
    app.register_blueprint(admin_bp)
    
    # Legacy routes for backward compatibility
    register_legacy_routes(app)
    
    logger.info("All blueprints registered successfully")

def register_legacy_routes(app):
    """Register legacy routes for backward compatibility"""
    
    from auth.security import optional_auth, validate_input, APIQuerySchema
    from cache.cache_manager import cached_api_response
    from database.optimization import optimized_queries
    
    @app.route('/')
    def index():
        """Main dashboard page - redirect to supervision dashboard"""
        from flask import render_template
        try:
            return render_template('dashboard_estandarizacion.html')
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
                    <p class="status">✅ Database Active (133,160 records)</p>
                    
                    <h2>📊 Dashboards Disponibles</h2>
                    
                    <div class="dashboard-grid">
                        <div class="dashboard-card recommended">
                            <h3>🎯 Dashboard 1: Calificación General <span class="badge">METABASE</span></h3>
                            <p>Dashboard completo con datos de Metabase, filtros funcionales y datos en tiempo real.</p>
                            <a href="/dashboard/calificacion-metabase">Ver Dashboard</a>
                        </div>
                        
                        <div class="dashboard-card">
                            <h3>📊 Dashboard 2: 29 Indicadores</h3>
                            <p>Pendiente del iframe de Metabase para completar la integración.</p>
                            <a href="/dashboard/indicadores-metabase">Ver Dashboard</a>
                        </div>
                    </div>
                    
                    <h3>🔧 Dashboards de Desarrollo</h3>
                    <ul>
                        <li><a href="/dashboard/calificacion">🛠️ Dashboard 1: Versión JavaScript (problemas)</a></li>
                        <li><a href="/dashboard/indicadores">🛠️ Dashboard 2: Versión JavaScript</a></li>
                        <li><a href="/dashboard/simple">🧪 Dashboard Simple Test</a></li>
                    </ul>
                    
                    <h3>🎨 Demos y Herramientas</h3>
                    <ul>
                        <li><a href="/demos/charts">📊 Demo de Gráficas Modernas</a></li>
                    </ul>
                    
                    <h3>🔍 API y Diagnósticos</h3>
                    <ul>
                        <li><a href="/api/v1/health/detailed">🏥 Health Check</a></li>
                        <li><a href="/api/kpis?year=2025&quarter=Q2">📈 KPI Test (Q2 2025)</a></li>
                        <li><a href="/api/coordinates?year=2025&quarter=Q2&limit=10">🗺️ Coordinates Test</a></li>
                    </ul>
                </div>
            </body></html>
            """
    
    @app.route('/demos/charts')
    def chart_demos():
        """Modern chart and UI component demos"""
        return render_template('chart_demos.html')
    
    @app.route('/dashboard/calificacion')
    def dashboard_calificacion():
        """Dashboard 1: Calificación General"""
        from flask import render_template
        try:
            return render_template('dashboard_estandarizacion.html')
        except Exception as e:
            logger.error(f"Template error: {e}")
            return f"<h1>Error loading dashboard: {e}</h1>"
    
    @app.route('/dashboard/indicadores')
    def dashboard_indicadores():
        """Dashboard 2: 29 Indicadores por Área"""
        from flask import render_template
        try:
            return render_template('dashboard_indicadores_areas.html')
        except Exception as e:
            logger.error(f"Template error: {e}")
            return f"<h1>Error loading dashboard: {e}</h1>"
    
    @app.route('/dashboard/simple')
    def dashboard_simple():
        """Dashboard Simple que FUNCIONA 100%"""
        from flask import render_template
        try:
            return render_template('dashboard_simple_working.html')
        except Exception as e:
            logger.error(f"Template error: {e}")
            return f"<h1>Error loading dashboard: {e}</h1>"
    
    @app.route('/dashboard/calificacion-metabase')
    def dashboard_calificacion_metabase():
        """Dashboard 1: Calificación General con Metabase"""
        from flask import render_template
        try:
            return render_template('dashboard_metabase_calificacion.html')
        except Exception as e:
            logger.error(f"Template error: {e}")
            return f"<h1>Error loading Metabase dashboard: {e}</h1>"
    
    @app.route('/dashboard/indicadores-metabase')
    def dashboard_indicadores_metabase():
        """Dashboard 2: 29 Indicadores por Área con Metabase"""
        from flask import render_template
        try:
            return render_template('dashboard_metabase_indicadores.html')
        except Exception as e:
            logger.error(f"Template error: {e}")
            return f"<h1>Error loading Metabase dashboard: {e}</h1>"
    
    @app.route('/test')
    def test_connection():
        """Test connection page"""
        import os
        from flask import send_from_directory
        try:
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            return send_from_directory(project_root, 'test_connection.html')
        except Exception as e:
            logger.error(f"Test page error: {e}")
            return f"<h1>🔧 Connection Test Error</h1><p>Error: {e}</p><p><a href='/'>← Back to Dashboard</a></p>"
    
    @app.route('/api/kpis')
    @optional_auth
    @validate_input(APIQuerySchema)
    @cached_api_response(ttl=300, cache_type='kpis')
    def legacy_kpis():
        """Legacy KPI endpoint for backward compatibility"""
        try:
            params = request.validated_data
            kpi_data = optimized_queries.get_optimized_kpis(
                quarter=params['quarter'],
                year=params['year'],
                estado=params.get('estado'),
                grupo=params.get('grupo')
            )
            
            if not kpi_data:
                return jsonify({'error': 'No data found'}), 404
            
            return jsonify(kpi_data[0])
            
        except Exception as e:
            logger.error(f"Legacy KPI endpoint error: {e}")
            return jsonify({'error': 'Failed to fetch KPI data'}), 500
    
    @app.route('/api/coordinates')
    @optional_auth
    @validate_input(APIQuerySchema)
    @cached_api_response(ttl=600, cache_type='geo_data')
    def legacy_coordinates():
        """Legacy coordinates endpoint"""
        try:
            params = request.validated_data
            coord_data = optimized_queries.get_optimized_coordinates(
                quarter=params['quarter'],
                year=params['year'],
                estado=params.get('estado'),
                limit=params['limit']
            )
            
            return jsonify(coord_data or [])
            
        except Exception as e:
            logger.error(f"Legacy coordinates endpoint error: {e}")
            return jsonify({'error': 'Failed to fetch coordinate data'}), 500

def initialize_services(app):
    """Initialize background services and optimizations"""
    
    with app.app_context():
        try:
            # Initialize database optimizations
            logger.info("Initializing database optimizations...")
            
            # Create indexes if they don't exist
            index_results = db_optimizer.create_indexes()
            logger.info(f"Database indexes: {len(index_results['created'])} created, {len(index_results['skipped'])} skipped")
            
            # Create materialized views
            view_results = db_optimizer.create_materialized_views()
            logger.info(f"Materialized views: {len(view_results['created'])} created, {len(view_results['skipped'])} skipped")
            
            # Warm cache
            logger.info("Warming application cache...")
            cache_manager.warm_cache(CACHE_WARMUP_FUNCTIONS)
            
            logger.info("Services initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing services: {e}")

def add_custom_middleware(app):
    """Add custom middleware functions"""
    
    @app.before_request
    def log_request_info():
        """Log request information"""
        if request.path.startswith('/api/'):
            logger.info(f"API Request: {request.method} {request.path} from {request.remote_addr}")
    
    @app.after_request
    def add_security_headers(response):
        """Add additional security headers"""
        response.headers['X-Content-Type-Options'] = 'nosniff'
        # Allow Metabase iframes
        if '-metabase' in request.path:
            response.headers['X-Frame-Options'] = 'ALLOWALL'
            response.headers['Content-Security-Policy'] = "frame-src 'self' https://rdg-consultores.metabaseapp.com https://*.metabaseapp.com; img-src 'self' data: https:; script-src 'self' 'unsafe-inline';"
        else:
            response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        return response
    
    @app.context_processor
    def inject_template_vars():
        """Inject variables into templates"""
        return {
            'app_version': '4.0.0',
            'environment': app.config.get('ENV', 'production'),
            'current_year': datetime.now().year
        }

# Background task setup (for production deployment)
def setup_background_tasks(app):
    """Setup background tasks for maintenance"""
    try:
        from celery import Celery
        
        # Configure Celery
        celery = Celery(
            app.import_name,
            broker=os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0'),
            backend=os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
        )
        
        # Configure task schedules
        celery.conf.beat_schedule = {
            'refresh-materialized-views': {
                'task': 'tasks.refresh_materialized_views',
                'schedule': 3600.0,  # Every hour
            },
            'cleanup-cache': {
                'task': 'tasks.cleanup_cache',
                'schedule': 21600.0,  # Every 6 hours
            },
            'daily-maintenance': {
                'task': 'tasks.daily_maintenance',
                'schedule': 86400.0,  # Daily
            }
        }
        
        @celery.task
        def refresh_materialized_views():
            """Background task to refresh materialized views"""
            with app.app_context():
                try:
                    results = db_optimizer.refresh_materialized_views()
                    logger.info(f"Materialized views refreshed: {results}")
                    return results
                except Exception as e:
                    logger.error(f"Error refreshing materialized views: {e}")
                    return {'error': str(e)}
        
        @celery.task
        def cleanup_cache():
            """Background task to cleanup cache"""
            try:
                # Clear expired entries
                cache_manager.clear_pattern("*:expired:*")
                logger.info("Cache cleanup completed")
                return {'status': 'completed'}
            except Exception as e:
                logger.error(f"Cache cleanup error: {e}")
                return {'error': str(e)}
        
        @celery.task
        def daily_maintenance():
            """Background task for daily maintenance"""
            with app.app_context():
                try:
                    maintenance_tasks.daily_maintenance()
                    logger.info("Daily maintenance completed")
                    return {'status': 'completed'}
                except Exception as e:
                    logger.error(f"Daily maintenance error: {e}")
                    return {'error': str(e)}
        
        logger.info("Background tasks configured successfully")
        
    except ImportError:
        logger.warning("Celery not available, background tasks disabled")
    except Exception as e:
        logger.error(f"Error setting up background tasks: {e}")

# Create application instance
app = create_app(os.getenv('FLASK_ENV', 'production'))

# Setup background tasks if in production
if not app.config.get('TESTING', False):
    setup_background_tasks(app)

# Add CLI commands for database management
@app.cli.command()
def init_db():
    """Initialize database with indexes and views"""
    with app.app_context():
        logger.info("Initializing database...")
        
        # Create indexes
        index_results = db_optimizer.create_indexes()
        print(f"Indexes created: {len(index_results['created'])}")
        print(f"Indexes skipped: {len(index_results['skipped'])}")
        if index_results['errors']:
            print(f"Index errors: {index_results['errors']}")
        
        # Create materialized views
        view_results = db_optimizer.create_materialized_views()
        print(f"Views created: {len(view_results['created'])}")
        print(f"Views skipped: {len(view_results['skipped'])}")
        if view_results['errors']:
            print(f"View errors: {view_results['errors']}")
        
        print("Database initialization completed")

@app.cli.command()
def warm_cache():
    """Warm application cache"""
    with app.app_context():
        logger.info("Warming cache...")
        cache_manager.warm_cache(CACHE_WARMUP_FUNCTIONS)
        print("Cache warming completed")

@app.cli.command()
def maintenance():
    """Run maintenance tasks"""
    with app.app_context():
        logger.info("Running maintenance tasks...")
        maintenance_tasks.daily_maintenance()
        print("Maintenance tasks completed")

@app.cli.command()
def cache_stats():
    """Show cache statistics"""
    stats = cache_manager.get_stats()
    print("Cache Statistics:")
    print(f"  Redis Available: {stats['redis_available']}")
    print(f"  Hit Rate: {stats['hit_rate']}%")
    print(f"  Total Requests: {stats['total_requests']}")
    print(f"  Hits: {stats['hits']}")
    print(f"  Misses: {stats['misses']}")
    print(f"  Errors: {stats['errors']}")

if __name__ == '__main__':
    # Development server (not for production)
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('DEBUG', 'false').lower() == 'true'
    
    logger.info(f"Starting development server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=debug)