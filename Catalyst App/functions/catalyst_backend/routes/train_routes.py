"""
Train Routes routes — route/stop CRUD and connection endpoints.
Handles the Train_Routes parent form and Route_Stops subform.
"""

import re
import logging
from typing import Any, Dict
from flask import Blueprint, jsonify, request
from services.zoho_service import zoho
from config import TABLES
from utils.validators import extract_lookup_id
from utils.log_helper import log_admin_action
from core.security import require_admin

logger = logging.getLogger(__name__)

train_routes_bp = Blueprint('train_routes', __name__)


# ==================== HELPER FUNCTIONS ====================

def _extract_train_id(field):
    """Extract train ID from lookup field (dict or string)."""
    if isinstance(field, dict):
        return field.get('ID', '')
    return str(field or '')


def _build_stop_payload(data: Dict[str, Any]) -> Dict[str, Any]:
    """Build a clean subform row dict from request data."""
    stop: Dict[str, Any] = {}
    station_id = extract_lookup_id(data.get('Stations') or data.get('station_id'))
    if station_id:
        stop['Stations'] = station_id

    station_name = data.get('Station_Name')
    if station_name and isinstance(station_name, str) and station_name.strip():
        stop['Station_Name'] = station_name.strip()

    station_code = data.get('Station_Code')
    if station_code and isinstance(station_code, str) and station_code.strip():
        stop['Station_Code'] = station_code.strip().upper()

    if data.get('Sequence') not in (None, ''):
        stop['Sequence'] = int(data['Sequence'])
    if data.get('Arrival_Time'):
        stop['Arrival_Time'] = str(data['Arrival_Time'])
    if data.get('Departure_Time'):
        stop['Departure_Time'] = str(data['Departure_Time'])
    if data.get('Halt_Minutes') not in (None, ''):
        stop['Halt_Minutes'] = int(data['Halt_Minutes'])
    if data.get('Distance_KM') not in (None, ''):
        stop['Distance_KM'] = float(data['Distance_KM'])
    if data.get('Platform_Number') not in (None, ''):
        stop['Platform_Number'] = int(data['Platform_Number'])
    stop['Day_Count'] = int(data['Day_Count']) if data.get('Day_Count') not in (None, '') else 1
    return stop


def _parse_stop_display_value(dv, stop_id):
    """
    Parse Zoho stub display_value into a real stop dict.
    Used as fallback when get_record_by_id returns stub-only Route_Stops.
    """
    raw = str(dv).strip()
    time_re = r'\b\d{2}:\d{2}(?::\d{2})?\b'

    tokens = raw.split()
    seq = int(tokens[0]) if tokens and tokens[0].isdigit() else None

    times = re.findall(time_re, raw)
    arr_time = times[0][:5] if len(times) >= 1 else None
    dep_time = times[1][:5] if len(times) >= 2 else None

    # Remove seq, times, long Zoho IDs
    clean = re.sub(r'\b\d{15,}\b', '', raw)
    clean = re.sub(time_re, '', clean)
    clean = re.sub(r'^\s*\d+\s+', '', clean)
    clean = re.sub(r'\s+', ' ', clean).strip()

    # Day count: first single-digit token
    day_match = re.match(r'^(\d)\s+', clean)
    day = int(day_match.group(1)) if day_match else 1
    if day_match:
        clean = clean[day_match.end():]

    # Station code: short ALL-CAPS word (2–5 letters)
    code_match = re.search(r'\b([A-Z]{2,5})\b', clean)
    code = code_match.group(1) if code_match else ''

    # Station name: text before the code
    if code:
        idx = clean.find(code)
        name = clean[:idx].strip()
    else:
        parts = re.split(r'\s{2,}', clean)
        name = parts[0].strip() if parts else clean.strip()

    return {
        'ID':             stop_id,
        'Sequence':       seq,
        'Station_Name':   name,
        'Station_Code':   code,
        'Arrival_Time':   arr_time,
        'Departure_Time': dep_time,
        'Day_Count':      day,
        'Halt_Minutes':   '',
        'Distance_KM':    '',
    }


