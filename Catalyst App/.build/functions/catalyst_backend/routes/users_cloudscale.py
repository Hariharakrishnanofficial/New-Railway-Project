"""
Users CloudScale Routes — CRUD operations following Catalyst CloudScale pattern.
Based on: only reference/app.py sample code

CloudScale Table: Users
Fields: Full_Name, Email, Password, Phone_Number, Role, Account_Status,
        Aadhar_Verified, Date_of_Birth, ID_Proof_Type, ID_Proof_Number,
        Address, Last_Login, Created_Time, Modified_Time
"""

import logging
from flask import Blueprint, request, jsonify
from datetime import datetime
import zcatalyst_sdk

from core.security import require_admin, hash_password

logger = logging.getLogger(__name__)
users_cloudscale_bp = Blueprint('users_cloudscale', __name__)

# ══════════════════════════════════════════════════════════════════════════════
#  CLOUDSCALE TABLE CONFIGURATION
# ══════════════════════════════════════════════════════════════════════════════

TABLE_NAME = 'Users'

# Field mapping: API field name -> CloudScale column name
FIELDS = {
    'fullName': 'Full_Name',
    'email': 'Email',
    'password': 'Password',
    'phoneNumber': 'Phone_Number',
    'role': 'Role',
    'accountStatus': 'Account_Status',
    'aadharVerified': 'Aadhar_Verified',
    'dateOfBirth': 'Date_of_Birth',
    'idProofType': 'ID_Proof_Type',
    'idProofNumber': 'ID_Proof_Number',
    'address': 'Address',
    'lastLogin': 'Last_Login',
}

# ══════════════════════════════════════════════════════════════════════════════
#  HELPER FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════════

def _get_catalyst_app():
    """Initialize and return Catalyst app instance."""
    try:
        return zcatalyst_sdk.initialize()
    except Exception as e:
        logger.error(f"Failed to initialize Catalyst SDK: {e}")
        return None


def _format_user_response(row):
    """Format database row to API response format."""
    return {
        'id': row.get('ROWID'),
        'fullName': row.get('Full_Name', ''),
        'email': row.get('Email', ''),
        'phoneNumber': row.get('Phone_Number', ''),
        'role': row.get('Role', 'User'),
        'accountStatus': row.get('Account_Status', 'Active'),
        'aadharVerified': row.get('Aadhar_Verified', 'false'),
        'dateOfBirth': row.get('Date_of_Birth', ''),
        'idProofType': row.get('ID_Proof_Type', ''),
        'idProofNumber': row.get('ID_Proof_Number', ''),
        'address': row.get('Address', ''),
        'lastLogin': row.get('Last_Login', ''),
        'createdTime': row.get('Created_Time', ''),
        'modifiedTime': row.get('Modified_Time', ''),
    }


def _is_true(val):
    """Convert various boolean representations to 'true'/'false' string."""
    if isinstance(val, bool):
        return 'true' if val else 'false'
    if isinstance(val, str):
        return 'true' if val.lower() in ('true', '1', 'yes', 'active') else 'false'
    if isinstance(val, (int, float)):
        return 'true' if val != 0 else 'false'
    return 'false'


# ══════════════════════════════════════════════════════════════════════════════
#  CREATE USER (POST /api/users)
# ══════════════════════════════════════════════════════════════════════════════

