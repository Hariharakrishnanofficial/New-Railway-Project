import logging
import base64
import json
import ssl
import os
from datetime import datetime, timedelta
from flask import Request, make_response, jsonify
import zcatalyst_sdk
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

# Fix SSL certificate issues for local development
import certifi
os.environ['SSL_CERT_FILE'] = certifi.where()
os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()

ph = PasswordHasher()

# Simple secret for token signing (in production, use environment variable)
TOKEN_SECRET = "smart_railway_secret_key_2026"

def create_token(user_id, email, role, expires_days=7):
    """Create a base64 encoded token with user info and expiry"""
    expires_at = (datetime.utcnow() + timedelta(days=expires_days)).isoformat()
    token_data = {
        'user_id': str(user_id),
        'email': email,
        'role': role,
        'expires_at': expires_at,
        'secret': TOKEN_SECRET
    }
    token_json = json.dumps(token_data)
    return base64.urlsafe_b64encode(token_json.encode()).decode()

def decode_token(token):
    """Decode and validate a token"""
    try:
        token_json = base64.urlsafe_b64decode(token.encode()).decode()
        token_data = json.loads(token_json)

        if token_data.get('secret') != TOKEN_SECRET:
            return None

        expires_at = datetime.fromisoformat(token_data['expires_at'])
        if datetime.utcnow() > expires_at:
            return None

        return token_data
    except Exception:
        return None

