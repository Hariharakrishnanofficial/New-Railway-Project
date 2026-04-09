"""
Email OTP Service - Smart Railway Ticketing System

Handles OTP generation and email verification using Zoho Catalyst Email Service.

Features:
  - Generate secure 6-digit OTP
  - Send OTP via Zoho Catalyst Email
  - Verify OTP with expiration (15 minutes)
  - Rate limiting on OTP requests
"""

import os
import secrets
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Tuple

try:
    import zcatalyst_sdk
    CATALYST_AVAILABLE = True
except ImportError:
    CATALYST_AVAILABLE = False

from config import TABLES
from repositories.cloudscale_repository import cloudscale_repo

logger = logging.getLogger(__name__)

# Configuration
OTP_LENGTH = 6
OTP_EXPIRY_MINUTES = int(os.getenv('OTP_EXPIRY_MINUTES', '15'))
OTP_MAX_ATTEMPTS = int(os.getenv('OTP_MAX_ATTEMPTS', '3'))
OTP_RESEND_COOLDOWN_SECONDS = int(os.getenv('OTP_RESEND_COOLDOWN_SECONDS', '60'))
OTP_MAX_RESEND_ATTEMPTS = int(os.getenv('OTP_MAX_RESEND_ATTEMPTS', '3'))  # Max times user can resend OTP

# Email configuration
FROM_EMAIL = os.getenv('CATALYST_FROM_EMAIL', 'noreply@smartrailway.com')
APP_NAME = os.getenv('APP_NAME', 'Smart Railway')

# In-memory store for tracking resend attempts per email+purpose
# Format: {f"{email}:{purpose}": {"count": int, "first_request_at": datetime}}
_resend_attempt_tracker = {}


def _parse_db_datetime(value: Optional[str]) -> Optional[datetime]:
    """Parse DB datetime strings into timezone-aware UTC datetimes.

    Supports both:
    - "YYYY-MM-DD HH:MM:SS" (stored by this service)
    - ISO8601 strings (optionally with trailing 'Z')
    """
    if not value:
        return None

    s = str(value).strip()
    if not s:
        return None

    try:
        dt = datetime.fromisoformat(s.replace('Z', '+00:00'))
    except Exception:
        return None

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    return dt.astimezone(timezone.utc)


def generate_otp() -> str:
    """
    Generate a cryptographically secure 6-digit OTP.
    
    Returns:
        6-digit OTP string (e.g., "123456")
    """
    # Use secrets for cryptographic security
    otp = ''.join(str(secrets.randbelow(10)) for _ in range(OTP_LENGTH))
    return otp


def create_otp_record(email: str, otp: str, purpose: str = 'registration') -> Dict:
    """
    Store OTP in database for verification.
    
    Args:
        email: User's email address
        otp: Generated OTP
        purpose: 'registration' | 'password_reset' | 'email_change'
    
    Returns:
        Result dict with success status
    """
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(minutes=OTP_EXPIRY_MINUTES)
    
    # Format dates for Catalyst compatibility
    created_at_str = now.strftime('%Y-%m-%d %H:%M:%S')
    expires_at_str = expires_at.strftime('%Y-%m-%d %H:%M:%S')
    
    otp_data = {
        'User_Email': email.lower().strip(),
        'OTP': otp,
        'Purpose': purpose,
        'Expires_At': expires_at_str,
        'Is_Used': 'false',  # String boolean for Catalyst
        'Attempts': '0',   # String to match DB format
        'Created_At': created_at_str,
    }
    
    try:
        # Delete any existing unused OTPs for this email and purpose
        _cleanup_old_otps(email, purpose)
        
        # Create new OTP record
        result = cloudscale_repo.create_record(TABLES.get('otp_tokens', 'OTP_Tokens'), otp_data)
        
        if result.get('success'):
            logger.info(f"OTP created for {email} (purpose: {purpose})")
            return {'success': True, 'rowid': result.get('data', {}).get('ROWID')}
        else:
            logger.error(f"Failed to create OTP: {result.get('error')}")
            return {'success': False, 'error': result.get('error')}
            
    except Exception as e:
        logger.exception(f"Error creating OTP record: {e}")
        return {'success': False, 'error': str(e)}


