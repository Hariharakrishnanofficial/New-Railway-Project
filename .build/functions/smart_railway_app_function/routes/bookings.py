"""
Bookings Routes - Booking management and PNR lookup.
"""

import logging
import uuid
from datetime import datetime
from flask import Blueprint, jsonify, request

from repositories.cloudscale_repository import cloudscale_repo, CriteriaBuilder
from config import TABLES
from core.security import require_auth, require_admin, get_current_user_id

logger = logging.getLogger(__name__)
bookings_bp = Blueprint('bookings', __name__)


def generate_pnr():
    """Generate IRCTC-style PNR."""
    return 'PNR' + uuid.uuid4().hex[:8].upper()


@bookings_bp.route('/bookings', methods=['GET'])
@require_admin
def get_all_bookings():
    """Get all bookings (admin only)."""
    try:
        limit = request.args.get('limit', 100, type=int)
        offset = request.args.get('offset', 0, type=int)
        result = cloudscale_repo.get_all_records(TABLES['bookings'], limit=limit, offset=offset)
        if result.get('success'):
            return jsonify({'status': 'success', 'data': result.get('data', {}).get('data', [])}), 200
        return jsonify({'status': 'error', 'message': 'Failed to fetch bookings'}), 500
    except Exception as e:
        logger.exception(f'Get bookings error: {e}')
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


@bookings_bp.route('/bookings/<booking_id>', methods=['GET'])
@require_auth
def get_booking(booking_id):
    """Get booking by ID."""
    try:
        result = cloudscale_repo.get_record_by_id(TABLES['bookings'], booking_id)
        if result.get('success') and result.get('data'):
            booking = result['data']
            passengers = cloudscale_repo.get_passengers_by_booking(booking_id)
            booking['passengers'] = passengers
            return jsonify({'status': 'success', 'data': booking}), 200
        return jsonify({'status': 'error', 'message': 'Booking not found'}), 404
    except Exception as e:
        logger.exception(f'Get booking error: {e}')
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


@bookings_bp.route('/bookings/pnr/<pnr>', methods=['GET'])
def get_booking_by_pnr(pnr):
    """Lookup booking by PNR."""
    try:
        booking = cloudscale_repo.get_booking_by_pnr(pnr)
        if booking:
            passengers = cloudscale_repo.get_passengers_by_booking(booking.get('ROWID'))
            booking['passengers'] = passengers
            return jsonify({'status': 'success', 'data': booking}), 200
        return jsonify({'status': 'error', 'message': 'Booking not found'}), 404
    except Exception as e:
        logger.exception(f'PNR lookup error: {e}')
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


@bookings_bp.route('/bookings', methods=['POST'])
@require_auth
def create_booking():
    """Create a new booking."""
    user_id = get_current_user_id()
    data = request.get_json(silent=True) or {}

    try:
        pnr = generate_pnr()
        booking_data = {
            'PNR': pnr,
            'User_ID': int(user_id),
            'Train_ID': data.get('trainId') or data.get('Train_ID'),
            'Journey_Date': data.get('journeyDate') or data.get('Journey_Date'),
            'Travel_Class': data.get('travelClass') or data.get('Travel_Class') or 'SL',
            'Quota': data.get('quota') or data.get('Quota') or 'GN',
            'From_Station': data.get('fromStation') or data.get('From_Station'),
            'To_Station': data.get('toStation') or data.get('To_Station'),
            'Booking_Status': 'Pending',
            'Payment_Status': 'Unpaid',
            'Total_Fare': data.get('totalFare') or data.get('Total_Fare') or 0,
            'Booking_Time': datetime.utcnow().isoformat(),
        }

        result = cloudscale_repo.create_record(TABLES['bookings'], booking_data)
        if result.get('success'):
            booking_id = result.get('data', {}).get('ROWID')

            # Create passengers
            passengers = data.get('passengers', [])
            for i, p in enumerate(passengers):
                passenger_data = {
                    'Booking_ID': int(booking_id),
                    'Passenger_Name': p.get('name', ''),
                    'Age': p.get('age', 0),
                    'Gender': p.get('gender', ''),
                    'Berth_Preference': p.get('berthPreference', ''),
                    'Seat_Status': 'WL',
                    'Seat_Number': '',
                    'Coach': '',
                }
                cloudscale_repo.create_record(TABLES['passengers'], passenger_data)

            booking_data['ROWID'] = booking_id
            return jsonify({'status': 'success', 'data': {'booking': booking_data, 'pnr': pnr}}), 201

        return jsonify({'status': 'error', 'message': 'Failed to create booking'}), 500

    except Exception as e:
        logger.exception(f'Create booking error: {e}')
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


@bookings_bp.route('/bookings/<booking_id>/confirm', methods=['POST'])
@require_admin
def confirm_booking(booking_id):
    """Confirm a booking (admin only)."""
    try:
        result = cloudscale_repo.update_record(TABLES['bookings'], booking_id, {'Booking_Status': 'Confirmed'})
        if result.get('success'):
            return jsonify({'status': 'success', 'message': 'Booking confirmed'}), 200
        return jsonify({'status': 'error', 'message': 'Failed to confirm booking'}), 500
    except Exception as e:
        logger.exception(f'Confirm booking error: {e}')
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


@bookings_bp.route('/bookings/<booking_id>/pay', methods=['POST'])
@require_auth
def pay_booking(booking_id):
    """Mark booking as paid."""
    try:
        result = cloudscale_repo.update_record(TABLES['bookings'], booking_id, {'Payment_Status': 'Paid'})
        if result.get('success'):
            return jsonify({'status': 'success', 'message': 'Payment recorded'}), 200
        return jsonify({'status': 'error', 'message': 'Failed to record payment'}), 500
    except Exception as e:
        logger.exception(f'Pay booking error: {e}')
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


@bookings_bp.route('/bookings/<booking_id>/cancel', methods=['POST'])
@require_auth
def cancel_booking(booking_id):
    """Cancel a booking."""
    user_id = get_current_user_id()
    data = request.get_json(silent=True) or {}

    try:
        result = cloudscale_repo.get_record_by_id(TABLES['bookings'], booking_id)
        if not result.get('success') or not result.get('data'):
            return jsonify({'status': 'error', 'message': 'Booking not found'}), 404

        booking = result['data']
        if booking.get('Booking_Status') == 'Cancelled':
            return jsonify({'status': 'error', 'message': 'Booking already cancelled'}), 400

        update_result = cloudscale_repo.update_record(TABLES['bookings'], booking_id, {
            'Booking_Status': 'Cancelled',
            'Cancellation_Time': datetime.utcnow().isoformat(),
            'Cancellation_Reason': data.get('reason', ''),
        })

        if update_result.get('success'):
            return jsonify({'status': 'success', 'message': 'Booking cancelled'}), 200

        return jsonify({'status': 'error', 'message': 'Failed to cancel booking'}), 500

    except Exception as e:
        logger.exception(f'Cancel booking error: {e}')
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


@bookings_bp.route('/users/<user_id>/bookings', methods=['GET'])
@require_auth
def get_user_bookings(user_id):
    """Get bookings for a user."""
    try:
        criteria = CriteriaBuilder().id_eq('User_ID', user_id).build()
        result = cloudscale_repo.get_all_records(TABLES['bookings'], criteria=criteria, limit=100)
        if result.get('success'):
            return jsonify({'status': 'success', 'data': result.get('data', {}).get('data', [])}), 200
        return jsonify({'status': 'error', 'message': 'Failed to fetch bookings'}), 500
    except Exception as e:
        logger.exception(f'Get user bookings error: {e}')
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500
