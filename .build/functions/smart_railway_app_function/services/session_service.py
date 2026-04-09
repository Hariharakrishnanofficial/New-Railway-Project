"""
Session Management Service - Smart Railway Ticketing System

Implements server-side session management using Zoho Catalyst CloudScale.

Features:
  - Cryptographically secure session ID generation
  - Session CRUD operations with CloudScale storage
  - Concurrent session limiting (max 3 per user)
  - Session validation with sliding window timeout
  - CSRF token management
  - Device fingerprinting support
  - Audit logging for security events
"""

from __future__ import annotations

import os
import secrets
import hashlib
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List, Tuple

from config import (
    TABLES,
    SESSION_TIMEOUT_HOURS,
    SESSION_IDLE_TIMEOUT_HOURS,
    MAX_CONCURRENT_SESSIONS,
    SESSION_SECRET,
    CSRF_TOKEN_LENGTH,
)
from repositories.cloudscale_repository import cloudscale_repo, CriteriaBuilder
from core.cookie_signer import sign_cookie, unsign_cookie

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════════════════════
#  SESSION ID GENERATION
# ══════════════════════════════════════════════════════════════════════════════

def generate_session_id() -> str:
    """
    Generate a cryptographically secure session ID.
    
    Since the Sessions table has Session_ID as BIGINT, we generate a 
    large random integer that fits within BIGINT range.
    BIGINT range: -9223372036854775808 to 9223372036854775807
    We use positive values only for simplicity.
    
    Returns a string representation of a large random integer (18-19 digits).
    """
    # Generate a random integer in safe BIGINT range (positive only)
    # Using 63 bits gives us values up to 9223372036854775807
    session_int = secrets.randbits(62)  # 62 bits = up to ~4.6 quintillion
    return str(session_int)


def generate_csrf_token() -> str:
    """
    Generate a CSRF token for the session.
    
    Returns a 43-character URL-safe base64 string.
    """
    return secrets.token_urlsafe(CSRF_TOKEN_LENGTH)


def hash_fingerprint(fingerprint_data: Dict[str, Any]) -> str:
    """
    Create a hash of device fingerprint data for comparison.
    
    Args:
        fingerprint_data: Dict containing user_agent, screen_resolution, timezone, etc.
    
    Returns:
        SHA-256 hash of fingerprint data (hex string)
    """
    if not fingerprint_data:
        return ""
    
    # Create a consistent string representation
    fp_string = "|".join(
        f"{k}:{v}" for k, v in sorted(fingerprint_data.items()) if v
    )
    return hashlib.sha256(fp_string.encode()).hexdigest()[:32]


# ══════════════════════════════════════════════════════════════════════════════
#  SESSION CRUD OPERATIONS
# ══════════════════════════════════════════════════════════════════════════════

def create_session(
    user_id: str,
    user_email: str,
    user_role: str,
    ip_address: str,
    user_agent: str,
    device_fingerprint: Optional[Dict[str, Any]] = None
) -> Tuple[str, str]:
    """
    Create a new session for a user.
    
    Args:
        user_id: User's ROWID from Users table
        user_email: User's email address
        user_role: User's role (User/Admin)
        ip_address: Client IP address
        user_agent: Client User-Agent header
        device_fingerprint: Optional device fingerprint data
    
    Returns:
        Tuple of (session_id, csrf_token)
    
    Side Effects:
        - Enforces concurrent session limit (removes oldest if exceeded)
        - Logs session creation to audit log
    """
    # Enforce concurrent session limit first
    _enforce_session_limit(user_id)
    
    # Generate secure tokens
    session_id = generate_session_id()
    csrf_token = generate_csrf_token()
    
    # Calculate expiry times
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(hours=SESSION_TIMEOUT_HOURS)
    
    # Hash fingerprint for storage
    fp_hash = hash_fingerprint(device_fingerprint) if device_fingerprint else ""
    
    # Prepare session record
    # User_ID is a foreign key (LOOKUP to Users table) - pass ROWID as string
    # Start with minimal required fields to avoid column name mismatches
    session_data = {
        "Session_ID": session_id,
        "User_ID": str(user_id),
        "User_Email": user_email,
        "User_Role": user_role,
        "CSRF_Token": csrf_token,
        "Expires_At": expires_at.isoformat(),
        "Is_Active": True,
    }
    
    # Add optional fields only if they have values
    if ip_address:
        session_data["IP_Address"] = ip_address
    if user_agent:
        session_data["User_Agent"] = (user_agent or "")[:500]
    if fp_hash:
        session_data["Device_Fingerprint"] = fp_hash
    
    session_data["Last_Accessed_At"] = now.isoformat()
    
    try:
        # Insert into CloudScale
        logger.info(f"Creating session for user {user_id}: {session_id[:8]}... with data keys: {list(session_data.keys())}")
        result = cloudscale_repo.create_record(TABLES['sessions'], session_data)
        
        
        if not result.get('success'):
            raise Exception(f"Failed to create session: {result.get('error')}")
        
        # Audit log
        _log_session_event(
            event_type="SESSION_CREATED",
            session_id=session_id,
            user_id=user_id,
            user_email=user_email,
            ip_address=ip_address,
            details={"user_agent": user_agent[:100] if user_agent else ""}
        )
        
        logger.info(f"Session created for user {user_id} ({user_email})")
        
        # Sign the session ID before returning to protect against tampering
        signed_session_id = sign_cookie(session_id)
        logger.debug(f"Session ID signed: {session_id[:8]}... -> {signed_session_id[:20]}...")
        
        return signed_session_id, csrf_token
        
    except Exception as exc:
        logger.error(f"Failed to create session: {exc}")
        raise


