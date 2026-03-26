"""
Trains routes — optimized with Zoho-side filtering and response caching.
"""

import logging
from datetime import datetime
from flask import Blueprint, jsonify, request
from repositories.cloudscale_repository import zoho_repo, TABLES
from repositories.cache_manager import cache, TTL_TRAINS
from utils.validators import extract_lookup_id
from utils.log_helper import log_admin_action
from core.security import require_admin

logger   = logging.getLogger(__name__)
trains_bp = Blueprint('trains', __name__)


def _is_true(val):
    if isinstance(val, bool): return val
    if isinstance(val, str):  return val.lower() == 'true'
    return bool(val)


# ── CREATE ────────────────────────────────────────────────────────────────────
@trains_bp.route('/api/trains', methods=['POST'])
@require_admin
def create_train():
    try:
        data    = request.get_json()
        payload = {
            'Train_Number':   data.get('Train_Number') or data.get('train_number'),
            'Train_Name':     data.get('Train_Name')   or data.get('train_name'),
            'Train_Type':     data.get('Train_Type')   or data.get('train_type'),
            'From_Station':   extract_lookup_id(data.get('From_Station')),
            'To_Station':     extract_lookup_id(data.get('To_Station')),
            'Departure_Time': data.get('Departure_Time'),
            'Arrival_Time':   data.get('Arrival_Time'),
            'Duration':       data.get('Duration')        or None,
            'Distance':       data.get('Distance')        or None,
            'Fare_SL':        float(data.get('Fare_SL')  or 0),
            'Fare_3A':        float(data.get('Fare_3A')  or 0),
            'Fare_2A':        float(data.get('Fare_2A')  or 0),
            'Fare_1A':        float(data.get('Fare_1A')  or 0),
            'Fare_CC':        float(data.get('Fare_CC')  or 0),
            'Fare_EC':        float(data.get('Fare_EC')  or 0),
            'Fare_2S':        float(data.get('Fare_2S')  or 0),
            'Total_Seats_SL': int(data.get('Total_Seats_SL') or 0),
            'Total_Seats_3A': int(data.get('Total_Seats_3A') or 0),
            'Total_Seats_2A': int(data.get('Total_Seats_2A') or 0),
            'Total_Seats_1A': int(data.get('Total_Seats_1A') or 0),
            'Total_Seats_CC': int(data.get('Total_Seats_CC') or 0),
            'Available_Seats_SL': int(data.get('Total_Seats_SL') or 0),
            'Available_Seats_3A': int(data.get('Total_Seats_3A') or 0),
            'Available_Seats_2A': int(data.get('Total_Seats_2A') or 0),
            'Available_Seats_1A': int(data.get('Total_Seats_1A') or 0),
            'Available_Seats_CC': int(data.get('Total_Seats_CC') or 0),
            'Run_Days':       data.get('Run_Days')         or None,
            'Is_Active':      _is_true(data.get('Is_Active', True)),
            'Pantry_Car_Available': _is_true(data.get('Pantry_Car_Available', False)),
            'Running_Status': data.get('Running_Status', 'On Time'),
            'Delay_Minutes':  int(data.get('Delay_Minutes') or 0),
            'Expected_Departure': data.get('Expected_Departure'),
        }
        payload = {k: v for k, v in payload.items() if v is not None}
        result = zoho_repo.create_record(TABLES['trains'], payload)
        if result.get('success'):
            zoho_repo.invalidate_train_cache()       # bust trains:all cache
            record_id = result.get('data', {}).get('ID')
            user_email = request.headers.get('X-User-Email', 'Unknown')
            log_admin_action(user_email, 'CREATE_TRAIN', {'record_id': record_id, 'details': payload})
        return jsonify(result), result.get('status_code', 200)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ── LIST / SEARCH (optimized — cached train list, Python-side filters) ────────
