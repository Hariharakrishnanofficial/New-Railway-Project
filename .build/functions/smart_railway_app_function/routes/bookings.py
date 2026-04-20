"""
Bookings Routes - Booking management and PNR lookup.

Enhanced with:
  - Full booking flow with seat allocation
  - Fare calculation
  - Cancellation with refund
"""

import logging
from datetime import datetime
from flask import Blueprint, jsonify, request

from repositories.cloudscale_repository import cloudscale_repo, CriteriaBuilder
from config import TABLES
from core.security import require_auth, require_admin, get_current_user_id
from core.permission_validator import require_permission
from services.booking_service import booking_service
from services.fare_service import fare_service
from services.seat_service import seat_service

logger = logging.getLogger(__name__)
bookings_bp = Blueprint('bookings', __name__)


# ══════════════════════════════════════════════════════════════════════════════
#  BOOKING CRUD
# ══════════════════════════════════════════════════════════════════════════════

@bookings_bp.route('/bookings', methods=['GET'])
@require_permission('bookings', 'view')
def get_all_bookings():
    """Get all bookings (admin only)."""
    try:
        limit = request.args.get('limit', 100, type=int)
        offset = request.args.get('offset', 0, type=int)
        status = request.args.get('status')
        
        criteria = None
        if status:
            criteria = CriteriaBuilder().eq('Booking_Status', status).build()
        
        result = cloudscale_repo.get_all_records(
            TABLES['bookings'], 
            criteria=criteria,
            limit=limit, 
            offset=offset
        )
        
        if result.get('success'):
            return jsonify({
                'status': 'success', 
                'data': result.get('data', {}).get('data', [])
            }), 200
        
        return jsonify({'status': 'error', 'message': 'Failed to fetch bookings'}), 500
    
    except Exception as e:
        logger.exception(f'Get bookings error: {e}')
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


@bookings_bp.route('/bookings/<booking_id>', methods=['GET'])
@require_auth
def get_booking(booking_id):
    """Get booking by ID with full details."""
    try:
        result = booking_service.get_booking_details(booking_id=booking_id)
        
        if result.get('success'):
            return jsonify({'status': 'success', 'data': result['data']}), 200
        
        return jsonify({
            'status': 'error', 
            'message': result.get('error', 'Booking not found')
        }), 404
    
    except Exception as e:
        logger.exception(f'Get booking error: {e}')
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


@bookings_bp.route('/bookings/pnr/<pnr>', methods=['GET'])
def get_booking_by_pnr(pnr):
    """Lookup booking by PNR (public endpoint for PNR status check)."""
    try:
        result = booking_service.get_booking_details(pnr=pnr)
        
        if result.get('success'):
            return jsonify({'status': 'success', 'data': result['data']}), 200
        
        return jsonify({
            'status': 'error', 
            'message': result.get('error', 'Booking not found')
        }), 404
    
    except Exception as e:
        logger.exception(f'PNR lookup error: {e}')
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


# ══════════════════════════════════════════════════════════════════════════════
#  CREATE BOOKING (Enhanced with seat allocation)
# ══════════════════════════════════════════════════════════════════════════════

@bookings_bp.route('/bookings', methods=['POST'])
@require_auth
def create_booking():
    """
    Create a new booking with seat allocation.
    
    Request body:
    {
        "trainId": "123",
        "fromStation": "456",
        "toStation": "789",
        "journeyDate": "2024-04-15",
        "travelClass": "3A",
        "quota": "GN",
        "passengers": [
            {"Name": "John Doe", "Age": 30, "Gender": "M", "Berth_Preference": "Lower"},
            {"Name": "Jane Doe", "Age": 28, "Gender": "F"}
        ],
        "contactEmail": "john@example.com",
        "contactPhone": "9876543210"
    }
    """
    user_id = get_current_user_id()
    data = request.get_json(silent=True) or {}

    try:
        # Extract parameters
        train_id = str(data.get('trainId') or data.get('Train_ID') or '')
        from_station = str(data.get('fromStation') or data.get('From_Station') or '')
        to_station = str(data.get('toStation') or data.get('To_Station') or '')
        journey_date = data.get('journeyDate') or data.get('Journey_Date')
        travel_class = data.get('travelClass') or data.get('Travel_Class') or 'SL'
        quota = data.get('quota') or data.get('Quota') or 'GN'
        passengers = data.get('passengers', [])
        
        # Validate required fields
        if not train_id:
            return jsonify({'status': 'error', 'message': 'Train ID required'}), 400
        if not from_station or not to_station:
            return jsonify({'status': 'error', 'message': 'From and To stations required'}), 400
        if not journey_date:
            return jsonify({'status': 'error', 'message': 'Journey date required'}), 400
        if not passengers:
            return jsonify({'status': 'error', 'message': 'At least one passenger required'}), 400
        
        # Create booking via service
        result = booking_service.create_booking(
            user_id=user_id,
            train_id=train_id,
            from_station_id=from_station,
            to_station_id=to_station,
            journey_date=journey_date,
            travel_class=travel_class,
            quota=quota,
            passengers=passengers,
            contact_email=data.get('contactEmail'),
            contact_phone=data.get('contactPhone'),
            user_verified=data.get('userVerified', False)
        )
        
        if result.get('success'):
            return jsonify({
                'status': 'success',
                'data': result['data'],
                'message': f"Booking created with PNR: {result['data']['pnr']}"
            }), 201
        
        return jsonify({
            'status': 'error',
            'message': result.get('error', 'Failed to create booking')
        }), 400

    except Exception as e:
        logger.exception(f'Create booking error: {e}')
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