def validate_session(signed_session_id: str) -> Optional[Dict[str, Any]]:
    """
    Validate a signed session ID and return session data.
    
    Checks:
        1. Cookie signature is valid (tamper detection)
        2. Session exists
        3. Session is active
        4. Session not expired
        5. Idle timeout not exceeded
    
    Args:
        signed_session_id: The signed session ID from cookie
    
    Returns:
        Session data dict if valid, None otherwise
    
    Side Effects:
        - Updates last_accessed_at (sliding window)
        - Marks expired sessions as inactive
    """
    if not signed_session_id:
        return None
    
    # Unsign and verify the session ID
    session_id = unsign_cookie(signed_session_id)
    
    if not session_id:
        logger.warning("Invalid session cookie signature - possible tampering detected")
        return None
    
    try:
        # Query session from CloudScale - use explicit fields instead of SELECT *
        # Note: CREATEDTIME is auto-generated by Catalyst, Created_At might not exist
        # Session_ID is BIGINT so no quotes needed
        query = f"""
            SELECT ROWID, Session_ID, User_ID, User_Email, User_Role, IP_Address,
                   User_Agent, CSRF_Token, CREATEDTIME, Last_Accessed_At, Expires_At, Is_Active
            FROM {TABLES['sessions']}
            WHERE Session_ID = {session_id}
            AND Is_Active = true
        """
        result = cloudscale_repo.execute_query(query)
        
        if not result.get('success'):
            logger.debug(f"Session query failed: {result.get('error')}")
            return None
        
        data = result.get('data', {}).get('data', [])
        if not data or len(data) == 0:
            logger.debug(f"Session not found or inactive: {session_id[:8]}...")
            return None
        
        session = data[0]
        now = datetime.now(timezone.utc)
        
        # Parse timestamps
        expires_at = _parse_datetime(session.get("Expires_At"))
        last_accessed = _parse_datetime(session.get("Last_Accessed_At"))
        
        # Check hard expiry
        if expires_at and now > expires_at:
            logger.debug(f"Session expired: {session_id[:8]}...")
            _revoke_session_internal(session_id, reason="expired")
            return None
        
        # Check idle timeout
        if last_accessed:
            idle_duration = now - last_accessed
            if idle_duration > timedelta(hours=SESSION_IDLE_TIMEOUT_HOURS):
                logger.debug(f"Session idle timeout: {session_id[:8]}...")
                _revoke_session_internal(session_id, reason="idle_timeout")
                return None
        
        # Update last accessed time (sliding window)
        _update_session_activity(session_id, now)
        
        return {
            "session_id": session.get("Session_ID"),
            "user_id": session.get("User_ID"),
            "user_email": session.get("User_Email"),
            "user_role": session.get("User_Role"),
            "csrf_token": session.get("CSRF_Token"),
            "ip_address": session.get("IP_Address"),
            "created_at": session.get("CREATEDTIME"),  # Use Catalyst's auto field
            "last_accessed_at": now.isoformat(),
        }
        
    except Exception as exc:
        logger.error(f"Session validation error: {exc}")
        return None