@trains_bp.route('/api/trains', methods=['GET'])
def get_trains():
    source      = request.args.get('source', '').strip().upper()
    destination = request.args.get('destination', '').strip().upper()
    journey_date= request.args.get('journey_date')
    train_number= request.args.get('train_number', '').strip()
    train_name  = request.args.get('train_name', '').strip().lower()
    limit       = request.args.get('limit', 200, type=int)

    def get_code(field):
        if not field: return ''
        dv = field.get('display_value', '') if isinstance(field, dict) else str(field)
        return dv.strip().split('-')[0].strip().upper()

    # Use cached list
    records = zoho_repo.get_all_trains_cached()

    if source:
        records = [r for r in records if get_code(r.get('From_Station')) == source]
    if destination:
        records = [r for r in records if get_code(r.get('To_Station')) == destination]
    if train_number:
        records = [r for r in records if train_number in str(r.get('Train_Number', ''))]
    if train_name:
        records = [r for r in records if train_name in str(r.get('Train_Name', '')).lower()]

    if journey_date:
        try:
            DAY_ABBR = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
            day_name = DAY_ABBR[datetime.strptime(journey_date, '%Y-%m-%d').weekday()]
            def runs_on(rec):
                run_days = rec.get('Run_Days', '')
                if isinstance(run_days, list):
                    days = [d.strip() for d in run_days]
                elif isinstance(run_days, str) and run_days.strip():
                    days = [d.strip() for d in run_days.split(',')]
                else:
                    days = []
                return not days or day_name in days
            records = [r for r in records if runs_on(r)]
        except Exception as e:
            logger.warning(f'journey_date filter error: {e}')

    records = records[:limit]
    return jsonify({'success': True, 'data': {'data': records, 'count': len(records)}}), 200


# ── CONNECTING TRAINS SEARCH ──────────────────────────────────────────────────
@trains_bp.route('/api/trains/connecting', methods=['GET'])
def get_connecting_trains():
    """
    GET /api/trains/connecting?from=MAS&to=SBC&date=2024-03-15
    Finds direct and one-stop connecting routes.
    """
    from_st = request.args.get('from', '').strip().upper()
    to_st   = request.args.get('to', '').strip().upper()
    date    = request.args.get('date')

    if not from_st or not to_st:
        return jsonify({'success': False, 'error': 'from and to stations are required'}), 400

    from routes.train_routes import _fetch_all_routes_full, _get_route_stops
    from collections import defaultdict

    # 1. Fetch all routes and index them
    all_routes  = _fetch_all_routes_full(limit=500)
    train_stops = defaultdict(list)

    for r in all_routes:
        t_field = r.get('Trains') or r.get('Train') or {}
        t_id    = t_field.get('ID') if isinstance(t_field, dict) else str(t_field or '')
        if t_id:
            stops = r.get('_parsed_stops') or _get_route_stops(r)
            for stop in stops:
                stop['_train_id'] = t_id
            train_stops[t_id] = sorted(stops, key=lambda s: int(s.get('Sequence') or 0))

    def get_stop_code(stop):
        code = (stop.get('Station_Code') or '').strip().upper()
        if code: return code
        st = stop.get('Stations', {})
        if isinstance(st, dict):
            dv = (st.get('display_value') or '').strip()
            return dv.split('-')[0].strip().upper() if dv else ''
        return ''

    # 2. Find DIRECT trains
    direct_trains = []
    for t_id, stops in train_stops.items():
        from_idx = -1
        to_idx   = -1
        for i, stop in enumerate(stops):
            code = get_stop_code(stop)
            if code == from_st: from_idx = i
            if code == to_st:   to_idx   = i

        if from_idx != -1 and to_idx != -1 and from_idx < to_idx:
            # Check date (Run_Days)
            train_meta = zoho_repo.get_train_cached(t_id)
            if not train_meta: continue

            if date:
                try:
                    DAY_ABBR = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
                    day_name = DAY_ABBR[datetime.strptime(date, '%Y-%m-%d').weekday()]
                    run_days = train_meta.get('Run_Days', '')
                    days_list = [d.strip() for d in (run_days if isinstance(run_days, list) else str(run_days).split(','))] if run_days else []
                    if days_list and day_name not in days_list:
                        continue
                except Exception: pass

            direct_trains.append({
                'type': 'direct',
                'train': train_meta,
                'from_stop': stops[from_idx],
                'to_stop':   stops[to_idx],
                'duration':  '--' # could calculate
            })

    # 3. Handle connections (optional, for now return direct if found)
    # If no direct trains, ideally look for MAS -> X and X -> SBC
    # For now, return what we found.
    return jsonify({
        'success': True,
        'data': {
            'records': direct_trains,
            'count':   len(direct_trains),
            'direct_count': len(direct_trains),
            'connecting_count': 0
        }
    }), 200