@users_cloudscale_bp.route('/api/users', methods=['POST'])
def create_user():
    """
    Create a new user record.

    Request Body:
    {
        "fullName": "John Doe",
        "email": "john@example.com",
        "password": "secret123",
        "phoneNumber": "9876543210",
        "role": "User",
        "accountStatus": "Active",
        "aadharVerified": false,
        "dateOfBirth": "01-Jan-1990",
        "idProofType": "Aadhaar",
        "idProofNumber": "1234-5678-9012",
        "address": "123 Main St, City"
    }
    """
    app = _get_catalyst_app()
    if not app:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500

    req_data = request.get_json() or {}

    # Validate required fields
    full_name = (req_data.get('fullName') or req_data.get('Full_Name') or '').strip()
    email = (req_data.get('email') or req_data.get('Email') or '').strip().lower()
    password = req_data.get('password') or req_data.get('Password') or ''

    if not full_name or not email:
        return jsonify({
            'status': 'error',
            'message': 'Missing required fields: fullName and email are required'
        }), 400

    # Build user data for CloudScale
    user_data = {
        'Full_Name': full_name,
        'Email': email,
        'Password': hash_password(password) if password else '',
        'Phone_Number': req_data.get('phoneNumber') or req_data.get('Phone_Number') or '',
        'Role': req_data.get('role') or req_data.get('Role') or 'User',
        'Account_Status': req_data.get('accountStatus') or req_data.get('Account_Status') or 'Active',
        'Aadhar_Verified': _is_true(req_data.get('aadharVerified') or req_data.get('Aadhar_Verified')),
        'Date_of_Birth': req_data.get('dateOfBirth') or req_data.get('Date_of_Birth') or '',
        'ID_Proof_Type': req_data.get('idProofType') or req_data.get('ID_Proof_Type') or '',
        'ID_Proof_Number': req_data.get('idProofNumber') or req_data.get('ID_Proof_Number') or '',
        'Address': req_data.get('address') or req_data.get('Address') or '',
    }

    try:
        # Use Datastore API for INSERT
        table = app.datastore().table(TABLE_NAME)
        row = table.insert_row(user_data)

        # Format response
        user_response = {
            'id': row['ROWID'],
            'fullName': row.get('Full_Name', ''),
            'email': row.get('Email', ''),
            'phoneNumber': row.get('Phone_Number', ''),
            'role': row.get('Role', 'User'),
            'accountStatus': row.get('Account_Status', 'Active'),
            'aadharVerified': row.get('Aadhar_Verified', 'false'),
            'dateOfBirth': row.get('Date_of_Birth', ''),
            'idProofType': row.get('ID_Proof_Type', ''),
            'idProofNumber': row.get('ID_Proof_Number', ''),
            'address': row.get('Address', ''),
        }

        logger.info(f"Created user: {email} with ROWID: {row['ROWID']}")
        return jsonify({
            'status': 'success',
            'data': {'user': user_response}
        }), 201

    except Exception as e:
        logger.error(f"Failed to create user: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Database error: {str(e)}'
        }), 500


# ══════════════════════════════════════════════════════════════════════════════
#  GET ALL USERS (GET /api/users)
# ══════════════════════════════════════════════════════════════════════════════

@users_cloudscale_bp.route('/api/users', methods=['GET'])
@require_admin
def get_all_users():
    """
    Get all users with optional filters.

    Query Parameters:
    - limit: Max records (default: 200)
    - role: Filter by role (Admin/User)
    - search: Search in name, email, phone
    - status: Filter by Account_Status
    """
    app = _get_catalyst_app()
    if not app:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500

    limit = request.args.get('limit', 200, type=int)
    role_filter = request.args.get('role', '').strip()
    search = request.args.get('search', '').strip().lower()
    status_filter = request.args.get('status', '').strip()

    try:
        # Build ZCQL query
        zcql_service = app.zcql()

        # Build WHERE clause
        conditions = []
        if role_filter:
            conditions.append(f"Role = '{role_filter}'")
        if status_filter:
            conditions.append(f"Account_Status = '{status_filter}'")

        where_clause = f" WHERE {' AND '.join(conditions)}" if conditions else ""

        query = f"""
            SELECT ROWID, Full_Name, Email, Phone_Number, Role, Account_Status,
                   Aadhar_Verified, Date_of_Birth, ID_Proof_Type, ID_Proof_Number,
                   Address, Last_Login, CREATEDTIME, MODIFIEDTIME
            FROM {TABLE_NAME}
            {where_clause}
            ORDER BY ROWID DESC
            LIMIT {limit}
        """

        query_result = zcql_service.execute_query(query)

        # Format response
        users = []
        for item in query_result:
            row = item.get(TABLE_NAME, item)
            user = {
                'id': row.get('ROWID'),
                'fullName': row.get('Full_Name', ''),
                'email': row.get('Email', ''),
                'phoneNumber': row.get('Phone_Number', ''),
                'role': row.get('Role', 'User'),
                'accountStatus': row.get('Account_Status', 'Active'),
                'aadharVerified': row.get('Aadhar_Verified', 'false'),
                'dateOfBirth': row.get('Date_of_Birth', ''),
                'idProofType': row.get('ID_Proof_Type', ''),
                'idProofNumber': row.get('ID_Proof_Number', ''),
                'address': row.get('Address', ''),
                'lastLogin': row.get('Last_Login', ''),
                'createdTime': row.get('CREATEDTIME', ''),
                'modifiedTime': row.get('MODIFIEDTIME', ''),
            }
            users.append(user)

        # Apply client-side search filter if provided
        if search:
            users = [
                u for u in users
                if search in (u.get('fullName') or '').lower()
                or search in (u.get('email') or '').lower()
                or search in (u.get('phoneNumber') or '').lower()
            ]

        return jsonify({
            'status': 'success',
            'data': {'users': users, 'count': len(users)}
        }), 200

    except Exception as e:
        logger.warning(f"Database query error: {e}")
        return jsonify({
            'status': 'error',
            'data': {'users': []},
            'message': f'Database error: {str(e)}'
        }), 500


