"""
Admin Reports routes — revenue reports, occupancy reports, admin logs.
"""

import json
import logging
from datetime import datetime
from flask import Blueprint, jsonify, request
from services.zoho_service import zoho
from config import TABLES
from core.security import require_admin
from utils.date_helpers import to_zoho_date_only

logger = logging.getLogger(__name__)

admin_reports_bp = Blueprint('admin_reports', __name__)


# ==================== REVENUE REPORT ====================

@admin_reports_bp.route('/reports/revenue', methods=['GET'])
@require_admin
def revenue_report():
    """
    GET /api/reports/revenue?from=YYYY-MM-DD&to=YYYY-MM-DD
    Revenue aggregation by date range, grouped by class and train.
    """
    from_date = request.args.get('from', '').strip()
    to_date   = request.args.get('to', '').strip()

    result = zoho.get_all_records(TABLES['bookings'], criteria=None, limit=1000)
    if not result.get('success'):
        return jsonify(result), result.get('status_code', 500)

    bookings = result.get('data', {}).get('data', []) or []

    # Filter by date range
    def parse_to_ymd(d):
        if not d:
            return ''
        try:
            return datetime.strptime(str(d).split(' ')[0], '%d-%b-%Y').strftime('%Y-%m-%d')
        except Exception:
            return str(d)[:10]

    filtered = []
    for b in bookings:
        if (b.get('Booking_Status') or '').lower() == 'cancelled':
            continue

        bt = parse_to_ymd(b.get('Booking_Time') or b.get('Added_Time', ''))
        if from_date and bt < from_date:
            continue
        if to_date and bt > to_date:
            continue
        filtered.append(b)

    # Aggregate
    total_revenue = 0
    by_class = {}
    by_train = {}
    by_date = {}
    total_passengers = 0

    for b in filtered:
        fare = float(b.get('Total_Fare') or 0)
        cls = b.get('Class', 'Unknown')
        pax_count = int(b.get('Num_Passengers') or 0)
        booking_date = parse_to_ymd(b.get('Booking_Time') or b.get('Added_Time', ''))

        total_revenue += fare
        total_passengers += pax_count

        # By class
        if cls not in by_class:
            by_class[cls] = {'revenue': 0, 'bookings': 0, 'passengers': 0}
        by_class[cls]['revenue'] += fare
        by_class[cls]['bookings'] += 1
        by_class[cls]['passengers'] += pax_count

        # By train
        train_field = b.get('Trains', {})
        train_name = train_field.get('display_value', 'Unknown') if isinstance(train_field, dict) else str(train_field or 'Unknown')
        if train_name not in by_train:
            by_train[train_name] = {'revenue': 0, 'bookings': 0, 'passengers': 0}
        by_train[train_name]['revenue'] += fare
        by_train[train_name]['bookings'] += 1
        by_train[train_name]['passengers'] += pax_count

        # By date
        if booking_date:
            if booking_date not in by_date:
                by_date[booking_date] = {'revenue': 0, 'bookings': 0}
            by_date[booking_date]['revenue'] += fare
            by_date[booking_date]['bookings'] += 1

    # Round values
    for k in by_class:
        by_class[k]['revenue'] = round(by_class[k]['revenue'], 2)
    for k in by_train:
        by_train[k]['revenue'] = round(by_train[k]['revenue'], 2)
    for k in by_date:
        by_date[k]['revenue'] = round(by_date[k]['revenue'], 2)

    return jsonify({
        'success': True,
        'data': {
            'total_revenue':     round(total_revenue, 2),
            'total_bookings':    len(filtered),
            'total_passengers':  total_passengers,
            'by_class':          by_class,
            'by_train':          by_train,
            'by_date':           dict(sorted(by_date.items())),
            'details':           filtered if request.args.get('details') == 'true' else None,
            'date_range': {
                'from': from_date or 'All time',
                'to':   to_date or 'Present',
            }
        },
        'status_code': 200
    }), 200


# ==================== OCCUPANCY REPORT ====================