# ── GET BY ID ─────────────────────────────────────────────────────────────────
@trains_bp.route('/api/trains/<train_id>', methods=['GET'])
def get_train(train_id):
    result = zoho_repo.get_record_by_id(TABLES['trains'], train_id)
    return jsonify(result), result.get('status_code', 200)


# ── UPDATE ────────────────────────────────────────────────────────────────────
@trains_bp.route('/api/trains/<train_id>', methods=['PUT'])
@require_admin
def update_train(train_id):
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'No data provided'}), 400
    
    # Create payload with only the fields present in the request
    payload = {}
    for key, value in data.items():
        # This is a simplified mapping. A more robust solution would map
        # camelCase from frontend to PascalCase for backend/Zoho.
        # For now, we assume keys match.
        if key in [
            'Train_Number', 'Train_Name', 'Train_Type', 'Departure_Time', 
            'Arrival_Time', 'Duration', 'Distance', 'Run_Days', 'Running_Status', 
            'Delay_Minutes', 'Expected_Departure'
        ]:
            payload[key] = value
        elif key in ['From_Station', 'To_Station']:
            payload[key] = extract_lookup_id(value)
        elif 'Fare_' in key or 'Total_Seats_' in key:
            try:
                payload[key] = float(value) if 'Fare_' in key else int(value)
            except (ValueError, TypeError):
                pass # Ignore invalid number formats
        elif key in ['Is_Active', 'Pantry_Car_Available']:
            payload[key] = _is_true(value)

    if not payload:
        return jsonify({'success': False, 'error': 'No valid fields to update'}), 400

    result = zoho_repo.update_record(TABLES['trains'], train_id, payload)
    
    if result.get('success'):
        zoho_repo.invalidate_train_cache(train_id) # bust specific train cache
        zoho_repo.invalidate_train_cache()         # bust trains:all cache
        user_email = request.headers.get('X-User-Email', 'Unknown')
        log_admin_action(user_email, 'UPDATE_TRAIN', {'record_id': train_id, 'updated_data': payload})
        
    return jsonify(result), result.get('status_code', 200)


# ── DELETE ────────────────────────────────────────────────────────────────────
@trains_bp.route('/api/trains/<train_id>', methods=['DELETE'])
@require_admin
def delete_train(train_id):
    result = zoho_repo.delete_record(TABLES['trains'], train_id)
    if result.get('success'):
        zoho_repo.invalidate_train_cache(train_id)
        zoho_repo.invalidate_train_cache()
        user_email = request.headers.get('X-User-Email', 'Unknown')
        log_admin_action(user_email, 'DELETE_TRAIN', {'record_id': train_id})
    return jsonify(result), result.get('status_code', 200)


