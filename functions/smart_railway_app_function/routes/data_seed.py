"""
Comprehensive Sample Data Seeder - Populate All Railway Modules

Creates sample data for all requested modules:
Passengers, Bookings, Quotas, Fares, Train_Inventory, Coach_Layouts,
Route_Stops, Train_Routes, Trains, Stations, Settings, Admin_Logs, Announcements

Handles dependencies: Stations -> Trains -> Routes -> Stops -> Bookings -> Passengers
"""

import logging
import random
import string
from datetime import datetime, timedelta
from flask import Blueprint, jsonify, request

from repositories.cloudscale_repository import cloudscale_repo
from config import TABLES
from core.security import hash_password

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════════════════════
#  CLOUDSCALE CONNECTION HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def _is_backend_setup_error(value) -> bool:
    """Check if error indicates backend setup issue."""
    if not value:
        return False
    error_str = str(value).lower()
    return any(keyword in error_str for keyword in [
        'invalid oauth', 'oauth error', 'authentication failed',
        'tls bundle', 'certificate', 'ssl error', 'connection refused'
    ])


def _probe_cloudscale_connection() -> tuple:
    """Probe CloudScale once to distinguish setup issues from auth failures."""
    try:
        probe = cloudscale_repo.execute_query("SELECT ROWID FROM Users LIMIT 1")
        if probe.get('success'):
            return True, ''
        return False, str(probe.get('error', 'CloudScale query failed'))
    except Exception as exc:
        return False, str(exc)
data_seed_bp = Blueprint('data_seed', __name__)

# Sample data generators
def random_string(length=8):
    return ''.join(random.choices(string.ascii_letters, k=length))

def random_digits(length=6):
    return ''.join(random.choices(string.digits, k=length))

def random_phone():
    return f"9{random_digits(9)}"

def random_email():
    return f"{random_string(5).lower()}@{random_string(6).lower()}.com"

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

def random_fare():
    return random.randint(100, 2000)

def random_seat_number():
    return f"{random.randint(1, 80)}"

def random_coach_number():
    return f"S{random.randint(1, 24)}"

def random_pnr():
    return f"PNR{random_digits(10)}"

# Sample data templates
INDIAN_CITIES = [
    "Mumbai", "Delhi", "Bangalore", "Hyderabad", "Chennai", "Kolkata",
    "Pune", "Ahmedabad", "Jaipur", "Lucknow", "Kanpur", "Nagpur",
    "Indore", "Thane", "Bhopal", "Visakhapatnam", "Pimpri", "Patna"
]

INDIAN_STATES = [
    "Maharashtra", "Delhi", "Karnataka", "Telangana", "Tamil Nadu",
    "West Bengal", "Gujarat", "Rajasthan", "Uttar Pradesh", "Madhya Pradesh"
]

RAILWAY_ZONES = ["CR", "WR", "SR", "NR", "ER", "NER", "NCR", "SCR", "SWR", "ECR"]

TRAIN_TYPES = ["Express", "Superfast", "Mail", "Local", "Rajdhani", "Shatabdi", "Duronto", "Jan Shatabdi"]

CLASS_TYPES = ["SL", "3A", "2A", "1A", "CC"]

QUOTA_TYPES = ["GENERAL", "TATKAL", "LADIES", "SENIOR_CITIZEN", "HANDICAPPED", "DEFENSE", "FOREIGN_TOURIST"]

BERTH_PREFERENCES = ["Lower", "Middle", "Upper", "Side Lower", "Side Upper", "Window"]

FOOD_CHOICES = ["Veg", "Non-Veg", "Jain", "None"]

ANNOUNCEMENT_TYPES = ["INFO", "WARNING", "DELAY", "PLATFORM", "CANCELLATION", "MAINTENANCE"]

@data_seed_bp.route('/data-seed/all', methods=['POST'])
def create_all_sample_data():
    """Create comprehensive sample data for all railway modules."""
    try:
        results = {}

        # Step 1: Create Stations (Foundation)
        logger.info("Creating sample stations...")
        stations_result = create_sample_stations()
        results['stations'] = stations_result

        if not stations_result.get('success'):
            return jsonify({'status': 'error', 'message': 'Failed to create stations', 'results': results}), 500

        # Step 2: Create Trains
        logger.info("Creating sample trains...")
        trains_result = create_sample_trains()
        results['trains'] = trains_result

        # Step 3: Create Train Routes
        logger.info("Creating sample train routes...")
        routes_result = create_sample_train_routes()
        results['train_routes'] = routes_result

        # Step 4: Create Route Stops
        logger.info("Creating sample route stops...")
        stops_result = create_sample_route_stops()
        results['route_stops'] = stops_result

        # Step 5: Create Coach Layouts
        logger.info("Creating sample coach layouts...")
        coach_layouts_result = create_sample_coach_layouts()
        results['coach_layouts'] = coach_layouts_result

        # Step 6: Create Train Inventory
        logger.info("Creating sample train inventory...")
        inventory_result = create_sample_train_inventory()
        results['train_inventory'] = inventory_result

        # Step 7: Create Fares
        logger.info("Creating sample fares...")
        fares_result = create_sample_fares()
        results['fares'] = fares_result

        # Step 8: Create Quotas
        logger.info("Creating sample quotas...")
        quotas_result = create_sample_quotas()
        results['quotas'] = quotas_result

        # Step 9: Create Bookings
        logger.info("Creating sample bookings...")
        bookings_result = create_sample_bookings()
        results['bookings'] = bookings_result

        # Step 10: Create Passengers
        logger.info("Creating sample passengers...")
        passengers_result = create_sample_passengers()
        results['passengers'] = passengers_result

        # Step 11: Create Settings
        logger.info("Creating sample settings...")
        settings_result = create_sample_settings()
        results['settings'] = settings_result

        # Step 12: Create Announcements
        logger.info("Creating sample announcements...")
        announcements_result = create_sample_announcements()
        results['announcements'] = announcements_result

        # Step 13: Create Admin Logs (sample log entries)
        logger.info("Creating sample admin logs...")
        admin_logs_result = create_sample_admin_logs()
        results['admin_logs'] = admin_logs_result

        # Summary
        success_count = sum(1 for r in results.values() if r.get('success'))
        total_count = len(results)

        return jsonify({
            'status': 'success',
            'message': f'Sample data creation completed: {success_count}/{total_count} modules successful',
            'summary': {
                'total_modules': total_count,
                'successful': success_count,
                'failed': total_count - success_count
            },
            'results': results
        }), 200

    except Exception as e:
        logger.exception(f'Sample data creation error: {e}')
        return jsonify({
            'status': 'error',
            'message': 'Failed to create sample data',
            'error': str(e)
        }), 500


