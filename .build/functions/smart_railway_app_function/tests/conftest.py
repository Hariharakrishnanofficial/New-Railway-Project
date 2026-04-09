"""
Test Configuration and Fixtures

Common test utilities and mock data generators.
"""

import random
import string
from datetime import datetime, timedelta


class MockDataGenerator:
    """Generate mock data for testing."""

    @staticmethod
    def random_string(length: int = 10) -> str:
        """Generate random alphanumeric string."""
        return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

    @staticmethod
    def random_email() -> str:
        """Generate random email address."""
        username = MockDataGenerator.random_string(8).lower()
        domains = ['gmail.com', 'yahoo.com', 'outlook.com', 'test.com']
        return f"{username}@{random.choice(domains)}"

    @staticmethod
    def random_phone() -> str:
        """Generate random Indian phone number."""
        return f"9{random.randint(100000000, 999999999)}"

    @staticmethod
    def random_pnr() -> str:
        """Generate random PNR."""
        letters = ''.join(random.choices(string.ascii_uppercase, k=4))
        digits = ''.join(random.choices(string.digits, k=6))
        return f"{letters}{digits}"

    @staticmethod
    def random_date(days_ahead: int = 30) -> str:
        """Generate random future date."""
        offset = random.randint(1, days_ahead)
        date = datetime.now() + timedelta(days=offset)
        return date.strftime('%Y-%m-%d')

    @staticmethod
    def mock_user() -> dict:
        """Generate mock user data."""
        return {
            'User_Name': f"Test User {MockDataGenerator.random_string(4)}",
            'Email': MockDataGenerator.random_email(),
            'Phone': MockDataGenerator.random_phone(),
            'Password': 'TestPassword123!',
            'Role': random.choice(['passenger', 'admin', 'operator']),
            'Is_Active': True,
        }

    @staticmethod
    def mock_train() -> dict:
        """Generate mock train data."""
        train_types = ['Express', 'Superfast', 'Rajdhani', 'Shatabdi', 'Local']
        return {
            'Train_Number': str(random.randint(10000, 99999)),
            'Train_Name': f"{random.choice(train_types)} {MockDataGenerator.random_string(5)}",
            'Train_Type': random.choice(train_types),
            'Total_Seats': random.randint(500, 1500),
            'Is_Active': True,
        }

    @staticmethod
    def mock_station() -> dict:
        """Generate mock station data."""
        return {
            'Station_Code': MockDataGenerator.random_string(4).upper(),
            'Station_Name': f"Test Station {MockDataGenerator.random_string(5)}",
            'City': f"City {MockDataGenerator.random_string(4)}",
            'State': 'Test State',
            'Zone': random.choice(['NR', 'SR', 'ER', 'WR', 'CR']),
            'Is_Active': True,
        }

    @staticmethod
    def mock_booking(user_id: str, train_id: str) -> dict:
        """Generate mock booking data."""
        return {
            'User_ID': user_id,
            'Train_ID': train_id,
            'PNR': MockDataGenerator.random_pnr(),
            'Journey_Date': MockDataGenerator.random_date(),
            'Class': random.choice(['SL', '3A', '2A', '1A', 'CC', 'EC']),
            'Passengers': random.randint(1, 6),
            'Status': 'Confirmed',
            'Total_Fare': round(random.uniform(500, 5000), 2),
        }