# ── SCHEDULE ──────────────────────────────────────────────────────────────────
@trains_bp.route('/api/trains/<train_id>/schedule', methods=['GET'])
def get_train_schedule(train_id):
    try:
        route_result = zoho_repo.get_all_records(TABLES['train_routes'],
                                             criteria=f'Trains = {train_id}', limit=5)
        if route_result.get('success'):
            route_list = route_result.get('data', {}).get('data', [])
            if route_list:
                route_id     = route_list[0].get('ROWID') or route_list[0].get('ID')
                stops_result = zoho_repo.get_all_records(TABLES['route_stops'],
                                                     criteria=f'Train_Routes = {route_id}', limit=200)
                if stops_result.get('success'):
                    raw_stops = stops_result.get('data', {}).get('data', []) or []
                    raw_stops.sort(key=lambda r: int(r.get('Sequence') or 0))
                    if raw_stops:
                        stops = [{'sequence': r.get('Sequence'), 'station_name': r.get('Station_Name') or '',
                                  'station_code': r.get('Station_Code', ''), 'arrival': r.get('Arrival_Time', '--'),
                                  'departure': r.get('Departure_Time', '--'), 'halt_mins': r.get('Halt_Minutes', 0),
                                  'distance_km': r.get('Distance_KM', '')} for r in raw_stops]
                        return jsonify({'success': True, 'data': {'stops': stops, 'count': len(stops)}}), 200
    except Exception as e:
        logger.warning(f'get_train_schedule: {e}')

    # Fallback: origin + destination only
    train = zoho_repo.get_train_cached(train_id)
    if not train:
        return jsonify({'success': False, 'error': 'Train not found'}), 404

    from_st = train.get('From_Station', {})
    to_st   = train.get('To_Station', {})
    stops = [
        {'sequence': 1, 'station_name': from_st.get('display_value', '') if isinstance(from_st, dict) else str(from_st),
         'arrival': None, 'departure': train.get('Departure_Time', '--'), 'halt_mins': 0},
        {'sequence': 2, 'station_name': to_st.get('display_value', '') if isinstance(to_st, dict) else str(to_st),
         'arrival': train.get('Arrival_Time', '--'), 'departure': None, 'halt_mins': 0},
    ]
    return jsonify({'success': True, 'data': {'stops': stops, 'count': 2, 'note': 'Intermediate stops not configured'}}), 200