def create_sample_stations():
    """Create 10 sample stations across India."""
    try:
        stations_data = []
        created_ids = []

        for i in range(10):
            city = random.choice(INDIAN_CITIES)
            station_code = f"{city[:3].upper()}{random.randint(10, 99)}"

            station_data = {
                'Station_Code': station_code,
                'Station_Name': f"{city} {random.choice(['Junction', 'Central', 'Terminal', 'Railway Station'])}",
                'City': city,
                'State': random.choice(INDIAN_STATES),
                'Zone': random.choice(RAILWAY_ZONES),
                'Platform_Count': random.randint(2, 8),
                'Is_Active': 'true',
            }

            result = cloudscale_repo.create_record(TABLES['stations'], station_data)
            if result.get('success'):
                created_ids.append(result.get('data', {}).get('ROWID'))
                stations_data.append(station_data)

        return {
            'success': len(created_ids) > 0,
            'created_count': len(created_ids),
            'created_ids': created_ids,
            'sample_data': stations_data[:3]  # Show first 3 for reference
        }

    except Exception as e:
        logger.exception(f'Create sample stations error: {e}')
        return {'success': False, 'error': str(e)}


def create_sample_trains():
    """Create 8 sample trains."""
    try:
        trains_data = []
        created_ids = []

        # Get some station IDs
        stations = cloudscale_repo.get_all_records(TABLES['stations'], limit=10)
        station_ids = [s.get('ROWID') for s in stations.get('data', {}).get('data', [])] if stations.get('success') else ['1', '2']

        for i in range(8):
            train_number = f"{random.randint(10000, 99999)}"
            train_name = f"{random_string(6)} {random.choice(TRAIN_TYPES)}"

            train_data = {
                'Train_Number': train_number,
                'Train_Name': train_name,
                'Train_Type': random.choice(TRAIN_TYPES),
                'Source_Station_ID': str(random.choice(station_ids)),
                'Destination_Station_ID': str(random.choice(station_ids)),
                'Departure_Time': random_time(),
                'Arrival_Time': random_time(),
                'Journey_Duration': random.randint(120, 1440),  # 2-24 hours
                'Distance': random.randint(100, 2500),
                'Run_Days': 'Mon,Tue,Wed,Thu,Fri,Sat,Sun',
                'Is_Active': 'true',
            }

            result = cloudscale_repo.create_record(TABLES['trains'], train_data)
            if result.get('success'):
                created_ids.append(result.get('data', {}).get('ROWID'))
                trains_data.append(train_data)

        return {
            'success': len(created_ids) > 0,
            'created_count': len(created_ids),
            'created_ids': created_ids,
            'sample_data': trains_data[:3]
        }

    except Exception as e:
        logger.exception(f'Create sample trains error: {e}')
        return {'success': False, 'error': str(e)}


def create_sample_train_routes():
    """Create sample train routes."""
    try:
        routes_data = []
        created_ids = []

        # Get train IDs
        trains = cloudscale_repo.get_all_records(TABLES['trains'], limit=8)
        train_ids = [t.get('ROWID') for t in trains.get('data', {}).get('data', [])] if trains.get('success') else ['1', '2']

        for train_id in train_ids:
            route_data = {
                'Train_ID': str(train_id),
                'Route_Name': f"Route-{random_string(4)}",
                'Total_Distance': random.randint(200, 2500),
                'Total_Stops': random.randint(5, 20),
                'Is_Active': 'true',
            }

            result = cloudscale_repo.create_record(TABLES['train_routes'], route_data)
            if result.get('success'):
                created_ids.append(result.get('data', {}).get('ROWID'))
                routes_data.append(route_data)

        return {
            'success': len(created_ids) > 0,
            'created_count': len(created_ids),
            'created_ids': created_ids,
            'sample_data': routes_data[:3]
        }

    except Exception as e:
        logger.exception(f'Create sample train routes error: {e}')
        return {'success': False, 'error': str(e)}


