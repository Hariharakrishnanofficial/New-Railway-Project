"""
Smart Railway Ticketing System - Zoho Catalyst Functions Entry Point

This is the main entry point for the Flask API.
Uses Flask blueprints for modular route organization.
"""

import os
import json
import logging
import inspect
from datetime import datetime
from flask import Flask, jsonify, request
import zcatalyst_sdk

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# Debug: Log environment variables to verify loading
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
logger.info(f"FROM_EMAIL loaded: {os.getenv('CATALYST_FROM_EMAIL', 'NOT_SET')}")
logger.info(f"CORS_ALLOWED_ORIGINS: {os.getenv('CORS_ALLOWED_ORIGINS', 'NOT_SET')}")

try:
    import certifi
except Exception:  # pragma: no cover
    certifi = None


def _get_stable_ca_bundle_path():
    """Return a CA bundle path that remains valid across `.build` cleanups."""
    # Prefer a previously-copied stable bundle if it exists (survives `.build` churn).
    try:
        import tempfile
        stable_path = os.path.join(tempfile.gettempdir(), 'smart_railway_cacert.pem')
        if os.path.exists(stable_path):
            return stable_path
    except Exception:
        pass

    if certifi is None:
        return None

    try:
        candidate = certifi.where()
    except Exception:
        return None

    if not candidate or not os.path.exists(candidate):
        return None

    if '.build' not in str(candidate).lower():
        return candidate

    # `.build` paths can disappear during Catalyst CLI cleanup; copy to a stable temp file.
    try:
        import tempfile
        import shutil

        stable_path = os.path.join(tempfile.gettempdir(), 'smart_railway_cacert.pem')
        src_size = os.path.getsize(candidate)
        dst_ok = os.path.exists(stable_path) and os.path.getsize(stable_path) == src_size
        if not dst_ok:
            shutil.copyfile(candidate, stable_path)

        return stable_path if os.path.exists(stable_path) else candidate
    except Exception:
        return candidate