# ── VACANCY ───────────────────────────────────────────────────────────────────
@trains_bp.route('/api/trains/<train_id>/vacancy', methods=['GET'])
def get_train_vacancy(train_id):
    import json as jsonlib
    journey_date = request.args.get('date')

    rec = zoho_repo.get_train_cached(train_id)
    if not rec:
        return jsonify({'success': False, 'error': 'Train not found'}), 404

    fare_map  = {'SL': 'Fare_SL', '3AC': 'Fare_3A', '2AC': 'Fare_2A', '1AC': 'Fare_1A', 'CC': 'Fare_CC'}
    label_map = {'SL': 'Sleeper', '3AC': '3rd AC', '2AC': '2nd AC', '1AC': '1st AC', 'CC': 'Chair Car'}
    classes   = ['SL', '3AC', '2AC', '1AC', 'CC']
    fallback  = {
        'SL': int(rec.get('Total_Seats_SL') or 0), '3AC': int(rec.get('Total_Seats_3A') or 0),
        '2AC': int(rec.get('Total_Seats_2A') or 0), '1AC': int(rec.get('Total_Seats_1A') or 0),
        'CC': int(rec.get('Total_Seats_CC') or 0),
    }

    if not journey_date:
        vacancy = {}
        for cls in classes:
            if fallback[cls] > 0:
                vacancy[cls] = {'label': label_map[cls], 'total': fallback[cls], 'booked': 0,
                                 'available': fallback[cls], 'fare': float(rec.get(fare_map[cls]) or 0),
                                 'status': f'AVAILABLE-{fallback[cls]}'}
        return jsonify({'success': True, 'data': vacancy, 'meta': {'train_id': train_id}}), 200

    # Check inventory cache
    cache_key = f'inventory:{train_id}:{journey_date}'
    cached    = cache.get(cache_key)
    if cached:
        return jsonify({'success': True, 'data': cached, 'meta': {'train_id': train_id, 'cached': True}}), 200

    try:
        dt             = datetime.strptime(journey_date, '%Y-%m-%d')
        date_criteria  = dt.strftime('%d-%b-%Y')
    except Exception:
        date_criteria  = journey_date

    inv_result = zoho_repo.get_all_records(TABLES['train_inventory'],
                                       criteria=f"Train_ID = {train_id} AND Journey_Date = '{date_criteria}'",
                                       limit=200)
    inventory  = inv_result.get('data', {}).get('data', []) if inv_result.get('success') else []

    aggregated  = {c: {'total': 0, 'confirmed': 0, 'rac': 0, 'wl': 0} for c in classes}
    has_inv     = len(inventory) > 0

    if has_inv:
        for inv in inventory:
            cls_raw = (inv.get('Class') or '').upper().strip()
            cls_map = {'SLEEPER': 'SL', '3A': '3AC', '2A': '2AC', '1A': '1AC'}
            cls     = cls_map.get(cls_raw, cls_raw)
            if cls not in aggregated: continue
            aggregated[cls]['total'] += int(inv.get('Total_Capacity') or 0)
            aggregated[cls]['rac']   += int(inv.get('RAC_Count') or 0)
            aggregated[cls]['wl']    += int(inv.get('Waitlist_Count') or 0)
            raw_json = inv.get('Confirmed_Seats_JSON')
            if raw_json:
                try: aggregated[cls]['confirmed'] += len(jsonlib.loads(raw_json))
                except Exception: pass

    vacancy = {}
    for cls in classes:
        tot       = aggregated[cls]['total'] if has_inv else 0
        if tot == 0: tot = fallback[cls]
        if tot <= 0: continue
        confirmed = aggregated[cls]['confirmed']
        rac       = aggregated[cls]['rac']
        wl        = aggregated[cls]['wl']
        available = max(0, tot - confirmed)
        if available == 0:
            status = f'RAC {rac}' if rac > 0 and wl == 0 else f'WL {wl}' if wl > 0 else 'WL 1'
        else:
            status = f'AVAILABLE-{available}'
        vacancy[cls] = {'label': label_map[cls], 'total': tot, 'booked': confirmed, 'available': available,
                         'waitlist': wl, 'rac': rac, 'fare': float(rec.get(fare_map[cls]) or 0), 'status': status}

    cache.set(cache_key, vacancy, ttl=300)
    return jsonify({'success': True, 'data': vacancy,
                    'meta': {'train_id': train_id, 'journey_date': journey_date, 'inventory_used': has_inv}}), 200


# ── RUNNING STATUS ────────────────────────────────────────────────────────────
@trains_bp.route('/api/trains/<train_id>/running-status', methods=['GET'])
def get_running_status(train_id):
    rec = zoho_repo.get_train_cached(train_id)
    if not rec:
        return jsonify({'success': False, 'error': 'Train not found'}), 404
    return jsonify({'success': True, 'data': {
        'train_id': train_id, 'train_name': rec.get('Train_Name', ''),
        'train_number': rec.get('Train_Number', ''),
        'running_status': rec.get('Running_Status', 'On Time'),
        'delay_minutes': int(rec.get('Delay_Minutes') or 0),
        'expected_departure': rec.get('Expected_Departure', rec.get('Departure_Time', '')),
        'last_updated': rec.get('Modified_Time', ''),
    }}), 200


@trains_bp.route('/api/trains/<train_id>/running-status', methods=['PUT'])
@require_admin
def update_running_status(train_id):
    data    = request.get_json() or {}
    payload = {}
    if 'Running_Status'    in data: payload['Running_Status']    = data['Running_Status']
    if 'Delay_Minutes'     in data: payload['Delay_Minutes']     = int(data.get('Delay_Minutes') or 0)
    if 'Expected_Departure' in data: payload['Expected_Departure'] = data['Expected_Departure']
    if not payload:
        return jsonify({'success': False, 'error': 'No valid fields to update'}), 400
    result = zoho_repo.update_record(TABLES['trains'], train_id, payload)
    if result.get('success'):
        zoho_repo.invalidate_train_cache(train_id)
        log_admin_action('update_running_status', record_id=train_id, details=payload)
    return jsonify(result), result.get('status_code', 200)


