"""
Configuration Module - Smart Railway Ticketing System

All secrets loaded from environment variables. NO hardcoded credentials.
Uses Zoho Catalyst CloudScale database (ZCQL).
"""

import os

# ══════════════════════════════════════════════════════════════════════════════
#  CLOUDSCALE TABLE CONFIGURATION (Zoho Catalyst CloudScale)
# ══════════════════════════════════════════════════════════════════════════════

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
    'module_master':   'Module_Master',
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
    """
    return {
        'forms': TABLES,
        'reports': TABLES,
    }


# ══════════════════════════════════════════════════════════════════════════════
#  AI CONFIGURATION
# ══════════════════════════════════════════════════════════════════════════════

def get_ai_config():
    """Get AI service configuration from environment."""
    return {
        'gemini_api_key': os.getenv('GEMINI_API_KEY', ''),
        'gemini_model': os.getenv('GEMINI_MODEL', 'gemini-2.0-flash'),
    }


# ══════════════════════════════════════════════════════════════════════════════
#  AUTH CONSTANTS
# ══════════════════════════════════════════════════════════════════════════════

ADMIN_EMAIL = os.getenv('ADMIN_EMAIL', 'admin@railway.com')
ADMIN_DOMAIN = os.getenv('ADMIN_DOMAIN', 'catalyst-cs2.onslate.in')


# ══════════════════════════════════════════════════════════════════════════════
#  SEAT ALLOCATION CONSTANTS
# ══════════════════════════════════════════════════════════════════════════════

# Map class codes to inventory field names
SEAT_CLASS_MAP = {
    'SL':  'Available_Seats_SL',
    '2S':  'Available_Seats_SL',
    '3A':  'Available_Seats_3A',
    '3AC': 'Available_Seats_3A',
    '2A':  'Available_Seats_2A',
    '2AC': 'Available_Seats_2A',
    '1A':  'Available_Seats_1A',
    '1AC': 'Available_Seats_1A',
    'CC':  'Available_Seats_CC',
    'EC':  'Available_Seats_CC',
    'FC':  'Available_Seats_1A',
}

# Berth allocation cycle per class
BERTH_CYCLE = {
    'SL': ['Lower', 'Middle', 'Upper', 'Side Lower', 'Side Upper'],
    '3A': ['Lower', 'Middle', 'Upper', 'Side Lower', 'Side Upper'],
    '2A': ['Lower', 'Upper', 'Side Lower', 'Side Upper'],
    '1A': ['Lower', 'Upper'],
    'CC': ['Window', 'Aisle', 'Middle'],
    'EC': ['Window', 'Aisle'],
    'FC': ['Lower', 'Upper'],
}

# Coach naming prefixes
COACH_PREFIX = {
    'SL':  'S',
    '2S':  'S',
    '3A':  'B',
    '3AC': 'B',
    '2A':  'A',
    '2AC': 'A',
    '1A':  'H',
    '1AC': 'H',
    'CC':  'C',
    'EC':  'EC',
    'FC':  'FC',
}

# Seats per coach by class
COACH_CAPACITY = {
    'SL':  72,
    '2S':  100,
    '3A':  64,
    '3AC': 64,
    '2A':  46,
    '2AC': 46,
    '1A':  18,
    '1AC': 18,
    'CC':  78,
    'EC':  56,
    'FC':  18,
}


# ══════════════════════════════════════════════════════════════════════════════
#  FARE CALCULATION CONSTANTS (IRCTC-style)
# ══════════════════════════════════════════════════════════════════════════════

# Base fare per km by class
BASE_FARE_PER_KM = {
    '1A':  4.50,
    '1AC': 4.50,
    '2A':  2.70,
    '2AC': 2.70,
    '3A':  1.70,
    '3AC': 1.70,
    'CC':  1.25,
    'EC':  1.80,
    'SL':  0.60,
    '2S':  0.40,
    'FC':  4.50,
}

# Reservation charges by class
RESERVATION_CHARGE = {
    '1A':  60,
    '1AC': 60,
    '2A':  50,
    '2AC': 50,
    '3A':  40,
    '3AC': 40,
    'CC':  40,
    'EC':  40,
    'SL':  20,
    '2S':  15,
    'FC':  60,
}

# Superfast surcharge by class
SUPERFAST_SURCHARGE = {
    '1A':  75,
    '1AC': 75,
    '2A':  55,
    '2AC': 55,
    '3A':  45,
    '3AC': 45,
    'CC':  45,
    'EC':  45,
    'SL':  30,
    '2S':  15,
    'FC':  75,
}

# Tatkal charges
TATKAL_PREMIUM_PERCENT = 30  # 30% of base fare
TATKAL_MIN_CHARGE = {
    '1A':  400,
    '1AC': 400,
    '2A':  400,
    '2AC': 400,
    '3A':  300,
    '3AC': 300,
    'CC':  125,
    'EC':  125,
    'SL':  100,
    '2S':  75,
    'FC':  400,
}
TATKAL_MAX_CHARGE = {
    '1A':  500,
    '1AC': 500,
    '2A':  500,
    '2AC': 500,
    '3A':  400,
    '3AC': 400,
    'CC':  225,
    'EC':  225,
    'SL':  200,
    '2S':  125,
    'FC':  500,
}

# GST rate (5% for AC classes only)
GST_RATE = 0.05

# AC classes (subject to GST)
AC_CLASSES = {'1A', '1AC', '2A', '2AC', '3A', '3AC', 'CC', 'EC', 'FC'}
NON_AC_CLASSES = {'SL', '2S'}

# Concession rates
CONCESSION_RATES = {
    'senior_male':   0.40,  # 40% discount for male seniors (60+)
    'senior_female': 0.50,  # 50% discount for female seniors (58+)
    'student':       0.50,  # 50% discount for students
    'disabled':      0.50,  # 50% discount for disabled
    'child':         0.50,  # 50% discount for children (5-12)
}


# ══════════════════════════════════════════════════════════════════════════════
#  CANCELLATION POLICY
# ══════════════════════════════════════════════════════════════════════════════

# Minimum cancellation deduction by class
CANCEL_MIN_DEDUCTION = {
    '1A':  240,
    '1AC': 240,
    '2A':  200,
    '2AC': 200,
    '3A':  180,
    '3AC': 180,
    'CC':  90,
    'EC':  90,
    'SL':  60,
    '2S':  60,
    'FC':  240,
}

# Cancellation charges based on time before departure
CANCEL_CHARGES = {
    # Hours before departure: % of fare to deduct
    'more_than_48h': 0.10,   # 10%
    '48h_to_24h':    0.25,   # 25%
    '24h_to_12h':    0.50,   # 50%
    'less_than_12h': 0.75,   # 75%
    'after_departure': 1.00,  # No refund
}


# ══════════════════════════════════════════════════════════════════════════════
#  BOOKING RULES
# ══════════════════════════════════════════════════════════════════════════════

BOOKING_ADVANCE_DAYS = 120  # Can book up to 120 days in advance
TATKAL_OPEN_HOUR = 10       # Tatkal booking opens at 10 AM
MONTHLY_BOOKING_LIMIT_UNVERIFIED = 6   # Max bookings for unverified users
MONTHLY_BOOKING_LIMIT_VERIFIED = 12    # Max bookings for verified users

# Maximum passengers per booking
MAX_PASSENGERS_PER_BOOKING = 6

# RAC and Waitlist limits
RAC_LIMIT_PER_COACH = 8
WAITLIST_LIMIT_PER_TRAIN = 100


# ══════════════════════════════════════════════════════════════════════════════
#  TRAIN TYPES & CATEGORIES
# ══════════════════════════════════════════════════════════════════════════════

TRAIN_TYPES = [
    'Superfast',
    'Mail/Express',
    'Rajdhani',
    'Shatabdi',
    'Duronto',
    'Garib Rath',
    'Jan Shatabdi',
    'Vande Bharat',
    'Tejas',
    'Passenger',
    'Local',
]

# Superfast train types (qualified for superfast surcharge)
SUPERFAST_TRAIN_TYPES = {
    'Superfast',
    'Rajdhani',
    'Shatabdi',
    'Duronto',
    'Vande Bharat',
    'Tejas',
}


# ══════════════════════════════════════════════════════════════════════════════
#  QUOTA TYPES
# ══════════════════════════════════════════════════════════════════════════════

QUOTA_TYPES = {
    'GN':    'General Quota',
    'TK':    'Tatkal Quota',
    'PT':    'Premium Tatkal',
    'LD':    'Ladies Quota',
    'HP':    'Handicapped Quota',
    'DF':    'Defence Quota',
    'FT':    'Foreign Tourist Quota',
    'SS':    'Senior Citizen Quota',
    'YU':    'Youth Quota',
    'DU':    'Duty Pass Quota',
    'RC':    'Remote Location Quota',
}


# ══════════════════════════════════════════════════════════════════════════════
#  CORS & SECURITY
# ══════════════════════════════════════════════════════════════════════════════

DEFAULT_ALLOWED_ORIGINS = [
    'https://smart-railway-app.onslate.in',
    'https://railway-ticketing-app.onslate.in',
    'http://localhost:3000',
    'http://localhost:3001',
    'http://localhost:5173',
    'http://127.0.0.1:3000',
    'http://127.0.0.1:3001',
    'http://127.0.0.1:5173',
]

# Request size limits
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB
