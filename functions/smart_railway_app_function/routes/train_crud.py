"""
Train CRUD Operations - Complete Implementation
Uses dynamic station ROWID discovery for foreign key references.
"""

from flask import Blueprint, jsonify, request
import logging
from repositories.cloudscale_repository import cloudscale_repo, get_catalyst_app
from config import TABLES

logger = logging.getLogger(__name__)

train_crud_bp = Blueprint('train_crud', __name__, url_prefix='/train-crud')


def get_station_rowid_map():
    """Dynamically discover station ROWIDs from CloudScale."""
    try:
        app = get_catalyst_app()
        zcql = app.zcql()

        query = "SELECT ROWID, Station_Code, Station_Name FROM Stations"
        response = zcql.execute_query(query)
        stations = response if isinstance(response, list) else []

        # Build station code -> ROWID mapping
        rowid_map = {}
        for station in stations:
            station_data = station.get('Stations', station)
            code = station_data.get('Station_Code')
            rowid = station_data.get('ROWID')
            if code and rowid:
                rowid_map[code] = int(rowid)

        logger.info(f"Station ROWID map: {rowid_map}")
        return rowid_map

    except Exception as e:
        logger.exception("Error getting station ROWID map")
        return {}


# ============ CREATE ============

@train_crud_bp.route('/create', methods=['POST'])
def create_train():
    """Create a new train with automatic station ROWID resolution."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'status': 'error', 'message': 'No data provided'}), 400

        # Required fields
        required = ['Train_Number', 'Train_Name', 'From_Station', 'To_Station', 'Departure_Time', 'Arrival_Time']
        missing = [f for f in required if f not in data]
        if missing:
            return jsonify({'status': 'error', 'message': f'Missing required fields: {missing}'}), 400

        # Get station ROWID map for foreign key resolution
        station_map = get_station_rowid_map()
        if not station_map:
            return jsonify({'status': 'error', 'message': 'Could not get station ROWID mapping'}), 500

        # Resolve station codes to ROWIDs if provided as strings
        train_data = data.copy()

        from_station = data['From_Station']
        to_station = data['To_Station']

        # If station codes provided as strings, convert to ROWIDs
        if isinstance(from_station, str):
            if from_station not in station_map:
                return jsonify({'status': 'error', 'message': f'Unknown station code: {from_station}'}), 400
            train_data['From_Station'] = station_map[from_station]

        if isinstance(to_station, str):
            if to_station not in station_map:
                return jsonify({'status': 'error', 'message': f'Unknown station code: {to_station}'}), 400
            train_data['To_Station'] = station_map[to_station]

        logger.info(f"Creating train: {train_data}")
        result = cloudscale_repo.create_record(TABLES['trains'], train_data)

        if result.get('success'):
            return jsonify({
                'status': 'success',
                'message': 'Train created successfully',
                'data': result.get('data', {})
            }), 201
        else:
            return jsonify({
                'status': 'error',
                'message': 'Failed to create train',
                'error': result.get('error', 'Unknown error')
            }), 400

    except Exception as e:
        logger.exception("Error creating train")
        return jsonify({'status': 'error', 'message': f'Exception: {str(e)}'}), 500


@train_crud_bp.route('/create-sample', methods=['POST'])
def create_sample_trains():
    """Create sample trains using discovered station ROWIDs."""
    try:
        station_map = get_station_rowid_map()
        if not station_map:
            return jsonify({'status': 'error', 'message': 'No stations found'}), 500

        # Sample trains with only required and working fields
        sample_trains = [
            {
                'Train_Number': '12951',
                'Train_Name': 'Mumbai Rajdhani Express',
                'From_Station': 'MMCT',
                'To_Station': 'NDLS',
                'Departure_Time': '16:45',
                'Arrival_Time': '08:35'
            },
            {
                'Train_Number': '12002',
                'Train_Name': 'Shatabdi Express',
                'From_Station': 'NDLS',
                'To_Station': 'BNC',
                'Departure_Time': '06:00',
                'Arrival_Time': '22:30'
            }
        ]

        results = []
        created = 0

        for train in sample_trains:
            # Convert station codes to ROWIDs
            train_data = train.copy()
            from_code = train['From_Station']
            to_code = train['To_Station']

            if from_code in station_map:
                train_data['From_Station'] = station_map[from_code]
            else:
                results.append({'train': train['Train_Number'], 'error': f'Station {from_code} not found'})
                continue

            if to_code in station_map:
                train_data['To_Station'] = station_map[to_code]
            else:
                results.append({'train': train['Train_Number'], 'error': f'Station {to_code} not found'})
                continue

            result = cloudscale_repo.create_record(TABLES['trains'], train_data)

            if result.get('success'):
                created += 1
                results.append({
                    'train': train['Train_Number'],
                    'status': 'created',
                    'rowid': result.get('data', {}).get('ROWID')
                })
            else:
                results.append({
                    'train': train['Train_Number'],
                    'status': 'failed',
                    'error': result.get('error')
                })

        return jsonify({
            'status': 'success',
            'message': f'Created {created}/{len(sample_trains)} trains',
            'created': created,
            'results': results,
            'station_map': station_map
        }), 201 if created > 0 else 200

    except Exception as e:
        logger.exception("Error creating sample trains")
        return jsonify({'status': 'error', 'message': f'Exception: {str(e)}'}), 500


# ============ READ ============

@train_crud_bp.route('/list', methods=['GET'])
def list_trains():
    """Get all trains."""
    try:
        app = get_catalyst_app()
        zcql = app.zcql()

        query = "SELECT ROWID, Train_Number, Train_Name, Train_Type, From_Station, To_Station, Departure_Time, Arrival_Time FROM Trains"
        response = zcql.execute_query(query)
        trains = response if isinstance(response, list) else []

        # Extract train data from response
        train_list = []
        for train in trains:
            train_data = train.get('Trains', train)
            train_list.append(train_data)

        return jsonify({
            'status': 'success',
            'count': len(train_list),
            'trains': train_list
        }), 200

    except Exception as e:
        logger.exception("Error listing trains")
        return jsonify({'status': 'error', 'message': f'Exception: {str(e)}'}), 500


@train_crud_bp.route('/get/<train_id>', methods=['GET'])
def get_train(train_id):
    """Get a specific train by ROWID or Train_Number."""
    try:
        app = get_catalyst_app()
        zcql = app.zcql()

        # Check if train_id is ROWID or Train_Number
        if train_id.isdigit() and len(train_id) > 10:
            query = f"SELECT ROWID, Train_Number, Train_Name, Train_Type, From_Station, To_Station, Departure_Time, Arrival_Time, Duration, Distance, Run_Days FROM Trains WHERE ROWID = {train_id}"
        else:
            query = f"SELECT ROWID, Train_Number, Train_Name, Train_Type, From_Station, To_Station, Departure_Time, Arrival_Time, Duration, Distance, Run_Days FROM Trains WHERE Train_Number = '{train_id}'"

        response = zcql.execute_query(query)
        trains = response if isinstance(response, list) else []

        if trains:
            train_data = trains[0].get('Trains', trains[0])
            return jsonify({
                'status': 'success',
                'train': train_data
            }), 200
        else:
            return jsonify({
                'status': 'not_found',
                'message': f'Train {train_id} not found'
            }), 404

    except Exception as e:
        logger.exception(f"Error getting train {train_id}")
        return jsonify({'status': 'error', 'message': f'Exception: {str(e)}'}), 500


# ============ UPDATE ============

@train_crud_bp.route('/update/<train_id>', methods=['PUT', 'PATCH'])
def update_train(train_id):
    """Update a train by ROWID."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'status': 'error', 'message': 'No data provided'}), 400

        # If updating station references, resolve to ROWIDs
        if 'From_Station' in data or 'To_Station' in data:
            station_map = get_station_rowid_map()

            if 'From_Station' in data and isinstance(data['From_Station'], str):
                if data['From_Station'] in station_map:
                    data['From_Station'] = station_map[data['From_Station']]
                else:
                    return jsonify({'status': 'error', 'message': f'Unknown station: {data["From_Station"]}'}), 400

            if 'To_Station' in data and isinstance(data['To_Station'], str):
                if data['To_Station'] in station_map:
                    data['To_Station'] = station_map[data['To_Station']]
                else:
                    return jsonify({'status': 'error', 'message': f'Unknown station: {data["To_Station"]}'}), 400

        result = cloudscale_repo.update_record(TABLES['trains'], train_id, data)

        if result.get('success'):
            return jsonify({
                'status': 'success',
                'message': 'Train updated successfully',
                'data': result.get('data', {})
            }), 200
        else:
            return jsonify({
                'status': 'error',
                'message': 'Failed to update train',
                'error': result.get('error', 'Unknown error')
            }), 400

    except Exception as e:
        logger.exception(f"Error updating train {train_id}")
        return jsonify({'status': 'error', 'message': f'Exception: {str(e)}'}), 500


