"""
Smart Railway Ticketing System - Zoho Catalyst Functions Entry Point

This is the main entry point for the Flask API.
Uses Flask blueprints for modular route organization.
"""

import os
import logging
from datetime import datetime
from flask import Flask, jsonify, request
import zcatalyst_sdk

# Fix SSL certificate issues for local development
try:
    import certifi
    os.environ['SSL_CERT_FILE'] = certifi.where()
    os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()
except ImportError:
    pass

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
    from config import DEFAULT_ALLOWED_ORIGINS

    @app.after_request
    def add_cors_headers(response):
        origin = request.headers.get('Origin', '')
        allowed_origins = os.getenv('CORS_ALLOWED_ORIGINS', '*')

        if allowed_origins == '*':
            response.headers['Access-Control-Allow-Origin'] = '*'
        elif origin in DEFAULT_ALLOWED_ORIGINS:
            response.headers['Access-Control-Allow-Origin'] = origin
        elif origin:
            origins_list = [o.strip() for o in allowed_origins.split(',') if o.strip()]
            if origin in origins_list:
                response.headers['Access-Control-Allow-Origin'] = origin

        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, PATCH, DELETE, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With'
        response.headers['Access-Control-Max-Age'] = '3600'
        return response

    # ── Global OPTIONS handler for CORS preflight ──────────────────────────────
    @app.before_request
    def handle_preflight():
        if request.method == 'OPTIONS':
            response = app.make_default_options_response()
            return response

    # ── Error Handlers ────────────────────────────────────────────────────────
    @app.errorhandler(Exception)
    def handle_unhandled(exc):
        logger.exception(f'Unhandled exception: {exc}')
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500

    @app.errorhandler(404)
    def handle_404(exc):
        return jsonify({'status': 'error', 'message': 'Endpoint not found'}), 404

    @app.errorhandler(405)
    def handle_405(exc):
        return jsonify({'status': 'error', 'message': 'Method not allowed'}), 405

    # ── Root Endpoint ─────────────────────────────────────────────────────────
    @app.route('/')
    def index():
        return jsonify({
            'status': 'success',
            'message': 'Smart Railway Ticketing System API',
            'version': '2.0.0',
            'runtime': 'Zoho Catalyst Functions + CloudScale Database',
            'endpoints': {
                'health': '/health',
                'auth': '/auth/*',
                'users': '/users',
                'trains': '/trains',
                'stations': '/stations',
                'bookings': '/bookings',
                'fares': '/fares',
            }
        })

    # ── Health Check ──────────────────────────────────────────────────────────
    @app.route('/health')
    def health_check():
        from repositories.cloudscale_repository import get_catalyst_app
        from repositories.cache_manager import cache

        catalyst_ready = get_catalyst_app() is not None

        return jsonify({
            'status': 'healthy' if catalyst_ready else 'initializing',
            'timestamp': datetime.utcnow().isoformat(),
            'version': '2.0.0',
            'runtime': 'Catalyst Functions + CloudScale',
            'cloudscale': {
                'initialized': catalyst_ready,
            },
            'cache': cache.stats(),
        }), 200

    # ── Debug Endpoints ───────────────────────────────────────────────────────
    @app.route('/debug/columns')
    def debug_columns():
        """Debug endpoint to list table columns."""
        from repositories.cloudscale_repository import get_catalyst_app

        try:
            catalyst_app = get_catalyst_app()
            if not catalyst_app:
                return jsonify({'status': 'error', 'message': 'Catalyst not initialized'}), 500

            zcql = catalyst_app.zcql()
            result = zcql.execute_query("SELECT * FROM Users LIMIT 1")

            if result:
                columns = list(result[0]['Users'].keys())
                return jsonify({'status': 'success', 'columns': columns}), 200
            else:
                return jsonify({'status': 'success', 'message': 'No users found'}), 200

        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)}), 500

    @app.route('/debug/config')
    def debug_config():
        """Debug endpoint to show configuration."""
        from config import TABLES
        from repositories.cloudscale_repository import get_catalyst_app

        catalyst_ready = get_catalyst_app() is not None
        return jsonify({
            'database': 'CloudScale (ZCQL)',
            'catalyst_initialized': catalyst_ready,
            'tables': list(TABLES.keys()),
            'table_count': len(TABLES),
        })

    # ── Register Route Blueprints ─────────────────────────────────────────────
    from routes import register_blueprints
    register_blueprints(app)

    return app


# ══════════════════════════════════════════════════════════════════════════════
#  CATALYST HANDLER - Basic I/O Function
# ══════════════════════════════════════════════════════════════════════════════

# Create Flask app instance
flask_app = create_flask_app()

# CloudScale initialization flag
_cloudscale_initialized = False


@flask_app.before_request
def ensure_cloudscale():
    """Initialize CloudScale repository on first request."""
    global _cloudscale_initialized
    if not _cloudscale_initialized:
        try:
            catalyst_app = zcatalyst_sdk.initialize()
            from repositories.cloudscale_repository import init_catalyst
            init_catalyst(catalyst_app)
            _cloudscale_initialized = True
            logger.info('CloudScale repository initialized on first request')
        except Exception as e:
            logger.exception(f'CloudScale init failed: {e}')
            # Continue without CloudScale - some endpoints may still work


def handler(request):
    """
    Zoho Catalyst Basic I/O Function handler.
    Routes requests through Flask app.
    """
    global _cloudscale_initialized

    # Initialize CloudScale if not already done
    if not _cloudscale_initialized:
        try:
            catalyst_app = zcatalyst_sdk.initialize()
            from repositories.cloudscale_repository import init_catalyst
            init_catalyst(catalyst_app)
            _cloudscale_initialized = True
        except Exception as e:
            logger.error(f'CloudScale init failed in handler: {e}')

    # Use Flask test client to handle the request
    with flask_app.test_request_context(
        path=request.path,
        method=request.method,
        headers=dict(request.headers),
        data=request.get_data(),
        content_type=request.content_type
    ):
        try:
            # Dispatch the request through Flask
            response = flask_app.full_dispatch_request()
            return response
        except Exception as e:
            logger.exception(f'Request handling error: {e}')
            from flask import make_response, jsonify
            return make_response(jsonify({'status': 'error', 'message': 'Internal server error'}), 500)


# ══════════════════════════════════════════════════════════════════════════════
#  LOCAL DEVELOPMENT MODE
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    port = int(os.getenv('PORT', 9000))
    debug_mode = os.getenv('APP_ENVIRONMENT', 'production') == 'development'
    logger.info(f'Smart Railway API v2.0 starting on port {port}')
    flask_app.run(host='0.0.0.0', port=port, debug=debug_mode, threaded=True)