def _ensure_valid_ca_bundle_env():
    """Ensure requests/curl use a real CA bundle; prefer stable temp copy over `.build`."""
    stable_bundle = _get_stable_ca_bundle_path()

    # Remove invalid paths (missing files)
    for key in ('SSL_CERT_FILE', 'REQUESTS_CA_BUNDLE', 'CURL_CA_BUNDLE'):
        current = os.environ.get(key)
        if current and not os.path.exists(str(current)):
            logger.warning(f"Removing invalid TLS path from {key}: {current}")
            os.environ.pop(key, None)

    if stable_bundle and os.path.exists(stable_bundle):
        for key in ('SSL_CERT_FILE', 'REQUESTS_CA_BUNDLE', 'CURL_CA_BUNDLE'):
            if os.environ.get(key) != stable_bundle:
                os.environ[key] = stable_bundle
        logger.info(f"Using TLS CA bundle: {stable_bundle}")
    else:
        logger.warning("No valid TLS CA bundle found via certifi")


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

    from core.exceptions import RailwayException
    from core.error_tracking import (
        attach_request_id_header,
        ensure_request_id,
        get_request_id,
        record_application_error,
    )

    @app.before_request
    def assign_request_id():
        ensure_request_id()

    @app.after_request
    def attach_request_id(response):
        return attach_request_id_header(response)

    # ── Error Handlers ────────────────────────────────────────────────────────
    @app.errorhandler(RailwayException)
    def handle_railway_exception(exc):
        request_id = get_request_id()
        error_code = exc.error_code or 'APPLICATION_ERROR'
        logger.warning(
            'Handled RailwayException [%s] %s %s (%s)',
            error_code,
            request.method,
            request.path,
            request_id,
        )
        record_application_error(exc, exc.status_code, error_code, exc.message)

        payload = exc.to_response()
        payload.setdefault('error_code', error_code)
        payload['request_id'] = request_id
        return jsonify(payload), exc.status_code

    @app.errorhandler(Exception)
    def handle_unhandled(exc):
        request_id = get_request_id()
        logger.exception('Unhandled exception (%s): %s', request_id, exc)
        record_application_error(exc, 500, 'INTERNAL_SERVER_ERROR', 'Internal server error')
        return jsonify({
            'status': 'error',
            'message': 'Internal server error',
            'error_code': 'INTERNAL_SERVER_ERROR',
            'request_id': request_id,
        }), 500

    @app.errorhandler(404)
    def handle_404(exc):
        request_id = get_request_id()
        return jsonify({
            'status': 'error',
            'message': 'Endpoint not found',
            'error_code': 'ENDPOINT_NOT_FOUND',
            'request_id': request_id,
        }), 404

    @app.errorhandler(405)
    def handle_405(exc):
        request_id = get_request_id()
        return jsonify({
            'status': 'error',
            'message': 'Method not allowed',
            'error_code': 'METHOD_NOT_ALLOWED',
            'request_id': request_id,
        }), 405

    # ── Root Endpoint - API Info ────────────────────────────────────────────
    @app.route('/')
    def index():
        """API information endpoint."""
        return jsonify({
            'status': 'success',
            'message': 'Smart Railway Ticketing System API',
            'version': '2.0.0',
            'client_url': '/app/index.html',
            'endpoints': {
                'health': '/health',
                'auth': '/auth/*',
                'session': '/session/*',
                'users': '/users',
                'trains': '/trains',
                'bookings': '/bookings',
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
        
        @app.route('/debug/env')
        def debug_environment():
            """Debug endpoint to check environment variable loading."""
            from services.otp_service import FROM_EMAIL, APP_NAME, OTP_EXPIRY_MINUTES, CATALYST_AVAILABLE
            
            env_debug = {
                'email_config': {
                    'CATALYST_FROM_EMAIL': os.getenv('CATALYST_FROM_EMAIL', 'NOT_SET'),
                    'APP_NAME': os.getenv('APP_NAME', 'NOT_SET'),
                },
                'otp_config': {
                    'OTP_EXPIRY_MINUTES': os.getenv('OTP_EXPIRY_MINUTES', 'NOT_SET'),
                    'OTP_MAX_ATTEMPTS': os.getenv('OTP_MAX_ATTEMPTS', 'NOT_SET'),
                    'OTP_RESEND_COOLDOWN_SECONDS': os.getenv('OTP_RESEND_COOLDOWN_SECONDS', 'NOT_SET'),
                    'OTP_MAX_RESEND_ATTEMPTS': os.getenv('OTP_MAX_RESEND_ATTEMPTS', 'NOT_SET'),
                },
                'cors_config': {
                    'CORS_ALLOWED_ORIGINS': os.getenv('CORS_ALLOWED_ORIGINS', 'NOT_SET'),
                },
                'session_config': {
                    'SESSION_SECRET': os.getenv('SESSION_SECRET', 'NOT_SET')[:20] + '...' if os.getenv('SESSION_SECRET') else 'NOT_SET',
                    'SESSION_TIMEOUT_HOURS': os.getenv('SESSION_TIMEOUT_HOURS', 'NOT_SET'),
                    'SESSION_COOKIE_SECURE': os.getenv('SESSION_COOKIE_SECURE', 'NOT_SET'),
                },
                'environment_info': {
                    'APP_ENVIRONMENT': os.getenv('APP_ENVIRONMENT', 'NOT_SET'),
                    'env_file_exists': os.path.exists('.env'),
                    'current_working_directory': os.getcwd(),
                },
                'loaded_values_in_service': {
                    'FROM_EMAIL_in_otp_service': FROM_EMAIL,
                    'APP_NAME_in_otp_service': APP_NAME,
                    'OTP_EXPIRY_MINUTES_in_service': OTP_EXPIRY_MINUTES,
                    'CATALYST_AVAILABLE': CATALYST_AVAILABLE,
                }
            }
            
            return jsonify({
                'status': 'success',
                'environment_debug': env_debug,
                'timestamp': datetime.utcnow().isoformat()
            }), 200
        
        @app.route('/debug/create-tables', methods=['POST'])
        def create_missing_tables():
            """Debug endpoint to create missing tables (DEVELOPMENT ONLY)."""
            from repositories.cloudscale_repository import get_catalyst_app

            try:
                catalyst_app = get_catalyst_app()
                if not catalyst_app:
                    return jsonify({'status': 'error', 'message': 'Catalyst not initialized'}), 500
                
                # Create Employee_Invitations table if it doesn't exist
                try:
                    table_service = catalyst_app.datastore()
                    
                    # Check if Employee_Invitations table exists
                    try:
                        table_service.get_table('Employee_Invitations')
                        table_exists = True
                    except:
                        table_exists = False
                    
                    if not table_exists:
                        # Create Employee_Invitations table
                        table_instance = table_service.get_table()
                        table_instance.table_name = 'Employee_Invitations'
                        
                        # Add columns
                        table_instance.add_column('email', 'text')
                        table_instance.add_column('token', 'text')  
                        table_instance.add_column('expires_at', 'datetime')
                        table_instance.add_column('invited_by_user_id', 'bigint')
                        table_instance.add_column('used_at', 'datetime')
                        table_instance.add_column('registered_user_id', 'bigint')
                        table_instance.add_column('created_at', 'datetime')
                        
                        # Create the table
                        created_table = table_service.create(table_instance)
                        
                        return jsonify({
                            'status': 'success',
                            'message': 'Employee_Invitations table created successfully',
                            'table_id': created_table.table_id if hasattr(created_table, 'table_id') else None
                        }), 200
                    else:
                        return jsonify({
                            'status': 'info',
                            'message': 'Employee_Invitations table already exists'
                        }), 200
                
                except Exception as table_error:
                    logger.error(f"Table creation error: {str(table_error)}")
                    return jsonify({
                        'status': 'error',
                        'message': f'Failed to create table: {str(table_error)}'
                    }), 500
            
            except Exception as e:
                logger.error(f"Create tables error: {str(e)}")
                return jsonify({'status': 'error', 'message': str(e)}), 500

        @app.route('/debug/tables')
        def debug_tables():
            """Debug endpoint to check table existence and create missing tables (DEVELOPMENT ONLY)."""
            from repositories.cloudscale_repository import get_catalyst_app, CloudScaleRepository
            from config import TABLES

            try:
                catalyst_app = get_catalyst_app()
                if not catalyst_app:
                    return jsonify({'status': 'error', 'message': 'Catalyst not initialized'}), 500
                
                repo = CloudScaleRepository()
                table_status = {}
                
                for table_key, table_name in TABLES.items():
                    try:
                        actual_name = repo._resolve_table(table_name)
                        
                        exists = False
                        error_msg = None
                        try:
                            # Use datastore to check existence instead of ZCQL
                            datastore = catalyst_app.datastore()
                            datastore.table(actual_name)
                            exists = True
                        except Exception as e:
                            error_msg = str(e)
                            exists = False

                        table_status[table_key] = {
                            'name': actual_name,
                            'exists': exists,
                            'records_count': 0,
                            'check_error': error_msg
                        }
                        
                        if exists:
                            try:
                                # Try to get record count via ZCQL if table exists
                                count = repo.count_records(actual_name)
                                table_status[table_key]['records_count'] = count
                            except:
                                pass
                    except Exception as e:
                        table_status[table_key] = {
                            'name': table_name,
                            'exists': False,
                            'error': str(e)
                        }
                
                return jsonify({
                    'status': 'success',
                    'table_status': table_status,
                    'timestamp': datetime.utcnow().isoformat()
                }), 200
            
            except Exception as e:
                logger.error(f"Debug tables error: {str(e)}")
                return jsonify({'status': 'error', 'message': str(e)}), 500

        @app.route('/debug/columns')
        def debug_columns():
            """Debug endpoint to list table columns (DEVELOPMENT ONLY)."""
            from repositories.cloudscale_repository import get_catalyst_app
            from config import TABLES

            try:
                table_name = request.args.get('table', 'Users')
                # Resolve table name from alias
                actual_table = TABLES.get(table_name.lower(), table_name)
                
                catalyst_app = get_catalyst_app()
                if not catalyst_app:
                    return jsonify({'status': 'error', 'message': 'Catalyst not initialized'}), 500
                
                # Check for table existence first using Datastore
                try:
                    datastore = catalyst_app.datastore()
                    table_obj = datastore.table(actual_table)
                except Exception as e:
                    return jsonify({'status': 'error', 'message': f"Table '{actual_table}' access error: {str(e)}"}), 400

                # Try to get columns from ZCQL (requires at least one record)
                zcql = catalyst_app.zcql()
                result = zcql.execute_query(f"SELECT * FROM {actual_table} LIMIT 1")

                if result:
                    # Provide full data for debugging User setup
                    return jsonify({
                        'status': 'success',
                        'table': actual_table,
                        'data': result,
                        'count': len(result)
                    }), 200
                
                # If no records, try to find the structure via an empty INSERT attempt (hacky but works for schema discovery if it fails with specific error)
                # Alternatively, try to insert a dummy row and delete it, but that's risky.
                # Better: try to use the 'meta' or 'describe' if Catalyst supported it.
                # Since it doesn't, we'll try to guess columns from common knowledge or return a message.
                
                return jsonify({
                    'status': 'success', 
                    'table': actual_table, 
                    'message': f'No records found in {actual_table}',
                    'hint': 'Add at least one record to see columns via this endpoint.'
                }), 200
            except Exception as e:
                return jsonify({'status': 'error', 'message': str(e)}), 500

        @app.route('/debug/force-update-admin', methods=['POST'])
        def debug_force_update_admin():
            """Force update Role and Account_Status of a user to Admin in development."""
            from repositories.cloudscale_repository import CloudScaleRepository
            from config import TABLES
            try:
                data = request.json or {}
                email = data.get('email', 'test@railway.com').lower()
                repo = CloudScaleRepository()
                
                # Update role and status
                update_q = f"UPDATE Users SET Role = 'ADMIN', Account_Status = 'Active' WHERE Email = '{email}'"
                res = repo.execute_query(update_q)
                
                # Verify
                check_q = f"SELECT ROWID, Role, Account_Status FROM Users WHERE Email = '{email}'"
                check_res = repo.execute_query(check_q)

                # Attempt to create Employee record if not existing
                status = "Not Created"
                try:
                    # Execute manual check
                    zcql = repo._get_zcql()
                    q = f"SELECT ROWID FROM Employees WHERE Email = '{email}'"
                    emp_check = zcql.execute_query(q)
                    
                    # If empty list, create
                    if isinstance(emp_check, list) and len(emp_check) == 0:
                        # Create record using direct Datastore to bypass any logic errors
                        ds = repo._get_datastore()
                        table = ds.table(TABLES['employees'])
                        emp_data = {
                            'Full_Name': 'System Admin',
                            'Email': email,
                            'Role': 'Admin',
                            'Account_Status': 'Active',
                            'Password': 'DUMMY_PASSWORD' # Add mandatory field
                        }
                        create_res = table.insert_row(emp_data)
                        status = f"Created: {str(create_res)}"
                    else:
                        status = f"Already Exists (Count: {len(emp_check)})"
                except Exception as e:
                    status = f"Error: {str(e)}"
                
                return jsonify({
                    'status': 'success',
                    'update_result': res,
                    'current_state': check_res,
                    'employee_record': status
                }), 200
            except Exception as e:
                return jsonify({'status': 'error', 'message': str(e)}), 500

        @app.route('/debug/create-admin', methods=['POST'])
        def debug_create_admin():
            """Development-only endpoint to bootstrap admin user."""
            from repositories.cloudscale_repository import CloudScaleRepository
            from config import TABLES
            import bcrypt
            
            try:
                data = request.json or {}
                email = data.get('email', 'admin@railway.com')
                full_name = data.get('full_name', 'System Admin')
                password = data.get('password', 'Admin@123')
                
                repo = CloudScaleRepository()
                
                # 1. Create User
                user_pwd_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                user_data = {
                    'Full_Name': full_name,
                    'Email': email.lower(),
                    'Password': user_pwd_hash,
                    'Role': 'ADMIN',
                    'Account_Status': 'Active'
                }
                
                user_res = repo.create_record(TABLES['users'], user_data)
                if not user_res.get('success'):
                    return jsonify({'status': 'error', 'step': 'user', 'message': user_res.get('error')}), 400
                    
                user_id = user_res['data'].get('ROWID')
                
                # 2. Create Employee
                emp_data = {
                    'Employee_ID': 'ADM-001',
                    'Full_Name': full_name,
                    'Email': email.lower(),
                    'Role': 'Admin',
                    'Invited_By': user_id, # Self-link as first admin
                    'Department': 'Admin', # Added common missing fields
                    'Designation': 'Admin'
                }
                
                emp_res = repo.create_record(TABLES['employees'], emp_data)
                if not emp_res.get('success'):
                    return jsonify({
                        'status': 'error', 
                        'step': 'employee', 
                        'message': emp_res.get('error'),
                        'user_id': user_id,
                        'sent_data': emp_data
                    }), 400
                    
                return jsonify({
                    'status': 'success',
                    'user_id': user_id,
                    'employee_id': emp_res['data'].get('ROWID')
                }), 201
                
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


def _initialize_catalyst_app_for_request(catalyst_request):
    """Initialize Catalyst SDK safely across SDK versions.

    Some SDK versions accept a request context via a named parameter (commonly
    `req` or `request`). Passing the request object positionally is unsafe
    because it can be interpreted as an app name/options and lead to
    INVALID_APP_NAME.
    """
    try:
        sig = inspect.signature(zcatalyst_sdk.initialize)
        params = sig.parameters
        if 'req' in params:
            return zcatalyst_sdk.initialize(req=catalyst_request)
        if 'request' in params:
            return zcatalyst_sdk.initialize(request=catalyst_request)
    except Exception:
        # If signature introspection fails, fall back to no-arg init below.
        pass

    # Preferred fallback for most SDKs
    try:
        return zcatalyst_sdk.initialize()
    except TypeError:
        # Some older helpers use a dict options arg
        return zcatalyst_sdk.initialize({})


@flask_app.before_request
def ensure_cloudscale():
    """Initialize CloudScale repository on first request.

    NOTE: When running under Catalyst (via the `handler(request)` entrypoint), we
    initialize using the Catalyst request object inside the handler.

    This hook is primarily a safety net for direct `python main.py` runs.
    """
    global _cloudscale_initialized
    if not _cloudscale_initialized:
        try:
            _ensure_valid_ca_bundle_env()
            catalyst_app = zcatalyst_sdk.initialize()
            from repositories.cloudscale_repository import init_catalyst
            init_catalyst(catalyst_app)
            _cloudscale_initialized = True
            logger.info('CloudScale repository initialized on first request (no request context)')
        except Exception as e:
            logger.exception(f'CloudScale init failed: {e}')
            # Continue without CloudScale - some endpoints may still work


def handler(request):
    """Zoho Catalyst Basic I/O Function handler.

    IMPORTANT: Initialize the Catalyst Python SDK with the incoming Catalyst
    request so it can use the correct auth context/headers.

    Without request-context initialization, local `catalyst serve` can fall back
    to stale OAuth tokens and ZCQL calls fail with INVALID_TOKEN.
    """
    global _cloudscale_initialized

    # Initialize/refresh CloudScale using the Catalyst request context (preferred)
    # Do this on every request so auth stays in sync with Catalyst CLI/runtime token refreshes.
    try:
        _ensure_valid_ca_bundle_env()

        catalyst_app = _initialize_catalyst_app_for_request(request)

        from repositories.cloudscale_repository import init_catalyst
        init_catalyst(catalyst_app)

        if not _cloudscale_initialized:
            _cloudscale_initialized = True
            logger.info('CloudScale initialized in handler (request context)')
    except Exception as e:
        logger.exception('CloudScale init failed in handler: %s', e)

    def _normalize_path(raw_path: str) -> str:
        """Strip Catalyst function prefixes so Flask sees '/session/login' etc.

        Catalyst often calls functions at:
          /server/<function_name>/<your_route>
          /app/server/<function_name>/<your_route>
        """
        path = raw_path or '/'

        def _strip_server_prefix(p: str) -> str:
            # /server/<fn>/... -> /...
            parts = p.split('/')
            # ['', 'server', '<fn>', ...]
            if len(parts) >= 3 and parts[1] == 'server':
                remainder = '/' + '/'.join(parts[3:]) if len(parts) > 3 else '/'
                return remainder or '/'
            return p

        if path.startswith('/app/server/'):
            return _strip_server_prefix(path[len('/app'):])
        if path.startswith('/server/'):
            return _strip_server_prefix(path)
        return path

    normalized_path = _normalize_path(getattr(request, 'path', '/') or '/')

    # Preferred path: if request already has a WSGI environ, dispatch directly.
    if hasattr(request, 'environ'):
        try:
            environ = dict(request.environ)
            environ['PATH_INFO'] = _normalize_path(environ.get('PATH_INFO', normalized_path) or normalized_path)
            with flask_app.request_context(environ):
                return flask_app.full_dispatch_request()
        except Exception as e:
            logger.exception(f'Request handling error (environ dispatch): {e}')
            from flask import make_response, jsonify
            from core.error_tracking import get_request_id, record_application_error
            request_id = get_request_id()
            record_application_error(e, 500, 'INTERNAL_SERVER_ERROR', 'Internal server error')
            return make_response(jsonify({
                'status': 'error',
                'message': 'Internal server error',
                'error_code': 'INTERNAL_SERVER_ERROR',
                'request_id': request_id,
            }), 500)

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
            try:
                candidate = getattr(request, attr)
                candidate = candidate() if callable(candidate) else candidate
                if candidate not in (None, b'', ''):
                    body_source = candidate
                    break
            except Exception:
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
    try:
        headers = dict(request.headers)
    except Exception:
        headers = {}

    content_type = getattr(request, 'content_type', None) or headers.get('Content-Type')

    with flask_app.test_request_context(
        path=normalized_path,
        method=getattr(request, 'method', 'GET'),
        headers=headers,
        data=body_bytes,
        content_type=content_type
    ):
        try:
            # Dispatch the request through Flask
            response = flask_app.full_dispatch_request()
            return response
        except Exception as e:
            logger.exception(f'Request handling error: {e}')
            from flask import make_response, jsonify
            from core.error_tracking import get_request_id, record_application_error
            request_id = get_request_id()
            record_application_error(e, 500, 'INTERNAL_SERVER_ERROR', 'Internal server error')
            return make_response(jsonify({
                'status': 'error',
                'message': 'Internal server error',
                'error_code': 'INTERNAL_SERVER_ERROR',
                'request_id': request_id,
            }), 500)


# ══════════════════════════════════════════════════════════════════════════════
#  LOCAL DEVELOPMENT MODE
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    port = int(os.getenv('PORT', 9000))
    debug_mode = os.getenv('APP_ENVIRONMENT', 'production') == 'development'
    logger.info(f'Smart Railway API v2.0 starting on port {port}')
    flask_app.run(host='0.0.0.0', port=port, debug=debug_mode, threaded=True)
