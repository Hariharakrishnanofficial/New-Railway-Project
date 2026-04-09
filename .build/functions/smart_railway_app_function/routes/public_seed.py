"""
Public Data Seeding Routes - No Authentication Required
For initial setup and sample data population
"""

import logging
import random
import string
from datetime import datetime, timedelta
from flask import Blueprint, jsonify, request

from repositories.cloudscale_repository import cloudscale_repo
from config import TABLES

logger = logging.getLogger(__name__)
public_seed_bp = Blueprint('public_seed', __name__)

# Sample data generators
def random_string(length=8):
    return ''.join(random.choices(string.ascii_letters, k=length))

def random_digits(length=6):
    return ''.join(random.choices(string.digits, k=length))

def future_date(days=30):
    date = datetime.now() + timedelta(days=random.randint(1, days))
    return date.strftime('%Y-%m-%d')

def past_date(days=30):
    date = datetime.now() - timedelta(days=random.randint(1, days))
    return date.strftime('%Y-%m-%d')

def random_time():
    hour = random.randint(0, 23)
    minute = random.randint(0, 59)
    return f"{hour:02d}:{minute:02d}"

# Realistic Indian Railway data
INDIAN_STATIONS = [
    {"code": "NDLS", "name": "New Delhi", "city": "Delhi", "state": "Delhi", "zone": "NR"},
    {"code": "BCT", "name": "Mumbai Central", "city": "Mumbai", "state": "Maharashtra", "zone": "WR"},
    {"code": "CSTM", "name": "Mumbai CST", "city": "Mumbai", "state": "Maharashtra", "zone": "CR"},
    {"code": "MAS", "name": "Chennai Central", "city": "Chennai", "state": "Tamil Nadu", "zone": "SR"},
    {"code": "HWH", "name": "Howrah Junction", "city": "Kolkata", "state": "West Bengal", "zone": "ER"},
    {"code": "SBC", "name": "Bangalore City", "city": "Bangalore", "state": "Karnataka", "zone": "SWR"},
    {"code": "SC", "name": "Secunderabad", "city": "Hyderabad", "state": "Telangana", "zone": "SCR"},
    {"code": "JP", "name": "Jaipur Junction", "city": "Jaipur", "state": "Rajasthan", "zone": "NWR"},
    {"code": "ADI", "name": "Ahmedabad Junction", "city": "Ahmedabad", "state": "Gujarat", "zone": "WR"},
    {"code": "PUNE", "name": "Pune Junction", "city": "Pune", "state": "Maharashtra", "zone": "CR"},
]

INDIAN_TRAINS = [
    {"number": "12301", "name": "Howrah Rajdhani Express", "type": "Rajdhani", "from": "NDLS", "to": "HWH", "dept": "16:55", "arr": "09:55", "duration": "17h 00m"},
    {"number": "12951", "name": "Mumbai Rajdhani Express", "type": "Rajdhani", "from": "NDLS", "to": "BCT", "dept": "16:25", "arr": "08:35", "duration": "16h 10m"},
    {"number": "12002", "name": "Bhopal Shatabdi Express", "type": "Shatabdi", "from": "NDLS", "to": "BPL", "dept": "06:00", "arr": "13:40", "duration": "7h 40m"},
    {"number": "12259", "name": "Sealdah Duronto Express", "type": "Duronto", "from": "NDLS", "to": "SDAH", "dept": "12:55", "arr": "05:45", "duration": "16h 50m"},
    {"number": "12627", "name": "Karnataka Express", "type": "Superfast", "from": "NDLS", "to": "SBC", "dept": "21:15", "arr": "06:40", "duration": "33h 25m"},
    {"number": "12621", "name": "Tamil Nadu Express", "type": "Superfast", "from": "NDLS", "to": "MAS", "dept": "22:30", "arr": "07:10", "duration": "32h 40m"},
    {"number": "12309", "name": "Rajdhani Express", "type": "Rajdhani", "from": "NDLS", "to": "PNBE", "dept": "17:00", "arr": "08:00", "duration": "15h 00m"},
    {"number": "12032", "name": "Shatabdi Express", "type": "Shatabdi", "from": "NDLS", "to": "ADI", "dept": "06:20", "arr": "14:00", "duration": "7h 40m"},
]

TRAIN_TYPES = ["Express", "Superfast", "Mail", "Rajdhani", "Shatabdi", "Duronto", "Garib Rath"]
CLASS_TYPES = ["SL", "3A", "2A", "1A", "CC"]

