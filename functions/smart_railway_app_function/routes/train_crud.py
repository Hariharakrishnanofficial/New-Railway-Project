"""
Train CRUD Focus - Systematic ROWID Discovery
Creates one train at a time with different ROWID patterns to find the correct station references.
"""

from flask import Blueprint, jsonify, request
import logging
from repositories.cloudscale_repository import cloudscale_repo, get_catalyst_app
from config import TABLES

logger = logging.getLogger(__name__)

train_crud_bp = Blueprint('train_crud', __name__, url_prefix='/train-crud')

# Test train data with minimal fields
TEST_TRAIN = {
    'Train_Number': 'TEST001',
    'Train_Name': 'ROWID Test Express',
    'Train_Type': 'EXPRESS',
    'Departure_Time': '10:00',
    'Arrival_Time': '18:00',
    'Duration': '8:00',
    'Distance': 500.0,
    'Run_Days': 'Mon,Tue,Wed,Thu,Fri',
    'Is_Active': 'true'
}

@train_crud_bp.route('/test-rowid-pattern/<int:pattern_id>', methods=['POST'])
def test_rowid_pattern(pattern_id):
    """Test train creation with specific ROWID pattern."""

    # Different ROWID patterns to test
    rowid_patterns = [
        [1001, 1002],           # Pattern 0: Development range
        [1, 2],                 # Pattern 1: Simple sequential
        [100, 200],             # Pattern 2: Hundreds
        [1000001, 1000002],     # Pattern 3: Million+ range
        [999999999999999999, 1000000000000000000],  # Pattern 4: Large numbers
        [1804000000000000001, 1804000000000000002],  # Pattern 5: Timestamp-like
    ]

    if pattern_id >= len(rowid_patterns):
        return jsonify({
            'status': 'error',
            'message': f'Pattern {pattern_id} not available. Max: {len(rowid_patterns)-1}'
        }), 400

    try:
        # Get the pattern
        rowids = rowid_patterns[pattern_id]

        # Create test train with this pattern
        train_data = TEST_TRAIN.copy()
        train_data['From_Station'] = rowids[0]  # MMCT -> first ROWID
        train_data['To_Station'] = rowids[1]    # NDLS -> second ROWID
        train_data['Train_Number'] = f'TEST{pattern_id:03d}'  # Unique number per pattern

        logger.info(f"Testing ROWID pattern {pattern_id}: {rowids}")
        logger.info(f"Train data: {train_data}")

        # Attempt creation
        result = cloudscale_repo.create_record(TABLES['trains'], train_data)

        if result.get('success'):
            return jsonify({
                'status': 'success',
                'message': f'SUCCESS! Pattern {pattern_id} worked: {rowids}',
                'pattern_id': pattern_id,
                'rowids': rowids,
                'train_data': train_data,
                'result': result.get('data', {})
            }), 201
        else:
            return jsonify({
                'status': 'failed',
                'message': f'Pattern {pattern_id} failed: {rowids}',
                'pattern_id': pattern_id,
                'rowids': rowids,
                'error': result.get('error', 'Unknown error'),
                'train_data': train_data
            }), 200

    except Exception as e:
        logger.exception(f"Error testing pattern {pattern_id}")
        return jsonify({
            'status': 'error',
            'message': f'Exception testing pattern {pattern_id}: {str(e)}'
        }), 500

@train_crud_bp.route('/get-all-trains', methods=['GET'])
def get_all_trains():
    """Get all trains from CloudScale."""
    try:
        trains = cloudscale_repo.get_all_records(TABLES['trains'], limit=50)

        if trains.get('success'):
            train_data = trains.get('data', {}).get('data', [])
            return jsonify({
                'status': 'success',
                'count': len(train_data),
                'trains': train_data
            }), 200
        else:
            return jsonify({
                'status': 'error',
                'message': 'Failed to get trains',
                'error': trains.get('error', 'Unknown error')
            }), 500

    except Exception as e:
        logger.exception("Error getting trains")
        return jsonify({
            'status': 'error',
            'message': f'Exception getting trains: {str(e)}'
        }), 500

@train_crud_bp.route('/delete-test-trains', methods=['DELETE'])
def delete_test_trains():
    """Delete test trains to clean up."""
    try:
        # Get all trains first
        trains_result = cloudscale_repo.get_all_records(TABLES['trains'], limit=50)

        if not trains_result.get('success'):
            return jsonify({
                'status': 'error',
                'message': 'Could not get trains to delete'
            }), 500

        trains = trains_result.get('data', {}).get('data', [])
        deleted_count = 0

        for train in trains:
            train_number = train.get('Train_Number', '')
            if train_number.startswith('TEST'):
                train_id = train.get('ROWID')
                if train_id:
                    delete_result = cloudscale_repo.delete_record(TABLES['trains'], str(train_id))
                    if delete_result.get('success'):
                        deleted_count += 1
                        logger.info(f"Deleted test train {train_number} (ID: {train_id})")

        return jsonify({
            'status': 'success',
            'message': f'Deleted {deleted_count} test trains',
            'deleted_count': deleted_count
        }), 200

    except Exception as e:
        logger.exception("Error deleting test trains")
        return jsonify({
            'status': 'error',
            'message': f'Exception deleting test trains: {str(e)}'
        }), 500