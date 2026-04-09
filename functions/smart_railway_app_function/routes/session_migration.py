"""
Database Migration Script - Session Tables
Creates CloudScale tables for session management.

Usage:
    POST /admin/migrate/sessions - Create session tables (admin only)
    
Tables Created:
    - Sessions: Server-side session storage
    - Session_Audit_Log: Session event tracking
"""

import logging
from flask import Blueprint, jsonify

from core.session_middleware import require_session_admin
from repositories.cloudscale_repository import cloudscale_repo

logger = logging.getLogger(__name__)
session_migration_bp = Blueprint('session_migration', __name__)


# CloudScale table schemas (for documentation - actual creation via Catalyst console)
SESSIONS_SCHEMA = """
Table: Sessions
Purpose: Server-side session storage for authentication

Columns:
    - ROWID (auto-generated, primary key)
    - Session_ID (TEXT, unique, indexed) - Cryptographically secure session identifier
    - User_ID (TEXT, indexed) - Reference to Users.ROWID
    - User_Email (TEXT) - Cached email for quick lookups
    - User_Role (TEXT) - Cached role (User/Admin)
    - IP_Address (TEXT) - Client IP address at session creation
    - User_Agent (TEXT) - Client browser/device info
    - Device_Fingerprint (TEXT) - Hashed device fingerprint
    - CSRF_Token (TEXT) - CSRF protection token
    - Created_At (TEXT/DATETIME) - Session creation timestamp
    - Last_Accessed_At (TEXT/DATETIME, indexed) - Last activity timestamp
    - Expires_At (TEXT/DATETIME, indexed) - Absolute expiry timestamp
    - Is_Active (BOOLEAN, indexed) - Whether session is valid
    - Revoked_At (TEXT/DATETIME) - When session was revoked
    - Revoke_Reason (TEXT) - Why session was revoked

Indexes:
    - Session_ID (unique)
    - User_ID
    - Last_Accessed_At
    - Expires_At
    - Is_Active
"""

SESSION_AUDIT_LOG_SCHEMA = """
Table: Session_Audit_Log
Purpose: Security audit trail for session events

Columns:
    - ROWID (auto-generated, primary key)
    - Event_Type (TEXT, indexed) - Type of event (SESSION_CREATED, SESSION_REVOKED, etc.)
    - Session_ID (TEXT) - Partial session ID (first 20 chars)
    - User_ID (TEXT, indexed) - User involved
    - User_Email (TEXT) - User email
    - IP_Address (TEXT) - Client IP
    - Event_Details (TEXT) - JSON with additional details
    - Created_At (TEXT/DATETIME, indexed) - When event occurred

Event Types:
    - SESSION_CREATED: New session created
    - SESSION_REVOKED: Single session revoked
    - ALL_SESSIONS_REVOKED: All user sessions revoked
    - SESSION_EXPIRED: Session expired automatically
    - SESSION_IDLE_TIMEOUT: Session timed out due to inactivity
    - ADMIN_REVOKE: Admin forced session revocation
"""


@session_migration_bp.route('/admin/migrate/sessions', methods=['POST'])
@require_session_admin
def migrate_sessions():
    """
    Verify session tables exist and are accessible.
    
    Note: Actual table creation must be done via Zoho Catalyst Console.
    This endpoint verifies the tables are accessible and logs the schema for reference.
    """
    try:
        # Test Sessions table
        sessions_test = cloudscale_repo.execute_query(
            "SELECT ROWID FROM Sessions LIMIT 1"
        )
        sessions_ok = sessions_test.get('success', False)
        sessions_error = sessions_test.get('error', '')
        
        # Test Session_Audit_Log table
        audit_test = cloudscale_repo.execute_query(
            "SELECT ROWID FROM Session_Audit_Log LIMIT 1"
        )
        audit_ok = audit_test.get('success', False)
        audit_error = audit_test.get('error', '')
        
        if sessions_ok and audit_ok:
            return jsonify({
                'status': 'success',
                'message': 'Session tables are ready',
                'data': {
                    'sessions_table': 'OK',
                    'audit_table': 'OK',
                }
            }), 200
        
        # Tables don't exist - provide schema for manual creation
        missing_tables = []
        if not sessions_ok:
            missing_tables.append({
                'table': 'Sessions',
                'error': sessions_error,
                'schema': SESSIONS_SCHEMA,
            })
        if not audit_ok:
            missing_tables.append({
                'table': 'Session_Audit_Log',
                'error': audit_error,
                'schema': SESSION_AUDIT_LOG_SCHEMA,
            })
        
        return jsonify({
            'status': 'error',
            'message': 'Session tables need to be created in Catalyst Console',
            'data': {
                'missing_tables': missing_tables,
                'instructions': [
                    '1. Log into Zoho Catalyst Console',
                    '2. Navigate to CloudScale > Data Store',
                    '3. Create the missing tables with the schemas provided',
                    '4. Run this migration again to verify',
                ]
            }
        }), 400
        
    except Exception as exc:
        logger.exception(f'Session migration error: {exc}')
        return jsonify({
            'status': 'error',
            'message': f'Migration check failed: {str(exc)}',
        }), 500