def _get_route_stops(route_record):
    """
    Extract Route_Stops subform rows from a Train_Routes record.
    Handles both full data and stub display_value formats.
    """
    stops = route_record.get('Route_Stops', [])
    if not isinstance(stops, list):
        return []

    real_stops = []
    for s in stops:
        if not isinstance(s, dict):
            continue
        if not s.get('Station_Name') and not s.get('Station_Code') and s.get('display_value'):
            parsed = _parse_stop_display_value(s['display_value'], s.get('ID', ''))
            real_stops.append(parsed)
        else:
            real_stops.append(s)
    return real_stops


def _fetch_all_routes_full(limit=500):
    """
    Returns list of Train_Routes records, each enriched with full Route_Stops data.
    2 API calls total regardless of how many route records exist.
    """
    # 1. Fetch all Train_Routes records
    list_res = zoho.get_all_records(
        TABLES['train_routes'],
        criteria=None,
        limit=limit
    )
    if not list_res.get('success'):
        return []

    route_list = list_res.get('data', {}).get('data', [])
    if not route_list:
        return []

    # 2. Fetch ALL Route_Stops rows in one call
    stops_res = zoho.get_all_records(
        TABLES['route_stops'],
        criteria=None,
        limit=2000
    )
    all_stops = []
    if stops_res.get('success'):
        all_stops = stops_res.get('data', {}).get('data', []) or []

    # 3. Index stops by their Train_Routes parent ID
    stops_by_route = {}
    for stop in all_stops:
        tr_field  = stop.get('Train_Routes') or {}
        tr_id     = tr_field.get('ID', '') if isinstance(tr_field, dict) else str(tr_field or '')
        if tr_id:
            stops_by_route.setdefault(tr_id, []).append(stop)

    # 4. Attach stops to their parent route records
    full_routes = []
    for r in route_list:
        rid = r.get('ID', '')
        r = dict(r)
        route_stops = stops_by_route.get(rid, [])
        route_stops_sorted = sorted(route_stops, key=lambda s: int(s.get('Sequence') or 0))
        r['_parsed_stops'] = route_stops_sorted
        full_routes.append(r)

    return full_routes


# ==================== ROUTE ENDPOINTS ====================

@train_routes_bp.route('/api/train-routes', methods=['GET'])
def get_train_routes():
    """
    GET /api/train-routes             → all Train_Routes records with full stop details
    GET /api/train-routes?train_id=X  → specific route record + full stops for that train
    """
    train_id = request.args.get('train_id', '').strip()
    limit = request.args.get('limit', 200, type=int)

    if train_id:
        # This logic is complex, defer to a helper
        return _get_single_route_by_train_id(train_id)

    # No train_id — return a list of all routes with their stops embedded
    try:
        full_routes = _fetch_all_routes_full(limit=limit)
        return jsonify({
            'success': True,
            'data': {'data': full_routes, 'count': len(full_routes)},
            'status_code': 200
        }), 200
    except Exception as e:
        logger.error(f"Failed to fetch all routes: {e}", exc_info=True)
        return jsonify({'success': False, 'error': 'Server error fetching routes'}), 500


def _get_single_route_by_train_id(train_id: str):
    """Helper to fetch a single train route and its stops by the train's ID."""
    try:
        # 1. Find the Train_Routes record for the given train_id
        route_records = zoho.get_all_records(
            TABLES['train_routes'],
            criteria=f'(Trains == "{train_id}")',
            limit=1
        )
        if not route_records.get('success') or not route_records.get('data', {}).get('data'):
            return jsonify({'success': False, 'error': 'Route not found for this train'}), 404

        route_record = route_records['data']['data'][0]
        route_id = route_record.get('ID')

        # 2. Fetch all stops associated with this Train_Routes record
        stops_result = zoho.get_all_records(
            TABLES['route_stops'],
            criteria=f'(Train_Routes == "{route_id}")',
            limit=200  # A train route is unlikely to have more than 200 stops
        )
        
        stops = []
        if stops_result.get('success'):
            stops = stops_result.get('data', {}).get('data', []) or []
        
        # 3. Sort stops by sequence number
        stops.sort(key=lambda s: int(s.get('Sequence') or 0))

        # 4. Combine and return
        return jsonify({
            'success': True,
            'data': {
                'route_record': route_record,
                'stops': stops,
                'count': len(stops),
            },
            'status_code': 200
        }), 200

    except Exception as e:
        logger.error(f"Error fetching route for train_id {train_id}: {e}", exc_info=True)
        return jsonify({'success': False, 'error': 'Server error fetching route data'}), 500


