"""
CloudScale Direct Test Route - Bypass all logic and test raw CloudScale insertion
"""

import logging
import time
from flask import Blueprint, jsonify, request

from repositories.cloudscale_repository import cloudscale_repo, get_catalyst_app
from config import TABLES

logger = logging.getLogger(__name__)
cloudscale_test_bp = Blueprint('cloudscale_test', __name__)

@cloudscale_test_bp.route('/cloudscale-test/status', methods=['GET'])
def test_cloudscale_status():
    """Test CloudScale connection and basic functionality."""
    try:
        # Test 1: Check if Catalyst is initialized
        catalyst_app = get_catalyst_app()
        catalyst_ready = catalyst_app is not None

        # Test 2: Try basic ZCQL query
        zcql_test = None
        if catalyst_app:
            try:
                zcql = catalyst_app.zcql()
                # Try to execute a simple query
                result = zcql.execute_query("SELECT ROWID FROM Users LIMIT 1")
                zcql_test = "Success"
            except Exception as e:
                zcql_test = f"Failed: {str(e)}"

        # Test 3: Try datastore access
        datastore_test = None
        if catalyst_app:
            try:
                datastore = catalyst_app.datastore()
                # Try to access a table
                table = datastore.table('Settings')
                datastore_test = "Success"
            except Exception as e:
                datastore_test = f"Failed: {str(e)}"

        return jsonify({
            'status': 'success',
            'catalyst_initialized': catalyst_ready,
            'zcql_test': zcql_test,
            'datastore_test': datastore_test,
            'tables_configured': list(TABLES.keys())
        }), 200

    except Exception as e:
        logger.exception(f'CloudScale status test error: {e}')
        return jsonify({
            'status': 'error',
            'message': 'CloudScale status check failed',
            'error': str(e)
        }), 500


@cloudscale_test_bp.route('/cloudscale-test/insert', methods=['POST'])
def test_direct_insert():
    """Test direct CloudScale record insertion with detailed error reporting."""
    try:
        # Test simple Settings record insertion
        test_data = {
            'Setting_Key': f'TEST_DIRECT_{int(time.time())}',
            'Setting_Value': 'test_value_direct',
            'Setting_Type': 'STRING',
            'Description': 'Direct CloudScale insertion test',
            'Category': 'TESTING',
            'Is_Public': 'true',
            'Is_Active': 'true',
        }

        logger.info(f"Attempting to create record: {test_data}")

        # Call repository method with detailed logging
        result = cloudscale_repo.create_record(TABLES['settings'], test_data)

        logger.info(f"Repository result: {result}")

        if result.get('success'):
            # Try to immediately fetch the record
            fetch_result = cloudscale_repo.get_all_records(TABLES['settings'], limit=10)

            return jsonify({
                'status': 'success',
                'message': 'Direct CloudScale insertion successful',
                'creation_result': result,
                'fetch_result': fetch_result,
                'test_data': test_data
            }), 200
        else:
            return jsonify({
                'status': 'error',
                'message': 'Direct CloudScale insertion failed',
                'creation_result': result,
                'test_data': test_data
            }), 500

    except Exception as e:
        logger.exception(f'Direct CloudScale insert error: {e}')
        return jsonify({
            'status': 'error',
            'message': 'Direct CloudScale insertion exception',
            'error': str(e)
        }), 500


@cloudscale_test_bp.route('/cloudscale-test/manual-settings', methods=['POST'])
def test_manual_settings_creation():
    """Create settings manually step by step with debugging."""
    import time

    try:
        # Step 1: Get catalyst app
        catalyst_app = get_catalyst_app()
        if not catalyst_app:
            return jsonify({'error': 'Catalyst not initialized'}), 500

        # Step 2: Get datastore
        datastore = catalyst_app.datastore()

        # Step 3: Get settings table
        settings_table = datastore.table('Settings')

        # Step 4: Prepare test data
        test_setting = {
            'Setting_Key': f'MANUAL_TEST_{int(time.time())}',
            'Setting_Value': 'manual_test_value',
            'Setting_Type': 'STRING',
            'Description': 'Manual CloudScale test setting',
            'Category': 'TESTING',
            'Is_Public': 'true',
            'Is_Active': 'true',
        }

        # Step 5: Insert record
        insert_result = settings_table.insert_row(test_setting)

        # Step 6: Verify insertion by querying
        zcql = catalyst_app.zcql()
        verify_query = "SELECT * FROM Settings WHERE Setting_Key LIKE 'MANUAL_TEST_%' ORDER BY CREATEDTIME DESC LIMIT 5"
        verify_result = zcql.execute_query(verify_query)

        return jsonify({
            'status': 'success',
            'message': 'Manual CloudScale insertion completed',
            'test_data': test_setting,
            'insert_result': insert_result,
            'verify_result': verify_result
        }), 200

    except Exception as e:
        logger.exception(f'Manual CloudScale test error: {e}')
        return jsonify({
            'status': 'error',
            'message': 'Manual CloudScale test failed',
            'error': str(e)
        }), 500