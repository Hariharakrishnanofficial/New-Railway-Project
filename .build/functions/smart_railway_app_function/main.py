"""
Smart Railway Ticketing System - Zoho Catalyst Functions Entry Point

This is the main entry point for the Flask API.
Uses Flask blueprints for modular route organization.
"""

import os
import json
import logging
from datetime import datetime
from flask import Flask, jsonify, request
import zcatalyst_sdk

try:
    import certifi
except Exception:  # pragma: no cover
    certifi = None


def _ensure_valid_ca_bundle_env():
    """Ensure requests/curl use a real CA bundle, not stale .build paths."""
    valid_bundle = None
    if certifi is not None:
        try:
            bundle_candidate = certifi.where()
            if bundle_candidate and os.path.exists(bundle_candidate):
                valid_bundle = bundle_candidate
        except Exception:
            valid_bundle = None

    # Remove any stale/invalid paths (especially from .build folder)
    for key in ('SSL_CERT_FILE', 'REQUESTS_CA_BUNDLE', 'CURL_CA_BUNDLE'):
        current = os.environ.get(key)
        if current:
            # Check if path exists, or if it points to .build (often stale)
            if not os.path.exists(current) or '.build' in current:
                os.environ.pop(key, None)

    if valid_bundle:
        os.environ['SSL_CERT_FILE'] = valid_bundle
        os.environ['REQUESTS_CA_BUNDLE'] = valid_bundle
        os.environ['CURL_CA_BUNDLE'] = valid_bundle


_ensure_valid_ca_bundle_env()

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════════════════════
#  FLASK APPLICATION SETUP
# ══════════════════════════════════════════════════════════════════════════════