def create_sample_route_stops():
    """Create sample route stops."""
    try:
        stops_data = []
        created_ids = []

        # Get route and station IDs
        routes = cloudscale_repo.get_all_records(TABLES['train_routes'], limit=8)
        route_ids = [r.get('ROWID') for r in routes.get('data', {}).get('data', [])] if routes.get('success') else ['1']

        stations = cloudscale_repo.get_all_records(TABLES['stations'], limit=10)
        station_ids = [s.get('ROWID') for s in stations.get('data', {}).get('data', [])] if stations.get('success') else ['1', '2']

        for route_id in route_ids:
            # Create 3-5 stops per route
            stop_count = random.randint(3, 5)
            for sequence in range(1, stop_count + 1):
                arrival = random_time()
                departure = random_time()

                stop_data = {
                    'Route_ID': str(route_id),
                    'Station_ID': str(random.choice(station_ids)),
                    'Stop_Sequence': sequence,
                    'Arrival_Time': arrival,
                    'Departure_Time': departure,
                    'Distance_From_Origin': sequence * random.randint(50, 200),
                    'Halt_Duration': random.randint(2, 15),  # 2-15 minutes
                    'Platform': f"{random.randint(1, 8)}",
                }

                result = cloudscale_repo.create_record(TABLES['route_stops'], stop_data)
                if result.get('success'):
                    created_ids.append(result.get('data', {}).get('ROWID'))
                    stops_data.append(stop_data)

        return {
            'success': len(created_ids) > 0,
            'created_count': len(created_ids),
            'created_ids': created_ids,
            'sample_data': stops_data[:5]
        }

    except Exception as e:
        logger.exception(f'Create sample route stops error: {e}')
        return {'success': False, 'error': str(e)}


def create_sample_coach_layouts():
    """Create sample coach layouts."""
    try:
        layouts_data = []
        created_ids = []

        # Get train IDs
        trains = cloudscale_repo.get_all_records(TABLES['trains'], limit=8)
        train_ids = [t.get('ROWID') for t in trains.get('data', {}).get('data', [])] if trains.get('success') else ['1', '2']

        for train_id in train_ids:
            # Create layouts for different coach types
            for class_type in CLASS_TYPES:
                for coach_num in range(1, 4):  # 3 coaches per type
                    layout_data = {
                        'Train_ID': str(train_id),
                        'Coach_Type': class_type,
                        'Coach_Number': f"{class_type}{coach_num}",
                        'Total_Seats': {
                            'SL': 72, '3A': 64, '2A': 48, '1A': 24, 'CC': 80
                        }.get(class_type, 60),
                        'Seat_Configuration': {
                            'SL': '3+3', '3A': '2+2', '2A': '2+2', '1A': '2+0', 'CC': '3+2'
                        }.get(class_type, '3+3'),
                        'Facilities': f"AC,Charging Point,Reading Light,{'TV' if class_type in ['1A', '2A'] else 'Fan'}",
                        'Position': coach_num,
                    }

                    result = cloudscale_repo.create_record(TABLES['coach_layouts'], layout_data)
                    if result.get('success'):
                        created_ids.append(result.get('data', {}).get('ROWID'))
                        layouts_data.append(layout_data)

        return {
            'success': len(created_ids) > 0,
            'created_count': len(created_ids),
            'created_ids': created_ids,
            'sample_data': layouts_data[:5]
        }

    except Exception as e:
        logger.exception(f'Create sample coach layouts error: {e}')
        return {'success': False, 'error': str(e)}


def create_sample_train_inventory():
    """Create sample train inventory."""
    try:
        inventory_data = []
        created_ids = []

        # Get train IDs
        trains = cloudscale_repo.get_all_records(TABLES['trains'], limit=8)
        train_ids = [t.get('ROWID') for t in trains.get('data', {}).get('data', [])] if trains.get('success') else ['1', '2']

        # Create inventory for next 30 days for each train
        for train_id in train_ids:
            for day_offset in range(0, 30, 3):  # Every 3rd day
                journey_date = (datetime.now() + timedelta(days=day_offset)).strftime('%Y-%m-%d')

                inventory_rec = {
                    'Train_ID': str(train_id),
                    'Journey_Date': journey_date,
                    'Available_Seats_SL': random.randint(0, 200),
                    'Available_Seats_3A': random.randint(0, 150),
                    'Available_Seats_2A': random.randint(0, 100),
                    'Available_Seats_1A': random.randint(0, 50),
                    'Available_Seats_CC': random.randint(0, 180),
                }

                result = cloudscale_repo.create_record(TABLES['train_inventory'], inventory_rec)
                if result.get('success'):
                    created_ids.append(result.get('data', {}).get('ROWID'))
                    inventory_data.append(inventory_rec)

        return {
            'success': len(created_ids) > 0,
            'created_count': len(created_ids),
            'created_ids': created_ids,
            'sample_data': inventory_data[:5]
        }

    except Exception as e:
        logger.exception(f'Create sample train inventory error: {e}')
        return {'success': False, 'error': str(e)}


def create_sample_fares():
    """Create sample fares."""
    try:
        fares_data = []
        created_ids = []

        # Get train and station IDs
        trains = cloudscale_repo.get_all_records(TABLES['trains'], limit=8)
        train_ids = [t.get('ROWID') for t in trains.get('data', {}).get('data', [])] if trains.get('success') else ['1', '2']

        stations = cloudscale_repo.get_all_records(TABLES['stations'], limit=10)
        station_ids = [s.get('ROWID') for s in stations.get('data', {}).get('data', [])] if stations.get('success') else ['1', '2']

        for train_id in train_ids:
            for class_type in CLASS_TYPES:
                # Create fare between random stations
                source_id = random.choice(station_ids)
                dest_id = random.choice([s for s in station_ids if s != source_id])

                base_fare = random_fare()

                fare_data = {
                    'Train_ID': str(train_id),
                    'Source_Station_ID': str(source_id),
                    'Destination_Station_ID': str(dest_id),
                    'Class_Type': class_type,
                    'Base_Fare': base_fare,
                    'Reservation_Charge': 40 if class_type != 'CC' else 20,
                    'Superfast_Charge': 45 if class_type not in ['SL', 'CC'] else 0,
                    'GST_Percentage': 5.0,
                    'Total_Fare': int(base_fare * 1.1),  # includes charges
                    'Distance': random.randint(100, 1500),
                    'Effective_From': past_date(30),
                    'Effective_Until': future_date(365),
                    'Is_Active': 'true',
                }

                result = cloudscale_repo.create_record(TABLES['fares'], fare_data)
                if result.get('success'):
                    created_ids.append(result.get('data', {}).get('ROWID'))
                    fares_data.append(fare_data)

        return {
            'success': len(created_ids) > 0,
            'created_count': len(created_ids),
            'created_ids': created_ids,
            'sample_data': fares_data[:5]
        }

    except Exception as e:
        logger.exception(f'Create sample fares error: {e}')
        return {'success': False, 'error': str(e)}


