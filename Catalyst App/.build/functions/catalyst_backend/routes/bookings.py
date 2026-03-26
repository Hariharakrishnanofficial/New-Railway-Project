"""
Bookings routes — thin HTTP handlers delegating to BookingService.
All business logic lives in services/booking_service.py.
"""

import json
import logging
from datetime import datetime
from flask import Blueprint, jsonify, request

from services.booking_service import booking_service
from services.zoho_service import zoho
from config import get_form_config
from core.security import require_admin, require_auth, get_current_user_id
from core.exceptions import RailwayException
from utils.date_helpers import to_zoho_date_only, to_zoho_datetime
from utils.log_helper import log_admin_action

logger    = logging.getLogger(__name__)
bookings_bp = Blueprint('bookings', __name__)


# ── CREATE ────────────────────────────────────────────────────────────────────
@bookings_bp.route('/api/bookings', methods=['POST'])
def create_booking():
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'No data provided'}), 400
    try:
        result = booking_service.create(data)
        return jsonify({'success': True, 'data': result, 'status_code': 201}), 201
    except RailwayException as e:
        return jsonify(e.to_response()), e.status_code
    except Exception as e:
        logger.exception(f'create_booking: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500


# ── LIST ──────────────────────────────────────────────────────────────────────
@bookings_bp.route('/api/bookings', methods=['GET'])
def get_bookings():
    forms         = get_form_config()
    limit         = request.args.get('limit', 200, type=int)
    status_filter = request.args.get('status')
    user_filter   = request.args.get('user_id')

    from repositories.cloudscale_repository import CriteriaBuilder
    cb = CriteriaBuilder()
    if status_filter: cb.eq('Booking_Status', status_filter)
    if user_filter:   cb.eq('Users', user_filter)
    criteria = cb.build()

    result = zoho.get_all_records(forms['reports']['bookings'], criteria=criteria, limit=limit)
    return jsonify(result), result.get('status_code', 200)


# ── GET BY ID ─────────────────────────────────────────────────────────────────
@bookings_bp.route('/api/bookings/<booking_id>', methods=['GET'])
def get_booking(booking_id):
    forms  = get_form_config()
    result = zoho.get_record_by_id(forms['reports']['bookings'], booking_id)
    return jsonify(result), result.get('status_code', 200)


# ── PNR LOOKUP ────────────────────────────────────────────────────────────────
@bookings_bp.route('/api/bookings/pnr/<pnr>', methods=['GET'])
def get_booking_by_pnr(pnr):
    forms  = get_form_config()
    result = zoho.get_all_records(forms['reports']['bookings'],
                                   criteria=f'(PNR == "{pnr}")', limit=1)
    if not result.get('success'):
        return jsonify(result), result.get('status_code', 500)
    records = result.get('data', {}).get('data', [])
    if records:
        booking = records[0]
        raw = booking.get('Passengers', '[]')
        if isinstance(raw, str):
            try: booking['Passengers'] = json.loads(raw)
            except Exception: booking['Passengers'] = []
        return jsonify({'success': True, 'data': {'data': booking}}), 200
    return jsonify({'success': False, 'error': 'PNR not found'}), 404


# ── UPDATE ────────────────────────────────────────────────────────────────────
@bookings_bp.route('/api/bookings/<booking_id>', methods=['PUT'])
@require_admin
def update_booking(booking_id):
    forms = get_form_config()
    data  = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'No data provided'}), 400
    
    user_email = request.headers.get('X-User-Email', 'Unknown')
    log_admin_action(user_email, 'UPDATE_BOOKING', {'record_id': booking_id, 'updated_data': data})

    result = zoho.update_record(forms['reports']['bookings'], booking_id, data)
    return jsonify(result), result.get('status_code', 200)


# ── DELETE ────────────────────────────────────────────────────────────────────
@bookings_bp.route('/api/bookings/<booking_id>', methods=['DELETE'])
@require_admin
def delete_booking(booking_id):
    forms  = get_form_config()
    
    user_email = request.headers.get('X-User-Email', 'Unknown')
    log_admin_action(user_email, 'DELETE_BOOKING', {'record_id': booking_id})

    result = zoho.delete_record(forms['reports']['bookings'], booking_id)
    return jsonify(result), result.get('status_code', 200)


# ── CONFIRM ───────────────────────────────────────────────────────────────────
@bookings_bp.route('/api/bookings/<booking_id>/confirm', methods=['POST'])
@require_admin
def confirm_booking(booking_id):
    forms  = get_form_config()

    user_email = request.headers.get('X-User-Email', 'Unknown')
    log_admin_action(user_email, 'CONFIRM_BOOKING', {'record_id': booking_id})

    result = zoho.update_record(forms['reports']['bookings'], booking_id,
                                 {'Booking_Status': 'confirmed'})
    return jsonify(result), result.get('status_code', 200)


# ── PAY ───────────────────────────────────────────────────────────────────────
@bookings_bp.route('/api/bookings/<booking_id>/pay', methods=['POST'])
@require_admin
def mark_booking_paid(booking_id):
    forms = get_form_config()
    data  = request.get_json(silent=True) or {}
    result = zoho.update_record(forms['reports']['bookings'], booking_id, {
        'Payment_Status': 'paid',
        'Payment_Method': data.get('Payment_Method', 'online'),
    })
    if result.get('success'):
        log_admin_action('mark_booking_paid', record_id=booking_id)
    return jsonify(result), result.get('status_code', 200)


