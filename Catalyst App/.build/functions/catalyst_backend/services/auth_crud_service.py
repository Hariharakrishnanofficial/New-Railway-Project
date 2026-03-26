"""
Enhanced Auth Service — Registration & SignIn with full CRUD operations
Implements: Create (Register), Read (SignIn/Profile), Update (Profile), Delete (Account)
"""

import logging
from datetime import datetime
from config import TABLES, ADMIN_EMAIL, ADMIN_DOMAIN
from repositories.cloudscale_repository import zoho_repo, CriteriaBuilder
from core.security import hash_password, verify_password, generate_access_token, generate_refresh_token
from core.exceptions import AuthenticationError, ValidationError, UserNotFoundError, RailwayException

logger = logging.getLogger(__name__)


class AuthCRUDService:
    """Complete CRUD operations for authentication"""

    def __init__(self):
        self._users_table = None

    @property
    def users_table(self):
        """Lazy load users table name"""
        if self._users_table is None:
            self._users_table = TABLES.get('users', 'Users')
        return self._users_table

    # ════════════════════════════════════════════════════════════════════════
    #  CREATE - REGISTRATION
    # ════════════════════════════════════════════════════════════════════════

    def create_user(self, data: dict) -> dict:
        """
        CREATE: Register new user
        POST /api/auth/register
        """
        try:
            # Validate required fields
            required = ["Full_Name", "Email", "Password"]
            missing = [f for f in required if not data.get(f)]
            if missing:
                raise ValidationError(f"Missing required fields: {', '.join(missing)}")

            email = (data.get("Email") or "").strip().lower()
            
            # Validate email format
            if "@" not in email:
                raise ValidationError("Invalid email format")

            # Validate password strength
            password = data.get("Password", "")
            if len(password) < 6:
                raise ValidationError("Password must be at least 6 characters")

            # Check duplicate
            criteria = CriteriaBuilder().eq("Email", email).build()
            existing = zoho_repo.get_records(self.users_table, criteria=criteria, limit=1)
            
            if existing:
                raise ValidationError("Email already registered")

            # Determine role
            is_admin = email == ADMIN_EMAIL.lower() or email.endswith("@" + ADMIN_DOMAIN)
            role = "Admin" if is_admin else "User"

            # Create user record
            payload = {
                "Full_Name": (data.get("Full_Name") or "").strip(),
                "Email": (data.get("Email") or "").strip(),
                "Password": hash_password(password),
                "Phone_Number": (data.get("Phone_Number") or "").strip(),
                "Address": (data.get("Address") or "").strip(),
                "Role": role,
                "Account_Status": "Active",
                "Created_Date": datetime.now().isoformat(),
            }

            result = zoho_repo.create_record(self.users_table, payload)
            if not result.get("success"):
                raise ValidationError(result.get("message", "Registration failed"))

            return {
                "message": "User registered successfully",
                "user_id": result.get("id"),
                "email": data.get("Email"),
                "role": role,
            }
        except ValidationError:
            raise
        except RailwayException:
            raise
        except Exception as e:
            logger.exception(f"Create user error: {e}")
            raise ValidationError("Registration failed")

    # ════════════════════════════════════════════════════════════════════════
    #  READ - SIGNIN / GET PROFILE
    # ════════════════════════════════════════════════════════════════════════

    def read_user_by_email(self, email: str) -> dict:
        """
        READ: Get user by email (for signin)
        """
        if not email:
            raise ValidationError("Email is required")

        email = email.strip().lower()
        
        criteria = CriteriaBuilder().eq("Email", email).build()
        records = zoho_repo.get_records(self.users_table, criteria=criteria, limit=1)

        if not records:
            raise UserNotFoundError(f"No user found with email: {email}")

        user = records[0]
        
        # Remove sensitive data
        user.pop("Password", None)
        
        return {
            "success": True,
            "user": user,
        }

    def signin(self, email: str, password: str) -> dict:
        """
        READ + AUTH: SignIn with credentials
        POST /api/auth/signin
        Returns: access_token, refresh_token, user data
        """
        if not email or not password:
            raise ValidationError("Email and password are required")

        email = email.strip().lower()

        try:
            # Get user
            criteria = CriteriaBuilder().eq("Email", email).build()
            records = zoho_repo.get_records(self.users_table, criteria=criteria, limit=1)

            if not records:
                raise AuthenticationError("Invalid email or password")

            user = records[0]

            # Verify password
            if not verify_password(password, user.get("Password", "")):
                raise AuthenticationError("Invalid email or password")

            # Check account status
            if user.get("Account_Status") != "Active":
                raise AuthenticationError("Account is not active")

            # Generate tokens
            user_id = user.get("RECORDID", user.get("id"))
            role = user.get("Role", "User")

            access_token = generate_access_token(user_id, email, role)
            refresh_token = generate_refresh_token(user_id, email)

            # Update last login
            update_payload = {"Last_Login": datetime.now().isoformat()}
            zoho_repo.update_record(self.users_table, user_id, update_payload)

            # Prepare response (remove sensitive fields)
            user_data = {
                "id": user_id,
                "email": user.get("Email"),
                "full_name": user.get("Full_Name"),
                "phone_number": user.get("Phone_Number"),
                "role": role,
                "account_status": user.get("Account_Status"),
            }

            return {
                "success": True,
                "message": "Signin successful",
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "Bearer",
                "expires_in": 3600,
                "user": user_data,
            }
        except (AuthenticationError, RailwayException) as e:
            raise
        except Exception as e:
            logger.exception(f"CloudScale signin failed: {e}")
            raise AuthenticationError("SignIn failed")

    def get_user_profile(self, user_id: str) -> dict:
        """
        READ: Get user profile
        GET /api/auth/profile/:user_id
        """
        if not user_id:
            raise ValidationError("User ID is required")

        try:
            user = zoho_repo.get_record(self.users_table, user_id)

            if not user:
                raise UserNotFoundError(f"User not found: {user_id}")

            # Remove sensitive fields
            user.pop("Password", None)

            return {
                "success": True,
                "user": user,
            }
        except RailwayException:
            raise
        except Exception as e:
            logger.exception(f"Get profile failed: {e}")
            raise ValidationError("Failed to retrieve profile")

    # ════════════════════════════════════════════════════════════════════════
    #  UPDATE - PROFILE UPDATE / CHANGE PASSWORD
    # ════════════════════════════════════════════════════════════════════════

    def update_profile(self, user_id: str, data: dict) -> dict:
        """
        UPDATE: Update user profile
        PUT /api/auth/profile/:user_id
        """
        if not user_id:
            raise ValidationError("User ID is required")

        try:
            # Get existing user
            user = zoho_repo.get_record(self.users_table, user_id)
            if not user:
                raise UserNotFoundError(f"User not found: {user_id}")

            # Prepare update payload (only allowed fields)
            update_payload = {}
            
            if "Full_Name" in data:
                update_payload["Full_Name"] = data["Full_Name"].strip()
            
            if "Phone_Number" in data:
                update_payload["Phone_Number"] = data["Phone_Number"].strip()
            
            if "Address" in data:
                update_payload["Address"] = data["Address"].strip()

            if not update_payload:
                raise ValidationError("No fields to update")

            update_payload["Updated_Date"] = datetime.now().isoformat()

            result = zoho_repo.update_record(self.users_table, user_id, update_payload)

            if not result.get("success"):
                raise ValidationError(result.get("message", "Update failed"))

            return {
                "success": True,
                "message": "Profile updated successfully",
                "user_id": user_id,
            }
        except RailwayException:
            raise
        except Exception as e:
            logger.exception(f"Update profile failed: {e}")
            raise ValidationError("Failed to update profile")

    def change_password(self, user_id: str, old_password: str, new_password: str) -> dict:
        """
        UPDATE: Change password
        POST /api/auth/change-password
        """
        if not user_id or not old_password or not new_password:
            raise ValidationError("User ID, old password, and new password are required")

        try:
            # Get user
            user = zoho_repo.get_record(self.users_table, user_id)
            if not user:
                raise UserNotFoundError(f"User not found: {user_id}")

            # Verify old password
            if not verify_password(old_password, user.get("Password", "")):
                raise AuthenticationError("Old password is incorrect")

            # Validate new password
            if len(new_password) < 6:
                raise ValidationError("New password must be at least 6 characters")

            if old_password == new_password:
                raise ValidationError("New password must be different from old password")

            # Update password
            update_payload = {
                "Password": hash_password(new_password),
                "Updated_Date": datetime.now().isoformat(),
            }

            result = zoho_repo.update_record(self.users_table, user_id, update_payload)

            if not result.get("success"):
                raise ValidationError(result.get("message", "Password change failed"))

            return {
                "success": True,
                "message": "Password changed successfully",
            }
        except RailwayException:
            raise
        except Exception as e:
            logger.exception(f"Change password failed: {e}")
            raise ValidationError("Failed to change password")

    # ════════════════════════════════════════════════════════════════════════
    #  DELETE - ACCOUNT DELETION
    # ════════════════════════════════════════════════════════════════════════

    def delete_account(self, user_id: str, password: str) -> dict:
        """
        DELETE: Delete user account
        POST /api/auth/delete-account
        Requires password confirmation
        """
        if not user_id or not password:
            raise ValidationError("User ID and password are required")

        try:
            # Get user
            user = zoho_repo.get_record(self.users_table, user_id)
            if not user:
                raise UserNotFoundError(f"User not found: {user_id}")

            # Verify password
            if not verify_password(password, user.get("Password", "")):
                raise AuthenticationError("Password is incorrect")

            # Delete user
            result = zoho_repo.delete_record(self.users_table, user_id)

            if not result.get("success"):
                raise ValidationError(result.get("message", "Account deletion failed"))

            return {
                "success": True,
                "message": "Account deleted successfully",
            }
        except RailwayException:
            raise
        except Exception as e:
            logger.exception(f"Delete account failed: {e}")
            raise ValidationError("Failed to delete account")

    def deactivate_account(self, user_id: str, password: str) -> dict:
        """
        SOFT DELETE: Deactivate account (don't permanently delete)
        POST /api/auth/deactivate-account
        """
        if not user_id or not password:
            raise ValidationError("User ID and password are required")

        try:
            # Get user
            user = zoho_repo.get_record(self.users_table, user_id)
            if not user:
                raise UserNotFoundError(f"User not found: {user_id}")

            # Verify password
            if not verify_password(password, user.get("Password", "")):
                raise AuthenticationError("Password is incorrect")

            # Deactivate
            update_payload = {
                "Account_Status": "Inactive",
                "Deactivated_Date": datetime.now().isoformat(),
            }

            result = zoho_repo.update_record(self.users_table, user_id, update_payload)

            if not result.get("success"):
                raise ValidationError(result.get("message", "Deactivation failed"))

            return {
                "success": True,
                "message": "Account deactivated successfully",
            }
        except RailwayException:
            raise
        except Exception as e:
            logger.exception(f"Deactivate account failed: {e}")
            raise ValidationError("Failed to deactivate account")


# Singleton instance
auth_crud_service = AuthCRUDService()