@train_routes_bp.route('/api/train-routes/<route_id>', methods=['GET'])
def get_train_route(route_id):
    """Return a single Train_Routes record + its Route_Stops rows."""
    result = zoho.get_record_by_id(TABLES['train_routes'], route_id)
    if not result.get('success'):
        return jsonify(result), result.get('status_code', 200)

    route = result.get('data', {}).get('data', result.get('data', {}))

    stops_result = zoho.get_all_records(
        TABLES['route_stops'],
        criteria=f'(Train_Routes == "{route_id}")',
        limit=200
    )
    stops = []
    if stops_result.get('success'):
        stops = stops_result.get('data', {}).get('data', []) or []
    stops.sort(key=lambda s: int(s.get('Sequence') or 0))

    return jsonify({
        'success': True,
        'data': {'route_record': route, 'stops': stops, 'count': len(stops)},
        'status_code': 200
    }), 200


@train_routes_bp.route('/api/train-routes', methods=['POST'])
@require_admin
def create_train_route():
    """Create a Train_Routes parent record for a train."""
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'No data provided'}), 400

    train_id = extract_lookup_id(data.get('Train') or data.get('Trains') or data.get('train_id'))
    if not train_id:
        return jsonify({'success': False, 'error': 'Train is required'}), 400

    # Check if a route record already exists
    existing = zoho.get_all_records(
        TABLES['train_routes'],
        criteria=f'(Trains == "{train_id}")',
        limit=5
    )
    if existing.get('success'):
        dup = existing.get('data', {}).get('data', [])
        if dup:
            return jsonify({'success': False, 'error': f'Route already exists for this train (ID: {dup[0].get("ID")})'}), 409

    payload = {
        'Train': train_id,
        'Route_Name': data.get('Route_Name', f'Route for Train {train_id}'),
        'Route_Stops': [_build_stop_payload(s) for s in data.get('Route_Stops', [])]
    }
    
    # Support optional Route_Priority field
    if 'Route_Priority' in data and data['Route_Priority'] not in (None, ''):
        payload['Route_Priority'] = int(data['Route_Priority'])

    result = zoho.create_record(TABLES['train_routes'], payload)
    
    if result.get('success'):
        record_id = result.get('data', {}).get('ID')
        user_email = request.headers.get('X-User-Email', 'Unknown')
        log_admin_action(user_email, 'CREATE_TRAIN_ROUTE', {'record_id': record_id, 'details': payload})

    return jsonify(result), result.get('status_code', 200)


@train_routes_bp.route('/api/train-routes/<route_id>', methods=['PUT'])
@require_admin
def update_train_route(route_id):
    """
    Update a Train_Routes record.
    Handles both top-level fields and Route_Stops subform updates.
    Supports Route_Priority for route ordering.
    """
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'No data provided'}), 400

    payload = {}
    if 'Route_Name' in data:
        payload['Route_Name'] = data['Route_Name']
    if 'Train' in data:
        payload['Train'] = extract_lookup_id(data['Train'])
    if 'Route_Priority' in data and data['Route_Priority'] not in (None, ''):
        payload['Route_Priority'] = int(data['Route_Priority'])

    if 'Route_Stops' in data and isinstance(data['Route_Stops'], list):
        payload['Route_Stops'] = []
        for stop_data in data['Route_Stops']:
            stop_payload = _build_stop_payload(stop_data)
            # For updates, subform rows need their ID if they exist
            if 'ID' in stop_data and stop_data['ID']:
                stop_payload['ID'] = stop_data['ID']
            payload['Route_Stops'].append(stop_payload)

    if not payload:
        return jsonify({'success': False, 'error': 'No valid fields to update'}), 400

    result = zoho.update_record(TABLES['train_routes'], route_id, payload)

    if result.get('success'):
        user_email = request.headers.get('X-User-Email', 'Unknown')
        log_admin_action(user_email, 'UPDATE_TRAIN_ROUTE', {'record_id': route_id, 'updated_data': payload})

    return jsonify(result), result.get('status_code', 200)


