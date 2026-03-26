"""
Configuration module for Railway Ticketing System.
All secrets loaded from environment variables. NO hardcoded credentials.

NOTE: This system uses Zoho Catalyst CloudScale database (ZCQL).
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ══════════════════════════════════════════════════════════════════
#  CLOUDSCALE TABLE CONFIGURATION (Zoho Catalyst CloudScale)
# ══════════════════════════════════════════════════════════════════

# CloudScale table names - unified for all CRUD operations
TABLES = {
    'users':           'Users',
    'stations':        'Stations',
    'trains':          'Trains',
    'train_routes':    'Train_Routes',
    'route_stops':     'Route_Stops',
    'coach_layouts':   'Coach_Layouts',
    'train_inventory': 'Train_Inventory',
    'fares':           'Fares',
    'quotas':          'Quotas',
    'bookings':        'Bookings',
    'passengers':      'Passengers',
    'announcements':   'Announcements',
    'admin_logs':      'Admin_Logs',
    'settings':        'Settings',
    'reset_tokens':    'Password_Reset_Tokens',
}


def get_tables():
    """Get CloudScale table configuration."""
    return TABLES


def get_table(key: str) -> str:
    """Get a specific CloudScale table name."""
    return TABLES.get(key, key)


def get_form_config():
    """
    Backward compatibility function.
    Returns a dict with 'forms' and 'reports' both pointing to the same TABLES.
    This maintains compatibility with code that expects the old Zoho Creator structure.
    """
    return {
        'forms': TABLES,
        'reports': TABLES,
    }


# ══════════════════════════════════════════════════════════════════
#  AI KEYS  (all from environment — NEVER hardcode)
# ══════════════════════════════════════════════════════════════════

def get_ai_config():
    return {
        'gemini_api_key': os.getenv('GEMINI_API_KEY', ''),
        'gemini_model':   os.getenv('GEMINI_MODEL', 'gemini-2.0-flash'),
    }


# ══════════════════════════════════════════════════════════════════
#  SEAT ALLOCATION CONSTANTS
# ══════════════════════════════════════════════════════════════════

SEAT_CLASS_MAP = {
    'SL': 'Available_Seats_SL', '2S': 'Available_Seats_SL',
    '3A': 'Available_Seats_3A', '3AC': 'Available_Seats_3A',
    '2A': 'Available_Seats_2A', '2AC': 'Available_Seats_2A',
    '1A': 'Available_Seats_1A', '1AC': 'Available_Seats_1A',
    'CC': 'Available_Seats_CC', 'EC':  'Available_Seats_CC',
    'FC': 'Available_Seats_1A',
}

BERTH_CYCLE = {
    'SL': ['Lower', 'Middle', 'Upper', 'Side Lower', 'Side Upper'],
    '3A': ['Lower', 'Middle', 'Upper', 'Side Lower', 'Side Upper'],
    '2A': ['Lower', 'Upper', 'Side Lower', 'Side Upper'],
    '1A': ['Lower', 'Upper'],
    'CC': ['Window', 'Aisle', 'Middle'],
    'EC': ['Window', 'Aisle'],
    'FC': ['Lower', 'Upper'],
}

COACH_PREFIX = {
    'SL': 'S', '2S': 'S',
    '3A': 'B', '3AC': 'B',
    '2A': 'A', '2AC': 'A',
    '1A': 'H', '1AC': 'H',
    'CC': 'C', 'EC':  'EC',
    'FC': 'FC',
}

COACH_CAPACITY = {
    'SL': 72, '2S': 100,
    '3A': 64, '3AC': 64,
    '2A': 46, '2AC': 46,
    '1A': 18, '1AC': 18,
    'CC': 78, 'EC':  56,
    'FC': 18,
}

# ══════════════════════════════════════════════════════════════════
#  AUTH CONSTANTS
# ══════════════════════════════════════════════════════════════════

ADMIN_EMAIL  = os.getenv('ADMIN_EMAIL',  'admin@admin.com')
ADMIN_DOMAIN = os.getenv('ADMIN_DOMAIN', 'admin.com')

# ══════════════════════════════════════════════════════════════════
#  CANCELLATION POLICY
# ══════════════════════════════════════════════════════════════════

CANCEL_MIN_DEDUCTION = {
    '1A': 240, '1AC': 240,
    '2A': 200, '2AC': 200,
    '3A': 180, '3AC': 180,
    'CC': 90,  'EC':  90,
    'FC': 240,
    'SL': 60,  '2S':  60,
}

BOOKING_ADVANCE_DAYS = 120
TATKAL_OPEN_HOUR     = 10
AC_CLASSES           = {'1A', '1AC', '2A', '2AC', '3A', '3AC', 'CC', 'EC', 'FC'}
NON_AC_CLASSES       = {'SL', '2S'}