def revoke_session(session_id: str, user_id: Optional[str] = None) -> bool:
    """
    Revoke (invalidate) a specific session.
    
    Args:
        session_id: The session ID to revoke
        user_id: Optional user ID for ownership verification
    
    Returns:
        True if session was revoked, False otherwise
    """
    return _revoke_session_internal(session_id, user_id=user_id, reason="user_logout")


def _revoke_session_internal(
    session_id: str,
    user_id: Optional[str] = None,
    reason: str = "revoked"
) -> bool:
    """Internal session revocation with audit logging."""
    try:
        # First get session info for audit
        # Session_ID is BIGINT, no quotes needed
        criteria_parts = [f"Session_ID = {session_id}"]
        if user_id:
            criteria_parts.append(f"User_ID = '{_escape_zcql(str(user_id))}'")
        criteria = " AND ".join(criteria_parts)
        
        query = f"""
            SELECT ROWID, User_ID, User_Email, IP_Address FROM {TABLES['sessions']}
            WHERE {criteria}
        """
        result = cloudscale_repo.execute_query(query)
        
        if not result.get('success'):
            return False
        
        data = result.get('data', {}).get('data', [])
        if not data:
            return False
        
        session = data[0]
        row_id = session.get("ROWID")
        
        if not row_id:
            return False
        
        # Update session as inactive
        update_data = {
            "Is_Active": False,
            "Revoked_At": datetime.now(timezone.utc).isoformat(),
            "Revoke_Reason": reason,
        }
        
        update_result = cloudscale_repo.update_record(TABLES['sessions'], str(row_id), update_data)
        
        if update_result.get('success'):
            # Audit log
            _log_session_event(
                event_type="SESSION_REVOKED",
                session_id=session_id,
                user_id=session.get("User_ID"),
                user_email=session.get("User_Email"),
                ip_address=session.get("IP_Address"),
                details={"reason": reason}
            )
            
            logger.info(f"Session revoked: {session_id[:8]}... (reason: {reason})")
            return True
        
        return False
        
    except Exception as exc:
        logger.error(f"Failed to revoke session: {exc}")
        return False


def revoke_all_user_sessions(user_id: str, exclude_session: Optional[str] = None) -> int:
    """
    Revoke all sessions for a user.
    
    Used on password change, security breach, or admin action.
    
    Args:
        user_id: User ID whose sessions to revoke
        exclude_session: Optional session ID to keep active (current session)
    
    Returns:
        Number of sessions revoked
    """
    try:
        # Get all active sessions for user
        query = f"""
            SELECT ROWID, Session_ID, IP_Address FROM {TABLES['sessions']}
            WHERE User_ID = '{_escape_zcql(str(user_id))}'
            AND Is_Active = true
        """
        result = cloudscale_repo.execute_query(query)
        
        if not result.get('success'):
            return 0
        
        data = result.get('data', {}).get('data', [])
        if not data:
            return 0
        
        revoked_count = 0
        now = datetime.now(timezone.utc).isoformat()
        
        for session in data:
            session_id = session.get("Session_ID")
            row_id = session.get("ROWID")
            
            if exclude_session and session_id == exclude_session:
                continue
            
            if not row_id:
                continue
            
            # Mark as inactive
            update_data = {
                "Is_Active": False,
                "Revoked_At": now,
                "Revoke_Reason": "all_sessions_revoked",
            }
            update_result = cloudscale_repo.update_record(TABLES['sessions'], str(row_id), update_data)
            if update_result.get('success'):
                revoked_count += 1
        
        # Audit log
        _log_session_event(
            event_type="ALL_SESSIONS_REVOKED",
            session_id="",
            user_id=user_id,
            user_email="",
            ip_address="",
            details={"revoked_count": revoked_count, "excluded": exclude_session}
        )
        
        logger.info(f"Revoked {revoked_count} sessions for user {user_id}")
        return revoked_count
        
    except Exception as exc:
        logger.error(f"Failed to revoke all sessions: {exc}")
        return 0


