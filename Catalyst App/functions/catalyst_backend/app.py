"""
Railway Ticketing System — Catalyst Advanced I/O Functions Entry Point
"""

import os
import logging
from datetime import datetime
from flask import Flask, jsonify, request
from flask_cors import CORS
import zcatalyst_sdk
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# ══════════════════════════════════════════════════════════════════════════════
#  FLASK APPLICATION SETUP
# ══════════════════════════════════════════════════════════════════════════════

def create_flask_app():
    """Create and configure the Flask application with all routes."""


    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'change-me-in-production')

    # ── CORS Configuration ────────────────────────────────────────────────────
    # Explicit allowed origins for proper CORS handling
    DEFAULT_ORIGINS = [
        'https://railway-ticketing-app.onslate.in',
        'http://localhost:3001',
        'http://localhost:5173',
        'http://127.0.0.1:3001',
        'http://127.0.0.1:5173',
    ]
    ALLOWED_ORIGINS = os.getenv('CORS_ALLOWED_ORIGINS', '*')
    if ALLOWED_ORIGINS == '*':
        # Use wildcard but also allow specific origins for preflight
        cors_config = {
            'origins': '*',
            'allow_headers': ['Content-Type', 'Authorization', 'X-User-Email', 'X-User-Role', 'X-User-ID', 'X-Requested-With'],
            'methods': ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS'],
            'max_age': 3600
        }
    else:
        origins = [o.strip() for o in ALLOWED_ORIGINS.split(',') if o.strip()]
        origins.extend([o for o in DEFAULT_ORIGINS if o not in origins])
        cors_config = {
            'origins': origins,
            'allow_headers': ['Content-Type', 'Authorization', 'X-User-Email', 'X-User-Role', 'X-User-ID', 'X-Requested-With'],
            'methods': ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS'],
            'supports_credentials': True,
            'send_wildcard': False,
            'max_age': 3600
        }
    CORS(app, resources={r'/api/*': cors_config})

    # ── Global OPTIONS handler for CORS preflight ──────────────────────────────
    @app.before_request
    def handle_preflight():
        if request.method == 'OPTIONS':
            response = app.make_default_options_response()
            origin = request.headers.get('Origin', '')

            # Allow known origins or wildcard
            if ALLOWED_ORIGINS == '*' or origin in DEFAULT_ORIGINS:
                response.headers['Access-Control-Allow-Origin'] = origin if origin else '*'
            else:
                origins_list = [o.strip() for o in ALLOWED_ORIGINS.split(',') if o.strip()]
                if origin in origins_list:
                    response.headers['Access-Control-Allow-Origin'] = origin

            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, PATCH, DELETE, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-User-Email, X-User-Role, X-User-ID, X-Requested-With'
            response.headers['Access-Control-Max-Age'] = '3600'
            return response

    # ── Error Handlers ────────────────────────────────────────────────────────
    @app.errorhandler(Exception)
    def handle_unhandled(exc):
        logger.exception(f'Unhandled exception: {exc}')
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

    @app.errorhandler(404)
    def handle_404(exc):
        return jsonify({'success': False, 'error': 'Endpoint not found'}), 404

    @app.errorhandler(405)
    def handle_405(exc):
        return jsonify({'success': False, 'error': 'Method not allowed'}), 405

    # ── Root Endpoint ─────────────────────────────────────────────────────────
    @app.route('/')
    def index():
        from repositories.cloudscale_repository import get_catalyst_app
        return jsonify({
            'message': 'Railway Ticketing System API v2.0 (CloudScale)',
            'status': 'running',
            'version': '2.0.0-cloudscale',
            'runtime': 'Zoho Catalyst Functions + CloudScale Database',
            'database': 'CloudScale (ZCQL)',
            'endpoints': {
                'health': '/api/health',
                'trains': '/api/trains',
                'bookings': '/api/bookings',
                'stations': '/api/stations',
                'users': '/api/users',
                'ai_search': '/api/ai/search',
                'ai_chat': '/api/ai/chat',
            }
        })

    # ── Health Check ──────────────────────────────────────────────────────────
    @app.route('/api/health')
    def health_check():
        from repositories.cache_manager import cache
        from config import get_ai_config
        from repositories.cloudscale_repository import get_catalyst_app, TABLES

        ai_config = get_ai_config()
        catalyst_ready = get_catalyst_app() is not None

        return jsonify({
            'status': 'healthy' if catalyst_ready else 'initializing',
            'timestamp': datetime.now().isoformat(),
            'version': '2.0.0-cloudscale',
            'runtime': 'Catalyst Functions + CloudScale',
            'cloudscale': {
                'initialized': catalyst_ready,
                'tables_configured': len(TABLES),
            },
            'ai': {
                'gemini_key_set': bool(ai_config['gemini_api_key']),
                'model': ai_config['gemini_model'],
            },
            'cache': cache.stats(),
        }), 200

    # ── Debug Endpoints ───────────────────────────────────────────────────────
    @app.route('/api/debug/system')
    def debug_system():
        import config as cfg
        return jsonify({
            'seat_class_map': cfg.SEAT_CLASS_MAP,
            'berth_cycle': cfg.BERTH_CYCLE,
            'coach_capacity': cfg.COACH_CAPACITY,
            'coach_prefix': cfg.COACH_PREFIX,
            'cancel_min_deduction': cfg.CANCEL_MIN_DEDUCTION,
            'ac_classes': list(cfg.AC_CLASSES),
            'booking_advance_days': cfg.BOOKING_ADVANCE_DAYS,
            'tatkal_open_hour': cfg.TATKAL_OPEN_HOUR,
        })

    @app.route('/api/debug/config')
    def debug_config():
        from repositories.cloudscale_repository import TABLES, get_catalyst_app
        catalyst_ready = get_catalyst_app() is not None
        return jsonify({
            'database': 'CloudScale (ZCQL)',
            'catalyst_initialized': catalyst_ready,
            'tables': TABLES,
            'table_count': len(TABLES),
        })

    # ── Analytics Endpoints ───────────────────────────────────────────────────
    @app.route('/api/analytics/overview', methods=['GET'])
    def analytics_overview():
        from services.analytics_service import analytics_service
        return jsonify({'success': True, 'data': analytics_service.get_overview_stats()}), 200

    @app.route('/api/analytics/trends', methods=['GET'])
    def analytics_trends():
        from services.analytics_service import analytics_service
        days = request.args.get('days', 30, type=int)
        return jsonify({'success': True, 'data': analytics_service.get_booking_trends(days=days)}), 200

    @app.route('/api/analytics/top-trains', methods=['GET'])
    def analytics_top_trains():
        from services.analytics_service import analytics_service
        top_n = request.args.get('n', 10, type=int)
        return jsonify({'success': True, 'data': analytics_service.get_top_trains(top_n=top_n)}), 200

    @app.route('/api/analytics/routes', methods=['GET'])
    def analytics_routes():
        from services.analytics_service import analytics_service
        return jsonify({'success': True, 'data': analytics_service.get_route_popularity()}), 200

    @app.route('/api/analytics/revenue', methods=['GET'])
    def analytics_revenue():
        from services.analytics_service import analytics_service
        return jsonify({'success': True, 'data': analytics_service.get_class_revenue()}), 200

    # ── Register Route Blueprints ─────────────────────────────────────────────
    from routes import register_blueprints
    from routes.admin_reports import admin_reports_bp

    app.register_blueprint(admin_reports_bp, url_prefix='/api')
    register_blueprints(app)

    # ── SPA Catch-All Route (React Client-Side Routing) ─────────────────────────
    # This MUST be registered LAST, after all other routes
    @app.route('/app/')
    @app.route('/app/<path:path>')
    def serve_spa(path=''):
        """
        Serve React SPA for client-side routing.
        For any /app/* request, return index.html to let React Router handle it.
        """
        try:
            import os
            from flask import send_file
            
            build_path = os.path.join(os.path.dirname(__file__), '../catalyst-frontend/build')
            index_path = os.path.join(build_path, 'index.html')
            
            # For asset files with extensions, try to serve directly
            if path and '.' in path.split('/')[-1]:
                asset_path = os.path.join(build_path, path)
                if os.path.isfile(asset_path):
                    try:
                        return send_file(asset_path)
                    except:
                        pass
            
            # For all other /app/* routes, serve index.html (React Router will handle)
            if os.path.isfile(index_path):
                return send_file(index_path, mimetype='text/html')
            else:
                return jsonify({'error': 'index.html not found'}), 404
                
        except Exception as e:
            logger.error(f'SPA route error: {str(e)}')
            return jsonify({'error': 'Unable to serve app'}), 500

    return app