def create_sample_quotas():
    """Create sample quotas."""
    try:
        quotas_data = []
        created_ids = []

        # Get train and station IDs
        trains = cloudscale_repo.get_all_records(TABLES['trains'], limit=5)
        train_ids = [t.get('ROWID') for t in trains.get('data', {}).get('data', [])] if trains.get('success') else ['1', '2']

        stations = cloudscale_repo.get_all_records(TABLES['stations'], limit=5)
        station_ids = [s.get('ROWID') for s in stations.get('data', {}).get('data', [])] if stations.get('success') else ['1', '2']

        for train_id in train_ids:
            for station_id in station_ids:
                for class_type in CLASS_TYPES:
                    for quota_type in QUOTA_TYPES:
                        quota_data = {
                            'Train_ID': str(train_id),
                            'Station_ID': str(station_id),
                            'Class_Type': class_type,
                            'Quota_Type': quota_type,
                            'Total_Quota': random.randint(10, 50),
                            'Available_Quota': random.randint(0, 30),
                            'Journey_Date': future_date(30),
                            'Is_Active': 'true',
                        }

                        result = cloudscale_repo.create_record(TABLES['quotas'], quota_data)
                        if result.get('success'):
                            created_ids.append(result.get('data', {}).get('ROWID'))
                            quotas_data.append(quota_data)

        return {
            'success': len(created_ids) > 0,
            'created_count': len(created_ids),
            'created_ids': created_ids,
            'sample_data': quotas_data[:5]
        }

    except Exception as e:
        logger.exception(f'Create sample quotas error: {e}')
        return {'success': False, 'error': str(e)}


def create_sample_bookings():
    """Create sample bookings."""
    try:
        bookings_data = []
        created_ids = []

        # Get user, train, and station IDs
        users = cloudscale_repo.get_all_records(TABLES['users'], limit=5)
        user_ids = [u.get('ROWID') for u in users.get('data', {}).get('data', [])] if users.get('success') else ['1']

        trains = cloudscale_repo.get_all_records(TABLES['trains'], limit=5)
        train_ids = [t.get('ROWID') for t in trains.get('data', {}).get('data', [])] if trains.get('success') else ['1']

        stations = cloudscale_repo.get_all_records(TABLES['stations'], limit=5)
        station_ids = [s.get('ROWID') for s in stations.get('data', {}).get('data', [])] if stations.get('success') else ['1', '2']

        for i in range(15):  # 15 sample bookings
            booking_data = {
                'User_ID': str(random.choice(user_ids)),
                'Train_ID': str(random.choice(train_ids)),
                'PNR': random_pnr(),
                'Journey_Date': future_date(30),
                'Source_Station_ID': str(random.choice(station_ids)),
                'Destination_Station_ID': str(random.choice(station_ids)),
                'Class_Type': random.choice(CLASS_TYPES),
                'Passenger_Count': random.randint(1, 4),
                'Total_Fare': random.randint(500, 5000),
                'Booking_Status': random.choice(['CONFIRMED', 'WAITLISTED', 'RAC', 'CANCELLED']),
                'Payment_Status': random.choice(['COMPLETED', 'PENDING', 'FAILED']),
                'Booking_Date': past_date(7),
            }

            result = cloudscale_repo.create_record(TABLES['bookings'], booking_data)
            if result.get('success'):
                created_ids.append(result.get('data', {}).get('ROWID'))
                bookings_data.append(booking_data)

        return {
            'success': len(created_ids) > 0,
            'created_count': len(created_ids),
            'created_ids': created_ids,
            'sample_data': bookings_data[:3]
        }

    except Exception as e:
        logger.exception(f'Create sample bookings error: {e}')
        return {'success': False, 'error': str(e)}


def create_sample_passengers():
    """Create sample passengers."""
    try:
        passengers_data = []
        created_ids = []

        # Get booking IDs
        bookings = cloudscale_repo.get_all_records(TABLES['bookings'], limit=15)
        booking_ids = [b.get('ROWID') for b in bookings.get('data', {}).get('data', [])] if bookings.get('success') else ['1']

        first_names = ["Rajesh", "Priya", "Amit", "Sneha", "Vikram", "Kavya", "Arjun", "Meera", "Rohit", "Anita"]
        last_names = ["Sharma", "Patel", "Kumar", "Singh", "Gupta", "Reddy", "Yadav", "Joshi", "Nair", "Shah"]

        for booking_id in booking_ids:
            # Create 1-3 passengers per booking
            passenger_count = random.randint(1, 3)
            for p in range(passenger_count):
                passenger_data = {
                    'Booking_ID': str(booking_id),
                    'Passenger_Name': f"{random.choice(first_names)} {random.choice(last_names)}",
                    'Age': random.randint(18, 75),
                    'Gender': random.choice(['Male', 'Female', 'Other']),
                    'Berth_Preference': random.choice(BERTH_PREFERENCES),
                    'Seat_Number': random_seat_number(),
                    'Coach_Number': random_coach_number(),
                    'Booking_Status': random.choice(['CNF', 'RAC', 'WL']),
                    'Food_Choice': random.choice(FOOD_CHOICES),
                    'ID_Type': random.choice(['Aadhaar', 'Passport', 'Voter ID', 'Driving License']),
                    'ID_Number': random_digits(12),
                    'Contact_Number': random_phone(),
                }

                result = cloudscale_repo.create_record(TABLES['passengers'], passenger_data)
                if result.get('success'):
                    created_ids.append(result.get('data', {}).get('ROWID'))
                    passengers_data.append(passenger_data)

        return {
            'success': len(created_ids) > 0,
            'created_count': len(created_ids),
            'created_ids': created_ids,
            'sample_data': passengers_data[:5]
        }

    except Exception as e:
        logger.exception(f'Create sample passengers error: {e}')
        return {'success': False, 'error': str(e)}