def _cleanup_old_otps(email: str, purpose: str) -> None:
    """Remove old unused OTPs for this email."""
    try:
        email_safe = email.replace("'", "''")
        query = f"""
            SELECT ROWID FROM {TABLES.get('otp_tokens', 'OTP_Tokens')} 
            WHERE User_Email = '{email_safe}' 
            AND Purpose = '{purpose}' 
            AND Is_Used = 'false'
        """
        result = cloudscale_repo.execute_query(query)
        
        if result.get('success'):
            rows = result.get('data', {}).get('data', [])
            for row in rows:
                rowid = row.get('ROWID')
                if rowid:
                    cloudscale_repo.delete_record(
                        TABLES.get('otp_tokens', 'OTP_Tokens'), 
                        str(rowid)
                    )
    except Exception as e:
        logger.warning(f"Failed to cleanup old OTPs: {e}")


def verify_otp(email: str, otp: str, purpose: str = 'registration') -> Tuple[bool, str]:
    """
    Verify OTP against stored value.
    
    Args:
        email: User's email address
        otp: OTP entered by user
        purpose: Purpose of OTP
    
    Returns:
        Tuple of (success: bool, message: str)
    """
    email_safe = email.lower().strip().replace("'", "''")
    
    try:
        # Find the OTP record
        query = f"""
            SELECT ROWID, OTP, Expires_At, Is_Used, Attempts
            FROM {TABLES.get('otp_tokens', 'OTP_Tokens')}
            WHERE User_Email = '{email_safe}'
            AND Purpose = '{purpose}'
            AND Is_Used = 'false'
            ORDER BY Created_At DESC
            LIMIT 1
        """
        
        result = cloudscale_repo.execute_query(query)
        
        if not result.get('success'):
            return False, "Failed to verify OTP"
        
        rows = result.get('data', {}).get('data', [])
        if not rows:
            return False, "No valid OTP found. Please request a new one."
        
        record = rows[0]
        stored_otp = record.get('OTP')
        expires_at_str = record.get('Expires_At')
        # Attempts is stored as string in DB
        attempts = int(record.get('Attempts', '0') or '0')
        rowid = record.get('ROWID')
        
        # Check if expired
        expires_at = _parse_db_datetime(expires_at_str)
        if expires_at and datetime.now(timezone.utc) > expires_at:
            return False, "OTP has expired. Please request a new one."
        
        # Check max attempts
        if attempts >= OTP_MAX_ATTEMPTS:
            return False, "Maximum verification attempts exceeded. Please request a new OTP."
        
        # Increment attempts (store as string to match DB format)
        cloudscale_repo.update_record(
            TABLES.get('otp_tokens', 'OTP_Tokens'),
            str(rowid),
            {'Attempts': str(attempts + 1)}
        )
        
        # Verify OTP (constant-time comparison)
        if not secrets.compare_digest(otp.strip(), stored_otp):
            remaining = OTP_MAX_ATTEMPTS - attempts - 1
            return False, f"Invalid OTP. {remaining} attempts remaining."
        
        # Mark as used
        cloudscale_repo.update_record(
            TABLES.get('otp_tokens', 'OTP_Tokens'),
            str(rowid),
            {'Is_Used': 'true'}
        )
        
        # Reset resend tracker on successful verification
        _reset_resend_tracker(email, purpose)
        
        logger.info(f"OTP verified successfully for {email}")
        return True, "OTP verified successfully"
        
    except Exception as e:
        logger.exception(f"Error verifying OTP: {e}")
        return False, "OTP verification failed"


def send_otp_email(email: str, otp: str, purpose: str = 'registration') -> Dict:
    """
    Send OTP via Zoho Catalyst Email Service.
    
    Args:
        email: Recipient email address
        otp: The OTP to send
        purpose: Purpose for email template selection
    
    Returns:
        Result dict with success status
    """
    if not CATALYST_AVAILABLE:
        logger.warning("Catalyst SDK not available, simulating email send")
        # In development, log the OTP for testing
        logger.info(f"[DEV] OTP for {email}: {otp}")
        return {'success': True, 'simulated': True}
    
    try:
        # Initialize Catalyst SDK
        app = zcatalyst_sdk.initialize()
        mail_service = app.email()
        
        # Build email content based on purpose
        if purpose == 'registration':
            subject = f'{APP_NAME} - Verify Your Email'
            content = _build_registration_email(otp)
        elif purpose == 'password_reset':
            subject = f'{APP_NAME} - Password Reset OTP'
            content = _build_password_reset_email(otp)
        else:
            subject = f'{APP_NAME} - Verification Code'
            content = _build_generic_otp_email(otp)
        
        # Build email object for Zoho Catalyst
        # SDK supports: from_email, to_email, subject, content, html_mode (bool)
        mail_obj = {
            'from_email': FROM_EMAIL,
            'to_email': [email],
            'subject': subject,
            'content': content,
            'html_mode': True,  # Enable HTML rendering
        }
        
        # Send the email
        logger.info(f"Sending OTP email to {email} from {FROM_EMAIL}")
        response = mail_service.send_mail(mail_obj)
        logger.info(f"OTP email sent to {email}, response: {response}")
        return {'success': True}
        
    except Exception as e:
        # Log detailed error info
        error_msg = str(e)
        if hasattr(e, 'response'):
            try:
                error_msg = f"{e}: {e.response.json()}"
            except:
                error_msg = f"{e}: {e.response.text if hasattr(e.response, 'text') else 'no response text'}"
        logger.error(f"Failed to send OTP email: {error_msg}")
        return {'success': False, 'error': error_msg}