# ══════════════════════════════════════════════════════════════════════════════
#  CATALYST HANDLER
# ══════════════════════════════════════════════════════════════════════════════

# Create Flask app instance (singleton for warm starts)
_flask_app = None

def get_flask_app():
    """Get or create the Flask application (singleton pattern for warm starts)."""
    global _flask_app
    if _flask_app is None:
        _flask_app = create_flask_app()
    return _flask_app


# ══════════════════════════════════════════════════════════════════════════════
#  CATALYST ADVANCED I/O - RUN FLASK DIRECTLY
# ══════════════════════════════════════════════════════════════════════════════

# For Advanced I/O functions, Flask runs directly as a web server
# Catalyst provides the port via X_ZOHO_CATALYST_LISTEN_PORT environment variable

# Create and configure the Flask app
flask_app = create_flask_app()

# CloudScale initialization flag
_cloudscale_initialized = False

# Add middleware to init CloudScale on first request
@flask_app.before_request
def ensure_cloudscale():
    global _cloudscale_initialized
    if not _cloudscale_initialized:
        try:
            # Set Catalyst headers if missing (for local development)
            if not os.getenv('X_ZOHO_CATALYST_PROJECT_ID'):
                os.environ['X_ZOHO_CATALYST_PROJECT_ID'] = '31207000000011084'
            if not os.getenv('X_ZOHO_CATALYST_PROJECT_SECRET_KEY'):
                os.environ['X_ZOHO_CATALYST_PROJECT_SECRET_KEY'] = 'test'

            catalyst_app = zcatalyst_sdk.initialize()
            from repositories.cloudscale_repository import init_catalyst
            init_catalyst(catalyst_app)
            _cloudscale_initialized = True
            logger.info('CloudScale repository initialized on first request')
        except Exception as e:
            logger.exception(f'CloudScale init failed: {e}')
            # Continue without CloudScale

# ══════════════════════════════════════════════════════════════════════════════
#  CATALYST ADVANCED I/O - WSGI HANDLER
# ══════════════════════════════════════════════════════════════════════════════

# For Advanced I/O, expose Flask app as WSGI application
# Catalyst will call this as: handler(environ, start_response)
handler = flask_app

# Local development mode
if __name__ == '__main__':
    port = int(os.getenv('X_ZOHO_CATALYST_LISTEN_PORT', 9000))
    debug_mode = os.getenv('APP_ENVIRONMENT', 'production') == 'development'
    logger.info(f'Railway Ticketing System v2.0 (CloudScale) starting on port {port}')
    flask_app.run(host='0.0.0.0', port=port, debug=debug_mode, threaded=True)