def create_sample_settings():
    """Create sample system settings."""
    try:
        settings_data = []
        created_ids = []

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
                'Setting_Key': 'TATKAL_BOOKING_TIME',
                'Setting_Value': '10:00',
                'Setting_Type': 'TIME',
                'Description': 'Time when Tatkal booking opens',
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
                'Setting_Key': 'CANCELLATION_CHARGES_PERCENTAGE',
                'Setting_Value': '10.0',
                'Setting_Type': 'FLOAT',
                'Description': 'Cancellation charges as percentage of fare',
                'Category': 'FINANCE',
                'Is_Public': 'true',
                'Is_Active': 'true',
            },
            {
                'Setting_Key': 'SMS_API_ENABLED',
                'Setting_Value': 'true',
                'Setting_Type': 'BOOLEAN',
                'Description': 'Enable SMS notifications',
                'Category': 'NOTIFICATION',
                'Is_Public': 'false',
                'Is_Active': 'true',
            },
            {
                'Setting_Key': 'EMAIL_NOTIFICATIONS',
                'Setting_Value': 'true',
                'Setting_Type': 'BOOLEAN',
                'Description': 'Enable email notifications',
                'Category': 'NOTIFICATION',
                'Is_Public': 'false',
                'Is_Active': 'true',
            },
            {
                'Setting_Key': 'SYSTEM_MAINTENANCE_MODE',
                'Setting_Value': 'false',
                'Setting_Type': 'BOOLEAN',
                'Description': 'Enable maintenance mode',
                'Category': 'SYSTEM',
                'Is_Public': 'false',
                'Is_Active': 'true',
            }
        ]

        for setting in sample_settings:
            result = cloudscale_repo.create_record(TABLES['settings'], setting)
            if result.get('success'):
                created_ids.append(result.get('data', {}).get('ROWID'))
                settings_data.append(setting)

        return {
            'success': len(created_ids) > 0,
            'created_count': len(created_ids),
            'created_ids': created_ids,
            'sample_data': settings_data
        }

    except Exception as e:
        logger.exception(f'Create sample settings error: {e}')
        return {'success': False, 'error': str(e)}


def create_sample_announcements():
    """Create sample announcements."""
    try:
        announcements_data = []
        created_ids = []

        sample_announcements = [
            {
                'Title': 'Platform Change Notification',
                'Message': 'Train 12345 Express will now depart from Platform 3 instead of Platform 1. Please verify your platform before boarding.',
                'Announcement_Type': 'PLATFORM',
                'Target_Audience': 'PASSENGERS',
                'Priority': 'HIGH',
                'Valid_From': past_date(1),
                'Valid_Until': future_date(1),
                'Is_Active': 'true',
            },
            {
                'Title': 'Delayed Train Notification',
                'Message': 'Train 54321 Superfast is running 30 minutes late due to technical reasons. We apologize for the inconvenience.',
                'Announcement_Type': 'DELAY',
                'Target_Audience': 'PASSENGERS',
                'Priority': 'MEDIUM',
                'Valid_From': past_date(1),
                'Valid_Until': future_date(1),
                'Is_Active': 'true',
            },
            {
                'Title': 'Network Maintenance',
                'Message': 'Booking system will undergo maintenance from 2:00 AM to 4:00 AM. Online bookings will be unavailable during this time.',
                'Announcement_Type': 'MAINTENANCE',
                'Target_Audience': 'ALL',
                'Priority': 'HIGH',
                'Valid_From': future_date(1),
                'Valid_Until': future_date(2),
                'Is_Active': 'true',
            },
            {
                'Title': 'Festival Special Trains',
                'Message': 'Special festival trains are now available for booking. Check the schedule for additional services during Diwali.',
                'Announcement_Type': 'INFO',
                'Target_Audience': 'ALL',
                'Priority': 'LOW',
                'Valid_From': past_date(5),
                'Valid_Until': future_date(25),
                'Is_Active': 'true',
            },
            {
                'Title': 'COVID Safety Guidelines',
                'Message': 'Please follow COVID-19 safety protocols: wear masks, maintain social distancing, and carry valid ID proof.',
                'Announcement_Type': 'WARNING',
                'Target_Audience': 'ALL',
                'Priority': 'MEDIUM',
                'Valid_From': past_date(30),
                'Valid_Until': future_date(90),
                'Is_Active': 'true',
            }
        ]

        for announcement in sample_announcements:
            result = cloudscale_repo.create_record(TABLES['announcements'], announcement)
            if result.get('success'):
                created_ids.append(result.get('data', {}).get('ROWID'))
                announcements_data.append(announcement)

        return {
            'success': len(created_ids) > 0,
            'created_count': len(created_ids),
            'created_ids': created_ids,
            'sample_data': announcements_data
        }

    except Exception as e:
        logger.exception(f'Create sample announcements error: {e}')
        return {'success': False, 'error': str(e)}