# ══════════════════════════════════════════════════════════════════════════════
#  GET ONE USER (GET /api/users/:id)
# ══════════════════════════════════════════════════════════════════════════════

@users_cloudscale_bp.route('/api/users/<user_id>', methods=['GET'])
def get_user(user_id):
    """
    Get a single user by ID.

    Users can access their own profile.
    Admins can access any profile.
    """
    app = _get_catalyst_app()
    if not app:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500

    # Auth check - user can access own profile or admin can access any
    from core.security import _extract_bearer, decode_token
    token = _extract_bearer(request)

    current_user_id = None
    current_role = None

    if token:
        payload = decode_token(token)
        if payload and payload.get("type") == "access":
            current_user_id = payload.get('sub', '')
            current_role = payload.get('role', 'User')

    if not current_user_id:
        current_user_id = request.headers.get('X-User-ID', '').strip()
        current_role = request.headers.get('X-User-Role', 'User').strip()

    if not current_user_id:
        return jsonify({'status': 'error', 'message': 'Authentication required'}), 401

    is_admin = current_role.lower() == 'admin'
    is_own_profile = str(current_user_id) == str(user_id)

    if not (is_admin or is_own_profile):
        return jsonify({'status': 'error', 'message': 'You can only access your own profile'}), 403

    try:
        # Use Datastore API for GET ONE
        table = app.datastore().table(TABLE_NAME)
        row = table.get_row(int(user_id))

        if row:
            user = {
                'id': row.get('ROWID'),
                'fullName': row.get('Full_Name', ''),
                'email': row.get('Email', ''),
                'phoneNumber': row.get('Phone_Number', ''),
                'role': row.get('Role', 'User'),
                'accountStatus': row.get('Account_Status', 'Active'),
                'aadharVerified': row.get('Aadhar_Verified', 'false'),
                'dateOfBirth': row.get('Date_of_Birth', ''),
                'idProofType': row.get('ID_Proof_Type', ''),
                'idProofNumber': row.get('ID_Proof_Number', ''),
                'address': row.get('Address', ''),
                'lastLogin': row.get('Last_Login', ''),
                'createdTime': row.get('CREATEDTIME', ''),
                'modifiedTime': row.get('MODIFIEDTIME', ''),
            }
            return jsonify({'status': 'success', 'data': {'user': user}}), 200
        else:
            return jsonify({'status': 'error', 'message': 'User not found'}), 404

    except Exception as e:
        logger.error(f"Failed to get user {user_id}: {e}")
        return jsonify({'status': 'error', 'message': f'Database error: {str(e)}'}), 500


# ══════════════════════════════════════════════════════════════════════════════
#  UPDATE USER (PUT /api/users/:id)
# ══════════════════════════════════════════════════════════════════════════════

