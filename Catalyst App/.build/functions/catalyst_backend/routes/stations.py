"""
Stations routes — CRUD, search, bulk import, station manifest.
Updated: uses cached station list + cache invalidation on writes.
"""

from flask import Blueprint, jsonify, request
from services.zoho_service import zoho
from repositories.cloudscale_repository import zoho_repo
from repositories.cache_manager import cache
from core.security import require_admin
import logging

logger      = logging.getLogger(__name__)
stations_bp = Blueprint('stations', __name__)


def _is_true(val):
    if val is None:             return True
    if isinstance(val, bool):   return val
    if isinstance(val, str):    return val.lower().strip() in ('true', '1', 'yes', 'active')
    if isinstance(val, (int, float)): return val != 0
    return bool(val)


# ── CREATE ────────────────────────────────────────────────────────────────────
@stations_bp.route('/api/stations', methods=['POST'])
@require_admin
def create_station():
    data         = request.get_json() or {}
    station_code = (data.get('Station_Code') or data.get('station_code') or '').strip().upper()
    station_name = (data.get('Station_Name') or data.get('station_name') or '').strip()
    city         = (data.get('City')         or data.get('city')         or '').strip()
    state        = (data.get('State')        or data.get('state')        or '').strip()

    if not all([station_code, station_name, city, state]):
        missing = [f for f, v in [('Station_Code', station_code), ('Station_Name', station_name),
                                   ('City', city), ('State', state)] if not v]
        return jsonify({'success': False, 'error': f'Missing: {", ".join(missing)}'}), 400

    payload = {k: v for k, v in {
        'Station_Code': station_code,
        'Station_Name': station_name,
        'City':         city,
        'State':        state,
        'Zone':         data.get('Zone'),
        'Division':     data.get('Division'),
        'Station_Type': data.get('Station_Type') or 'Way Station',
        'Number_of_Platforms': int(data.get('Number_of_Platforms') or 0) if 'Number_of_Platforms' in data else None,
        'Latitude':     data.get('Latitude'),
        'Longitude':    data.get('Longitude'),
        'Is_Active':    _is_true(data.get('Is_Active', True)),
    }.items() if v is not None}

    result = zoho.create_record(zoho.forms['forms']['stations'], payload)
    if result.get('success'):
        cache.delete('stations:all')          # bust station cache
    return jsonify(result), result.get('status_code', 200)


# ── LIST (uses 24-hour cache) ─────────────────────────────────────────────────
@stations_bp.route('/api/stations', methods=['GET'])
def get_stations():
    limit  = request.args.get('limit', 500, type=int)
    search = request.args.get('search', '').strip()
    city   = request.args.get('city', '').strip()

    # Use cached list for full queries
    if not search and not city:
        records = zoho_repo.get_all_stations_cached()[:limit]
        return jsonify({'success': True, 'data': {'data': records, 'count': len(records)}}), 200

    # Filtered query — still use cached list, filter in Python
    records = zoho_repo.get_all_stations_cached()

    if city:
        records = [r for r in records if (r.get('City') or '').lower() == city.lower()]
    if search:
        s = search.lower()
        records = [r for r in records
                   if s in (r.get('Station_Code') or '').lower()
                   or s in (r.get('Station_Name') or '').lower()
                   or s in (r.get('City') or '').lower()]

    return jsonify({'success': True, 'data': {'data': records[:limit], 'count': len(records)}}), 200


# ── GET BY ID ─────────────────────────────────────────────────────────────────
@stations_bp.route('/api/stations/<station_id>', methods=['GET'])
def get_station(station_id):
    result = zoho.get_record_by_id(zoho.forms['reports']['stations'], station_id)
    return jsonify(result), result.get('status_code', 200)


# ── UPDATE ────────────────────────────────────────────────────────────────────
@stations_bp.route('/api/stations/<station_id>', methods=['PUT'])
@require_admin
def update_station(station_id):
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'No data provided'}), 400

    payload = {k: v for k, v in {
        'Station_Code': (data.get('Station_Code') or '').strip().upper() or None,
        'Station_Name': (data.get('Station_Name') or '').strip() or None,
        'City':         (data.get('City') or '').strip() or None,
        'State':        (data.get('State') or '').strip() or None,
        'Zone':         data.get('Zone'),
        'Division':     data.get('Division'),
        'Station_Type': data.get('Station_Type'),
        'Number_of_Platforms': int(data.get('Number_of_Platforms') or 0) if 'Number_of_Platforms' in data else None,
        'Latitude':     data.get('Latitude'),
        'Longitude':    data.get('Longitude'),
        'Is_Active':    _is_true(data['Is_Active']) if 'Is_Active' in data else None,
    }.items() if v is not None}

    result = zoho.update_record(zoho.forms['reports']['stations'], station_id, payload)
    if result.get('success'):
        cache.delete('stations:all')
    return jsonify(result), result.get('status_code', 200)