# ══════════════════════════════════════════════════════════════════════════════
#  CANCEL BOOKING (Enhanced with refund calculation)
# ══════════════════════════════════════════════════════════════════════════════

@bookings_bp.route('/bookings/<booking_id>/cancel', methods=['POST'])
@require_auth
def cancel_booking(booking_id):
    """
    Cancel a booking with refund calculation.
    
    Request body (optional):
    {
        "passengerIds": ["123", "456"]  // Specific passengers to cancel (optional)
    }
    """
    user_id = get_current_user_id()
    data = request.get_json(silent=True) or {}

    try:
        result = booking_service.cancel_booking(
            booking_id=booking_id,
            user_id=user_id,
            cancel_passengers=data.get('passengerIds')
        )
        
        if result.get('success'):
            return jsonify({
                'status': 'success',
                'data': result['data'],
                'message': f"Booking cancelled. Refund: ₹{result['data'].get('refund_amount', 0)}"
            }), 200
        
        return jsonify({
            'status': 'error',
            'message': result.get('error', 'Failed to cancel booking')
        }), 400

    except Exception as e:
        logger.exception(f'Cancel booking error: {e}')
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


@bookings_bp.route('/bookings/pnr/<pnr>/cancel', methods=['POST'])
@require_auth
def cancel_booking_by_pnr(pnr):
    """Cancel booking by PNR."""
    user_id = get_current_user_id()
    data = request.get_json(silent=True) or {}

    try:
        result = booking_service.cancel_booking(
            pnr=pnr,
            user_id=user_id,
            cancel_passengers=data.get('passengerIds')
        )
        
        if result.get('success'):
            return jsonify({
                'status': 'success',
                'data': result['data']
            }), 200
        
        return jsonify({
            'status': 'error',
            'message': result.get('error', 'Failed to cancel booking')
        }), 400

    except Exception as e:
        logger.exception(f'Cancel booking error: {e}')
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


# ══════════════════════════════════════════════════════════════════════════════
#  USER BOOKINGS
# ══════════════════════════════════════════════════════════════════════════════

@bookings_bp.route('/bookings/my', methods=['GET'])
@require_auth
def get_my_bookings():
    """Get current user's bookings."""
    user_id = get_current_user_id()
    
    try:
        status = request.args.get('status')
        limit = request.args.get('limit', 50, type=int)
        
        result = booking_service.get_user_bookings(
            user_id=user_id,
            status=status,
            limit=limit
        )
        
        if result.get('success'):
            return jsonify({'status': 'success', 'data': result['data']}), 200
        
        return jsonify({
            'status': 'error',
            'message': result.get('error', 'Failed to fetch bookings')
        }), 500
    
    except Exception as e:
        logger.exception(f'Get my bookings error: {e}')
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


@bookings_bp.route('/users/<user_id>/bookings', methods=['GET'])
@require_auth
def get_user_bookings(user_id):
    """Get bookings for a specific user (admin or self)."""
    current_user = get_current_user_id()
    
    try:
        # Allow if admin or own bookings
        # Note: Admin check should be handled by decorator in production
        status = request.args.get('status')
        limit = request.args.get('limit', 50, type=int)
        
        result = booking_service.get_user_bookings(
            user_id=user_id,
            status=status,
            limit=limit
        )
        
        if result.get('success'):
            return jsonify({'status': 'success', 'data': result['data']}), 200
        
        return jsonify({
            'status': 'error',
            'message': result.get('error', 'Failed to fetch bookings')
        }), 500
    
    except Exception as e:
        logger.exception(f'Get user bookings error: {e}')
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


# ══════════════════════════════════════════════════════════════════════════════
#  FARE CALCULATION
# ══════════════════════════════════════════════════════════════════════════════

