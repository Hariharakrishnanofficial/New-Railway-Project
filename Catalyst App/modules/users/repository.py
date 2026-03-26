"""
User Repository - CloudScale Data Access Layer
===============================================
Handles all database operations for the Users table.
Uses ZCQL (Zoho Catalyst Query Language) for queries.
"""

from __future__ import annotations
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# =============================================================================
# CLOUDSCALE DATABASE CONNECTION
# =============================================================================

class CloudScaleConnection:
    """
    CloudScale database connection wrapper.
    Provides ZCQL query execution and table operations.
    """

    _instance = None
    _app = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._app is None:
            try:
                from zcatalyst_sdk import CatalystApp
                self._app = CatalystApp()
                logger.info("CloudScale connection initialized")
            except ImportError:
                logger.warning("zcatalyst_sdk not available - using mock mode")
                self._app = None

    @property
    def zcql(self):
        """Get ZCQL service."""
        if self._app:
            return self._app.zcql()
        return None

    @property
    def datastore(self):
        """Get Datastore service."""
        if self._app:
            return self._app.datastore()
        return None

    def execute_query(self, query: str) -> List[Dict]:
        """Execute ZCQL SELECT query."""
        try:
            if self.zcql:
                result = self.zcql.execute_query(query)
                return result if result else []
            logger.warning(f"Mock query: {query}")
            return []
        except Exception as e:
            logger.error(f"Query failed: {query} | Error: {e}")
            raise

    def get_table(self, table_name: str):
        """Get table reference."""
        if self.datastore:
            return self.datastore.table(table_name)
        return None


# Global connection instance
db = CloudScaleConnection()


# =============================================================================
# USER REPOSITORY
# =============================================================================