# ── CANCEL TRAIN ON DATE ──────────────────────────────────────────────────────
@trains_bp.route('/api/trains/<train_id>/cancel-on-date', methods=['POST'])
@require_admin
def cancel_train_on_date(train_id):
    from utils.date_helpers import to_zoho_date_only
    data = request.get_json() or {}
    if not data.get('date'):
        return jsonify({'success': False, 'error': 'date is required'}), 400

    cancel_date = data['date']
    zoho_date   = to_zoho_date_only(cancel_date)

    bookings = zoho_repo.get_active_bookings_for_train_date(train_id, zoho_date)
    cancelled_count = 0
    total_refund    = 0.0

    for b in bookings:
        fare = float(b.get('Total_Fare') or 0)
        total_refund += fare
        cancelled_count += 1
        zoho_repo.update_record(TABLES['bookings'], b.get('ID'), {
            'Booking_Status': 'cancelled', 'Refund_Amount': fare,
            'Cancellation_Time': datetime.now().strftime('%d-%b-%Y %H:%M:%S'),
        })

    zoho_repo.invalidate_inventory_cache(train_id, zoho_date)
    return jsonify({'success': True, 'message': f'{cancelled_count} booking(s) cancelled',
                    'data': {'cancelled_bookings': cancelled_count, 'total_refund': round(total_refund, 2),
                             'reason': data.get('reason', 'Admin cancelled')}}), 200


# ── BULK CREATE ───────────────────────────────────────────────────────────────
@trains_bp.route('/api/trains/bulk', methods=['POST'])
@require_admin
def bulk_create_trains():
    data = request.get_json() or {}
    if not data.get('trains'):
        return jsonify({'success': False, 'error': 'trains array is required'}), 400

    results = {'created': 0, 'failed': 0, 'errors': []}
    for i, t in enumerate(data['trains']):
        try:
            payload = {k: v for k, v in {
                'Train_Number': t.get('Train_Number', ''), 'Train_Name': t.get('Train_Name', ''),
                'Train_Type': t.get('Train_Type', ''), 'From_Station': t.get('From_Station'),
                'To_Station': t.get('To_Station'), 'Departure_Time': t.get('Departure_Time'),
                'Arrival_Time': t.get('Arrival_Time'),
                'Fare_SL': float(t.get('Fare_SL') or 0), 'Fare_3A': float(t.get('Fare_3A') or 0),
                'Fare_2A': float(t.get('Fare_2A') or 0), 'Fare_1A': float(t.get('Fare_1A') or 0),
                'Fare_CC': float(t.get('Fare_CC') or 0),
                'Total_Seats_SL': int(t.get('Total_Seats_SL') or 0),
                'Total_Seats_3A': int(t.get('Total_Seats_3A') or 0),
                'Total_Seats_2A': int(t.get('Total_Seats_2A') or 0),
                'Total_Seats_1A': int(t.get('Total_Seats_1A') or 0),
                'Total_Seats_CC': int(t.get('Total_Seats_CC') or 0),
                'Available_Seats_SL': int(t.get('Total_Seats_SL') or 0),
                'Available_Seats_3A': int(t.get('Total_Seats_3A') or 0),
                'Available_Seats_2A': int(t.get('Total_Seats_2A') or 0),
                'Available_Seats_1A': int(t.get('Total_Seats_1A') or 0),
                'Available_Seats_CC': int(t.get('Total_Seats_CC') or 0),
                'Is_Active': True,
            }.items() if v is not None}
            res = zoho_repo.create_record(TABLES['trains'], payload)
            if res.get('success'): results['created'] += 1
            else: results['failed'] += 1; results['errors'].append(f"Row {i+1}: {res.get('error')}")
        except Exception as e:
            results['failed'] += 1; results['errors'].append(f"Row {i+1}: {e}")

    if results['created']:
        zoho_repo.invalidate_train_cache()
    return jsonify({'success': True, 'data': results,
                    'message': f"{results['created']} created, {results['failed']} failed"}), 200