# ── DELETE ────────────────────────────────────────────────────────────────────
@stations_bp.route('/api/stations/<station_id>', methods=['DELETE'])
@require_admin
def delete_station(station_id):
    result = zoho.delete_record(zoho.forms['reports']['stations'], station_id)
    if result.get('success'):
        cache.delete('stations:all')
    return jsonify(result), result.get('status_code', 200)


# ── BULK IMPORT ───────────────────────────────────────────────────────────────
@stations_bp.route('/api/stations/bulk', methods=['POST'])
@require_admin
def bulk_create_stations():
    data = request.get_json() or {}
    if not data.get('stations'):
        return jsonify({'success': False, 'error': 'stations array is required'}), 400

    results = {'created': 0, 'failed': 0, 'errors': []}
    for i, s in enumerate(data['stations']):
        code  = (s.get('Station_Code') or '').strip().upper()
        name  = (s.get('Station_Name') or '').strip()
        city  = (s.get('City') or '').strip()
        state = (s.get('State') or '').strip()
        if not all([code, name, city, state]):
            results['failed'] += 1; results['errors'].append(f"Row {i+1}: Missing required fields")
            continue
        payload = {k: v for k, v in {
            'Station_Code': code,
            'Station_Name': name,
            'City':         city,
            'State':        state,
            'Zone':         s.get('Zone'),
            'Division':     s.get('Division'),
            'Station_Type': s.get('Station_Type'),
            'Number_of_Platforms': int(s.get('Number_of_Platforms') or 0) if 'Number_of_Platforms' in s else None,
            'Latitude':     s.get('Latitude'),
            'Longitude':    s.get('Longitude'),
            'Is_Active':    True
        }.items() if v is not None}
        res = zoho.create_record(zoho.forms['forms']['stations'], payload)
        if res.get('success'): results['created'] += 1
        else: results['failed'] += 1; results['errors'].append(f"Row {i+1} ({code}): {res.get('error')}")

    if results['created']:
        cache.delete('stations:all')
    return jsonify({'success': True, 'data': results,
                    'message': f"{results['created']} created, {results['failed']} failed"}), 200


# ── STATION MANIFEST ──────────────────────────────────────────────────────────
@stations_bp.route('/api/stations/<station_id>/manifest', methods=['GET'])
@require_admin
def station_manifest(station_id):
    from utils.date_helpers import to_zoho_date_only
    import json as jsonlib
    from repositories.cloudscale_repository import CriteriaBuilder

    date = request.args.get('date', '').strip()

    station_res = zoho.get_record_by_id(zoho.forms['reports']['stations'], station_id)
    if not station_res.get('success'):
        return jsonify({'success': False, 'error': 'Station not found'}), 404
    station      = station_res.get('data', {}).get('data') or station_res.get('data') or {}
    station_code = station.get('Station_Code', '')

    zoho_date = to_zoho_date_only(date) if date else None

    # Fetch only active bookings for the date (optimized)
    cb = CriteriaBuilder().ne('Booking_Status', 'cancelled')
    if zoho_date: cb.eq('Journey_Date', zoho_date)
    bookings = zoho_repo.get_records(zoho.forms['reports']['bookings'], criteria=cb.build(), limit=500)

    boarding   = []
    deboarding = []

    for b in bookings:
        def get_code(f):
            if isinstance(f, dict): return f.get('display_value', '').split('-')[0].strip().upper()
            return str(f or '').split('-')[0].strip().upper()

        pax_raw = b.get('Passengers', '[]')
        try: passengers = jsonlib.loads(pax_raw) if isinstance(pax_raw, str) else (pax_raw or [])
        except Exception: passengers = []

        entry = {'PNR': b.get('PNR', ''), 'Class': b.get('Class', ''),
                 'Train': b.get('Trains', {}).get('display_value', '') if isinstance(b.get('Trains'), dict) else '',
                 'passengers': [{'name': p.get('Passenger_Name', p.get('Name', '')),
                                  'age': p.get('Age', ''), 'status': p.get('Current_Status', ''),
                                  'coach': p.get('Coach', ''), 'seat': p.get('Seat_Number', '')}
                                 for p in passengers if not p.get('Cancelled')]}

        if get_code(b.get('Boarding_Station'))   == station_code: boarding.append(entry)
        if get_code(b.get('Deboarding_Station')) == station_code: deboarding.append(entry)

    return jsonify({'success': True, 'data': {
        'station': station_code, 'station_name': station.get('Station_Name', ''),
        'date': date or 'All dates',
        'boarding': boarding, 'deboarding': deboarding,
        'total_boarding':   sum(len(e['passengers']) for e in boarding),
        'total_deboarding': sum(len(e['passengers']) for e in deboarding),
    }}), 200