@users_cloudscale_bp.route('/api/users/<user_id>', methods=['PUT'])
@require_admin
def update_user(user_id):
    """
    Update a user record (Admin only).

    Request Body: Same as create, but all fields optional
    """
    app = _get_catalyst_app()
    if not app:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500

    req_data = request.get_json() or {}

    # Build update data - only include provided fields
    update_data = {'ROWID': int(user_id)}

    # Map request fields to CloudScale columns
    field_mapping = {
        'fullName': 'Full_Name',
        'Full_Name': 'Full_Name',
        'email': 'Email',
        'Email': 'Email',
        'phoneNumber': 'Phone_Number',
        'Phone_Number': 'Phone_Number',
        'role': 'Role',
        'Role': 'Role',
        'accountStatus': 'Account_Status',
        'Account_Status': 'Account_Status',
        'aadharVerified': 'Aadhar_Verified',
        'Aadhar_Verified': 'Aadhar_Verified',
        'dateOfBirth': 'Date_of_Birth',
        'Date_of_Birth': 'Date_of_Birth',
        'idProofType': 'ID_Proof_Type',
        'ID_Proof_Type': 'ID_Proof_Type',
        'idProofNumber': 'ID_Proof_Number',
        'ID_Proof_Number': 'ID_Proof_Number',
        'address': 'Address',
        'Address': 'Address',
        'password': 'Password',
        'Password': 'Password',
    }

    for req_field, db_field in field_mapping.items():
        if req_field in req_data and req_data[req_field] is not None:
            value = req_data[req_field]

            # Special handling for password
            if db_field == 'Password':
                value = hash_password(value) if value else ''
            # Special handling for boolean fields
            elif db_field == 'Aadhar_Verified':
                value = _is_true(value)

            update_data[db_field] = value

    if len(update_data) <= 1:  # Only ROWID present
        return jsonify({'status': 'error', 'message': 'No valid fields to update'}), 400

    try:
        # Use Datastore API for UPDATE
        table = app.datastore().table(TABLE_NAME)
        updated_row = table.update_row(update_data)

        user = {
            'id': updated_row.get('ROWID'),
            'fullName': updated_row.get('Full_Name', ''),
            'email': updated_row.get('Email', ''),
            'phoneNumber': updated_row.get('Phone_Number', ''),
            'role': updated_row.get('Role', 'User'),
            'accountStatus': updated_row.get('Account_Status', 'Active'),
            'aadharVerified': updated_row.get('Aadhar_Verified', 'false'),
            'dateOfBirth': updated_row.get('Date_of_Birth', ''),
            'idProofType': updated_row.get('ID_Proof_Type', ''),
            'idProofNumber': updated_row.get('ID_Proof_Number', ''),
            'address': updated_row.get('Address', ''),
        }

        logger.info(f"Updated user: {user_id}")
        return jsonify({'status': 'success', 'data': {'user': user}}), 200

    except Exception as e:
        logger.error(f"Failed to update user {user_id}: {e}")
        return jsonify({'status': 'error', 'message': f'Update failed: {str(e)}'}), 500


# ══════════════════════════════════════════════════════════════════════════════
#  DELETE USER (DELETE /api/users/:id)
# ══════════════════════════════════════════════════════════════════════════════

@users_cloudscale_bp.route('/api/users/<user_id>', methods=['DELETE'])
@require_admin
def delete_user(user_id):
    """
    Delete a user record (Admin only).
    """
    app = _get_catalyst_app()
    if not app:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500

    try:
        # Use Datastore API for DELETE
        table = app.datastore().table(TABLE_NAME)
        table.delete_row(int(user_id))

        logger.info(f"Deleted user: {user_id}")
        return jsonify({
            'status': 'success',
            'data': {'user': {'id': user_id}}
        }), 200

    except Exception as e:
        logger.error(f"Failed to delete user {user_id}: {e}")
        return jsonify({'status': 'error', 'message': f'Delete failed: {str(e)}'}), 500


# ══════════════════════════════════════════════════════════════════════════════
#  ADDITIONAL ENDPOINTS (Self-service)
# ══════════════════════════════════════════════════════════════════════════════

