"""
Train Routes - Route and stops management.
"""

import logging
from flask import Blueprint, jsonify, request

from repositories.cloudscale_repository import cloudscale_repo, CriteriaBuilder
from config import TABLES
from core.security import require_admin

logger = logging.getLogger(__name__)
train_routes_bp = Blueprint('train_routes', __name__)


@train_routes_bp.route('/train-routes', methods=['GET'])
def get_all_routes():
    """Get all train routes."""
    try:
        result = cloudscale_repo.get_all_records(TABLES['train_routes'], limit=200)
        if result.get('success'):
            return jsonify({'status': 'success', 'data': result.get('data', {}).get('data', [])}), 200
        return jsonify({'status': 'error', 'message': 'Failed to fetch routes'}), 500
    except Exception as e:
        logger.exception(f'Get routes error: {e}')
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


@train_routes_bp.route('/train-routes/<route_id>', methods=['GET'])
def get_route(route_id):
    """Get route by ID with stops."""
    try:
        result = cloudscale_repo.get_record_by_id(TABLES['train_routes'], route_id)
        if result.get('success') and result.get('data'):
            route = result['data']
            stops = cloudscale_repo.get_route_stops(route_id)
            route['stops'] = stops
            return jsonify({'status': 'success', 'data': route}), 200
        return jsonify({'status': 'error', 'message': 'Route not found'}), 404
    except Exception as e:
        logger.exception(f'Get route error: {e}')
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


@train_routes_bp.route('/train-routes', methods=['POST'])
@require_admin
def create_route():
    """Create a new route (admin only)."""
    data = request.get_json(silent=True) or {}
    try:
        route_data = {
            'Train_ID': data.get('trainId') or data.get('Train_ID'),
            'Route_Name': data.get('routeName') or data.get('Route_Name') or '',
            'Total_Distance': data.get('totalDistance') or data.get('Total_Distance') or 0,
        }
        result = cloudscale_repo.create_record(TABLES['train_routes'], route_data)
        if result.get('success'):
            return jsonify({'status': 'success', 'data': result.get('data')}), 201
        return jsonify({'status': 'error', 'message': 'Failed to create route'}), 500
    except Exception as e:
        logger.exception(f'Create route error: {e}')
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


@train_routes_bp.route('/train-routes/<route_id>', methods=['PUT'])
@require_admin
def update_route(route_id):
    """Update route (admin only)."""
    data = request.get_json(silent=True) or {}
    try:
        update_data = {}
        if 'routeName' in data:
            update_data['Route_Name'] = data['routeName']
        if 'totalDistance' in data:
            update_data['Total_Distance'] = data['totalDistance']

        if not update_data:
            return jsonify({'status': 'error', 'message': 'No fields to update'}), 400

        result = cloudscale_repo.update_record(TABLES['train_routes'], route_id, update_data)
        if result.get('success'):
            return jsonify({'status': 'success', 'message': 'Route updated'}), 200
        return jsonify({'status': 'error', 'message': 'Failed to update route'}), 500
    except Exception as e:
        logger.exception(f'Update route error: {e}')
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


@train_routes_bp.route('/train-routes/<route_id>', methods=['DELETE'])
@require_admin
def delete_route(route_id):
    """Delete route (admin only)."""
    try:
        result = cloudscale_repo.delete_record(TABLES['train_routes'], route_id)
        if result.get('success'):
            return jsonify({'status': 'success', 'message': 'Route deleted'}), 200
        return jsonify({'status': 'error', 'message': 'Failed to delete route'}), 500
    except Exception as e:
        logger.exception(f'Delete route error: {e}')
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


@train_routes_bp.route('/train-routes/<route_id>/stops', methods=['GET'])
def get_route_stops(route_id):
    """Get all stops for a route."""
    try:
        stops = cloudscale_repo.get_route_stops(route_id)
        return jsonify({'status': 'success', 'data': stops}), 200
    except Exception as e:
        logger.exception(f'Get stops error: {e}')
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


@train_routes_bp.route('/train-routes/<route_id>/stops', methods=['POST'])
@require_admin
def add_stop(route_id):
    """Add a stop to a route (admin only)."""
    data = request.get_json(silent=True) or {}
    try:
        stop_data = {
            'Route_ID': int(route_id),
            'Station_ID': data.get('stationId') or data.get('Station_ID'),
            'Stop_Sequence': data.get('stopSequence') or data.get('Stop_Sequence') or 1,
            'Arrival_Time': data.get('arrivalTime') or data.get('Arrival_Time') or '',
            'Departure_Time': data.get('departureTime') or data.get('Departure_Time') or '',
            'Distance_From_Origin': data.get('distanceFromOrigin') or data.get('Distance_From_Origin') or 0,
            'Halt_Duration': data.get('haltDuration') or data.get('Halt_Duration') or 0,
            'Platform': data.get('platform') or data.get('Platform') or '',
        }
        result = cloudscale_repo.create_record(TABLES['route_stops'], stop_data)
        if result.get('success'):
            return jsonify({'status': 'success', 'data': result.get('data')}), 201
        return jsonify({'status': 'error', 'message': 'Failed to add stop'}), 500
    except Exception as e:
        logger.exception(f'Add stop error: {e}')
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500
