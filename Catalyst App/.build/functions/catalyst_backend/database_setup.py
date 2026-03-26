"""
Zoho Catalyst CloudScale Data Store Setup Script
Railway Ticketing System - Database Initialization

Run this in Catalyst Advanced I/O Function to create all tables.
"""

from __future__ import annotations
import zcatalyst_sdk
from typing import Dict, Any


def setup_database():
    """Create all data store tables for Railway Ticketing System."""

    catalyst_app = zcatalyst_sdk.initialize()
    datastore = catalyst_app.data_store

    tables = [
        create_users_table,
        create_stations_table,
        create_trains_table,
        create_train_routes_table,
        create_coach_layouts_table,
        create_train_inventory_table,
        create_fares_table,
        create_bookings_table,
        create_passengers_table,
        create_quotas_table,
        create_announcements_table,
        create_admin_logs_table,
        create_settings_table,
        create_password_reset_tokens_table,
    ]

    results = {}
    for table_creator in tables:
        try:
            table_name = table_creator.__name__.replace('create_', '').replace('_table', '')
            print(f"Creating table: {table_name}...")
            result = table_creator(datastore)
            results[table_name] = {'status': 'success', 'data': result}
            print(f"  ✓ {table_name} created successfully")
        except Exception as e:
            results[table_name] = {'status': 'error', 'error': str(e)}
            print(f"  ✗ {table_name} failed: {e}")

    return results


# ═════════════════════════════════════════════════════════════════════════════
#  TABLE CREATORS
# ═════════════════════════════════════════════════════════════════════════════

def create_users_table(datastore):
    """Users table - authentication & user profiles"""
    return datastore.create_table({
        'table_name': 'Users',
        'columns': [
            {'name': 'user_id', 'type': 'BIGINT', 'primary_key': True},
            {'name': 'email', 'type': 'STRING', 'unique': True, 'required': True},
            {'name': 'password_hash', 'type': 'STRING', 'required': True},
            {'name': 'full_name', 'type': 'STRING'},
            {'name': 'phone', 'type': 'STRING'},
            {'name': 'role', 'type': 'STRING', 'default': 'passenger'},  # passenger, admin, agent
            {'name': 'status', 'type': 'STRING', 'default': 'active'},  # active, inactive, suspended
            {'name': 'date_of_birth', 'type': 'DATE'},
            {'name': 'gender', 'type': 'STRING'},  # M, F, O
            {'name': 'created_at', 'type': 'DATETIME', 'default': 'NOW()'},
            {'name': 'updated_at', 'type': 'DATETIME', 'default': 'NOW()'},
            {'name': 'last_login', 'type': 'DATETIME'},
        ],
        'indexes': [
            {'columns': ['email'], 'unique': True},
            {'columns': ['role']},
            {'columns': ['status']},
        ]
    })


def create_stations_table(datastore):
    """Stations table - railway station master data"""
    return datastore.create_table({
        'table_name': 'Stations',
        'columns': [
            {'name': 'station_id', 'type': 'BIGINT', 'primary_key': True},
            {'name': 'station_code', 'type': 'STRING', 'unique': True, 'required': True},
            {'name': 'station_name', 'type': 'STRING', 'required': True},
            {'name': 'city', 'type': 'STRING'},
            {'name': 'state', 'type': 'STRING'},
            {'name': 'country', 'type': 'STRING', 'default': 'India'},
            {'name': 'latitude', 'type': 'DOUBLE'},
            {'name': 'longitude', 'type': 'DOUBLE'},
            {'name': 'timezone', 'type': 'STRING', 'default': 'Asia/Kolkata'},
            {'name': 'platform_count', 'type': 'INT', 'default': 4},
            {'name': 'is_major_station', 'type': 'BOOLEAN', 'default': False},
            {'name': 'created_at', 'type': 'DATETIME', 'default': 'NOW()'},
        ],
        'indexes': [
            {'columns': ['station_code'], 'unique': True},
            {'columns': ['city']},
            {'columns': ['state']},
        ]
    })