def handler(request: Request):
    app = zcatalyst_sdk.initialize()
    logger = logging.getLogger()
    path = request.path
    method = request.method

    def json_response(data, status=200):
        response = make_response(jsonify(data), status)
        response.headers['Content-Type'] = 'application/json'
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response

    def get_auth_token(req):
        auth_header = req.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            return auth_header[7:]
        return None

    try:
        # ========== AUTH: REGISTER ==========
        if path == "/auth/register" and method == "POST":
            req_data = request.get_json()
            logger.info(f"Register request data: {req_data}")

            full_name = req_data.get('fullName', '').strip()
            email = req_data.get('email', '').strip().lower()
            password = req_data.get('password', '')
            phone_number = req_data.get('phoneNumber', '').strip()

            if not full_name or not email or not password:
                return json_response({
                    'status': 'error',
                    'message': 'Full name, email, and password are required'
                }, 400)

            if len(password) < 8:
                return json_response({
                    'status': 'error',
                    'message': 'Password must be at least 8 characters'
                }, 400)

            # Check if email already exists
            try:
                zcql = app.zcql()
                existing = zcql.execute_query(
                    f"SELECT ROWID FROM Users WHERE Email = '{email}'"
                )
                if existing:
                    return json_response({
                        'status': 'error',
                        'message': 'Email already registered'
                    }, 409)
            except Exception as e:
                logger.warning(f"Check existing user query failed: {e}")
                # Continue anyway - table might not exist yet

            # Hash password with Argon2
            hashed_password = ph.hash(password)

            # Start with MINIMAL columns - only what definitely exists
            # We'll try different column name variations
            user_data_attempts = [
                # Attempt 1: Underscore naming (from schema doc)
                {
                    'Full_Name': full_name,
                    'Email': email,
                    'Password': hashed_password,
                    'Role': 'User',
                    'Account_Status': 'Active'
                },
                # Attempt 2: Hyphen naming (from reference app.py)
                {
                    'Full-Name': full_name,
                    'Email': email,
                    'Password': hashed_password,
                    'Role': 'User',
                    'Account_Status': 'Active'
                },
                # Attempt 3: Minimal - just Email and Password
                {
                    'Email': email,
                    'Password': hashed_password
                }
            ]

            logger.info(f"Attempting to create user for: {email}")

            table = app.datastore().table('Users')
            row = None
            last_error = None

            for i, user_data in enumerate(user_data_attempts):
                try:
                    logger.info(f"Attempt {i+1}: Using columns {list(user_data.keys())}")
                    row = table.insert_row(user_data)
                    logger.info(f"Success with attempt {i+1}!")
                    break
                except Exception as e:
                    last_error = str(e)
                    logger.warning(f"Attempt {i+1} failed: {last_error}")
                    continue

            if row:
                session_token = create_token(row['ROWID'], email, 'User')

                return json_response({
                    'status': 'success',
                    'message': 'Registration successful',
                    'data': {
                        'user': {
                            'id': row['ROWID'],
                            'fullName': full_name,
                            'email': email,
                            'phoneNumber': phone_number,
                            'role': 'User',
                            'accountStatus': 'Active'
                        },
                        'token': session_token
                    }
                }, 201)
            else:
                return json_response({
                    'status': 'error',
                    'message': f'Registration failed after all attempts: {last_error}'
                }, 500)

        # ========== AUTH: LOGIN ==========
        elif path == "/auth/login" and method == "POST":
            req_data = request.get_json()

            email = req_data.get('email', '').strip().lower()
            password = req_data.get('password', '')

            if not email or not password:
                return json_response({
                    'status': 'error',
                    'message': 'Email and password are required'
                }, 400)

            try:
                zcql = app.zcql()
                # Try to get user - use backticks for column names with special chars
                result = zcql.execute_query(
                    f"SELECT * FROM Users WHERE Email = '{email}'"
                )

                if not result:
                    return json_response({
                        'status': 'error',
                        'message': 'Invalid email or password'
                    }, 401)

                user_row = result[0]['Users']
                stored_hash = user_row.get('Password', '')

                # Verify password with Argon2
                try:
                    ph.verify(stored_hash, password)
                except VerifyMismatchError:
                    return json_response({
                        'status': 'error',
                        'message': 'Invalid email or password'
                    }, 401)

                # Check account status
                account_status = user_row.get('Account_Status', 'Active')
                if account_status == 'Blocked':
                    return json_response({
                        'status': 'error',
                        'message': 'Account is blocked. Contact support.'
                    }, 403)

                if account_status == 'Suspended':
                    return json_response({
                        'status': 'error',
                        'message': 'Account is suspended. Contact support.'
                    }, 403)

                # Create stateless token
                role = user_row.get('Role', 'User')
                session_token = create_token(user_row['ROWID'], email, role)

                # Build user response - handle both naming conventions
                user_response = {
                    'id': user_row['ROWID'],
                    'fullName': user_row.get('Full_Name') or user_row.get('Full-Name', ''),
                    'email': user_row.get('Email', ''),
                    'phoneNumber': user_row.get('Phone_Number') or user_row.get('Phone-Number', ''),
                    'role': role,
                    'accountStatus': account_status,
                    'aadharVerified': user_row.get('Aadhar_Verified') == 'true',
                    'dateOfBirth': user_row.get('Date_of_Birth') or user_row.get('Date-of-Birth', ''),
                    'idProofType': user_row.get('ID_Proof_Type') or user_row.get('ID-Proof-Type', ''),
                    'idProofNumber': user_row.get('ID_Proof_Number') or user_row.get('ID-Proof-Number', ''),
                    'address': user_row.get('Address', '')
                }

                return json_response({
                    'status': 'success',
                    'message': 'Login successful',
                    'data': {
                        'user': user_response,
                        'token': session_token
                    }
                }, 200)

            except Exception as e:
                logger.error(f"Login error: {e}")
                return json_response({
                    'status': 'error',
                    'message': 'Login failed. Please try again.'
                }, 500)

        # ========== AUTH: LOGOUT ==========
        elif path == "/auth/logout" and method == "POST":
            return json_response({
                'status': 'success',
                'message': 'Logged out successfully'
            }, 200)

        # ========== AUTH: VALIDATE SESSION ==========
        elif path == "/auth/validate" and method == "GET":
            token = get_auth_token(request)

            if not token:
                return json_response({
                    'status': 'error',
                    'message': 'No token provided'
                }, 401)

            token_data = decode_token(token)
            if not token_data:
                return json_response({
                    'status': 'error',
                    'message': 'Invalid or expired session'
                }, 401)

            try:
                zcql = app.zcql()
                result = zcql.execute_query(
                    f"SELECT * FROM Users WHERE ROWID = {token_data['user_id']}"
                )

                if not result:
                    return json_response({
                        'status': 'error',
                        'message': 'User not found'
                    }, 401)

                user_row = result[0]['Users']
                account_status = user_row.get('Account_Status', 'Active')

                if account_status != 'Active':
                    return json_response({
                        'status': 'error',
                        'message': 'Account is not active'
                    }, 403)

                user_response = {
                    'id': user_row['ROWID'],
                    'fullName': user_row.get('Full_Name') or user_row.get('Full-Name', ''),
                    'email': user_row.get('Email', ''),
                    'phoneNumber': user_row.get('Phone_Number') or user_row.get('Phone-Number', ''),
                    'role': user_row.get('Role', 'User'),
                    'accountStatus': account_status,
                    'aadharVerified': user_row.get('Aadhar_Verified') == 'true',
                    'dateOfBirth': user_row.get('Date_of_Birth') or user_row.get('Date-of-Birth', ''),
                    'idProofType': user_row.get('ID_Proof_Type') or user_row.get('ID-Proof-Type', ''),
                    'idProofNumber': user_row.get('ID_Proof_Number') or user_row.get('ID-Proof-Number', ''),
                    'address': user_row.get('Address', '')
                }

                return json_response({
                    'status': 'success',
                    'data': {
                        'user': user_response
                    }
                }, 200)

            except Exception as e:
                logger.error(f"Validate session error: {e}")
                return json_response({
                    'status': 'error',
                    'message': 'Session validation failed'
                }, 500)

        # ========== AUTH: UPDATE PROFILE ==========
        elif path == "/auth/profile" and method == "PUT":
            token = get_auth_token(request)

            if not token:
                return json_response({
                    'status': 'error',
                    'message': 'Authentication required'
                }, 401)

            token_data = decode_token(token)
            if not token_data:
                return json_response({
                    'status': 'error',
                    'message': 'Invalid session'
                }, 401)

            try:
                req_data = request.get_json()
                update_data = {'ROWID': token_data['user_id']}

                # Map fields - try underscore first, then hyphen
                field_mapping = {
                    'fullName': ['Full_Name', 'Full-Name'],
                    'phoneNumber': ['Phone_Number', 'Phone-Number'],
                    'dateOfBirth': ['Date_of_Birth', 'Date-of-Birth'],
                    'idProofType': ['ID_Proof_Type', 'ID-Proof-Type'],
                    'idProofNumber': ['ID_Proof_Number', 'ID-Proof-Number'],
                    'address': ['Address']
                }

                for key, db_fields in field_mapping.items():
                    if key in req_data:
                        update_data[db_fields[0]] = req_data[key]

                table = app.datastore().table('Users')
                updated = table.update_row(update_data)

                return json_response({
                    'status': 'success',
                    'message': 'Profile updated successfully'
                }, 200)

            except Exception as e:
                logger.error(f"Profile update error: {e}")
                return json_response({
                    'status': 'error',
                    'message': 'Failed to update profile'
                }, 500)

        # ========== AUTH: CHANGE PASSWORD ==========
        elif path == "/auth/change-password" and method == "POST":
            token = get_auth_token(request)

            if not token:
                return json_response({
                    'status': 'error',
                    'message': 'Authentication required'
                }, 401)

            token_data = decode_token(token)
            if not token_data:
                return json_response({
                    'status': 'error',
                    'message': 'Invalid session'
                }, 401)

            try:
                zcql = app.zcql()
                result = zcql.execute_query(
                    f"SELECT ROWID, Password, Email, Role FROM Users WHERE ROWID = {token_data['user_id']}"
                )

                if not result:
                    return json_response({
                        'status': 'error',
                        'message': 'User not found'
                    }, 401)

                user_row = result[0]['Users']
                req_data = request.get_json()

                current_password = req_data.get('currentPassword', '')
                new_password = req_data.get('newPassword', '')

                if not current_password or not new_password:
                    return json_response({
                        'status': 'error',
                        'message': 'Current and new passwords are required'
                    }, 400)

                if len(new_password) < 8:
                    return json_response({
                        'status': 'error',
                        'message': 'New password must be at least 8 characters'
                    }, 400)

                try:
                    ph.verify(user_row.get('Password', ''), current_password)
                except VerifyMismatchError:
                    return json_response({
                        'status': 'error',
                        'message': 'Current password is incorrect'
                    }, 401)

                new_hashed = ph.hash(new_password)

                table = app.datastore().table('Users')
                table.update_row({
                    'ROWID': user_row['ROWID'],
                    'Password': new_hashed
                })

                new_token = create_token(
                    user_row['ROWID'],
                    user_row.get('Email'),
                    user_row.get('Role', 'User')
                )

                return json_response({
                    'status': 'success',
                    'message': 'Password changed successfully',
                    'data': {
                        'token': new_token
                    }
                }, 200)

            except Exception as e:
                logger.error(f"Change password error: {e}")
                return json_response({
                    'status': 'error',
                    'message': 'Failed to change password'
                }, 500)

        # ========== DEBUG: LIST TABLE COLUMNS ==========
        elif path == "/debug/columns" and method == "GET":
            try:
                zcql = app.zcql()
                result = zcql.execute_query("SELECT * FROM Users LIMIT 1")
                if result:
                    columns = list(result[0]['Users'].keys())
                    return json_response({
                        'status': 'success',
                        'columns': columns
                    }, 200)
                else:
                    return json_response({
                        'status': 'success',
                        'message': 'No users found, cannot determine columns'
                    }, 200)
            except Exception as e:
                return json_response({
                    'status': 'error',
                    'message': str(e)
                }, 500)

        # ========== HEALTH CHECK ==========
        elif path == "/" and method == "GET":
            return json_response({
                'status': 'success',
                'message': 'Smart Railway API is running',
                'version': '1.0.0'
            }, 200)

        else:
            return json_response({
                'status': 'error',
                'message': f'Unknown path: {path}'
            }, 404)

    except Exception as err:
        logger.error(f"Unhandled exception: {err}")
        return json_response({
            'status': 'error',
            'message': 'Internal server error'
        }, 500)