def create_flask_app():
    """Create and configure the Flask application with all routes."""

    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'change-me-in-production')

    # ── HTTPS Enforcement (PRODUCTION ONLY) ───────────────────────────────
    from core.https_enforcer import create_https_enforcer
    create_https_enforcer(app)

    # ── Security Headers ──────────────────────────────────────────────────
    from core.security_headers import create_security_headers
    security_config = {
        'x_frame_options': 'DENY',
        'referrer_policy': 'strict-origin-when-cross-origin',
        'permissions_policy': 'geolocation=(), microphone=(), camera=(), payment=()',
        'hsts': 'max-age=31536000; includeSubDomains',
    }
    create_security_headers(app, security_config)

    # ── CORS Configuration (HARDENED) ─────────────────────────────────────
    from config import DEFAULT_ALLOWED_ORIGINS
    from core.cors_config import create_cors_middleware
    
    # Create CORS middleware with strict validation
    create_cors_middleware(app, DEFAULT_ALLOWED_ORIGINS)

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

    # ── Debug Endpoints (DEVELOPMENT ONLY) ────────────────────────────────
    # Only register debug endpoints in development environment
    if os.getenv('APP_ENVIRONMENT') == 'development':
        
        @app.route('/debug/columns')
        def debug_columns():
            """Debug endpoint to list table columns (DEVELOPMENT ONLY)."""
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
            """Debug endpoint to show configuration (DEVELOPMENT ONLY)."""
            from config import TABLES
            from repositories.cloudscale_repository import get_catalyst_app

            catalyst_ready = get_catalyst_app() is not None
            return jsonify({
                'database': 'CloudScale (ZCQL)',
                'catalyst_initialized': catalyst_ready,
                'tables': list(TABLES.keys()),
                'table_count': len(TABLES),
                'environment': os.getenv('APP_ENVIRONMENT', 'unknown')
            })
        
        @app.route('/debug/clear-rate-limits', methods=['POST'])
        def clear_rate_limits():
            """Clear all rate limit counters (DEVELOPMENT ONLY)."""
            from core.security import _rate_store, _rate_lock
            
            with _rate_lock:
                cleared_count = len(_rate_store)
                _rate_store.clear()
            
            return jsonify({
                'status': 'success',
                'message': f'Cleared {cleared_count} rate limit entries',
                'note': 'This endpoint is only available in development mode'
            }), 200
        
        logger.info("Debug endpoints registered (DEVELOPMENT MODE)")
    
    else:
        # Production: Return 404 for debug endpoints
        @app.route('/debug/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
        def debug_not_available(path):
            """Debug endpoints not available in production."""
            logger.warning(f"Attempt to access debug endpoint in production: /debug/{path}")
            return jsonify({
                'status': 'error',
                'message': 'Not found'
            }), 404

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
            _ensure_valid_ca_bundle_env()
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
            _ensure_valid_ca_bundle_env()
            catalyst_app = zcatalyst_sdk.initialize()
            from repositories.cloudscale_repository import init_catalyst
            init_catalyst(catalyst_app)
            _cloudscale_initialized = True
        except Exception as e:
            logger.error(f'CloudScale init failed in handler: {e}')

    # Preferred path: if request already has a WSGI environ, dispatch directly.
    if hasattr(request, 'environ'):
        try:
            with flask_app.request_context(request.environ):
                return flask_app.full_dispatch_request()
        except Exception as e:
            logger.exception(f'Request handling error (environ dispatch): {e}')
            from flask import make_response, jsonify
            return make_response(jsonify({'status': 'error', 'message': 'Internal server error'}), 500)

    # Normalize body extraction across Catalyst request object variants.
    body_bytes = b''
    body_source = None

    try:
        body_source = request.get_data() if hasattr(request, 'get_data') else None
    except Exception:
        body_source = None

    if body_source in (None, b'', ''):
        # Some Catalyst runtimes expose parsed JSON rather than raw bytes.
        for attr in ('get_json', 'json'):
            if not hasattr(request, attr):
                continue
            try:
                candidate = getattr(request, attr)
                candidate = candidate() if callable(candidate) else candidate
                if candidate not in (None, b'', ''):
                    body_source = candidate
                    break
            except Exception:
                continue

    if body_source in (None, b'', ''):
        for attr in ('body', 'data', 'raw_body', 'content', 'payload'):
            if not hasattr(request, attr):
                continue

    if body_source in (None, b'', ''):
        for attr in ('req_body', 'request_body', 'post_body', 'rawBody', 'requestBody'):
            if not hasattr(request, attr):
                continue
            try:
                candidate = getattr(request, attr)
                candidate = candidate() if callable(candidate) else candidate
                if candidate not in (None, b'', ''):
                    body_source = candidate
                    break
            except Exception:
                continue

    if body_source in (None, b'', ''):
        # Last-resort heuristic: probe request attributes for body-like values.
        for attr in dir(request):
            if attr.startswith('__'):
                continue
            low = attr.lower()
            if not any(k in low for k in ('body', 'data', 'json', 'payload', 'content', 'raw', 'post')):
                continue
            try:
                candidate = getattr(request, attr)
                candidate = candidate() if callable(candidate) else candidate
                if candidate not in (None, b'', ''):
                    body_source = candidate
                    break
            except Exception:
                continue
            try:
                candidate = getattr(request, attr)
                candidate = candidate() if callable(candidate) else candidate
                if candidate not in (None, b'', ''):
                    body_source = candidate
                    break
            except Exception:
                continue

    if isinstance(body_source, (dict, list)):
        body_bytes = json.dumps(body_source).encode('utf-8')
    elif isinstance(body_source, str):
        body_bytes = body_source.encode('utf-8')
    elif isinstance(body_source, (bytes, bytearray)):
        body_bytes = bytes(body_source)
    elif hasattr(body_source, 'read'):
        try:
            stream_data = body_source.read()
            if isinstance(stream_data, str):
                body_bytes = stream_data.encode('utf-8')
            elif isinstance(stream_data, (bytes, bytearray)):
                body_bytes = bytes(stream_data)
        except Exception:
            body_bytes = b''

    # Use Flask test client to handle the request
    with flask_app.test_request_context(
        path=request.path,
        method=request.method,
        headers=dict(request.headers),
        data=body_bytes,
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