def create_sample_admin_logs():
    """Create sample admin log entries."""
    try:
        logs_data = []
        created_ids = []

        sample_actions = [
            'User Registration', 'User Login', 'Password Reset', 'Booking Created',
            'Booking Cancelled', 'Train Schedule Updated', 'Fare Updated',
            'Station Added', 'System Maintenance', 'Data Backup'
        ]

        for i in range(20):  # 20 log entries
            log_data = {
                'Admin_ID': '1',  # Assume admin user ID 1
                'User_ID': str(random.randint(1, 10)),
                'Action': random.choice(sample_actions),
                'Description': f"Sample log entry for {random.choice(sample_actions).lower()} action",
                'IP_Address': f"192.168.1.{random.randint(1, 255)}",
                'User_Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Status': random.choice(['SUCCESS', 'FAILED', 'WARNING']),
                'Created_At': past_date(30),
            }

            result = cloudscale_repo.create_record(TABLES['admin_logs'], log_data)
            if result.get('success'):
                created_ids.append(result.get('data', {}).get('ROWID'))
                logs_data.append(log_data)

        return {
            'success': len(created_ids) > 0,
            'created_count': len(created_ids),
            'created_ids': created_ids,
            'sample_data': logs_data[:5]
        }

    except Exception as e:
        logger.exception(f'Create sample admin logs error: {e}')
        return {'success': False, 'error': str(e)}


@data_seed_bp.route('/data-seed/status', methods=['GET'])
def get_seed_status():
    """Check the status of sample data across all modules."""
    try:
        status = {}

        for module, table in TABLES.items():
            try:
                count = cloudscale_repo.count_records(table)
                status[module] = {
                    'table': table,
                    'record_count': count,
                    'has_data': count > 0
                }
            except Exception as e:
                status[module] = {
                    'table': table,
                    'record_count': 0,
                    'has_data': False,
                    'error': str(e)
                }

        total_records = sum(s.get('record_count', 0) for s in status.values())
        modules_with_data = sum(1 for s in status.values() if s.get('has_data'))

        return jsonify({
            'status': 'success',
            'summary': {
                'total_modules': len(status),
                'modules_with_data': modules_with_data,
                'total_records': total_records
            },
            'modules': status
        }), 200

    except Exception as e:
        logger.exception(f'Seed status error: {e}')
        return jsonify({
            'status': 'error',
            'message': 'Failed to get seed status',
            'error': str(e)
        }), 500


@data_seed_bp.route('/data-seed/clear', methods=['DELETE'])
def clear_all_sample_data():
    """Clear all sample data (USE WITH CAUTION)."""
    try:
        results = {}

        # Clear in reverse order to handle dependencies
        clear_order = [
            'passengers', 'bookings', 'route_stops', 'train_routes',
            'coach_layouts', 'train_inventory', 'fares', 'quotas',
            'trains', 'stations', 'announcements', 'admin_logs'
        ]

        for module in clear_order:
            if module in TABLES:
                try:
                    # This is a destructive operation - implement with extreme care
                    # For now, just return the count
                    count = cloudscale_repo.count_records(TABLES[module])
                    results[module] = {
                        'table': TABLES[module],
                        'records_found': count,
                        'cleared': False,  # Not implemented for safety
                        'note': 'Clear operation not implemented for safety'
                    }
                except Exception as e:
                    results[module] = {
                        'error': str(e)
                    }

        return jsonify({
            'status': 'success',
            'message': 'Clear operation completed (records not actually deleted for safety)',
            'results': results
        }), 200

    except Exception as e:
        logger.exception(f'Clear data error: {e}')
        return jsonify({
            'status': 'error',
            'message': 'Failed to clear sample data',
            'error': str(e)
        }), 500


# ══════════════════════════════════════════════════════════════════════════════
#  CREATE USER (PASSENGER) - For ticket booking customers
# ══════════════════════════════════════════════════════════════════════════════

@data_seed_bp.route('/data-seed/user', methods=['POST'])
def create_user():
    """
    Create a user (passenger) for testing.
    Users table is ONLY for passengers who book train tickets.
    
    POST /data-seed/user
    {
        "email": "passenger@example.com",
        "password": "Pass@123",
        "full_name": "John Doe",
        "phone_number": "+91-9876543210"
    }
    """
    try:
        data = request.get_json() or {}
        
        email = (data.get('email') or 'passenger@example.com').strip().lower()
        password = data.get('password') or 'Pass@123'
        full_name = data.get('full_name') or 'Test Passenger'
        phone_number = data.get('phone_number') or '+91-9999999999'
        
        logger.info(f"Creating user (passenger): {email}")
        
        # Hash the password
        password_hash = hash_password(password)
        
        # Check if user already exists
        check_query = f"SELECT ROWID, Email FROM {TABLES['users']} WHERE Email = '{email}'"
        existing = cloudscale_repo.execute_query(check_query)
        
        if existing.get('success') and existing.get('data', {}).get('data'):
            return jsonify({
                'status': 'error',
                'message': f'User with email {email} already exists',
                'existing_user_id': existing['data']['data'][0].get('ROWID')
            }), 409
        
        # Create Users record (passenger) - based on actual schema
        user_data = {
            'Full_Name': full_name,
            'Email': email,  # Mandatory, Unique
            'Password': password_hash,
            'Phone_Number': phone_number,
            'Role': 'USER',
            'Account_Status': 'Active',
            'Is_Verified': True,
        }
        
        result = cloudscale_repo.create_record(TABLES['users'], user_data)
        
        if result.get('success'):
            logger.info(f"User (passenger) created: {email}")
            return jsonify({
                'status': 'success',
                'message': 'User (passenger) created successfully',
                'data': {
                    'user_rowid': result.get('data', {}).get('ROWID'),
                    'email': email,
                    'full_name': full_name,
                    'role': 'USER',
                    'note': 'Login with /session/login endpoint (passenger login)'
                }
            }), 201
        else:
            logger.error(f"Failed to create user: {result.get('error')}")
            return jsonify({
                'status': 'error',
                'message': 'Failed to create user',
                'error': result.get('error')
            }), 500
            
    except Exception as e:
        logger.exception(f'Create user error: {e}')
        return jsonify({
            'status': 'error',
            'message': 'Failed to create user',
            'error': str(e)
        }), 500