def get_user_sessions(user_id: str) -> List[Dict[str, Any]]:
    """
    Get all active sessions for a user.
    
    Args:
        user_id: User ID to query
    
    Returns:
        List of session metadata (without sensitive tokens)
    """
    try:
        query = f"""
            SELECT Session_ID, IP_Address, User_Agent, CREATEDTIME, Last_Accessed_At
            FROM {TABLES['sessions']}
            WHERE User_ID = '{_escape_zcql(str(user_id))}'
            AND Is_Active = true
            ORDER BY Last_Accessed_At DESC
        """
        result = cloudscale_repo.execute_query(query)
        
        if not result.get('success'):
            return []
        
        data = result.get('data', {}).get('data', [])
        
        sessions = []
        for session in (data or []):
            sessions.append({
                "session_id": session.get("Session_ID"),
                "ip_address": session.get("IP_Address"),
                "user_agent": session.get("User_Agent"),
                "created_at": session.get("CREATEDTIME"),
                "last_accessed_at": session.get("Last_Accessed_At"),
                "is_current": False,  # Caller should set this based on request session
            })
        
        return sessions
        
    except Exception as exc:
        logger.error(f"Failed to get user sessions: {exc}")
        return []


# ══════════════════════════════════════════════════════════════════════════════
#  CONCURRENT SESSION MANAGEMENT
# ══════════════════════════════════════════════════════════════════════════════

def _enforce_session_limit(user_id: str) -> None:
    """
    Enforce maximum concurrent sessions per user.
    
    Removes oldest sessions when limit is exceeded.
    """
    try:
        # Count active sessions
        query = f"""
            SELECT ROWID, Session_ID, Last_Accessed_At FROM {TABLES['sessions']}
            WHERE User_ID = '{_escape_zcql(str(user_id))}'
            AND Is_Active = true
            ORDER BY Last_Accessed_At ASC
        """
        result = cloudscale_repo.execute_query(query)
        
        if not result.get('success'):
            return
        
        data = result.get('data', {}).get('data', [])
        if not data:
            return
        
        # If at or over limit, remove oldest
        sessions_to_remove = len(data) - MAX_CONCURRENT_SESSIONS + 1
        if sessions_to_remove > 0:
            for session in data[:sessions_to_remove]:
                session_id = session.get("Session_ID")
                if session_id:
                    _revoke_session_internal(
                        str(session_id),  # Convert to string for revocation
                        reason="concurrent_limit_exceeded"
                    )
                    logger.info(f"Removed oldest session due to limit: {str(session_id)[:8]}...")
                
    except Exception as exc:
        logger.error(f"Failed to enforce session limit: {exc}")


def _update_session_activity(session_id: str, timestamp: datetime) -> None:
    """Update last_accessed_at for sliding window timeout."""
    try:
        # Get ROWID first - Session_ID is BIGINT, no quotes
        query = f"""
            SELECT ROWID FROM {TABLES['sessions']}
            WHERE Session_ID = {session_id}
        """
        result = cloudscale_repo.execute_query(query)
        
        if result.get('success'):
            data = result.get('data', {}).get('data', [])
            if data and data[0].get('ROWID'):
                cloudscale_repo.update_record(
                    TABLES['sessions'],
                    str(data[0]['ROWID']),
                    {"Last_Accessed_At": timestamp.isoformat()}
                )
    except Exception as exc:
        logger.debug(f"Failed to update session activity: {exc}")


# ══════════════════════════════════════════════════════════════════════════════
#  SESSION CLEANUP
# ══════════════════════════════════════════════════════════════════════════════

def cleanup_expired_sessions() -> int:
    """
    Remove expired and revoked sessions from the database.
    
    Should be run periodically (e.g., every 6 hours).
    
    Returns:
        Number of sessions cleaned up
    """
    try:
        now = datetime.now(timezone.utc)
        cutoff = (now - timedelta(hours=SESSION_TIMEOUT_HOURS * 2)).isoformat()
        
        # Find sessions to delete - use CREATEDTIME (Catalyst auto-field)
        query = f"""
            SELECT ROWID, Session_ID FROM {TABLES['sessions']}
            WHERE (Is_Active = false AND CREATEDTIME < '{cutoff}')
            OR (Expires_At < '{now.isoformat()}')
        """
        result = cloudscale_repo.execute_query(query)
        
        if not result.get('success'):
            return 0
        
        data = result.get('data', {}).get('data', [])
        if not data:
            return 0
        
        deleted_count = 0
        for session in data:
            row_id = session.get("ROWID")
            if row_id:
                try:
                    delete_result = cloudscale_repo.delete_record(TABLES['sessions'], str(row_id))
                    if delete_result.get('success'):
                        deleted_count += 1
                except Exception:
                    pass  # Continue with other deletions
        
        logger.info(f"Cleaned up {deleted_count} expired sessions")
        return deleted_count
        
    except Exception as exc:
        logger.error(f"Session cleanup failed: {exc}")
        return 0