def create_trains_table(datastore):
    """Trains table - train master data"""
    return datastore.create_table({
        'table_name': 'Trains',
        'columns': [
            {'name': 'train_id', 'type': 'BIGINT', 'primary_key': True},
            {'name': 'train_number', 'type': 'INT', 'unique': True, 'required': True},
            {'name': 'train_name', 'type': 'STRING', 'required': True},
            {'name': 'train_type', 'type': 'STRING'},  # Express, Superfast, Local, etc.
            {'name': 'source_station_id', 'type': 'BIGINT', 'required': True},
            {'name': 'destination_station_id', 'type': 'BIGINT', 'required': True},
            {'name': 'departure_time', 'type': 'TIME', 'required': True},
            {'name': 'arrival_time', 'type': 'TIME', 'required': True},
            {'name': 'duration_minutes', 'type': 'INT'},
            {'name': 'total_coaches', 'type': 'INT', 'default': 16},
            {'name': 'status', 'type': 'STRING', 'default': 'active'},
            {'name': 'created_at', 'type': 'DATETIME', 'default': 'NOW()'},
        ],
        'indexes': [
            {'columns': ['train_number'], 'unique': True},
            {'columns': ['source_station_id', 'destination_station_id']},
            {'columns': ['status']},
        ]
    })


def create_train_routes_table(datastore):
    """Train_Routes table - train stops"""
    return datastore.create_table({
        'table_name': 'Train_Routes',
        'columns': [
            {'name': 'route_id', 'type': 'BIGINT', 'primary_key': True},
            {'name': 'train_id', 'type': 'BIGINT', 'required': True},
            {'name': 'station_id', 'type': 'BIGINT', 'required': True},
            {'name': 'sequence', 'type': 'INT', 'required': True},
            {'name': 'arrival_time', 'type': 'TIME'},
            {'name': 'departure_time', 'type': 'TIME'},
            {'name': 'halt_duration_minutes', 'type': 'INT', 'default': 5},
            {'name': 'distance_from_source_km', 'type': 'DOUBLE'},
            {'name': 'platform_number', 'type': 'INT'},
            {'name': 'created_at', 'type': 'DATETIME', 'default': 'NOW()'},
        ],
        'indexes': [
            {'columns': ['train_id', 'sequence']},
            {'columns': ['station_id']},
        ]
    })


def create_coach_layouts_table(datastore):
    """Coach_Layouts table - coach type configuration"""
    return datastore.create_table({
        'table_name': 'Coach_Layouts',
        'columns': [
            {'name': 'layout_id', 'type': 'BIGINT', 'primary_key': True},
            {'name': 'car_type_code', 'type': 'STRING', 'unique': True, 'required': True},
            {'name': 'car_type_name', 'type': 'STRING', 'required': True},
            {'name': 'total_berths', 'type': 'INT', 'required': True},
            {'name': 'layout_pattern', 'type': 'JSON'},
            {'name': 'seat_configuration', 'type': 'JSON'},
            {'name': 'amenities', 'type': 'JSON'},
            {'name': 'is_active', 'type': 'BOOLEAN', 'default': True},
            {'name': 'created_at', 'type': 'DATETIME', 'default': 'NOW()'},
        ],
        'indexes': [
            {'columns': ['car_type_code'], 'unique': True},
        ]
    })


def create_train_inventory_table(datastore):
    """Train_Inventory table - coaches per train"""
    return datastore.create_table({
        'table_name': 'Train_Inventory',
        'columns': [
            {'name': 'inventory_id', 'type': 'BIGINT', 'primary_key': True},
            {'name': 'train_id', 'type': 'BIGINT', 'required': True},
            {'name': 'coach_type_code', 'type': 'STRING', 'required': True},
            {'name': 'coach_count', 'type': 'INT', 'required': True},
            {'name': 'total_capacity', 'type': 'INT', 'required': True},
            {'name': 'sequence_start', 'type': 'INT'},
            {'name': 'sequence_end', 'type': 'INT'},
            {'name': 'created_at', 'type': 'DATETIME', 'default': 'NOW()'},
        ],
        'indexes': [
            {'columns': ['train_id', 'coach_type_code']},
        ]
    })


def create_fares_table(datastore):
    """Fares table - fare rules"""
    return datastore.create_table({
        'table_name': 'Fares',
        'columns': [
            {'name': 'fare_id', 'type': 'BIGINT', 'primary_key': True},
            {'name': 'train_id', 'type': 'BIGINT', 'required': True},
            {'name': 'source_station_id', 'type': 'BIGINT', 'required': True},
            {'name': 'destination_station_id', 'type': 'BIGINT', 'required': True},
            {'name': 'class_code', 'type': 'STRING', 'required': True},
            {'name': 'base_fare', 'type': 'DECIMAL(10,2)', 'required': True},
            {'name': 'reservation_charge', 'type': 'DECIMAL(10,2)', 'default': 0},
            {'name': 'gst_percentage', 'type': 'DECIMAL(5,2)', 'default': 5.00},
            {'name': 'total_fare', 'type': 'DECIMAL(10,2)'},
            {'name': 'effective_from', 'type': 'DATE'},
            {'name': 'effective_to', 'type': 'DATE'},
            {'name': 'created_at', 'type': 'DATETIME', 'default': 'NOW()'},
        ],
        'indexes': [
            {'columns': ['train_id', 'source_station_id', 'destination_station_id', 'class_code']},
        ]
    })