# ══════════════════════════════════════════════════════════════════════════════
#  CREATE ADMIN EMPLOYEE - For railway staff/admin
# ══════════════════════════════════════════════════════════════════════════════

@data_seed_bp.route('/data-seed/admin-employee', methods=['POST'])
def create_admin_employee():
    """
    Create an admin employee for testing.
    
    Creates ONLY an Employees record (NOT Users - Users is for passengers only).
    Employee authentication checks ONLY the Employees table.
    
    POST /data-seed/admin-employee
    {
        "email": "admin@railway.com",
        "password": "Admin@123",
        "full_name": "System Admin",
        "department": "Administration",
        "designation": "System Administrator",
        "phone_number": "+91-9876543210"
    }
    """
    # Log request details for debugging
    logger.info(f"Data-seed request from {request.remote_addr}, method: {request.method}")
    
    # Check CloudScale connection first
    cloudscale_ok, cloudscale_error = _probe_cloudscale_connection()
    if not cloudscale_ok and _is_backend_setup_error(cloudscale_error):
        logger.error(f"CloudScale backend setup error: {cloudscale_error}")
        return jsonify({
            'status': 'error',
            'message': 'Backend setup error',
            'details': cloudscale_error,
        }), 503
    
    if not cloudscale_ok:
        logger.warning(f"CloudScale connection issue (continuing): {cloudscale_error}")
    
    try:
        data = request.get_json() or {}
        
        # Required fields
        email = (data.get('email') or 'admin@railway.com').strip().lower()
        password = data.get('password') or 'Admin@123'
        full_name = data.get('full_name') or 'System Administrator'  # Mandatory
        department = data.get('department') or 'Administration'  # Mandatory
        designation = data.get('designation') or 'System Administrator'  # Mandatory
        
        # Optional fields
        phone_number = data.get('phone_number') or ''
        
        logger.info(f"Creating admin employee: {email}")
        
        # Hash the password
        password_hash = hash_password(password)
        
        # Step 1: Check if Employees record already exists
        check_emp_query = f"SELECT ROWID, Email FROM {TABLES['employees']} WHERE Email = '{email}'"
        existing_emp = cloudscale_repo.execute_query(check_emp_query)
        
        if existing_emp.get('success') and existing_emp.get('data', {}).get('data'):
            logger.info(f"Employees record already exists for {email}")
            return jsonify({
                'status': 'error',
                'message': f'Employee with email {email} already exists',
                'existing_employee_id': existing_emp['data']['data'][0].get('ROWID')
            }), 409
        
        # Step 2: Generate Employee_ID - count existing admins
        count_query = f"SELECT COUNT(ROWID) as cnt FROM {TABLES['employees']} WHERE Role = 'Admin'"
        count_result = cloudscale_repo.execute_query(count_query)
        admin_count = 1
        if count_result.get('success') and count_result.get('data', {}).get('data'):
            admin_count = int(count_result['data']['data'][0].get('cnt', 0)) + 1
        employee_id = f"ADM{admin_count:03d}"
        
        # Step 3: Create Employees record with ALL mandatory fields
        # Mandatory: Full_Name, Employee_ID, Role, Department, Designation
        admin_data = {
            'Employee_ID': employee_id,  # Mandatory
            'Full_Name': full_name,  # Mandatory
            'Email': email,  # Unique
            'Password': password_hash,
            'Role': 'Admin',  # Mandatory
            'Department': department,  # Mandatory
            'Designation': designation,  # Mandatory
            'Account_Status': 'Active',
            'Is_Active': True,
            'Phone_Number': phone_number,
        }
        
        emp_result = cloudscale_repo.create_record(TABLES['employees'], admin_data)
        
        if emp_result.get('success'):
            logger.info(f"Admin employee created: {email} with ID {employee_id}")
            return jsonify({
                'status': 'success',
                'message': 'Admin employee created successfully',
                'data': {
                    'employee_rowid': emp_result.get('data', {}).get('ROWID'),
                    'employee_id': employee_id,
                    'email': email,
                    'full_name': full_name,
                    'role': 'Admin',
                    'department': department,
                    'designation': designation,
                    'note': 'Login with /session/employee/login endpoint'
                }
            }), 201
        else:
            logger.error(f"Failed to create Employees record: {emp_result.get('error')}")
            return jsonify({
                'status': 'error',
                'message': 'Failed to create employee',
                'error': emp_result.get('error')
            }), 500
            
    except Exception as e:
        logger.exception(f'Create admin employee error: {e}')
        return jsonify({
            'status': 'error',
            'message': 'Failed to create admin employee',
            'error': str(e)
        }), 500


# ══════════════════════════════════════════════════════════════════════════════
#  DEBUG ENDPOINT - Check Employee Records
# ══════════════════════════════════════════════════════════════════════════════