# ============ DELETE ============

@train_crud_bp.route('/delete/<train_id>', methods=['DELETE'])
def delete_train(train_id):
    """Delete a train by ROWID."""
    try:
        result = cloudscale_repo.delete_record(TABLES['trains'], train_id)

        if result.get('success'):
            return jsonify({
                'status': 'success',
                'message': f'Train {train_id} deleted successfully'
            }), 200
        else:
            return jsonify({
                'status': 'error',
                'message': 'Failed to delete train',
                'error': result.get('error', 'Unknown error')
            }), 400

    except Exception as e:
        logger.exception(f"Error deleting train {train_id}")
        return jsonify({'status': 'error', 'message': f'Exception: {str(e)}'}), 500


@train_crud_bp.route('/delete-all-test', methods=['DELETE'])
def delete_all_test_trains():
    """Delete all test trains (MIN*, TEST*, FLD*)."""
    try:
        app = get_catalyst_app()
        zcql = app.zcql()

        # Find test trains
        query = "SELECT ROWID, Train_Number FROM Trains WHERE Train_Number LIKE 'MIN%' OR Train_Number LIKE 'TEST%' OR Train_Number LIKE 'FLD%'"
        response = zcql.execute_query(query)
        trains = response if isinstance(response, list) else []

        deleted = 0
        for train in trains:
            train_data = train.get('Trains', train)
            rowid = train_data.get('ROWID')
            if rowid:
                result = cloudscale_repo.delete_record(TABLES['trains'], str(rowid))
                if result.get('success'):
                    deleted += 1

        return jsonify({
            'status': 'success',
            'message': f'Deleted {deleted} test trains',
            'deleted': deleted
        }), 200

    except Exception as e:
        logger.exception("Error deleting test trains")
        return jsonify({'status': 'error', 'message': f'Exception: {str(e)}'}), 500


# ============ UTILITY ============

@train_crud_bp.route('/discover-stations', methods=['GET'])
def discover_stations():
    """Get station ROWID mapping for reference."""
    station_map = get_station_rowid_map()
    return jsonify({
        'status': 'success',
        'station_count': len(station_map),
        'station_map': station_map
    }), 200