def create_bookings_table(datastore):
    """Bookings table - main booking records"""
    return datastore.create_table({
        'table_name': 'Bookings',
        'columns': [
            {'name': 'booking_id', 'type': 'BIGINT', 'primary_key': True},
            {'name': 'pnr_number', 'type': 'STRING', 'unique': True, 'required': True},
            {'name': 'user_id', 'type': 'BIGINT', 'required': True},
            {'name': 'train_id', 'type': 'BIGINT', 'required': True},
            {'name': 'journey_date', 'type': 'DATE', 'required': True},
            {'name': 'source_station_id', 'type': 'BIGINT', 'required': True},
            {'name': 'destination_station_id', 'type': 'BIGINT', 'required': True},
            {'name': 'class_code', 'type': 'STRING', 'required': True},
            {'name': 'quota_type', 'type': 'STRING', 'default': 'General'},
            {'name': 'passenger_count', 'type': 'INT', 'required': True},
            {'name': 'total_fare', 'type': 'DECIMAL(10,2)', 'required': True},
            {'name': 'payment_status', 'type': 'STRING', 'default': 'pending'},
            {'name': 'booking_status', 'type': 'STRING', 'default': 'confirmed'},
            {'name': 'posted_status', 'type': 'STRING', 'default': 'reserved'},
            {'name': 'booking_date', 'type': 'DATETIME', 'default': 'NOW()'},
            {'name': 'confirmation_date', 'type': 'DATETIME'},
            {'name': 'cancelled_date', 'type': 'DATETIME'},
            {'name': 'cancellation_charge', 'type': 'DECIMAL(10,2)', 'default': 0},
            {'name': 'refund_amount', 'type': 'DECIMAL(10,2)', 'default': 0},
            {'name': 'created_at', 'type': 'DATETIME', 'default': 'NOW()'},
        ],
        'indexes': [
            {'columns': ['pnr_number'], 'unique': True},
            {'columns': ['user_id', 'booking_date']},
            {'columns': ['train_id', 'journey_date']},
            {'columns': ['booking_status']},
            {'columns': ['payment_status']},
        ]
    })


def create_passengers_table(datastore):
    """Passengers table - passenger details per booking"""
    return datastore.create_table({
        'table_name': 'Passengers',
        'columns': [
            {'name': 'passenger_id', 'type': 'BIGINT', 'primary_key': True},
            {'name': 'booking_id', 'type': 'BIGINT', 'required': True},
            {'name': 'first_name', 'type': 'STRING', 'required': True},
            {'name': 'last_name', 'type': 'STRING'},
            {'name': 'age', 'type': 'INT', 'required': True},
            {'name': 'gender', 'type': 'STRING', 'required': True},
            {'name': 'concession_type', 'type': 'STRING', 'default': 'None'},
            {'name': 'coach_number', 'type': 'INT'},
            {'name': 'berth_number', 'type': 'STRING'},
            {'name': 'berth_type', 'type': 'STRING'},
            {'name': 'status', 'type': 'STRING', 'default': 'confirmed'},
            {'name': 'document_type', 'type': 'STRING'},
            {'name': 'document_number', 'type': 'STRING'},
            {'name': 'ticket_number', 'type': 'STRING', 'unique': True},
            {'name': 'created_at', 'type': 'DATETIME', 'default': 'NOW()'},
        ],
        'indexes': [
            {'columns': ['booking_id']},
            {'columns': ['ticket_number'], 'unique': True},
            {'columns': ['status']},
        ]
    })


def create_quotas_table(datastore):
    """Quotas table - seat quota allocation"""
    return datastore.create_table({
        'table_name': 'Quotas',
        'columns': [
            {'name': 'quota_id', 'type': 'BIGINT', 'primary_key': True},
            {'name': 'train_id', 'type': 'BIGINT', 'required': True},
            {'name': 'class_code', 'type': 'STRING', 'required': True},
            {'name': 'quota_type', 'type': 'STRING', 'required': True},
            {'name': 'percentage', 'type': 'DECIMAL(5,2)', 'required': True},
            {'name': 'actual_capacity', 'type': 'INT'},
            {'name': 'available_seats', 'type': 'INT'},
            {'name': 'booked_seats', 'type': 'INT', 'default': 0},
            {'name': 'created_at', 'type': 'DATETIME', 'default': 'NOW()'},
        ],
        'indexes': [
            {'columns': ['train_id', 'class_code', 'quota_type']},
        ]
    })