@public_seed_bp.route('/public-seed/stations', methods=['POST'])
def create_sample_stations():
    """Create sample stations with realistic Indian Railway data (PUBLIC - no auth required)."""
    try:
        created_stations = []

        for station in INDIAN_STATIONS:
            station_data = {
                'Station_Code': station['code'],
                'Station_Name': station['name'],
                'City': station['city'],
                'State': station['state'],
                'Zone': station['zone'],
                'Platform_Count': random.randint(8, 16),
                'Is_Active': 'true',
            }

            result = cloudscale_repo.create_record(TABLES['stations'], station_data)
            if result.get('success'):
                created_stations.append({
                    'id': result.get('data', {}).get('ROWID'),
                    'code': station_data['Station_Code'],
                    'name': station_data['Station_Name']
                })

        return jsonify({
            'status': 'success',
            'message': f'Created {len(created_stations)} sample stations',
            'data': created_stations
        }), 201

    except Exception as e:
        logger.exception(f'Create sample stations error: {e}')
        return jsonify({
            'status': 'error',
            'message': 'Failed to create sample stations',
            'error': str(e)
        }), 500


@public_seed_bp.route('/public-seed/trains', methods=['POST'])
def create_sample_trains():
    """Create sample trains with realistic Indian Railway data (PUBLIC - no auth required)."""
    try:
        created_trains = []

        for train in INDIAN_TRAINS:
            train_data = {
                'Train_Number': train['number'],
                'Train_Name': train['name'],
                'Train_Type': train['type'],
                'From_Station': train['from'],
                'To_Station': train['to'],
                'Departure_Time': train['dept'],
                'Arrival_Time': train['arr'],
                'Duration': train['duration'],
                'Days_Of_Operation': 'All Days',
                'Is_Active': 'true',
                'Total_Seats_SL': random.randint(200, 400),
                'Total_Seats_3A': random.randint(100, 200),
                'Total_Seats_2A': random.randint(50, 100),
                'Total_Seats_1A': random.randint(20, 40),
                'Total_Seats_CC': random.randint(50, 100) if train['type'] == 'Shatabdi' else 0,
            }

            result = cloudscale_repo.create_record(TABLES['trains'], train_data)
            if result.get('success'):
                created_trains.append({
                    'id': result.get('data', {}).get('ROWID'),
                    'number': train_data['Train_Number'],
                    'name': train_data['Train_Name']
                })

        return jsonify({
            'status': 'success',
            'message': f'Created {len(created_trains)} sample trains',
            'data': created_trains
        }), 201

    except Exception as e:
        logger.exception(f'Create sample trains error: {e}')
        return jsonify({
            'status': 'error',
            'message': 'Failed to create sample trains',
            'error': str(e)
        }), 500


@public_seed_bp.route('/public-seed/fares', methods=['POST'])
def create_sample_fares():
    """Create sample fares (PUBLIC - no auth required)."""
    try:
        # Get train and station IDs
        trains_result = cloudscale_repo.get_all_records(TABLES['trains'], limit=5)
        train_ids = []
        if trains_result.get('success'):
            trains_data = trains_result.get('data', {}).get('data', [])
            train_ids = [t.get('ROWID') for t in trains_data]

        stations_result = cloudscale_repo.get_all_records(TABLES['stations'], limit=5)
        station_ids = []
        if stations_result.get('success'):
            stations_data = stations_result.get('data', {}).get('data', [])
            station_ids = [s.get('ROWID') for s in stations_data]

        if not train_ids:
            train_ids = ['1']
        if not station_ids:
            station_ids = ['1', '2']

        created_fares = []

        for train_id in train_ids:
            for class_type in CLASS_TYPES:
                source_id = random.choice(station_ids)
                dest_id = random.choice([s for s in station_ids if s != source_id])

                base_fare = random.randint(200, 1500)

                fare_data = {
                    'Train_ID': str(train_id),
                    'Source_Station_ID': str(source_id),
                    'Destination_Station_ID': str(dest_id),
                    'Class_Type': class_type,
                    'Base_Fare': base_fare,
                    'Reservation_Charge': 40,
                    'Superfast_Charge': 45 if class_type != 'SL' else 0,
                    'GST_Percentage': 5.0,
                    'Total_Fare': int(base_fare * 1.1),
                    'Distance': random.randint(100, 800),
                    'Effective_From': past_date(30),
                    'Effective_Until': future_date(365),
                    'Is_Active': 'true',
                }

                result = cloudscale_repo.create_record(TABLES['fares'], fare_data)
                if result.get('success'):
                    created_fares.append({
                        'id': result.get('data', {}).get('ROWID'),
                        'train_id': train_id,
                        'class_type': class_type,
                        'total_fare': fare_data['Total_Fare']
                    })

        return jsonify({
            'status': 'success',
            'message': f'Created {len(created_fares)} sample fares',
            'data': created_fares[:10]  # Show first 10
        }), 201

    except Exception as e:
        logger.exception(f'Create sample fares error: {e}')
        return jsonify({
            'status': 'error',
            'message': 'Failed to create sample fares',
            'error': str(e)
        }), 500