def _build_registration_email(otp: str) -> str:
    """Build HTML email for registration OTP."""
    return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background-color: #f5f5f5; margin: 0; padding: 20px;">
    <div style="max-width: 500px; margin: 0 auto; background: white; border-radius: 12px; padding: 40px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
        <div style="text-align: center; margin-bottom: 30px;">
            <h1 style="color: #1a1a2e; margin: 0; font-size: 24px;">🚂 {APP_NAME}</h1>
        </div>
        
        <h2 style="color: #333; margin: 0 0 10px;">Verify Your Email</h2>
        <p style="color: #666; margin: 0 0 30px; line-height: 1.6;">
            Welcome to {APP_NAME}! Use the verification code below to complete your registration.
        </p>
        
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 12px; padding: 30px; text-align: center; margin-bottom: 30px;">
            <p style="color: rgba(255,255,255,0.8); margin: 0 0 10px; font-size: 14px; text-transform: uppercase; letter-spacing: 2px;">
                Your Verification Code
            </p>
            <div style="font-size: 36px; font-weight: bold; color: white; letter-spacing: 8px; font-family: monospace;">
                {otp}
            </div>
        </div>
        
        <p style="color: #666; font-size: 14px; margin: 0 0 10px;">
            ⏱️ This code expires in <strong>{OTP_EXPIRY_MINUTES} minutes</strong>.
        </p>
        <p style="color: #999; font-size: 13px; margin: 0;">
            If you didn't request this code, you can safely ignore this email.
        </p>
        
        <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
        
        <p style="color: #999; font-size: 12px; text-align: center; margin: 0;">
            © 2026 {APP_NAME}. All rights reserved.
        </p>
    </div>
</body>
</html>"""


def _build_password_reset_email(otp: str) -> str:
    """Build HTML email for password reset OTP."""
    return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background-color: #f5f5f5; margin: 0; padding: 20px;">
    <div style="max-width: 500px; margin: 0 auto; background: white; border-radius: 12px; padding: 40px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
        <div style="text-align: center; margin-bottom: 30px;">
            <h1 style="color: #1a1a2e; margin: 0; font-size: 24px;">🚂 {APP_NAME}</h1>
        </div>
        
        <h2 style="color: #333; margin: 0 0 10px;">Reset Your Password</h2>
        <p style="color: #666; margin: 0 0 30px; line-height: 1.6;">
            We received a request to reset your password. Use the code below to proceed.
        </p>
        
        <div style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); border-radius: 12px; padding: 30px; text-align: center; margin-bottom: 30px;">
            <p style="color: rgba(255,255,255,0.8); margin: 0 0 10px; font-size: 14px; text-transform: uppercase; letter-spacing: 2px;">
                Password Reset Code
            </p>
            <div style="font-size: 36px; font-weight: bold; color: white; letter-spacing: 8px; font-family: monospace;">
                {otp}
            </div>
        </div>
        
        <p style="color: #666; font-size: 14px; margin: 0 0 10px;">
            ⏱️ This code expires in <strong>{OTP_EXPIRY_MINUTES} minutes</strong>.
        </p>
        <p style="color: #e74c3c; font-size: 13px; margin: 0; padding: 10px; background: #fdf2f2; border-radius: 6px;">
            ⚠️ If you didn't request a password reset, please secure your account immediately.
        </p>
        
        <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
        
        <p style="color: #999; font-size: 12px; text-align: center; margin: 0;">
            © 2026 {APP_NAME}. All rights reserved.
        </p>
    </div>
</body>
</html>"""