def create_announcements_table(datastore):
    """Announcements table - train alerts and updates"""
    return datastore.create_table({
        'table_name': 'Announcements',
        'columns': [
            {'name': 'announcement_id', 'type': 'BIGINT', 'primary_key': True},
            {'name': 'train_id', 'type': 'BIGINT'},
            {'name': 'title', 'type': 'STRING', 'required': True},
            {'name': 'content', 'type': 'TEXT', 'required': True},
            {'name': 'announcement_type', 'type': 'STRING', 'required': True},
            {'name': 'severity', 'type': 'STRING', 'default': 'info'},
            {'name': 'effective_from', 'type': 'DATETIME', 'required': True},
            {'name': 'effective_to', 'type': 'DATETIME'},
            {'name': 'created_by', 'type': 'BIGINT'},
            {'name': 'created_at', 'type': 'DATETIME', 'default': 'NOW()'},
        ],
        'indexes': [
            {'columns': ['train_id']},
            {'columns': ['announcement_type']},
        ]
    })


def create_admin_logs_table(datastore):
    """Admin_Logs table - audit trail"""
    return datastore.create_table({
        'table_name': 'Admin_Logs',
        'columns': [
            {'name': 'log_id', 'type': 'BIGINT', 'primary_key': True},
            {'name': 'admin_id', 'type': 'BIGINT', 'required': True},
            {'name': 'action', 'type': 'STRING', 'required': True},
            {'name': 'entity_type', 'type': 'STRING', 'required': True},
            {'name': 'entity_id', 'type': 'BIGINT'},
            {'name': 'old_value', 'type': 'JSON'},
            {'name': 'new_value', 'type': 'JSON'},
            {'name': 'ip_address', 'type': 'STRING'},
            {'name': 'user_agent', 'type': 'STRING'},
            {'name': 'status', 'type': 'STRING', 'default': 'success'},
            {'name': 'created_at', 'type': 'DATETIME', 'default': 'NOW()'},
        ],
        'indexes': [
            {'columns': ['admin_id', 'created_at']},
            {'columns': ['entity_type', 'entity_id']},
        ]
    })


def create_settings_table(datastore):
    """Settings table - system configuration"""
    return datastore.create_table({
        'table_name': 'Settings',
        'columns': [
            {'name': 'setting_id', 'type': 'BIGINT', 'primary_key': True},
            {'name': 'key', 'type': 'STRING', 'unique': True, 'required': True},
            {'name': 'value', 'type': 'TEXT'},
            {'name': 'setting_type', 'type': 'STRING', 'default': 'string'},
            {'name': 'description', 'type': 'STRING'},
            {'name': 'is_system', 'type': 'BOOLEAN', 'default': False},
            {'name': 'updated_by', 'type': 'BIGINT'},
            {'name': 'updated_at', 'type': 'DATETIME', 'default': 'NOW()'},
        ],
        'indexes': [
            {'columns': ['key'], 'unique': True},
        ]
    })


def create_password_reset_tokens_table(datastore):
    """Password_Reset_Tokens table - password reset links"""
    return datastore.create_table({
        'table_name': 'Password_Reset_Tokens',
        'columns': [
            {'name': 'token_id', 'type': 'BIGINT', 'primary_key': True},
            {'name': 'user_id', 'type': 'BIGINT', 'required': True},
            {'name': 'token', 'type': 'STRING', 'unique': True, 'required': True},
            {'name': 'expires_at', 'type': 'DATETIME', 'required': True},
            {'name': 'used', 'type': 'BOOLEAN', 'default': False},
            {'name': 'created_at', 'type': 'DATETIME', 'default': 'NOW()'},
        ],
        'indexes': [
            {'columns': ['token'], 'unique': True},
            {'columns': ['user_id', 'expires_at']},
        ]
    })


if __name__ == '__main__':
    print("Railway Ticketing System - Catalyst CloudScale Database Setup\n")
    results = setup_database()

    print("\n" + "=" * 70)
    print("SETUP RESULTS")
    print("=" * 70)

    success_count = sum(1 for r in results.values() if r['status'] == 'success')
    error_count = sum(1 for r in results.values() if r['status'] == 'error')

    for table, result in results.items():
        status = "✓" if result['status'] == 'success' else "✗"
        print(f"{status} {table}: {result['status']}")
        if result['status'] == 'error':
            print(f"   Error: {result['error']}")

    print("\n" + "=" * 70)
    print(f"Total: {success_count} success, {error_count} errors")
    print("=" * 70)