@train_routes_bp.route('/api/train-routes/<route_id>', methods=['DELETE'])
@require_admin
def delete_train_route(route_id):
    """Delete a Train_Routes record."""
    user_email = request.headers.get('X-User-Email', 'Unknown')
    log_admin_action(user_email, 'DELETE_TRAIN_ROUTE', {'record_id': route_id})
    
    result = zoho.delete_record(TABLES['train_routes'], route_id)
    return jsonify(result), result.get('status_code', 200)


# ==================== STOP ENDPOINTS ====================

@train_routes_bp.route('/api/train-routes/<route_id>/stops', methods=['GET'])
def get_route_stops(route_id):
    """Return all Route_Stops rows for a given Train_Routes record."""
    result = zoho.get_all_records(
        TABLES['route_stops'],
        criteria=f'(Train_Routes == "{route_id}")',
        limit=200
    )
    if not result.get('success'):
        return jsonify(result), result.get('status_code', 500)

    stops = result.get('data', {}).get('data', [])
    if not isinstance(stops, list):
        stops = []
    stops.sort(key=lambda s: int(s.get('Sequence') or 0))

    return jsonify({
        'success': True,
        'data': {'stops': stops, 'count': len(stops), 'route_id': route_id},
        'status_code': 200
    }), 200


@train_routes_bp.route('/api/train-routes/<route_id>/stops', methods=['POST'])
@require_admin
def add_route_stop(route_id):
    """Add a new Route_Stops row linked to this Train_Routes record."""
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'No data provided'}), 400

    seq = data.get('Sequence')
    try:
        seq_int = int(float(str(seq))) if seq is not None else None
        if seq_int is None or seq_int < 1:
            raise ValueError('out of range')
    except (TypeError, ValueError):
        return jsonify({'success': False, 'error': 'Sequence must be a whole number ≥ 1'}), 400

    if not ((data.get('Station_Name') or '').strip() or data.get('Stations')):
        return jsonify({'success': False, 'error': 'Station_Name or Stations lookup is required'}), 400

    stop_payload = _build_stop_payload(data)
    stop_payload['Train_Routes'] = route_id

    result = zoho.create_record(TABLES['route_stops'], stop_payload)
    if result.get('success'):
        record_id = result.get('data', {}).get('ID')
        log_admin_action('add_route_stop', record_id=record_id, summary=f"Added stop to route {route_id}", details=stop_payload)
    logger.info(f"add_route_stop route={route_id} payload={stop_payload} → {result}")
    return jsonify(result), result.get('status_code', 200)


