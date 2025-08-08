"""
Web dashboard routes for the main UI and Telegram Web App integration.
"""

import logging
from flask import Blueprint, render_template, request, jsonify, send_from_directory
from datetime import datetime

logger = logging.getLogger(__name__)
web_bp = Blueprint('web', __name__)

@web_bp.route('/')
def index():
    """Main dashboard page - Telegram Web App entry point"""
    try:
        # Get user agent to detect if coming from Telegram
        user_agent = request.headers.get('User-Agent', '')
        is_telegram = 'Telegram' in user_agent
        
        logger.info(f"Dashboard accessed - Telegram: {is_telegram}, UA: {user_agent[:50]}...")
        
        return render_template('index.html', 
                             is_telegram=is_telegram,
                             timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    
    except Exception as e:
        logger.error(f"Error serving main dashboard: {e}")
        return jsonify({'error': 'Dashboard error', 'message': str(e)}), 500

@web_bp.route('/dashboard')
def dashboard():
    """Alternative dashboard route"""
    return index()

@web_bp.route('/indicadores-areas')
def indicadores_areas():
    """Indicators by operational areas page"""
    try:
        return render_template('indicadores_areas.html',
                             timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    except Exception as e:
        logger.error(f"Error serving areas dashboard: {e}")
        return jsonify({'error': 'Areas dashboard error', 'message': str(e)}), 500

@web_bp.route('/test')
def test_connection():
    """Test connection page"""
    try:
        return send_from_directory('.', 'test_connection.html')
    except Exception as e:
        logger.error(f"Error serving test page: {e}")
        return jsonify({'error': 'Test page error', 'message': str(e)}), 500

@web_bp.route('/test-dashboard')
def test_dashboard():
    """Test dashboard page"""
    try:
        return send_from_directory('.', 'test_dashboard.html')
    except Exception as e:
        logger.error(f"Error serving test dashboard: {e}")
        return jsonify({'error': 'Test dashboard error', 'message': str(e)}), 500

@web_bp.route('/working-dashboard')
def working_dashboard():
    """Working dashboard page"""
    try:
        return send_from_directory('.', 'working_dashboard.html')
    except Exception as e:
        logger.error(f"Error serving working dashboard: {e}")
        return jsonify({'error': 'Working dashboard error', 'message': str(e)}), 500

@web_bp.route('/health-web')
def web_health():
    """Web health check"""
    return jsonify({
        'status': 'healthy',
        'service': 'web_dashboard',
        'timestamp': datetime.now().isoformat(),
        'templates_available': True
    })

# Error handlers for web routes
@web_bp.errorhandler(404)
def not_found_error(error):
    """Handle 404 errors for web routes"""
    return render_template('error.html', 
                         error_code=404, 
                         error_message='Page not found'), 404

@web_bp.errorhandler(500)
def internal_error(error):
    """Handle 500 errors for web routes"""
    logger.error(f"Web route 500 error: {error}")
    return render_template('error.html', 
                         error_code=500, 
                         error_message='Internal server error'), 500