def _build_generic_otp_email(otp: str) -> str:
    """Build generic OTP email template."""
    return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
</head>
<body style="font-family: Arial, sans-serif; padding: 20px;">
    <div style="max-width: 400px; margin: 0 auto; text-align: center;">
        <h2>{APP_NAME}</h2>
        <p>Your verification code is:</p>
        <h1 style="font-size: 32px; letter-spacing: 5px; color: #333;">{otp}</h1>
        <p style="color: #666;">This code expires in {OTP_EXPIRY_MINUTES} minutes.</p>
    </div>
</body>
</html>"""


def _track_resend_attempt(email: str, purpose: str) -> None:
    """
    Track OTP resend attempt for rate limiting.
    
    Args:
        email: User's email address
        purpose: OTP purpose ('registration' or 'password_reset')
    """
    key = f"{email.lower().strip()}:{purpose}"
    now = datetime.now(timezone.utc)
    
    if key in _resend_attempt_tracker:
        _resend_attempt_tracker[key]['count'] += 1
        _resend_attempt_tracker[key]['last_attempt_at'] = now
    else:
        _resend_attempt_tracker[key] = {
            'count': 1,
            'first_attempt_at': now,
            'last_attempt_at': now
        }


def _check_resend_limit(email: str, purpose: str) -> Tuple[bool, int]:
    """
    Check if user has exceeded resend limit.
    
    Args:
        email: User's email address
        purpose: OTP purpose ('registration' or 'password_reset')
    
    Returns:
        Tuple of (can_resend: bool, attempts_remaining: int)
    """
    key = f"{email.lower().strip()}:{purpose}"
    
    if key not in _resend_attempt_tracker:
        return True, OTP_MAX_RESEND_ATTEMPTS
    
    tracker = _resend_attempt_tracker[key]
    first_attempt = tracker['first_attempt_at']
    count = tracker['count']
    
    # Reset counter if more than 1 hour has passed since first attempt
    elapsed_hours = (datetime.now(timezone.utc) - first_attempt).total_seconds() / 3600
    if elapsed_hours > 1:
        # Reset the tracker
        del _resend_attempt_tracker[key]
        return True, OTP_MAX_RESEND_ATTEMPTS
    
    # Check if limit exceeded
    if count >= OTP_MAX_RESEND_ATTEMPTS:
        return False, 0
    
    return True, OTP_MAX_RESEND_ATTEMPTS - count


def _reset_resend_tracker(email: str, purpose: str) -> None:
    """
    Reset resend tracker when OTP is successfully verified.
    
    Args:
        email: User's email address
        purpose: OTP purpose ('registration' or 'password_reset')
    """
    key = f"{email.lower().strip()}:{purpose}"
    if key in _resend_attempt_tracker:
        del _resend_attempt_tracker[key]


def can_resend_otp(email: str, purpose: str = 'registration') -> Tuple[bool, int]:
    """
    Check if user can request a new OTP (cooldown check).
    
    Returns:
        Tuple of (can_resend: bool, seconds_remaining: int)
    """
    email_safe = email.lower().strip().replace("'", "''")
    
    try:
        query = f"""
            SELECT Created_At
            FROM {TABLES.get('otp_tokens', 'OTP_Tokens')}
            WHERE User_Email = '{email_safe}'
            AND Purpose = '{purpose}'
            ORDER BY Created_At DESC
            LIMIT 1
        """
        
        result = cloudscale_repo.execute_query(query)
        
        if not result.get('success'):
            return True, 0
        
        rows = result.get('data', {}).get('data', [])
        if not rows:
            return True, 0
        
        created_at_str = rows[0].get('Created_At')
        if not created_at_str:
            return True, 0
        
        try:
            created_at = _parse_db_datetime(created_at_str)
            if not created_at:
                return True, 0

            elapsed = (datetime.now(timezone.utc) - created_at).total_seconds()

            if elapsed < OTP_RESEND_COOLDOWN_SECONDS:
                remaining = int(OTP_RESEND_COOLDOWN_SECONDS - elapsed)
                return False, remaining

            return True, 0
        except Exception:
            return True, 0
            
    except Exception as e:
        logger.warning(f"Error checking OTP cooldown: {e}")
        return True, 0


def send_registration_otp(email: str, is_resend: bool = False) -> Dict:
    """
    Complete flow to generate and send registration OTP.
    
    Args:
        email: User's email address
        is_resend: Whether this is a resend request (for tracking)
    
    Returns:
        Result dict with success status and message
    """
    # Check resend limit (only for resend requests)
    if is_resend:
        can_resend_limit, remaining_attempts = _check_resend_limit(email, 'registration')
        if not can_resend_limit:
            return {
                'success': False,
                'error': f'Maximum resend limit ({OTP_MAX_RESEND_ATTEMPTS}) reached. Please try again after 1 hour.',
                'limit_exceeded': True,
                'remaining_attempts': 0
            }
    
    # Check cooldown
    can_send, remaining = can_resend_otp(email, 'registration')
    if not can_send:
        return {
            'success': False,
            'error': f'Please wait {remaining} seconds before requesting another OTP',
            'cooldown': remaining
        }
    
    # Track resend attempt
    if is_resend:
        _track_resend_attempt(email, 'registration')
    
    # Generate OTP
    otp = generate_otp()
    
    # Store OTP
    store_result = create_otp_record(email, otp, 'registration')
    if not store_result.get('success'):
        error_detail = store_result.get('error', 'Unknown database error')
        logger.error(f"Failed to create OTP record for {email}: {error_detail}")
        return {'success': False, 'error': f'Failed to create verification code: {error_detail}'}
    
    # Send email
    email_result = send_otp_email(email, otp, 'registration')
    if not email_result.get('success'):
        return {'success': False, 'error': 'Failed to send verification email'}
    
    # Get remaining attempts for response
    _, remaining_attempts = _check_resend_limit(email, 'registration')
    
    return {
        'success': True,
        'message': 'Verification code sent to your email',
        'expiresInMinutes': OTP_EXPIRY_MINUTES,
        'remaining_resend_attempts': remaining_attempts - 1 if is_resend else remaining_attempts
    }


def send_password_reset_otp(email: str, is_resend: bool = False) -> Dict:
    """
    Send OTP for password reset.
    
    Args:
        email: User's email address
        is_resend: Whether this is a resend request (for tracking)
    
    Returns:
        Result dict with success status and message
    """
    # Check resend limit (only for resend requests)
    if is_resend:
        can_resend_limit, remaining_attempts = _check_resend_limit(email, 'password_reset')
        if not can_resend_limit:
            return {
                'success': False,
                'error': f'Maximum resend limit ({OTP_MAX_RESEND_ATTEMPTS}) reached. Please try again after 1 hour.',
                'limit_exceeded': True,
                'remaining_attempts': 0
            }
    
    # Check cooldown
    can_send, remaining = can_resend_otp(email, 'password_reset')
    if not can_send:
        return {
            'success': False,
            'error': f'Please wait {remaining} seconds before requesting another code',
            'cooldown': remaining
        }
    
    # Track resend attempt
    if is_resend:
        _track_resend_attempt(email, 'password_reset')
    
    # Generate OTP
    otp = generate_otp()
    
    # Store OTP
    store_result = create_otp_record(email, otp, 'password_reset')
    if not store_result.get('success'):
        error_detail = store_result.get('error', 'Unknown database error')
        logger.error(f"Failed to create password reset OTP for {email}: {error_detail}")
        return {'success': False, 'error': 'Failed to create verification code'}
    
    # Send email
    email_result = send_otp_email(email, otp, 'password_reset')
    if not email_result.get('success'):
        return {'success': False, 'error': 'Failed to send verification email'}
    
    # Get remaining attempts for response
    _, remaining_attempts = _check_resend_limit(email, 'password_reset')
    
    return {
        'success': True,
        'message': 'Password reset code sent to your email',
        'expiresInMinutes': OTP_EXPIRY_MINUTES,
        'remaining_resend_attempts': remaining_attempts - 1 if is_resend else remaining_attempts
    }


def verify_password_reset_otp(email: str, otp: str) -> Tuple[bool, str]:
    """
    Verify OTP for password reset.
    
    Args:
        email: User's email address
        otp: OTP code to verify
    
    Returns:
        Tuple of (success, message)
    """
    result = verify_otp(email, otp, 'password_reset')
    
    # Reset resend tracker on successful verification
    if result[0]:  # If verification successful
        _reset_resend_tracker(email, 'password_reset')
    
    return result


def resend_password_reset_otp(email: str) -> Dict:
    """
    Resend password reset OTP.
    
    Args:
        email: User's email address
    
    Returns:
        Result dict with success status
    """
    return send_password_reset_otp(email, is_resend=True)