@data_seed_bp.route('/data-seed/debug-employees', methods=['GET'])
def debug_employees():
    """
    Debug endpoint to check employee records in the database.
    Lists all employees and their key fields.
    """
    try:
        # Get all employees
        query = f"SELECT ROWID, Employee_ID, Full_Name, Email, Role, Account_Status, Password FROM {TABLES['employees']} LIMIT 50"
        result = cloudscale_repo.execute_query(query)
        
        employees = []
        if result.get('success') and result.get('data', {}).get('data'):
            for emp in result['data']['data']:
                employees.append({
                    'rowid': emp.get('ROWID'),
                    'employee_id': emp.get('Employee_ID'),
                    'full_name': emp.get('Full_Name'),
                    'email': emp.get('Email'),
                    'role': emp.get('Role'),
                    'account_status': emp.get('Account_Status'),
                    'has_password': bool(emp.get('Password')),
                    'password_length': len(emp.get('Password', '')) if emp.get('Password') else 0,
                })
        
        # Also check Users table for admin/employee roles
        users_query = f"SELECT ROWID, Full_Name, Email, Role, Account_Status FROM {TABLES['users']} WHERE Role IN ('ADMIN', 'EMPLOYEE') LIMIT 50"
        users_result = cloudscale_repo.execute_query(users_query)
        
        admin_users = []
        if users_result.get('success') and users_result.get('data', {}).get('data'):
            for user in users_result['data']['data']:
                admin_users.append({
                    'rowid': user.get('ROWID'),
                    'full_name': user.get('Full_Name'),
                    'email': user.get('Email'),
                    'role': user.get('Role'),
                    'account_status': user.get('Account_Status'),
                })
        
        return jsonify({
            'status': 'success',
            'data': {
                'employees_table': employees,
                'employees_count': len(employees),
                'users_with_admin_role': admin_users,
                'users_count': len(admin_users),
            }
        }), 200
        
    except Exception as e:
        logger.exception(f'Debug employees error: {e}')
        return jsonify({
            'status': 'error',
            'message': 'Debug failed',
            'error': str(e)
        }), 500


@data_seed_bp.route('/data-seed/check-employee/<email>', methods=['GET'])
def check_employee_by_email(email):
    """
    Check if an employee exists by email.
    """
    try:
        email_lower = email.lower().strip()
        
        # Check Employees table
        employee = cloudscale_repo.get_employee_by_email(email_lower)
        
        # Check Users table
        user = cloudscale_repo.get_user_by_email(email_lower)
        
        return jsonify({
            'status': 'success',
            'data': {
                'email': email_lower,
                'employee_exists': employee is not None,
                'employee_data': {
                    'rowid': employee.get('ROWID') if employee else None,
                    'employee_id': employee.get('Employee_ID') if employee else None,
                    'role': employee.get('Role') if employee else None,
                    'account_status': employee.get('Account_Status') if employee else None,
                    'has_password': bool(employee.get('Password')) if employee else False,
                } if employee else None,
                'user_exists': user is not None,
                'user_data': {
                    'rowid': user.get('ROWID') if user else None,
                    'role': user.get('Role') if user else None,
                    'account_status': user.get('Account_Status') if user else None,
                } if user else None,
            }
        }), 200
        
    except Exception as e:
        logger.exception(f'Check employee error: {e}')
        return jsonify({
            'status': 'error',
            'message': 'Check failed',
            'error': str(e)
        }), 500


@data_seed_bp.route('/data-seed/debug-query/<email>', methods=['GET'])
def debug_query(email):
    """
    Debug endpoint to test direct query vs CriteriaBuilder.
    """
    try:
        from repositories.cloudscale_repository import CriteriaBuilder
        
        email_lower = email.lower().strip()
        
        # Method 1: Raw query (works in debug-employees)
        raw_query = f"SELECT ROWID, Employee_ID, Full_Name, Email, Password, Role, Account_Status FROM {TABLES['employees']} WHERE Email = '{email_lower}'"
        raw_result = cloudscale_repo.execute_query(raw_query)
        
        # Method 2: CriteriaBuilder + get_records
        criteria = CriteriaBuilder().eq("Email", email_lower).build()
        criteria_query = f"SELECT ROWID, Employee_ID, Full_Name, Email, Password, Role, Department, Designation, Account_Status, Joined_At, Is_Active, Phone_Number FROM {TABLES['employees']} WHERE {criteria} ORDER BY ROWID DESC LIMIT 1"
        criteria_result = cloudscale_repo.execute_query(criteria_query)
        
        # Method 3: get_employee_by_email
        employee = cloudscale_repo.get_employee_by_email(email_lower)
        
        return jsonify({
            'status': 'success',
            'data': {
                'email_searched': email_lower,
                'raw_query': raw_query,
                'raw_result_success': raw_result.get('success'),
                'raw_result_count': len(raw_result.get('data', {}).get('data', [])) if raw_result.get('success') else 0,
                'raw_result_data': raw_result.get('data', {}).get('data', []) if raw_result.get('success') else None,
                'criteria_built': criteria,
                'criteria_query': criteria_query,
                'criteria_result_success': criteria_result.get('success'),
                'criteria_result_count': len(criteria_result.get('data', {}).get('data', [])) if criteria_result.get('success') else 0,
                'get_employee_by_email_result': employee is not None,
                'employee_email': employee.get('Email') if employee else None,
            }
        }), 200
        
    except Exception as e:
        logger.exception(f'Debug query error: {e}')
        return jsonify({
            'status': 'error',
            'message': 'Debug query failed',
            'error': str(e)
        }), 500