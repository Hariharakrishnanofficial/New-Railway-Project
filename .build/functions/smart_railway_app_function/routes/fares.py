"""
Fares Routes - Fare rules and calculation.
"""

import logging
from flask import Blueprint, jsonify, request

from repositories.cloudscale_repository import cloudscale_repo
from config import (
    TABLES, BASE_FARE_PER_KM, RESERVATION_CHARGE, SUPERFAST_SURCHARGE,
    TATKAL_PREMIUM_PERCENT, TATKAL_MIN_CHARGE, TATKAL_MAX_CHARGE,
    GST_RATE, AC_CLASSES
)
from core.security import require_admin

logger = logging.getLogger(__name__)
fares_bp = Blueprint('fares', __name__)


def calculate_fare(distance_km, travel_class, is_tatkal=False, is_superfast=True, concession_type=None):
    """Calculate IRCTC-style fare."""
    # Base fare
    base_rate = BASE_FARE_PER_KM.get(travel_class, 1.0)
    base_fare = distance_km * base_rate

    # Reservation charge
    res_charge = RESERVATION_CHARGE.get(travel_class, 20)

    # Superfast surcharge
    sf_charge = SUPERFAST_SURCHARGE.get(travel_class, 30) if is_superfast else 0

    # Tatkal charge
    tatkal_charge = 0
    if is_tatkal:
        tatkal_raw = base_fare * (TATKAL_PREMIUM_PERCENT / 100)
        min_charge = TATKAL_MIN_CHARGE.get(travel_class, 100)
        max_charge = TATKAL_MAX_CHARGE.get(travel_class, 400)
        tatkal_charge = max(min_charge, min(tatkal_raw, max_charge))

    # Subtotal
    subtotal = base_fare + res_charge + sf_charge + tatkal_charge

    # GST (5% for AC classes only)
    gst = subtotal * GST_RATE if travel_class in AC_CLASSES else 0

    # Total
    total = subtotal + gst

    # Apply concession
    concession_discount = 0
    if concession_type:
        from config import CONCESSION_RATES
        discount_rate = CONCESSION_RATES.get(concession_type, 0)
        concession_discount = (base_fare + res_charge) * discount_rate

    final_total = max(total - concession_discount, res_charge)

    return {
        'baseFare': round(base_fare, 2),
        'reservationCharge': res_charge,
        'superfastSurcharge': sf_charge,
        'tatkalCharge': round(tatkal_charge, 2),
        'subtotal': round(subtotal, 2),
        'gst': round(gst, 2),
        'concessionDiscount': round(concession_discount, 2),
        'totalFare': round(final_total, 2),
    }


@fares_bp.route('/fares', methods=['GET'])
def get_all_fares():
    """Get all fare rules."""
    try:
        result = cloudscale_repo.get_all_records(TABLES['fares'], limit=200)
        if result.get('success'):
            return jsonify({'status': 'success', 'data': result.get('data', {}).get('data', [])}), 200
        return jsonify({'status': 'error', 'message': 'Failed to fetch fares'}), 500
    except Exception as e:
        logger.exception(f'Get fares error: {e}')
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


@fares_bp.route('/fares/calculate', methods=['POST'])
def calculate_fare_endpoint():
    """Calculate fare for a journey."""
    data = request.get_json(silent=True) or {}

    distance = data.get('distance', 0)
    travel_class = data.get('travelClass') or data.get('class') or 'SL'
    is_tatkal = data.get('isTatkal', False)
    is_superfast = data.get('isSuperfast', True)
    concession = data.get('concession')

    if distance <= 0:
        return jsonify({'status': 'error', 'message': 'Distance must be greater than 0'}), 400

    try:
        fare = calculate_fare(distance, travel_class, is_tatkal, is_superfast, concession)
        return jsonify({'status': 'success', 'data': fare}), 200
    except Exception as e:
        logger.exception(f'Calculate fare error: {e}')
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


@fares_bp.route('/fares', methods=['POST'])
@require_admin
def create_fare():
    """Create a new fare rule (admin only)."""
    data = request.get_json(silent=True) or {}
    try:
        fare_data = {
            'Train_Type': data.get('trainType') or data.get('Train_Type') or '',
            'Travel_Class': data.get('travelClass') or data.get('Travel_Class') or '',
            'Base_Rate_Per_Km': data.get('baseRatePerKm') or data.get('Base_Rate_Per_Km') or 0,
            'Min_Fare': data.get('minFare') or data.get('Min_Fare') or 0,
            'Max_Fare': data.get('maxFare') or data.get('Max_Fare') or 0,
        }
        result = cloudscale_repo.create_record(TABLES['fares'], fare_data)
        if result.get('success'):
            return jsonify({'status': 'success', 'data': result.get('data')}), 201
        return jsonify({'status': 'error', 'message': 'Failed to create fare'}), 500
    except Exception as e:
        logger.exception(f'Create fare error: {e}')
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


@fares_bp.route('/fares/<fare_id>', methods=['PUT'])
@require_admin
def update_fare(fare_id):
    """Update fare rule (admin only)."""
    data = request.get_json(silent=True) or {}
    try:
        update_data = {}
        field_mapping = {
            'trainType': 'Train_Type',
            'travelClass': 'Travel_Class',
            'baseRatePerKm': 'Base_Rate_Per_Km',
            'minFare': 'Min_Fare',
            'maxFare': 'Max_Fare',
        }
        for client_key, db_key in field_mapping.items():
            if client_key in data:
                update_data[db_key] = data[client_key]

        if not update_data:
            return jsonify({'status': 'error', 'message': 'No fields to update'}), 400

        result = cloudscale_repo.update_record(TABLES['fares'], fare_id, update_data)
        if result.get('success'):
            return jsonify({'status': 'success', 'message': 'Fare updated'}), 200
        return jsonify({'status': 'error', 'message': 'Failed to update fare'}), 500
    except Exception as e:
        logger.exception(f'Update fare error: {e}')
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


@fares_bp.route('/fares/<fare_id>', methods=['DELETE'])
@require_admin
def delete_fare(fare_id):
    """Delete fare rule (admin only)."""
    try:
        result = cloudscale_repo.delete_record(TABLES['fares'], fare_id)
        if result.get('success'):
            return jsonify({'status': 'success', 'message': 'Fare deleted'}), 200
        return jsonify({'status': 'error', 'message': 'Failed to delete fare'}), 500
    except Exception as e:
        logger.exception(f'Delete fare error: {e}')
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500