@train_routes_bp.route('/api/train-routes/<route_id>/stops/<stop_id>', methods=['PUT'])
@require_admin
def update_route_stop(route_id, stop_id):
    """Update an existing Route_Stops row by its own ID."""
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'No data provided'}), 400

    seq = data.get('Sequence')
    try:
        seq_int = int(float(str(seq))) if seq is not None else None
        if seq_int is None or seq_int < 1:
            raise ValueError('out of range')
    except (TypeError, ValueError):
        return jsonify({'success': False, 'error': 'Sequence must be a whole number ≥ 1'}), 400

    if 'Station_Name' in data or 'Stations' in data:
        if not ((data.get('Station_Name') or '').strip() or data.get('Stations')):
            return jsonify({'success': False, 'error': 'Station_Name or Stations lookup is required'}), 400

    stop_payload = _build_stop_payload(data)
    stop_payload['Train_Routes'] = route_id

    result = zoho.update_record(TABLES['route_stops'], stop_id, stop_payload)
    if result.get('success'):
        log_admin_action('update_route_stop', record_id=stop_id, summary=f"Updated stop {stop_id} in route {route_id}", details=stop_payload)
    logger.info(f"update_route_stop route={route_id} stop={stop_id} payload={stop_payload} → {result}")
    if not result.get('success'):
        logger.error(f"update_route_stop failed: {result.get('error') or result}")
    return jsonify(result), result.get('status_code', 200)


@train_routes_bp.route('/api/train-routes/<route_id>/stops/<stop_id>', methods=['DELETE'])
@require_admin
def delete_route_stop(route_id, stop_id):
    """Delete a Route_Stops row by its own ID."""
    result = zoho.delete_record(TABLES['route_stops'], stop_id)
    if result.get('success'):
        log_admin_action('delete_route_stop', record_id=stop_id, summary=f"Deleted stop {stop_id} from route {route_id}")
    logger.info(f"delete_route_stop route={route_id} stop={stop_id} → {result}")
    return jsonify(result), result.get('status_code', 200)


# ==================== CONNECTION ENDPOINTS ====================

@train_routes_bp.route('/api/train-routes/connections', methods=['GET'])
def get_route_connections():
    """
    GET /api/train-routes/connections?station_code=MAS
      → all trains passing through station MAS
    """
    station_code = request.args.get('station_code', '').strip().upper()

    all_routes = _fetch_all_routes_full(limit=500)

    # Fetch all trains for metadata
    trains_res = zoho.get_all_records(TABLES['trains'], limit=500)
    trains_list = trains_res.get('data', {}).get('data', []) if trains_res.get('success') else []
    trains_by_id = {str(t.get('ID', '')): t for t in trains_list}

    # Build station → trains index
    station_index = {}

    for route_rec in all_routes:
        train_field = route_rec.get('Trains') or route_rec.get('Train') or {}
        train_id    = _extract_train_id(train_field)
        train_meta  = trains_by_id.get(train_id, {})
        train_name  = train_meta.get('Train_Name', route_rec.get('Train_Name', ''))
        train_num   = train_meta.get('Train_Number', route_rec.get('Train_Number', ''))

        stops = route_rec.get('_parsed_stops') or _get_route_stops(route_rec)
        total_stops = len(stops)
        stops_sorted = sorted(stops, key=lambda s: int(s.get('Sequence') or 0))

        for i, stop in enumerate(stops_sorted):
            code = (stop.get('Station_Code') or '').strip().upper()
            name = (stop.get('Station_Name') or '').strip()
            if not code:
                continue

            seq = int(stop.get('Sequence') or 0)
            if i == 0:
                stop_type = 'origin'
            elif i == total_stops - 1:
                stop_type = 'destination'
            else:
                stop_type = 'intermediate'

            if code not in station_index:
                station_index[code] = {'station_code': code, 'station_name': name, 'trains': []}

            station_index[code]['trains'].append({
                'train_id':     train_id,
                'train_name':   train_name,
                'train_number': train_num,
                'stop_type':    stop_type,
                'sequence':     seq,
                'arrival':      stop.get('Arrival_Time'),
                'departure':    stop.get('Departure_Time'),
                'halt_minutes': stop.get('Halt_Minutes'),
                'distance_km':  stop.get('Distance_KM'),
                'day_count':    stop.get('Day_Count', 1),
            })

    connection_stations = {k: v for k, v in station_index.items() if len(v['trains']) >= 2}

    if station_code:
        if station_code not in station_index:
            return jsonify({'success': True, 'data': {'station_code': station_code, 'trains': [], 'is_connection': False}, 'status_code': 200}), 200
        entry = station_index[station_code]
        return jsonify({
            'success': True,
            'data': {
                'station_code':  station_code,
                'station_name':  entry['station_name'],
                'trains':        entry['trains'],
                'is_connection': len(entry['trains']) >= 2,
                'train_count':   len(entry['trains']),
            },
            'status_code': 200
        }), 200

    return jsonify({
        'success': True,
        'data': {
            'connection_stations': connection_stations,
            'all_stations':        station_index,
            'connection_count':    len(connection_stations),
            'total_stations':      len(station_index),
        },
        'status_code': 200
    }), 200


