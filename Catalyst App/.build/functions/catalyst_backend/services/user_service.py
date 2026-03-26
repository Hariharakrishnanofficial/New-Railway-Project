"""
User Service — authentication and user management logic.
Uses CloudScale (ZCQL) for all database operations.
"""

import logging
from datetime import datetime

from config import TABLES, ADMIN_EMAIL, ADMIN_DOMAIN
from repositories.cloudscale_repository import zoho_repo, CriteriaBuilder
from core.security import hash_password, verify_password, needs_rehash, generate_access_token, generate_refresh_token
from core.exceptions import AuthenticationError, UserNotFoundError, ValidationError
from utils.validators import validate_required

logger = logging.getLogger(__name__)


def is_admin_email(email: str) -> bool:
    e = (email or "").strip().lower()
    return e == ADMIN_EMAIL or e.endswith("@" + ADMIN_DOMAIN)


def resolve_role(user: dict) -> str:
    email = (user.get("Email") or "").strip().lower()
    if is_admin_email(email):
        return "Admin"
    role = (user.get("Role") or "").strip()
    return role if role in ("Admin", "User") else "User"


class UserService:
    """User authentication and management service using CloudScale."""

    def __init__(self):
        self.tables = TABLES

    # ════════════════════════════════════════════════════════════════════════
    #  REGISTRATION
    # ════════════════════════════════════════════════════════════════════════

    def register(self, data: dict) -> dict:
        is_valid, missing = validate_required(data, ["Full_Name", "Email", "Password"])
        if not is_valid:
            raise ValidationError(f"Missing fields: {', '.join(missing)}")

        email = (data.get("Email") or "").strip().lower()

        # Check duplicate (criteria-based first, then fallback)
        criteria = CriteriaBuilder().eq("Email", data["Email"]).build()
        existing = zoho_repo.get_records(TABLES['users'], criteria=criteria, limit=1)

        if not existing:
            all_users = zoho_repo.get_records(TABLES['users'], limit=500)
            existing  = [u for u in all_users if (u.get("Email") or "").lower() == email]

        if existing:
            raise ValidationError("Email already registered")

        assigned_role = "Admin" if is_admin_email(email) else "User"
        payload = {
            "Full_Name":      data.get("Full_Name"),
            "Email":          data.get("Email"),
            "Phone_Number":   data.get("Phone_Number", ""),
            "Address":        data.get("Address", ""),
            "Password":       hash_password(data.get("Password")),  # bcrypt
            "Role":           assigned_role,
            "Account_Status": "Active",
            # Note: CloudScale auto-generates CREATEDTIME, no need for Registered_Date
        }

        result = zoho_repo.create_record(TABLES['users'], payload)
        if not result.get("success"):
            error_msg = result.get("message") or result.get("error") or "Registration failed"
            raise ValidationError(error_msg)

        return {"message": "Registration successful"}

    # ════════════════════════════════════════════════════════════════════════
    #  LOGIN
    # ════════════════════════════════════════════════════════════════════════

    def login(self, email: str, password: str) -> dict:
        """
        Authenticate user and return JWT tokens + user data.
        Handles password migration from SHA-256 to bcrypt transparently.
        """
        if not email: raise ValidationError("Email is required")
        if not password: raise ValidationError("Password is required")

        # Fetch user
        criteria = CriteriaBuilder().eq("Email", email).build()
        records  = zoho_repo.get_records(TABLES['users'], criteria=criteria, limit=1)

        if not records:
            # Case-insensitive fallback
            all_users = zoho_repo.get_records(TABLES['users'], limit=500)
            records   = [u for u in all_users if (u.get("Email") or "").lower() == email.lower()]

        if not records:
            raise AuthenticationError("No account found with this email")

        user        = records[0]
        stored_hash = user.get("Password", "")

        if not verify_password(password, stored_hash):
            raise AuthenticationError("Invalid email or password")

        account_status = (user.get("Account_Status") or "Active").strip()
        if account_status in ("Blocked", "Suspended"):
            raise AuthenticationError(f"Account is {account_status.lower()}. Contact support.")

        canonical_role = resolve_role(user)
        user_id        = user.get("ROWID") or user.get("ID", "")

        # Migrate password from SHA-256 to bcrypt on successful login
        if needs_rehash(stored_hash):
            try:
                zoho_repo.update_record(
                    TABLES['users'],
                    user_id,
                    {"Password": hash_password(password)}
                )
                zoho_repo.invalidate_user_cache(user_id)
                logger.info(f"Password migrated to bcrypt for {email}")
            except Exception as exc:
                logger.warning(f"Password migration failed for {email}: {exc}")

        # Update last login (non-critical)
        try:
            zoho_repo.update_record(
                TABLES['users'],
                user_id,
                {"Last_Login": datetime.now().strftime("%d-%b-%Y %H:%M:%S")}
            )
        except Exception:
            pass

        # Generate JWT tokens
        access_token  = generate_access_token(user_id, user.get("Email", email), canonical_role)
        refresh_token = generate_refresh_token(user_id, user.get("Email", email))

        return {
            "access_token":  access_token,
            "refresh_token": refresh_token,
            "token_type":    "Bearer",
            "expires_in":    3600,
            "user": {
                "ID":           user_id,
                "Full_Name":    user.get("Full_Name"),
                "Email":        user.get("Email"),
                "Phone_Number": user.get("Phone_Number"),
                "Address":      user.get("Address"),
                "Role":         canonical_role,
            },
        }

    # ════════════════════════════════════════════════════════════════════════
    #  CHANGE PASSWORD
    # ════════════════════════════════════════════════════════════════════════

    def change_password(self, user_id: str, old_password: str, new_password: str) -> None:
        if not all([user_id, old_password, new_password]):
            raise ValidationError("user_id, old_password, and new_password are required")
        if len(new_password) < 6:
            raise ValidationError("New password must be at least 6 characters")

        user = zoho_repo.get_user_cached(user_id)
        if not user:
            raise UserNotFoundError(user_id)

        if not verify_password(old_password, user.get("Password", "")):
            raise AuthenticationError("Current password is incorrect")

        zoho_repo.update_record(
            TABLES['users'],
            user_id,
            {"Password": hash_password(new_password)}
        )
        zoho_repo.invalidate_user_cache(user_id)


# Singleton
user_service = UserService()