@admin_reports_bp.route('/reports/occupancy', methods=['GET'])
@require_admin
def occupancy_report():
    """
    GET /api/reports/occupancy?date=YYYY-MM-DD
    Train occupancy percentage by class for a given date.
    """
    date = request.args.get('date', '').strip()

    # Fetch all trains
    trains_res = zoho.get_all_records(TABLES['trains'], criteria=None, limit=500)
    trains = trains_res.get('data', {}).get('data', []) if trains_res.get('success') else []

    # Fetch all bookings
    bookings_res = zoho.get_all_records(TABLES['bookings'], criteria=None, limit=1000)
    bookings = bookings_res.get('data', {}).get('data', []) if bookings_res.get('success') else []

    zoho_date = to_zoho_date_only(date) if date else None

    # Count passengers by train and class, and store details
    train_bookings = {}
    detail_map = {}
    for b in bookings:
        if (b.get('Booking_Status') or '').lower() == 'cancelled':
            continue

        if zoho_date:
            b_date = to_zoho_date_only(b.get('Journey_Date', ''))
            if b_date != zoho_date:
                continue

        train_field = b.get('Trains', {})
        train_id = train_field.get('ID', '') if isinstance(train_field, dict) else str(train_field or '')
        cls = b.get('Class', 'Unknown')
        pax_count = int(b.get('Passenger_Count') or b.get('Num_Passengers') or 0)

        if train_id not in train_bookings:
            train_bookings[train_id] = {}
        if cls not in train_bookings[train_id]:
            train_bookings[train_id][cls] = 0
        train_bookings[train_id][cls] += pax_count

        if train_id not in detail_map:
            detail_map[train_id] = []
        detail_map[train_id].append(b)

    # Build occupancy data
    occupancy_list = []
    for t in trains:
        tid = str(t.get('ID', ''))
        # if str(t.get('Is_Active', 'true')).lower() == 'false':
        #     continue

        train_booked = train_bookings.get(tid, {})
        if not train_booked and date:
            continue  # Skip trains with no bookings on this date

        total_map = {
            'SL': int(t.get('Total_Seats_SL') or 0),
            '3A': int(t.get('Total_Seats_3A') or 0),
            '2A': int(t.get('Total_Seats_2A') or 0),
            '1A': int(t.get('Total_Seats_1A') or 0),
            'CC': int(t.get('Total_Seats_CC') or 0),
            '2S': int(t.get('Total_Seats_2S') or 0),
        }

        classes = {}
        for cls, total in total_map.items():
            if total <= 0:
                continue
            booked = train_booked.get(cls, 0)
            pct = round((booked / total) * 100, 1) if total > 0 else 0
            classes[cls] = {
                'total': total,
                'booked': booked,
                'available': max(0, total - booked),
                'occupancy_pct': pct,
            }

        total_capacity = sum(v['total'] for v in classes.values())
        total_booked = sum(v['booked'] for v in classes.values())
        overall_pct = round((total_booked / total_capacity) * 100, 1) if total_capacity > 0 else 0

        occupancy_list.append({
            'train_id':      tid,
            'train_name':    t.get('Train_Name', ''),
            'train_number':  t.get('Train_Number', ''),
            'classes':       classes,
            'overall': {
                'total_capacity': total_capacity,
                'total_booked':   total_booked,
                'occupancy_pct':  overall_pct,
            }
        })

    # Sort by occupancy descending
    occupancy_list.sort(key=lambda x: x['overall']['occupancy_pct'], reverse=True)

    return jsonify({
        'success': True,
        'data': {
            'date': date or 'All dates',
            'trains': occupancy_list,
            'total_trains': len(occupancy_list),
            'details': detail_map if request.args.get('details') == 'true' else None
        },
        'status_code': 200
    }), 200


# ==================== ADMIN LOGS ====================

@admin_reports_bp.route('/admin/logs', methods=['GET'])
@require_admin
def get_admin_logs():
    """GET /api/admin/logs — retrieves admin action audit trail."""
    limit = request.args.get('limit', 100, type=int)
    action = request.args.get('action')
    resource_type = request.args.get('resource_type')

    criteria = None
    if action:
        criteria = f'(Action == "{action}")'
    if resource_type:
        if criteria:
            criteria += f' && (Resource_Type == "{resource_type}")'
        else:
            criteria = f'(Resource_Type == "{resource_type}")'

    result = zoho.get_all_records(TABLES['admin_logs'], criteria=criteria, limit=limit)
    return jsonify(result), result.get('status_code', 200)


@admin_reports_bp.route('/admin/logs', methods=['POST'])
@require_admin
def create_admin_log():
    """POST /api/admin/logs — create an admin action log entry."""
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'No data provided'}), 400

    payload = {
        'Admin_User':    data.get('Admin_User', ''),
        'Action':        data.get('Action', ''),
        'Resource_Type': data.get('Resource_Type', ''),
        'Resource_ID':   data.get('Resource_ID', ''),
        'Old_Value':     data.get('Old_Value', ''),
        'New_Value':     data.get('New_Value', ''),
        'Timestamp':     datetime.now().strftime('%d-%b-%Y %H:%M:%S'),
        'IP_Address':    request.headers.get('X-Forwarded-For', request.remote_addr or ''),
    }

    result = zoho.create_record(TABLES['admin_logs'], payload)
    return jsonify(result), result.get('status_code', 200)