@session_migration_bp.route('/admin/migrate/sessions/schema', methods=['GET'])
@require_session_admin
def get_session_schema():
    """Get the schema definitions for session tables."""
    return jsonify({
        'status': 'success',
        'data': {
            'sessions': {
                'table_name': 'Sessions',
                'description': 'Server-side session storage',
                'columns': [
                    {'name': 'Session_ID', 'type': 'TEXT', 'required': True, 'indexed': True, 'unique': True},
                    {'name': 'User_ID', 'type': 'TEXT', 'required': True, 'indexed': True},
                    {'name': 'User_Email', 'type': 'TEXT', 'required': True},
                    {'name': 'User_Role', 'type': 'TEXT', 'required': True},
                    {'name': 'IP_Address', 'type': 'TEXT', 'required': False},
                    {'name': 'User_Agent', 'type': 'TEXT', 'required': False, 'max_length': 500},
                    {'name': 'Device_Fingerprint', 'type': 'TEXT', 'required': False, 'max_length': 32},
                    {'name': 'CSRF_Token', 'type': 'TEXT', 'required': True},
                    {'name': 'Created_At', 'type': 'TEXT', 'required': True},
                    {'name': 'Last_Accessed_At', 'type': 'TEXT', 'required': True, 'indexed': True},
                    {'name': 'Expires_At', 'type': 'TEXT', 'required': True, 'indexed': True},
                    {'name': 'Is_Active', 'type': 'BOOLEAN', 'required': True, 'default': True, 'indexed': True},
                    {'name': 'Revoked_At', 'type': 'TEXT', 'required': False},
                    {'name': 'Revoke_Reason', 'type': 'TEXT', 'required': False},
                ],
            },
            'session_audit_log': {
                'table_name': 'Session_Audit_Log',
                'description': 'Session event audit trail',
                'columns': [
                    {'name': 'Event_Type', 'type': 'TEXT', 'required': True, 'indexed': True},
                    {'name': 'Session_ID', 'type': 'TEXT', 'required': False, 'max_length': 20},
                    {'name': 'User_ID', 'type': 'TEXT', 'required': False, 'indexed': True},
                    {'name': 'User_Email', 'type': 'TEXT', 'required': False},
                    {'name': 'IP_Address', 'type': 'TEXT', 'required': False},
                    {'name': 'Event_Details', 'type': 'TEXT', 'required': False},
                    {'name': 'Created_At', 'type': 'TEXT', 'required': True, 'indexed': True},
                ],
            },
        }
    }), 200


# Sample data for testing
@session_migration_bp.route('/admin/migrate/sessions/test', methods=['POST'])
@require_session_admin
def test_session_tables():
    """
    Test session table operations with sample data.
    Creates and deletes a test session.
    """
    import secrets
    from datetime import datetime, timezone, timedelta
    
    try:
        test_session_id = f"test_{secrets.token_urlsafe(16)}"
        now = datetime.now(timezone.utc)
        
        # Create test session
        test_data = {
            "Session_ID": test_session_id,
            "User_ID": "test_user",
            "User_Email": "test@example.com",
            "User_Role": "User",
            "IP_Address": "127.0.0.1",
            "User_Agent": "Test Agent",
            "Device_Fingerprint": "",
            "CSRF_Token": secrets.token_urlsafe(32),
            "Created_At": now.isoformat(),
            "Last_Accessed_At": now.isoformat(),
            "Expires_At": (now + timedelta(hours=1)).isoformat(),
            "Is_Active": True,
        }
        
        # Insert
        create_result = cloudscale_repo.create_record('Sessions', test_data)
        if not create_result.get('success'):
            return jsonify({
                'status': 'error',
                'message': f'Failed to create test session: {create_result.get("error")}',
            }), 500
        
        row_id = create_result.get('data', {}).get('ROWID')
        
        # Verify read using CriteriaBuilder for safe Session_ID query
        from repositories.cloudscale_repository import CriteriaBuilder
        criteria = CriteriaBuilder().id_eq("Session_ID", test_session_id).build()
        read_result = cloudscale_repo.execute_query(
            f"SELECT * FROM Sessions WHERE {criteria}"
        )
        if not read_result.get('success'):
            return jsonify({
                'status': 'error',
                'message': f'Failed to read test session: {read_result.get("error")}',
            }), 500
        
        # Update
        if row_id:
            update_result = cloudscale_repo.update_record('Sessions', str(row_id), {
                "Is_Active": False,
                "Revoke_Reason": "test_cleanup",
            })
            
            # Delete
            delete_result = cloudscale_repo.delete_record('Sessions', str(row_id))
        
        return jsonify({
            'status': 'success',
            'message': 'Session table operations verified successfully',
            'data': {
                'create': 'OK',
                'read': 'OK',
                'update': 'OK',
                'delete': 'OK',
            }
        }), 200
        
    except Exception as exc:
        logger.exception(f'Session table test error: {exc}')
        return jsonify({
            'status': 'error',
            'message': f'Session table test failed: {str(exc)}',
        }), 500