# ══════════════════════════════════════════════════════════════════════════════
#  CSRF VALIDATION
# ══════════════════════════════════════════════════════════════════════════════

def validate_csrf_token(session_id: str, csrf_token: str) -> bool:
    """
    Validate CSRF token for a session.
    
    Args:
        session_id: Session ID
        csrf_token: CSRF token from request header
    
    Returns:
        True if valid, False otherwise
    """
    if not session_id or not csrf_token:
        return False
    
    try:
        # Session_ID is BIGINT, no quotes needed
        query = f"""
            SELECT CSRF_Token FROM {TABLES['sessions']}
            WHERE Session_ID = {session_id}
            AND Is_Active = true
        """
        result = cloudscale_repo.execute_query(query)
        
        if result.get('success'):
            data = result.get('data', {}).get('data', [])
            if data and len(data) > 0:
                stored_token = data[0].get("CSRF_Token", "")
                return secrets.compare_digest(stored_token, csrf_token)
        
        return False
        
    except Exception as exc:
        logger.error(f"CSRF validation error: {exc}")
        return False


def regenerate_csrf_token(session_id: str) -> Optional[str]:
    """
    Generate a new CSRF token for a session.
    
    Args:
        session_id: Session ID to update
    
    Returns:
        New CSRF token, or None on failure
    """
    try:
        # Get ROWID first - Session_ID is BIGINT, no quotes
        query = f"""
            SELECT ROWID FROM {TABLES['sessions']}
            WHERE Session_ID = {session_id}
        """
        result = cloudscale_repo.execute_query(query)
        
        if not result.get('success'):
            return None
        
        data = result.get('data', {}).get('data', [])
        if not data or not data[0].get('ROWID'):
            return None
        
        new_token = generate_csrf_token()
        update_result = cloudscale_repo.update_record(
            TABLES['sessions'],
            str(data[0]['ROWID']),
            {"CSRF_Token": new_token}
        )
        
        if update_result.get('success'):
            return new_token
        return None
        
    except Exception as exc:
        logger.error(f"Failed to regenerate CSRF token: {exc}")
        return None


# ══════════════════════════════════════════════════════════════════════════════
#  AUDIT LOGGING
# ══════════════════════════════════════════════════════════════════════════════

def _log_session_event(
    event_type: str,
    session_id: str,
    user_id: str,
    user_email: str,
    ip_address: str,
    details: Optional[Dict[str, Any]] = None,
    severity: str = "INFO"
) -> None:
    """
    Log session events to audit table for security monitoring.
    
    Args:
        event_type: Type of event (SESSION_CREATED, SESSION_REVOKED, etc.)
        session_id: Session ID (stored in Details since Session_ID column is FK)
        user_id: User's ROWID
        user_email: User's email
        ip_address: Client IP address
        details: Additional event details (JSON)
        severity: Event severity (INFO, WARNING, ERROR, CRITICAL)
    """
    try:
        import json
        
        # Include session_id in details since Session_ID column is a foreign key
        event_details = details.copy() if details else {}
        if session_id:
            event_details["session_ref"] = str(session_id)[:20]
        
        audit_data = {
            "Event_Type": event_type,
            # Skip Session_ID - it's a foreign key expecting ROWID
            "User_ID": str(user_id) if user_id else "",
            "User_Email": user_email or "",
            "IP_Address": ip_address or "",
            "Details": json.dumps(event_details),
            "Event_Timestamp": datetime.now(timezone.utc).isoformat(),
            "Severity": severity,
        }
        
        result = cloudscale_repo.create_record(TABLES['session_audit'], audit_data)
        
        if result.get('success'):
            logger.debug(f"Audit log created: {event_type} for {user_email}")
        else:
            logger.warning(f"Audit log failed: {result.get('error')}")
        
    except Exception as exc:
        # Don't fail on audit logging errors - just log it
        logger.warning(f"Session audit logging failed: {exc}")


