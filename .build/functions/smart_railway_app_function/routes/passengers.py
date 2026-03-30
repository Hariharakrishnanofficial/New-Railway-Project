"""
Passengers Routes - Passenger booking management.
"""

import logging
from flask import Blueprint, jsonify, request

from repositories.cloudscale_repository import cloudscale_repo, CriteriaBuilder
from config import TABLES
from core.security import require_auth, require_admin

logger = logging.getLogger(__name__)
passengers_bp = Blueprint('passengers', __name__)


@passengers_bp.route('/passengers', methods=['GET'])
@require_auth
def get_all_passengers():
    """Get all passengers (admin or booking-specific)."""
    try:
        booking_id = request.args.get('bookingId')

        cb = CriteriaBuilder()
        if booking_id:
            cb.id_eq('Booking_ID', booking_id)

        criteria = cb.build()
        result = cloudscale_repo.get_all_records(TABLES['passengers'], criteria=criteria, limit=200)

        if result.get('success'):
            return jsonify({'status': 'success', 'data': result.get('data', {}).get('data', [])}), 200
        return jsonify({'status': 'error', 'message': 'Failed to fetch passengers'}), 500
    except Exception as e:
        logger.exception(f'Get passengers error: {e}')
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


@passengers_bp.route('/passengers/<passenger_id>', methods=['GET'])
@require_auth
def get_passenger(passenger_id):
    """Get passenger by ID."""
    try:
        result = cloudscale_repo.get_record_by_id(TABLES['passengers'], passenger_id)
        if result.get('success') and result.get('data'):
            return jsonify({'status': 'success', 'data': result['data']}), 200
        return jsonify({'status': 'error', 'message': 'Passenger not found'}), 404
    except Exception as e:
        logger.exception(f'Get passenger error: {e}')
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


@passengers_bp.route('/passengers', methods=['POST'])
@require_auth
def create_passenger():
    """Create new passenger."""
    data = request.get_json(silent=True) or {}
    try:
        passenger_data = {
            'Booking_ID': data.get('bookingId') or data.get('Booking_ID'),
            'Passenger_Name': data.get('passengerName') or data.get('Passenger_Name') or '',
            'Age': data.get('age') or data.get('Age') or 0,
            'Gender': data.get('gender') or data.get('Gender') or '',
            'Berth_Preference': data.get('berthPreference') or data.get('Berth_Preference') or '',
            'Seat_Number': data.get('seatNumber') or data.get('Seat_Number') or '',
            'Coach_Number': data.get('coachNumber') or data.get('Coach_Number') or '',
            'Booking_Status': data.get('bookingStatus') or data.get('Booking_Status') or 'CNF',
            'Food_Choice': data.get('foodChoice') or data.get('Food_Choice') or 'None',
            'ID_Type': data.get('idType') or data.get('ID_Type') or '',
            'ID_Number': data.get('idNumber') or data.get('ID_Number') or '',
            'Contact_Number': data.get('contactNumber') or data.get('Contact_Number') or '',
        }
        result = cloudscale_repo.create_record(TABLES['passengers'], passenger_data)
        if result.get('success'):
            return jsonify({'status': 'success', 'data': result.get('data')}), 201
        return jsonify({'status': 'error', 'message': 'Failed to create passenger'}), 500
    except Exception as e:
        logger.exception(f'Create passenger error: {e}')
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


@passengers_bp.route('/passengers/<passenger_id>', methods=['PUT'])
@require_auth
def update_passenger(passenger_id):
    """Update passenger details."""
    data = request.get_json(silent=True) or {}
    try:
        update_data = {}
        field_mapping = {
            'passengerName': 'Passenger_Name',
            'age': 'Age',
            'gender': 'Gender',
            'berthPreference': 'Berth_Preference',
            'seatNumber': 'Seat_Number',
            'coachNumber': 'Coach_Number',
            'bookingStatus': 'Booking_Status',
            'foodChoice': 'Food_Choice',
            'idType': 'ID_Type',
            'idNumber': 'ID_Number',
            'contactNumber': 'Contact_Number',
        }

        for client_key, db_key in field_mapping.items():
            if client_key in data:
                update_data[db_key] = data[client_key]

        if not update_data:
            return jsonify({'status': 'error', 'message': 'No fields to update'}), 400

        result = cloudscale_repo.update_record(TABLES['passengers'], passenger_id, update_data)
        if result.get('success'):
            return jsonify({'status': 'success', 'message': 'Passenger updated'}), 200
        return jsonify({'status': 'error', 'message': 'Failed to update passenger'}), 500
    except Exception as e:
        logger.exception(f'Update passenger error: {e}')
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


@passengers_bp.route('/passengers/<passenger_id>', methods=['DELETE'])
@require_admin
def delete_passenger(passenger_id):
    """Delete passenger (admin only)."""
    try:
        result = cloudscale_repo.delete_record(TABLES['passengers'], passenger_id)
        if result.get('success'):
            return jsonify({'status': 'success', 'message': 'Passenger deleted'}), 200
        return jsonify({'status': 'error', 'message': 'Failed to delete passenger'}), 500
    except Exception as e:
        logger.exception(f'Delete passenger error: {e}')
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


@passengers_bp.route('/passengers/booking/<booking_id>', methods=['GET'])
@require_auth
def get_passengers_by_booking(booking_id):
    """Get all passengers for a specific booking."""
    try:
        result = cloudscale_repo.get_booking_passengers(booking_id)
        if result:
            return jsonify({'status': 'success', 'data': result}), 200
        return jsonify({'status': 'error', 'message': 'No passengers found for this booking'}), 404
    except Exception as e:
        logger.exception(f'Get booking passengers error: {e}')
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500