@public_seed_bp.route('/public-seed/settings', methods=['POST'])
def create_sample_settings():
    """Create sample settings (PUBLIC - no auth required)."""
    try:
        sample_settings = [
            {
                'Setting_Key': 'BOOKING_WINDOW_DAYS',
                'Setting_Value': '120',
                'Setting_Type': 'INTEGER',
                'Description': 'Number of days in advance bookings are allowed',
                'Category': 'BOOKING',
                'Is_Public': 'true',
                'Is_Active': 'true',
            },
            {
                'Setting_Key': 'MAX_PASSENGERS_PER_BOOKING',
                'Setting_Value': '6',
                'Setting_Type': 'INTEGER',
                'Description': 'Maximum passengers allowed per booking',
                'Category': 'BOOKING',
                'Is_Public': 'true',
                'Is_Active': 'true',
            },
            {
                'Setting_Key': 'TATKAL_BOOKING_TIME',
                'Setting_Value': '10:00',
                'Setting_Type': 'TIME',
                'Description': 'Time when Tatkal booking opens',
                'Category': 'BOOKING',
                'Is_Public': 'true',
                'Is_Active': 'true',
            },
            {
                'Setting_Key': 'SMS_NOTIFICATIONS',
                'Setting_Value': 'true',
                'Setting_Type': 'BOOLEAN',
                'Description': 'Enable SMS notifications',
                'Category': 'NOTIFICATION',
                'Is_Public': 'false',
                'Is_Active': 'true',
            }
        ]

        created_settings = []

        for setting in sample_settings:
            result = cloudscale_repo.create_record(TABLES['settings'], setting)
            if result.get('success'):
                created_settings.append({
                    'id': result.get('data', {}).get('ROWID'),
                    'key': setting['Setting_Key'],
                    'value': setting['Setting_Value']
                })

        return jsonify({
            'status': 'success',
            'message': f'Created {len(created_settings)} sample settings',
            'data': created_settings
        }), 201

    except Exception as e:
        logger.exception(f'Create sample settings error: {e}')
        return jsonify({
            'status': 'error',
            'message': 'Failed to create sample settings',
            'error': str(e)
        }), 500


@public_seed_bp.route('/public-seed/announcements', methods=['POST'])
def create_sample_announcements():
    """Create sample announcements (PUBLIC - no auth required)."""
    try:
        sample_announcements = [
            {
                'Title': 'Welcome to Smart Railway System',
                'Message': 'Thank you for using our advanced railway booking system. Experience seamless travel booking with real-time updates.',
                'Announcement_Type': 'INFO',
                'Target_Audience': 'ALL',
                'Priority': 'LOW',
                'Valid_From': past_date(5),
                'Valid_Until': future_date(30),
                'Is_Active': 'true',
            },
            {
                'Title': 'Platform Updates Available',
                'Message': 'Check platform information before boarding. Real-time updates are available on our mobile app.',
                'Announcement_Type': 'INFO',
                'Target_Audience': 'PASSENGERS',
                'Priority': 'MEDIUM',
                'Valid_From': past_date(2),
                'Valid_Until': future_date(15),
                'Is_Active': 'true',
            },
            {
                'Title': 'Digital Tickets Recommended',
                'Message': 'Save time and paper by using digital tickets. Show your e-ticket on mobile for faster boarding.',
                'Announcement_Type': 'INFO',
                'Target_Audience': 'ALL',
                'Priority': 'LOW',
                'Valid_From': past_date(10),
                'Valid_Until': future_date(60),
                'Is_Active': 'true',
            }
        ]

        created_announcements = []

        for announcement in sample_announcements:
            result = cloudscale_repo.create_record(TABLES['announcements'], announcement)
            if result.get('success'):
                created_announcements.append({
                    'id': result.get('data', {}).get('ROWID'),
                    'title': announcement['Title'],
                    'type': announcement['Announcement_Type']
                })

        return jsonify({
            'status': 'success',
            'message': f'Created {len(created_announcements)} sample announcements',
            'data': created_announcements
        }), 201

    except Exception as e:
        logger.exception(f'Create sample announcements error: {e}')
        return jsonify({
            'status': 'error',
            'message': 'Failed to create sample announcements',
            'error': str(e)
        }), 500