# ── CANCEL ────────────────────────────────────────────────────────────────────
@bookings_bp.route('/api/bookings/<booking_id>/cancel', methods=['POST'])
def cancel_booking(booking_id):
    try:
        result = booking_service.cancel(booking_id)
        return jsonify({'success': True, 'message': 'Booking cancelled', 'data': result}), 200
    except RailwayException as e:
        return jsonify(e.to_response()), e.status_code
    except Exception as e:
        logger.exception(f'cancel_booking: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500


# ── PARTIAL CANCEL ────────────────────────────────────────────────────────────
@bookings_bp.route('/api/bookings/<booking_id>/partial-cancel', methods=['POST'])
def partial_cancel(booking_id):
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'No data provided'}), 400
    indices = data.get('passenger_indices', [])
    if not indices:
        return jsonify({'success': False, 'error': 'passenger_indices is required'}), 400
    try:
        result = booking_service.partial_cancel(booking_id, indices)
        return jsonify({'success': True, 'data': result}), 200
    except RailwayException as e:
        return jsonify(e.to_response()), e.status_code
    except Exception as e:
        logger.exception(f'partial_cancel: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500


# ── TICKET ────────────────────────────────────────────────────────────────────
@bookings_bp.route('/api/bookings/<booking_id>/ticket', methods=['GET'])
def get_ticket(booking_id):
    forms  = get_form_config()
    bk     = zoho.get_record_by_id(forms['reports']['bookings'], booking_id)
    if not bk.get('success'):
        return jsonify({'success': False, 'error': 'Booking not found'}), 404

    booking = bk.get('data', {}).get('data') or bk.get('data') or {}
    raw = booking.get('Passengers', '[]')
    if isinstance(raw, str):
        try: passengers = json.loads(raw)
        except Exception: passengers = []
    else:
        passengers = raw or []

    train_field = booking.get('Trains', {})
    train_name  = train_field.get('display_value', '') if isinstance(train_field, dict) else ''
    user_field  = booking.get('Users', {})
    user_name   = user_field.get('display_value', '') if isinstance(user_field, dict) else ''

    ticket = {
        'PNR':               booking.get('PNR'),
        'Train':             train_name,
        'Journey_Date':      booking.get('Journey_Date'),
        'Class':             booking.get('Class'),
        'Quota':             booking.get('Quota', 'General'),
        'Booking_Status':    booking.get('Booking_Status'),
        'Payment_Status':    booking.get('Payment_Status'),
        'Total_Fare':        booking.get('Total_Fare'),
        'Passenger_Name':    user_name,
        'Boarding_Station':  booking.get('Boarding_Station', ''),
        'Deboarding_Station': booking.get('Deboarding_Station', ''),
        'Booking_Time':      booking.get('Booking_Time'),
        'passengers': [{
            'name':   p.get('Passenger_Name', p.get('Name', '')),
            'age':    p.get('Age', ''),
            'gender': p.get('Gender', ''),
            'status': p.get('Current_Status', ''),
            'coach':  p.get('Coach', ''),
            'seat':   p.get('Seat_Number', ''),
            'berth':  p.get('Berth', ''),
        } for p in passengers],
    }
    return jsonify({'success': True, 'data': ticket}), 200


# ── RESERVATION CHART (optimized — uses criteria, no full scan) ───────────────
@bookings_bp.route('/api/bookings/chart', methods=['GET'])
@require_admin
def reservation_chart():
    train_id     = request.args.get('train_id', '').strip()
    journey_date = request.args.get('date', '').strip()
    cls          = request.args.get('class', '').strip()

    if not train_id:
        return jsonify({'success': False, 'error': 'train_id is required'}), 400

    from repositories.cloudscale_repository import zoho_repo
    zoho_date = to_zoho_date_only(journey_date) if journey_date else None

    # Optimized: targeted query instead of fetching all bookings
    bookings = zoho_repo.get_active_bookings_for_train_date(train_id, zoho_date) if zoho_date \
               else zoho_repo.get_records(get_form_config()['reports']['bookings'],
                                           criteria=f'(Trains == "{train_id}") && (Booking_Status != "cancelled")',
                                           limit=500)

    chart = {}
    for b in bookings:
        if cls and (b.get('Class') or '').upper() != cls.upper():
            continue
        raw = b.get('Passengers', '[]')
        if isinstance(raw, str):
            try: plist = json.loads(raw)
            except Exception: plist = []
        else:
            plist = raw or []

        for p in plist:
            if p.get('Cancelled'):
                continue
            coach = p.get('Coach', 'Unassigned')
            chart.setdefault(coach, []).append({
                'PNR':    b.get('PNR', ''),
                'Name':   p.get('Passenger_Name', p.get('Name', '')),
                'Age':    p.get('Age', ''),
                'Gender': p.get('Gender', ''),
                'Status': p.get('Current_Status', ''),
                'Seat':   p.get('Seat_Number', ''),
                'Berth':  p.get('Berth', ''),
            })

    for coach in chart:
        chart[coach].sort(key=lambda x: int(x.get('Seat') or 0))

    return jsonify({'success': True, 'data': {
        'train_id': train_id, 'journey_date': journey_date,
        'class': cls or 'All', 'chart': chart,
        'total_passengers': sum(len(v) for v in chart.values()),
    }}), 200