class UserRepository:
    """
    Repository for User data access operations.
    All CloudScale interactions for the Users table.
    """

    TABLE_NAME = "Users"

    def __init__(self):
        self.db = db

    # -------------------------------------------------------------------------
    # CREATE OPERATIONS
    # -------------------------------------------------------------------------

    def create(self, user_data: Dict[str, Any]) -> Dict:
        """
        Create a new user record.

        Args:
            user_data: Dictionary containing user fields

        Returns:
            Created user record with ROWID
        """
        try:
            table = self.db.get_table(self.TABLE_NAME)
            if table:
                # Add timestamps
                user_data['Created_At'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                user_data['Updated_At'] = user_data['Created_At']

                result = table.insert_row(user_data)
                logger.info(f"User created: {user_data.get('Email')}")
                return result
            else:
                # Mock mode for testing
                user_data['ROWID'] = 1
                return user_data

        except Exception as e:
            logger.error(f"Failed to create user: {e}")
            raise

    # -------------------------------------------------------------------------
    # READ OPERATIONS
    # -------------------------------------------------------------------------

    def get_by_id(self, user_id: int) -> Optional[Dict]:
        """Get user by ROWID."""
        query = f"SELECT * FROM {self.TABLE_NAME} WHERE ROWID = {user_id}"
        results = self.db.execute_query(query)
        return results[0] if results else None

    def get_by_email(self, email: str) -> Optional[Dict]:
        """Get user by email address."""
        # Escape single quotes in email
        safe_email = email.replace("'", "''").lower().strip()
        query = f"SELECT * FROM {self.TABLE_NAME} WHERE Email = '{safe_email}'"
        results = self.db.execute_query(query)
        return results[0] if results else None

    def get_by_phone(self, phone: str) -> Optional[Dict]:
        """Get user by phone number."""
        # Normalize phone - keep only digits
        phone_digits = ''.join(filter(str.isdigit, phone))
        query = f"SELECT * FROM {self.TABLE_NAME} WHERE Phone LIKE '%{phone_digits}%'"
        results = self.db.execute_query(query)
        return results[0] if results else None

    def get_by_session_token(self, token: str) -> Optional[Dict]:
        """Get user by active session token."""
        safe_token = token.replace("'", "''")
        query = f"""
            SELECT * FROM {self.TABLE_NAME}
            WHERE Session_Token = '{safe_token}'
            AND Token_Expires_At > '{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}'
        """
        results = self.db.execute_query(query)
        return results[0] if results else None

    def get_by_refresh_token(self, token: str) -> Optional[Dict]:
        """Get user by refresh token."""
        safe_token = token.replace("'", "''")
        query = f"""
            SELECT * FROM {self.TABLE_NAME}
            WHERE Refresh_Token = '{safe_token}'
            AND Refresh_Expires_At > '{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}'
        """
        results = self.db.execute_query(query)
        return results[0] if results else None

    def get_by_reset_token(self, token: str) -> Optional[Dict]:
        """Get user by password reset token."""
        safe_token = token.replace("'", "''")
        query = f"""
            SELECT * FROM {self.TABLE_NAME}
            WHERE Reset_Token = '{safe_token}'
            AND Reset_Token_Expires > '{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}'
        """
        results = self.db.execute_query(query)
        return results[0] if results else None

    def get_all(self, limit: int = 100, offset: int = 0) -> List[Dict]:
        """Get all users with pagination."""
        query = f"""
            SELECT * FROM {self.TABLE_NAME}
            ORDER BY Created_At DESC
            LIMIT {limit} OFFSET {offset}
        """
        return self.db.execute_query(query)

    def search(self, search_term: str, limit: int = 50) -> List[Dict]:
        """Search users by email, name, or phone."""
        safe_term = search_term.replace("'", "''")
        query = f"""
            SELECT * FROM {self.TABLE_NAME}
            WHERE Email LIKE '%{safe_term}%'
               OR Full_Name LIKE '%{safe_term}%'
               OR Phone LIKE '%{safe_term}%'
            LIMIT {limit}
        """
        return self.db.execute_query(query)

    def get_by_role(self, role: str) -> List[Dict]:
        """Get all users with a specific role."""
        query = f"SELECT * FROM {self.TABLE_NAME} WHERE Role = '{role}'"
        return self.db.execute_query(query)

    def count(self, criteria: str = None) -> int:
        """Count users with optional criteria."""
        query = f"SELECT COUNT(ROWID) as count FROM {self.TABLE_NAME}"
        if criteria:
            query += f" WHERE {criteria}"
        results = self.db.execute_query(query)
        return int(results[0].get('count', 0)) if results else 0

    def email_exists(self, email: str) -> bool:
        """Check if email already exists."""
        user = self.get_by_email(email)
        return user is not None

    def phone_exists(self, phone: str) -> bool:
        """Check if phone number already exists."""
        user = self.get_by_phone(phone)
        return user is not None

    # -------------------------------------------------------------------------
    # UPDATE OPERATIONS
    # -------------------------------------------------------------------------

    def update(self, user_id: int, data: Dict[str, Any]) -> Dict:
        """
        Update user record by ROWID.

        Args:
            user_id: User's ROWID
            data: Fields to update

        Returns:
            Updated user record
        """
        try:
            table = self.db.get_table(self.TABLE_NAME)
            if table:
                data['ROWID'] = user_id
                data['Updated_At'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                result = table.update_row(data)
                logger.info(f"User {user_id} updated")
                return result
            else:
                return data

        except Exception as e:
            logger.error(f"Failed to update user {user_id}: {e}")
            raise

    def update_password(self, user_id: int, password_hash: str) -> bool:
        """Update user's password hash."""
        return self.update(user_id, {
            'Password_Hash': password_hash,
            'Reset_Token': None,
            'Reset_Token_Expires': None,
            'Failed_Login_Count': 0,
            'Locked_Until': None,
        })

    def update_session_token(
        self,
        user_id: int,
        session_token: str,
        refresh_token: str,
        token_expires_at: datetime,
        refresh_expires_at: datetime,
        ip_address: str = None
    ) -> bool:
        """Update user's session tokens after login."""
        return self.update(user_id, {
            'Session_Token': session_token,
            'Token_Expires_At': token_expires_at.strftime('%Y-%m-%d %H:%M:%S'),
            'Refresh_Token': refresh_token,
            'Refresh_Expires_At': refresh_expires_at.strftime('%Y-%m-%d %H:%M:%S'),
            'Last_Login_At': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'Last_Login_IP': ip_address,
            'Failed_Login_Count': 0,
            'Locked_Until': None,
        })

    def clear_session_token(self, user_id: int) -> bool:
        """Clear user's session tokens (logout)."""
        return self.update(user_id, {
            'Session_Token': None,
            'Token_Expires_At': None,
            'Refresh_Token': None,
            'Refresh_Expires_At': None,
        })

    def set_reset_token(self, user_id: int, token: str, expires_at: datetime) -> bool:
        """Set password reset token."""
        return self.update(user_id, {
            'Reset_Token': token,
            'Reset_Token_Expires': expires_at.strftime('%Y-%m-%d %H:%M:%S'),
        })

    def clear_reset_token(self, user_id: int) -> bool:
        """Clear password reset token."""
        return self.update(user_id, {
            'Reset_Token': None,
            'Reset_Token_Expires': None,
        })

    def increment_failed_login(self, user_id: int, current_count: int) -> bool:
        """Increment failed login count."""
        from modules.users.models import LOCKOUT_SETTINGS

        new_count = current_count + 1
        data = {'Failed_Login_Count': new_count}

        # Lock account if max attempts reached
        if new_count >= LOCKOUT_SETTINGS['max_failed_attempts']:
            lockout_until = datetime.now() + timedelta(
                minutes=LOCKOUT_SETTINGS['lockout_duration_minutes']
            )
            data['Locked_Until'] = lockout_until.strftime('%Y-%m-%d %H:%M:%S')
            logger.warning(f"User {user_id} locked until {lockout_until}")

        return self.update(user_id, data)

    def reset_failed_login(self, user_id: int) -> bool:
        """Reset failed login count."""
        return self.update(user_id, {
            'Failed_Login_Count': 0,
            'Locked_Until': None,
        })

    def update_booking_count(self, user_id: int, count: int, reset_date: str = None) -> bool:
        """Update monthly booking count."""
        data = {'Monthly_Booking_Count': count}
        if reset_date:
            data['Booking_Count_Reset_At'] = reset_date
        return self.update(user_id, data)

    def verify_email(self, user_id: int) -> bool:
        """Mark email as verified."""
        return self.update(user_id, {'Is_Email_Verified': True})

    def verify_phone(self, user_id: int) -> bool:
        """Mark phone as verified."""
        return self.update(user_id, {'Is_Phone_Verified': True})

    def verify_aadhar(self, user_id: int, aadhar_number: str) -> bool:
        """Mark Aadhar as verified."""
        return self.update(user_id, {
            'Is_Aadhar_Verified': True,
            'Aadhar_Number': aadhar_number,
        })

    def update_status(self, user_id: int, status: str) -> bool:
        """Update user account status."""
        return self.update(user_id, {'Status': status})

    def update_role(self, user_id: int, role: str) -> bool:
        """Update user role."""
        return self.update(user_id, {'Role': role})

    # -------------------------------------------------------------------------
    # DELETE OPERATIONS
    # -------------------------------------------------------------------------

    def delete(self, user_id: int) -> bool:
        """Delete user by ROWID (hard delete)."""
        try:
            table = self.db.get_table(self.TABLE_NAME)
            if table:
                table.delete_row(user_id)
                logger.info(f"User {user_id} deleted")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to delete user {user_id}: {e}")
            raise

    def soft_delete(self, user_id: int) -> bool:
        """Soft delete user by setting status to inactive."""
        return self.update_status(user_id, 'inactive')

    # -------------------------------------------------------------------------
    # BOOKING LIMIT OPERATIONS
    # -------------------------------------------------------------------------

    def get_monthly_booking_count(self, user_id: int) -> int:
        """Get user's monthly booking count, resetting if new month."""
        user = self.get_by_id(user_id)
        if not user:
            return 0

        reset_date = user.get('Booking_Count_Reset_At')
        current_month = datetime.now().strftime('%Y-%m')

        # Check if we need to reset (new month)
        if reset_date:
            reset_month = reset_date[:7] if len(reset_date) >= 7 else None
            if reset_month != current_month:
                # Reset count for new month
                self.update_booking_count(
                    user_id,
                    count=0,
                    reset_date=datetime.now().strftime('%Y-%m-%d')
                )
                return 0

        return int(user.get('Monthly_Booking_Count', 0) or 0)

    def increment_booking_count(self, user_id: int) -> int:
        """Increment user's monthly booking count."""
        current_count = self.get_monthly_booking_count(user_id)
        new_count = current_count + 1
        self.update_booking_count(
            user_id,
            count=new_count,
            reset_date=datetime.now().strftime('%Y-%m-%d')
        )
        return new_count

    def can_book(self, user_id: int) -> tuple[bool, int, int]:
        """
        Check if user can make a booking.

        Returns:
            Tuple of (can_book, current_count, max_limit)
        """
        from modules.users.models import BOOKING_LIMITS

        user = self.get_by_id(user_id)
        if not user:
            return False, 0, 0

        is_verified = user.get('Is_Aadhar_Verified', False)
        max_limit = BOOKING_LIMITS['verified'] if is_verified else BOOKING_LIMITS['unverified']
        current_count = self.get_monthly_booking_count(user_id)

        return current_count < max_limit, current_count, max_limit


# =============================================================================
# SINGLETON INSTANCE
# =============================================================================

user_repo = UserRepository()