@users_cloudscale_bp.route('/api/users/<user_id>/profile', methods=['PUT'])
def update_profile(user_id):
    """
    Update own profile (Self-service).
    Only allows limited fields: Full_Name, Phone_Number, Address, Date_of_Birth
    """
    app = _get_catalyst_app()
    if not app:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500

    req_data = request.get_json() or {}

    # Only allow specific fields for self-service update
    allowed_fields = {
        'fullName': 'Full_Name',
        'Full_Name': 'Full_Name',
        'phoneNumber': 'Phone_Number',
        'Phone_Number': 'Phone_Number',
        'address': 'Address',
        'Address': 'Address',
        'dateOfBirth': 'Date_of_Birth',
        'Date_of_Birth': 'Date_of_Birth',
        'idProofType': 'ID_Proof_Type',
        'ID_Proof_Type': 'ID_Proof_Type',
        'idProofNumber': 'ID_Proof_Number',
        'ID_Proof_Number': 'ID_Proof_Number',
    }

    update_data = {'ROWID': int(user_id)}
    for req_field, db_field in allowed_fields.items():
        if req_field in req_data and req_data[req_field] is not None:
            update_data[db_field] = req_data[req_field]

    if len(update_data) <= 1:
        return jsonify({'status': 'error', 'message': 'No valid fields to update'}), 400

    try:
        table = app.datastore().table(TABLE_NAME)
        updated_row = table.update_row(update_data)

        return jsonify({
            'status': 'success',
            'message': 'Profile updated',
            'data': {'user': {'id': updated_row.get('ROWID')}}
        }), 200

    except Exception as e:
        logger.error(f"Failed to update profile {user_id}: {e}")
        return jsonify({'status': 'error', 'message': f'Update failed: {str(e)}'}), 500


@users_cloudscale_bp.route('/api/users/<user_id>/status', methods=['PUT'])
@require_admin
def update_account_status(user_id):
    """
    Update user account status (Admin only).
    """
    app = _get_catalyst_app()
    if not app:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500

    req_data = request.get_json() or {}
    new_status = (req_data.get('accountStatus') or req_data.get('Account_Status') or '').strip()

    if new_status not in ('Active', 'Blocked', 'Suspended'):
        return jsonify({
            'status': 'error',
            'message': 'Account_Status must be Active, Blocked, or Suspended'
        }), 400

    try:
        table = app.datastore().table(TABLE_NAME)
        update_data = {
            'ROWID': int(user_id),
            'Account_Status': new_status
        }
        table.update_row(update_data)

        logger.info(f"Updated user {user_id} status to: {new_status}")
        return jsonify({
            'status': 'success',
            'message': f'User account {new_status.lower()}'
        }), 200

    except Exception as e:
        logger.error(f"Failed to update status for user {user_id}: {e}")
        return jsonify({'status': 'error', 'message': f'Update failed: {str(e)}'}), 500


# ══════════════════════════════════════════════════════════════════════════════
#  GET USER BY EMAIL (Helper endpoint)
# ══════════════════════════════════════════════════════════════════════════════

@users_cloudscale_bp.route('/api/users/email/<email>', methods=['GET'])
def get_user_by_email(email):
    """
    Get user by email address.
    Used internally for login and duplicate checks.
    """
    app = _get_catalyst_app()
    if not app:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500

    try:
        zcql_service = app.zcql()
        email_lower = email.lower().replace("'", "''")  # SQL escape

        query = f"""
            SELECT ROWID, Full_Name, Email, Password, Phone_Number, Role,
                   Account_Status, Aadhar_Verified, Date_of_Birth,
                   ID_Proof_Type, ID_Proof_Number, Address, Last_Login
            FROM {TABLE_NAME}
            WHERE Email = '{email_lower}'
            LIMIT 1
        """

        query_result = zcql_service.execute_query(query)

        if query_result and len(query_result) > 0:
            row = query_result[0].get(TABLE_NAME, query_result[0])
            user = {
                'id': row.get('ROWID'),
                'fullName': row.get('Full_Name', ''),
                'email': row.get('Email', ''),
                'password': row.get('Password', ''),  # Include for auth
                'phoneNumber': row.get('Phone_Number', ''),
                'role': row.get('Role', 'User'),
                'accountStatus': row.get('Account_Status', 'Active'),
                'aadharVerified': row.get('Aadhar_Verified', 'false'),
            }
            return jsonify({'status': 'success', 'data': {'user': user}}), 200
        else:
            return jsonify({'status': 'error', 'message': 'User not found'}), 404

    except Exception as e:
        logger.error(f"Failed to get user by email {email}: {e}")
        return jsonify({'status': 'error', 'message': f'Database error: {str(e)}'}), 500


# ══════════════════════════════════════════════════════════════════════════════
#  USER BOOKINGS (GET /api/users/:id/bookings)
# ══════════════════════════════════════════════════════════════════════════════

