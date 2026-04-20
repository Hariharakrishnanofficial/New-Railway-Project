"""
Database Migration Script - Application Errors Table

Provides admin endpoints to verify and test the dedicated Application_Errors
table used by centralized backend error tracking.
"""

import logging
from datetime import datetime, timezone
from flask import Blueprint, jsonify

from config import TABLES
from core.permission_validator import require_permission
from repositories.cloudscale_repository import cloudscale_repo, CriteriaBuilder

logger = logging.getLogger(__name__)
error_migration_bp = Blueprint('error_migration', __name__)


APPLICATION_ERRORS_SCHEMA = """
Table: Application_Errors
Purpose: Centralized backend error records for operations and debugging

Columns:
    - ROWID (auto-generated, primary key)
    - Request_ID (TEXT, indexed) - Correlation ID shared with API response header/body
    - Error_Code (TEXT, indexed) - Stable application error code
    - Status_Code (NUMBER, indexed) - HTTP status code
    - Message (TEXT) - User-safe message returned to client
    - Exception_Type (TEXT) - Python exception class name
    - Exception_Message (TEXT) - Truncated internal exception text
    - Request_Method (TEXT) - HTTP method
    - Request_Path (TEXT, indexed) - Route path
    - Endpoint (TEXT) - Flask endpoint name
    - User_ID (TEXT, indexed) - Current user if available
    - User_Email (TEXT) - Current user email if available
    - Session_ID (TEXT) - Session identifier (truncated)
    - IP_Address (TEXT) - Request source IP
    - User_Agent (TEXT) - Request user-agent
    - Severity (TEXT, indexed) - INFO/WARNING/ERROR
    - Error_Details (TEXT) - JSON details for diagnostics
    - Created_At (TEXT/DATETIME, indexed) - Event timestamp
"""


@error_migration_bp.route('/admin/migrate/errors', methods=['POST'])
@require_permission('settings', 'edit')
def migrate_error_table():
    """
    Verify dedicated Application_Errors table exists and is accessible.

    Note: Table creation is still done manually in Catalyst Console.
    This endpoint verifies readiness and returns schema instructions when missing.
    """
    table_name = TABLES.get('application_errors', 'Application_Errors')

    try:
        test_result = cloudscale_repo.execute_query(f"SELECT ROWID FROM {table_name} LIMIT 1")
        table_ok = test_result.get('success', False)
        table_error = test_result.get('error', '')

        if table_ok:
            return jsonify({
                'status': 'success',
                'message': f'{table_name} table is ready',
                'data': {
                    'table': table_name,
                    'status': 'OK',
                }
            }), 200

        return jsonify({
            'status': 'error',
            'message': f'{table_name} table needs to be created in Catalyst Console',
            'data': {
                'table': table_name,
                'error': table_error,
                'schema': APPLICATION_ERRORS_SCHEMA,
                'instructions': [
                    '1. Log into Zoho Catalyst Console',
                    '2. Navigate to CloudScale > Data Store',
                    f'3. Create table {table_name}',
                    '4. Add columns as defined in schema',
                    '5. Run this endpoint again to verify',
                ]
            }
        }), 400
    except Exception as exc:
        logger.exception('Error table migration check failed: %s', exc)
        return jsonify({
            'status': 'error',
            'message': f'Error table migration check failed: {str(exc)}',
        }), 500


@error_migration_bp.route('/admin/migrate/errors/schema', methods=['GET'])
@require_permission('settings', 'edit')
def get_error_table_schema():
    """Return machine-readable schema definition for Application_Errors."""
    table_name = TABLES.get('application_errors', 'Application_Errors')
    return jsonify({
        'status': 'success',
        'data': {
            'table_name': table_name,
            'description': 'Centralized backend application error records',
            'columns': [
                {'name': 'Request_ID', 'type': 'TEXT', 'required': True, 'indexed': True},
                {'name': 'Error_Code', 'type': 'TEXT', 'required': True, 'indexed': True},
                {'name': 'Status_Code', 'type': 'NUMBER', 'required': True, 'indexed': True},
                {'name': 'Message', 'type': 'TEXT', 'required': True},
                {'name': 'Exception_Type', 'type': 'TEXT', 'required': False},
                {'name': 'Exception_Message', 'type': 'TEXT', 'required': False},
                {'name': 'Request_Method', 'type': 'TEXT', 'required': False},
                {'name': 'Request_Path', 'type': 'TEXT', 'required': False, 'indexed': True},
                {'name': 'Endpoint', 'type': 'TEXT', 'required': False},
                {'name': 'User_ID', 'type': 'TEXT', 'required': False, 'indexed': True},
                {'name': 'User_Email', 'type': 'TEXT', 'required': False},
                {'name': 'Session_ID', 'type': 'TEXT', 'required': False},
                {'name': 'IP_Address', 'type': 'TEXT', 'required': False},
                {'name': 'User_Agent', 'type': 'TEXT', 'required': False},
                {'name': 'Severity', 'type': 'TEXT', 'required': True, 'indexed': True},
                {'name': 'Error_Details', 'type': 'TEXT', 'required': False},
                {'name': 'Created_At', 'type': 'TEXT', 'required': True, 'indexed': True},
            ]
        }
    }), 200


@error_migration_bp.route('/admin/migrate/errors/test', methods=['POST'])
@require_permission('settings', 'edit')
def test_error_table_operations():
    """
    Validate Application_Errors CRUD by inserting and deleting a test row.
    """
    table_name = TABLES.get('application_errors', 'Application_Errors')

    try:
        now = datetime.now(timezone.utc).isoformat()
        request_id = f"err_test_{int(datetime.now(timezone.utc).timestamp())}"

        test_row = {
            'Request_ID': request_id,
            'Error_Code': 'MIGRATION_TEST',
            'Status_Code': 500,
            'Message': 'Migration test error row',
            'Exception_Type': 'MigrationTestError',
            'Exception_Message': 'Synthetic row for table verification',
            'Request_Method': 'POST',
            'Request_Path': '/admin/migrate/errors/test',
            'Endpoint': 'test_error_table_operations',
            'User_ID': '0',
            'User_Email': 'migration@test.local',
            'Session_ID': 'migration-test-session',
            'IP_Address': '127.0.0.1',
            'User_Agent': 'Migration Test Runner',
            'Severity': 'ERROR',
            'Error_Details': '{"source":"migration_test"}',
            'Created_At': now,
        }

        create_result = cloudscale_repo.create_record(table_name, test_row)
        if not create_result.get('success'):
            return jsonify({
                'status': 'error',
                'message': f'Failed to insert test row: {create_result.get("error")}',
            }), 500

        row_id = str(create_result.get('data', {}).get('ROWID', ''))

        criteria = CriteriaBuilder().eq('Request_ID', request_id).build()
        read_result = cloudscale_repo.execute_query(
            f"SELECT ROWID, Request_ID, Error_Code FROM {table_name} WHERE {criteria} LIMIT 1"
        )
        if not read_result.get('success'):
            return jsonify({
                'status': 'error',
                'message': f'Failed to read test row: {read_result.get("error")}',
            }), 500

        if row_id:
            cloudscale_repo.delete_record(table_name, row_id)

        return jsonify({
            'status': 'success',
            'message': f'{table_name} CRUD test passed',
            'data': {
                'create': 'OK',
                'read': 'OK',
                'delete': 'OK' if row_id else 'SKIPPED',
            }
        }), 200
    except Exception as exc:
        logger.exception('Error table test failed: %s', exc)
        return jsonify({
            'status': 'error',
            'message': f'Error table test failed: {str(exc)}',
        }), 500