@public_seed_bp.route('/public-seed/quotas', methods=['POST'])
def create_sample_quotas():
    """Create sample quotas (PUBLIC - no auth required)."""
    try:
        # Get train and station IDs
        trains_result = cloudscale_repo.get_all_records(TABLES['trains'], limit=3)
        train_ids = []
        if trains_result.get('success'):
            trains_data = trains_result.get('data', {}).get('data', [])
            train_ids = [t.get('ROWID') for t in trains_data]

        stations_result = cloudscale_repo.get_all_records(TABLES['stations'], limit=3)
        station_ids = []
        if stations_result.get('success'):
            stations_data = stations_result.get('data', {}).get('data', [])
            station_ids = [s.get('ROWID') for s in stations_data]

        if not train_ids:
            train_ids = ['1']
        if not station_ids:
            station_ids = ['1']

        created_quotas = []
        quota_types = ['GENERAL', 'TATKAL', 'LADIES', 'SENIOR_CITIZEN']

        for train_id in train_ids:
            for station_id in station_ids:
                for class_type in CLASS_TYPES[:3]:  # First 3 class types
                    for quota_type in quota_types[:2]:  # First 2 quota types
                        quota_data = {
                            'Train_ID': str(train_id),
                            'Station_ID': str(station_id),
                            'Class_Type': class_type,
                            'Quota_Type': quota_type,
                            'Total_Quota': random.randint(20, 50),
                            'Available_Quota': random.randint(0, 30),
                            'Journey_Date': future_date(30),
                            'Is_Active': 'true',
                        }

                        result = cloudscale_repo.create_record(TABLES['quotas'], quota_data)
                        if result.get('success'):
                            created_quotas.append({
                                'id': result.get('data', {}).get('ROWID'),
                                'train_id': train_id,
                                'quota_type': quota_type,
                                'class_type': class_type
                            })

        return jsonify({
            'status': 'success',
            'message': f'Created {len(created_quotas)} sample quotas',
            'data': created_quotas[:10]  # Show first 10
        }), 201

    except Exception as e:
        logger.exception(f'Create sample quotas error: {e}')
        return jsonify({
            'status': 'error',
            'message': 'Failed to create sample quotas',
            'error': str(e)
        }), 500


@public_seed_bp.route('/public-seed/all-basic', methods=['POST'])
def create_all_basic_sample_data():
    """Create basic sample data for all major modules (PUBLIC - no auth required)."""
    try:
        results = {}

        # Step 1: Stations (foundation)
        stations_result = create_sample_stations()
        results['stations'] = {
            'success': stations_result[1] == 201,
            'message': stations_result[0].json.get('message', 'Unknown')
        }

        # Step 2: Trains
        trains_result = create_sample_trains()
        results['trains'] = {
            'success': trains_result[1] == 201,
            'message': trains_result[0].json.get('message', 'Unknown')
        }

        # Step 3: Fares
        fares_result = create_sample_fares()
        results['fares'] = {
            'success': fares_result[1] == 201,
            'message': fares_result[0].json.get('message', 'Unknown')
        }

        # Step 4: Settings
        settings_result = create_sample_settings()
        results['settings'] = {
            'success': settings_result[1] == 201,
            'message': settings_result[0].json.get('message', 'Unknown')
        }

        # Step 5: Announcements
        announcements_result = create_sample_announcements()
        results['announcements'] = {
            'success': announcements_result[1] == 201,
            'message': announcements_result[0].json.get('message', 'Unknown')
        }

        # Step 6: Quotas
        quotas_result = create_sample_quotas()
        results['quotas'] = {
            'success': quotas_result[1] == 201,
            'message': quotas_result[0].json.get('message', 'Unknown')
        }

        success_count = sum(1 for r in results.values() if r.get('success'))

        return jsonify({
            'status': 'success',
            'message': f'Basic sample data creation completed: {success_count}/6 modules successful',
            'results': results
        }), 200

    except Exception as e:
        logger.exception(f'Create all basic sample data error: {e}')
        return jsonify({
            'status': 'error',
            'message': 'Failed to create all basic sample data',
            'error': str(e)
        }), 500


@public_seed_bp.route('/public-seed/status', methods=['GET'])
def get_public_seed_status():
    """Get status of sample data creation (PUBLIC - no auth required)."""
    try:
        status = {}

        # Check key modules
        key_modules = ['stations', 'trains', 'fares', 'settings', 'announcements', 'quotas']

        for module in key_modules:
            try:
                count = cloudscale_repo.count_records(TABLES[module])
                status[module] = {
                    'table': TABLES[module],
                    'record_count': count,
                    'has_data': count > 0
                }
            except Exception as e:
                status[module] = {
                    'table': TABLES.get(module, 'Unknown'),
                    'record_count': 0,
                    'has_data': False,
                    'error': str(e)
                }

        total_records = sum(s.get('record_count', 0) for s in status.values())
        modules_with_data = sum(1 for s in status.values() if s.get('has_data'))

        return jsonify({
            'status': 'success',
            'summary': {
                'total_modules_checked': len(status),
                'modules_with_data': modules_with_data,
                'total_records': total_records
            },
            'modules': status
        }), 200

    except Exception as e:
        logger.exception(f'Public seed status error: {e}')
        return jsonify({
            'status': 'error',
            'message': 'Failed to get seed status',
            'error': str(e)
        }), 500