# Public wrapper for audit logging (used by routes)
def log_audit_event(
    event_type: str,
    user_email: str = "",
    user_id: str = "",
    ip_address: str = "",
    session_id: str = "",
    details: Optional[Dict[str, Any]] = None,
    severity: str = "INFO"
) -> None:
    """
    Public function to log audit events.
    
    Event types:
        - LOGIN_SUCCESS: Successful login
        - LOGIN_FAILED: Failed login attempt
        - LOGOUT: User logged out
        - PASSWORD_CHANGE: Password was changed
        - ACCOUNT_LOCKED: Account locked due to failed attempts
        - SUSPICIOUS_ACTIVITY: Unusual activity detected
    """
    _log_session_event(
        event_type=event_type,
        session_id=session_id,
        user_id=user_id,
        user_email=user_email,
        ip_address=ip_address,
        details=details,
        severity=severity
    )


# ══════════════════════════════════════════════════════════════════════════════
#  HELPER FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════════

def _escape_zcql(value: str) -> str:
    """Escape single quotes for ZCQL queries."""
    if value is None:
        return ""
    return str(value).replace("'", "''")


def _parse_datetime(dt_string: Optional[str]) -> Optional[datetime]:
    """Parse ISO format datetime string to timezone-aware datetime."""
    if not dt_string:
        return None
    try:
        # Try parsing ISO format
        dt = datetime.fromisoformat(dt_string.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return None


# ══════════════════════════════════════════════════════════════════════════════
#  ADMIN FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════════

def get_all_active_sessions(limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
    """
    Get all active sessions (admin only).
    
    Args:
        limit: Maximum number of sessions to return
        offset: Offset for pagination
    
    Returns:
        List of session metadata
    """
    try:
        query = f"""
            SELECT Session_ID, User_ID, User_Email, User_Role, IP_Address, 
                   User_Agent, CREATEDTIME, Last_Accessed_At
            FROM {TABLES['sessions']}
            WHERE Is_Active = true
            ORDER BY Last_Accessed_At DESC
            LIMIT {limit} OFFSET {offset}
        """
        result = cloudscale_repo.execute_query(query)
        
        if not result.get('success'):
            return []
        
        data = result.get('data', {}).get('data', [])
        
        return [
            {
                "session_id": s.get("Session_ID"),
                "user_id": s.get("User_ID"),
                "user_email": s.get("User_Email"),
                "user_role": s.get("User_Role"),
                "ip_address": s.get("IP_Address"),
                "user_agent": s.get("User_Agent"),
                "created_at": s.get("CREATEDTIME"),
                "last_accessed_at": s.get("Last_Accessed_At"),
            }
            for s in (data or [])
        ]
        
    except Exception as exc:
        logger.error(f"Failed to get all sessions: {exc}")
        return []


def admin_revoke_session(session_id: str, admin_id: str) -> bool:
    """
    Admin force-revoke a session.
    
    Args:
        session_id: Session to revoke
        admin_id: Admin user ID performing the action
    
    Returns:
        True if revoked successfully
    """
    success = _revoke_session_internal(session_id, reason=f"admin_revoke:{admin_id}")
    return success


def get_session_stats() -> Dict[str, Any]:
    """
    Get session statistics (admin only).
    
    Returns:
        Dict with session counts and metrics
    """
    try:
        # Active sessions count
        active_count = cloudscale_repo.count_records(TABLES['sessions'], "Is_Active = true")
        
        # For unique users, we'll do a simple count query
        query = f"""
            SELECT User_ID FROM {TABLES['sessions']}
            WHERE Is_Active = true
        """
        result = cloudscale_repo.execute_query(query)
        unique_users = 0
        if result.get('success'):
            data = result.get('data', {}).get('data', [])
            user_ids = set(s.get('User_ID') for s in data if s.get('User_ID'))
            unique_users = len(user_ids)
        
        return {
            "active_sessions": active_count,
            "unique_users": unique_users,
            "max_sessions_per_user": MAX_CONCURRENT_SESSIONS,
            "session_timeout_hours": SESSION_TIMEOUT_HOURS,
        }
        
    except Exception as exc:
        logger.error(f"Failed to get session stats: {exc}")
        return {}