# ── SEARCH BY STATION ─────────────────────────────────────────────────────────
@trains_bp.route('/api/trains/search-by-station', methods=['GET'])
def search_trains_by_station():
    from routes.train_routes import _fetch_all_routes_full, _get_route_stops
    from collections import defaultdict

    station_code = request.args.get('station_code', '').strip().upper()
    journey_date = request.args.get('journey_date', '')
    if not station_code:
        return jsonify({'success': False, 'error': 'station_code is required'}), 400

    all_routes  = _fetch_all_routes_full(limit=500)
    train_stops = defaultdict(list)
    for r in all_routes:
        t_field = r.get('Trains') or r.get('Train') or {}
        t_id    = t_field.get('ID') if isinstance(t_field, dict) else str(t_field or '')
        if t_id:
            for stop in (r.get('_parsed_stops') or _get_route_stops(r)):
                stop['_train_id'] = t_id
                train_stops[t_id].append(stop)
    for t_id in train_stops:
        train_stops[t_id].sort(key=lambda s: int(s.get('Sequence') or 0))

    def get_stop_code(stop):
        code = (stop.get('Station_Code') or '').strip().upper()
        if code: return code
        st = stop.get('Stations', {})
        if isinstance(st, dict):
            dv = (st.get('display_value') or '').strip()
            return dv.split('-')[0].strip().upper() if dv else ''
        return ''

    matching = {}
    for t_id, stops in train_stops.items():
        for stop in stops:
            if get_stop_code(stop) == station_code:
                seq     = int(stop.get('Sequence') or 0)
                max_seq = int(stops[-1].get('Sequence') or 0)
                stype   = 'origin' if seq == int(stops[0].get('Sequence') or 0) \
                          else 'destination' if seq == max_seq else 'intermediate'
                matching[t_id] = {'stop_type': stype, 'sequence': seq,
                                   'arrival_time': stop.get('Arrival_Time'),
                                   'departure_time': stop.get('Departure_Time'),
                                   'halt_minutes': stop.get('Halt_Minutes'),
                                   'distance_km': stop.get('Distance_KM')}
                break

    trains_list = zoho_repo.get_all_trains_cached()

    def get_code(field):
        if not field: return ''
        dv = field.get('display_value', '') if isinstance(field, dict) else str(field)
        return dv.strip().split('-')[0].strip().upper()

    result_trains = []
    for t in trains_list:
        t_id = str(t.get('ID', ''))
        if journey_date:
            try:
                DAY_ABBR = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
                day_name = DAY_ABBR[datetime.strptime(journey_date, '%Y-%m-%d').weekday()]
                run_days = t.get('Run_Days', '')
                days_list = [d.strip() for d in (run_days if isinstance(run_days, list) else run_days.split(','))] if run_days else []
                if days_list and day_name not in days_list:
                    continue
            except Exception:
                pass
        if t_id in matching:
            t['stop_info'] = matching[t_id]; t['stop_type'] = matching[t_id]['stop_type']
            result_trains.append(t)
        elif get_code(t.get('From_Station')) == station_code:
            t['stop_info'] = {'stop_type': 'origin', 'sequence': 1}; t['stop_type'] = 'origin'
            result_trains.append(t)
        elif get_code(t.get('To_Station')) == station_code:
            t['stop_info'] = {'stop_type': 'destination'}; t['stop_type'] = 'destination'
            result_trains.append(t)

    order = {'origin': 0, 'intermediate': 1, 'destination': 2}
    result_trains.sort(key=lambda x: order.get(x.get('stop_type', 'intermediate'), 1))
    return jsonify({'success': True, 'data': {'station_code': station_code, 'journey_date': journey_date,
                                               'trains': result_trains, 'count': len(result_trains)}}), 200