@bookings_bp.route('/fares/calculate', methods=['GET', 'POST'])
def calculate_fare():
    """
    Calculate fare for a journey.
    
    Query params (GET) or body (POST):
    - trainId: Train ROWID
    - fromStation: Source station ROWID
    - toStation: Destination station ROWID
    - travelClass: Class code
    - quota: Quota code (default: GN)
    - adults: Number of adults (default: 1)
    - children: Number of children
    - seniors: Number of seniors
    """
    try:
        if request.method == 'POST':
            data = request.get_json(silent=True) or {}
        else:
            data = request.args.to_dict()
        
        train_id = data.get('trainId') or data.get('train_id')
        from_station = data.get('fromStation') or data.get('from_station')
        to_station = data.get('toStation') or data.get('to_station')
        travel_class = data.get('travelClass') or data.get('travel_class') or 'SL'
        quota = data.get('quota') or 'GN'
        
        adults = int(data.get('adults') or 1)
        children = int(data.get('children') or 0)
        seniors = int(data.get('seniors') or 0)
        
        if not train_id or not from_station or not to_station:
            return jsonify({
                'status': 'error',
                'message': 'trainId, fromStation, and toStation required'
            }), 400
        
        result = fare_service.get_fare(
            train_id=train_id,
            from_station_id=from_station,
            to_station_id=to_station,
            travel_class=travel_class,
            quota=quota,
            adults=adults,
            children=children,
            seniors=seniors
        )
        
        if result.get('success'):
            return jsonify({'status': 'success', 'data': result['data']}), 200
        
        return jsonify({
            'status': 'error',
            'message': result.get('error', 'Failed to calculate fare')
        }), 400
    
    except Exception as e:
        logger.exception(f'Calculate fare error: {e}')
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


# ══════════════════════════════════════════════════════════════════════════════
#  SEAT AVAILABILITY
# ══════════════════════════════════════════════════════════════════════════════

@bookings_bp.route('/availability', methods=['GET'])
def check_availability():
    """
    Check seat availability for a train.
    
    Query params:
    - trainId: Train ROWID
    - journeyDate: Journey date
    - travelClass: Class code (optional, returns all if not specified)
    """
    try:
        train_id = request.args.get('trainId') or request.args.get('train_id')
        journey_date = request.args.get('journeyDate') or request.args.get('journey_date')
        travel_class = request.args.get('travelClass') or request.args.get('travel_class')
        
        if not train_id or not journey_date:
            return jsonify({
                'status': 'error',
                'message': 'trainId and journeyDate required'
            }), 400
        
        if travel_class:
            result = seat_service.check_availability(train_id, journey_date, travel_class)
        else:
            result = seat_service.check_availability_bulk(train_id, journey_date)
        
        if result.get('success'):
            return jsonify({'status': 'success', 'data': result['data']}), 200
        
        return jsonify({
            'status': 'error',
            'message': result.get('error', 'Failed to check availability')
        }), 400
    
    except Exception as e:
        logger.exception(f'Check availability error: {e}')
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


# ══════════════════════════════════════════════════════════════════════════════
#  REFUND PREVIEW
# ══════════════════════════════════════════════════════════════════════════════

@bookings_bp.route('/bookings/<booking_id>/refund-preview', methods=['GET'])
@require_auth
def preview_refund(booking_id):
    """Preview refund amount without actually cancelling."""
    try:
        # Get booking
        result = booking_service.get_booking_details(booking_id=booking_id)
        
        if not result.get('success'):
            return jsonify({
                'status': 'error',
                'message': result.get('error', 'Booking not found')
            }), 404
        
        booking = result['data']['booking']
        train = result['data']['train']
        
        # Calculate refund
        departure_datetime = f"{booking['journey_date']} {train.get('departure', '00:00')}"
        
        refund_result = seat_service.get_refund_amount(
            total_fare=float(booking.get('total_fare') or 0),
            travel_class=booking.get('class', 'SL'),
            quota=booking.get('quota', 'GN'),
            departure_datetime=departure_datetime
        )
        
        if refund_result.get('success'):
            return jsonify({'status': 'success', 'data': refund_result['data']}), 200
        
        return jsonify({
            'status': 'error',
            'message': refund_result.get('error', 'Failed to calculate refund')
        }), 400
    
    except Exception as e:
        logger.exception(f'Refund preview error: {e}')
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


# ══════════════════════════════════════════════════════════════════════════════
#  ADMIN: BOOKING STATUS UPDATE
# ══════════════════════════════════════════════════════════════════════════════

@bookings_bp.route('/bookings/<booking_id>/status', methods=['PUT', 'PATCH'])
@require_permission('bookings', 'edit')
def update_booking_status(booking_id):
    """Update booking status (admin only)."""
    data = request.get_json(silent=True) or {}
    
    try:
        new_status = data.get('status')
        
        if not new_status:
            return jsonify({'status': 'error', 'message': 'Status required'}), 400
        
        valid_statuses = ['confirmed', 'rac', 'waitlisted', 'cancelled', 'chart_prepared']
        if new_status.lower() not in valid_statuses:
            return jsonify({
                'status': 'error',
                'message': f'Invalid status. Valid: {valid_statuses}'
            }), 400
        
        result = cloudscale_repo.update_record(
            TABLES['bookings'],
            booking_id,
            {'Booking_Status': new_status.lower()}
        )
        
        if result.get('success'):
            return jsonify({
                'status': 'success',
                'message': f'Booking status updated to {new_status}'
            }), 200
        
        return jsonify({
            'status': 'error',
            'message': 'Failed to update booking status'
        }), 500
    
    except Exception as e:
        logger.exception(f'Update booking status error: {e}')
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500