@train_routes_bp.route('/api/train-routes/connections/all', methods=['GET'])
def get_all_connections():
    """Full cross-train connection map."""
    all_routes = _fetch_all_routes_full(limit=500)

    trains_res = zoho.get_all_records(TABLES['trains'], limit=500)
    trains_list = trains_res.get('data', {}).get('data', []) if trains_res.get('success') else []
    trains_by_id = {str(t.get('ID', '')): t for t in trains_list}

    station_trains = {}

    for route_rec in all_routes:
        train_id = _extract_train_id(route_rec.get('Trains') or route_rec.get('Train') or {})
        train_meta = trains_by_id.get(train_id, {})
        stops = sorted(route_rec.get('_parsed_stops') or _get_route_stops(route_rec), key=lambda s: int(s.get('Sequence') or 0))
        n = len(stops)

        for i, stop in enumerate(stops):
            code = (stop.get('Station_Code') or '').strip().upper()
            if not code:
                continue
            if code not in station_trains:
                station_trains[code] = {
                    'station_code': code,
                    'station_name': stop.get('Station_Name', ''),
                    'trains': []
                }
            station_trains[code]['trains'].append({
                'train_id':     train_id,
                'train_name':   train_meta.get('Train_Name', ''),
                'train_number': train_meta.get('Train_Number', ''),
                'from_station': train_meta.get('From_Station', {}).get('display_value', '') if isinstance(train_meta.get('From_Station'), dict) else '',
                'to_station':   train_meta.get('To_Station', {}).get('display_value', '') if isinstance(train_meta.get('To_Station'), dict) else '',
                'stop_type':    'origin' if i == 0 else ('destination' if i == n - 1 else 'intermediate'),
                'sequence':     int(stop.get('Sequence') or 0),
                'arrival':      stop.get('Arrival_Time'),
                'departure':    stop.get('Departure_Time'),
                'halt_minutes': stop.get('Halt_Minutes'),
                'distance_km':  stop.get('Distance_KM'),
            })

    connections = {k: v for k, v in station_trains.items() if len(v['trains']) >= 2}

    # Build route pairs
    pairs = []
    for code, info in connections.items():
        train_ids = [t['train_id'] for t in info['trains']]
        for idx_a in range(len(train_ids)):
            for idx_b in range(idx_a + 1, len(train_ids)):
                ta = info['trains'][idx_a]
                tb = info['trains'][idx_b]
                dep_a = ta.get('departure')
                arr_b = tb.get('arrival') or tb.get('departure')
                transfer = None
                if dep_a and arr_b:
                    try:
                        def _mins(t):
                            h, m = t.split(':')[:2]
                            return int(h) * 60 + int(m)
                        diff = _mins(arr_b) - _mins(dep_a)
                        if diff < 0: diff += 1440
                        transfer = diff
                    except Exception:
                        pass
                pairs.append({
                    'via_station':    code,
                    'via_name':       info['station_name'],
                    'train_a':        ta,
                    'train_b':        tb,
                    'transfer_mins':  transfer,
                    'feasible':       transfer is None or transfer >= 20,
                })

    pairs.sort(key=lambda p: (p['transfer_mins'] or 9999))

    return jsonify({
        'success': True,
        'data': {
            'connection_stations': connections,
            'connection_pairs':    pairs,
            'total_connections':   len(connections),
            'total_pairs':         len(pairs),
        },
        'status_code': 200
    }), 200