@users_cloudscale_bp.route('/api/users/<user_id>/bookings', methods=['GET'])
def get_user_bookings(user_id):
    """
    Get all bookings for a user.

    Query Parameters:
    - upcoming: 'true' to filter future journeys only
    - status: Filter by Booking_Status
    """
    app = _get_catalyst_app()
    if not app:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500

    upcoming_only = request.args.get('upcoming', '').lower() == 'true'
    status_filter = request.args.get('status', '').strip()

    try:
        zcql_service = app.zcql()

        # Build WHERE clause
        conditions = [f"Users = {user_id}"]
        if status_filter:
            conditions.append(f"Booking_Status = '{status_filter}'")

        where_clause = " AND ".join(conditions)

        query = f"""
            SELECT ROWID, PNR, Users, Trains, Journey_Date, Class, Quota,
                   Num_Passengers, Passengers, Total_Fare, Booking_Status,
                   Payment_Status, Booking_Time
            FROM Bookings
            WHERE {where_clause}
            ORDER BY Booking_Time DESC
            LIMIT 200
        """

        query_result = zcql_service.execute_query(query)

        bookings = []
        today = datetime.now().strftime('%Y-%m-%d')

        for item in query_result:
            row = item.get('Bookings', item)

            # Parse journey date for filtering
            journey_date = row.get('Journey_Date', '')
            journey_ymd = ''
            if journey_date:
                try:
                    if len(str(journey_date).split('-')[0]) == 4:
                        journey_ymd = str(journey_date)[:10]
                    else:
                        from datetime import datetime as dt
                        journey_ymd = dt.strptime(str(journey_date).split(' ')[0], '%d-%b-%Y').strftime('%Y-%m-%d')
                except:
                    journey_ymd = ''

            # Skip past bookings if upcoming_only
            if upcoming_only and journey_ymd and journey_ymd < today:
                continue

            booking = {
                'id': row.get('ROWID'),
                'pnr': row.get('PNR', ''),
                'trainId': row.get('Trains', ''),
                'journeyDate': row.get('Journey_Date', ''),
                'class': row.get('Class', ''),
                'quota': row.get('Quota', ''),
                'numPassengers': row.get('Num_Passengers', 0),
                'passengers': row.get('Passengers', '[]'),
                'totalFare': row.get('Total_Fare', 0),
                'bookingStatus': row.get('Booking_Status', ''),
                'paymentStatus': row.get('Payment_Status', ''),
                'bookingTime': row.get('Booking_Time', ''),
            }
            bookings.append(booking)

        return jsonify({
            'status': 'success',
            'data': {'bookings': bookings, 'count': len(bookings)}
        }), 200

    except Exception as e:
        logger.error(f"Failed to get bookings for user {user_id}: {e}")
        return jsonify({
            'status': 'error',
            'data': {'bookings': []},
            'message': f'Database error: {str(e)}'
        }), 500


# ══════════════════════════════════════════════════════════════════════════════
#  USER INSIGHTS (GET /api/users/:id/insights)
# ══════════════════════════════════════════════════════════════════════════════

@users_cloudscale_bp.route('/api/users/<user_id>/insights', methods=['GET'])
def get_user_insights(user_id):
    """
    Get travel statistics for a user.
    """
    app = _get_catalyst_app()
    if not app:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500

    try:
        zcql_service = app.zcql()

        query = f"""
            SELECT ROWID, Booking_Status, Class, Total_Fare
            FROM Bookings
            WHERE Users = {user_id}
            LIMIT 500
        """

        query_result = zcql_service.execute_query(query)

        total = len(query_result)
        confirmed = 0
        cancelled = 0
        total_spent = 0.0
        class_count = {}

        for item in query_result:
            row = item.get('Bookings', item)
            status = (row.get('Booking_Status') or '').lower()

            if status == 'confirmed':
                confirmed += 1
                total_spent += float(row.get('Total_Fare') or 0)
            elif status == 'cancelled':
                cancelled += 1

            cls = row.get('Class', 'Unknown')
            class_count[cls] = class_count.get(cls, 0) + 1

        preferred_class = max(class_count, key=class_count.get) if class_count else 'SL'

        return jsonify({
            'status': 'success',
            'data': {
                'totalBookings': total,
                'confirmed': confirmed,
                'cancelled': cancelled,
                'totalSpent': round(total_spent, 2),
                'preferredClass': preferred_class,
                'classBreakdown': class_count,
            }
        }), 200

    except Exception as e:
        logger.error(f"Failed to get insights for user {user_id}: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Database error: {str(e)}'
        }), 500
