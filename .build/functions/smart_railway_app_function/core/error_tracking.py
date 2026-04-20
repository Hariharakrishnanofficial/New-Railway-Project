"""
Centralized error tracking for API responses and audit persistence.

This module standardizes request correlation IDs and records selected
application errors to Session_Audit_Log without exposing sensitive details.
"""

from __future__ import annotations

import os
import uuid
import json
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any

from flask import g, request, has_request_context

logger = logging.getLogger(__name__)

_DEFAULT_MIN_STATUS = 500


def _min_audit_status() -> int:
    """Return minimum status code to persist into audit logs."""
    raw = os.getenv("ERROR_AUDIT_MIN_STATUS", str(_DEFAULT_MIN_STATUS))
    try:
        value = int(raw)
        if 100 <= value <= 599:
            return value
    except (TypeError, ValueError):
        pass
    return _DEFAULT_MIN_STATUS


def ensure_request_id() -> str:
    """Ensure request has a correlation ID and return it."""
    if not has_request_context():
        return uuid.uuid4().hex

    existing = getattr(g, "request_id", "")
    if existing:
        return existing

    incoming = (request.headers.get("X-Request-ID") or "").strip()
    request_id = incoming[:64] if incoming else uuid.uuid4().hex
    g.request_id = request_id
    return request_id


def get_request_id() -> str:
    """Get request correlation ID, creating one if needed."""
    return ensure_request_id()


def attach_request_id_header(response):
    """Attach correlation ID to outgoing responses."""
    response.headers["X-Request-ID"] = get_request_id()
    return response


def _severity_from_status(status_code: int) -> str:
    if status_code >= 500:
        return "ERROR"
    if status_code >= 400:
        return "WARNING"
    return "INFO"


def _safe_text(value: Any, max_len: int = 500) -> str:
    text = "" if value is None else str(value)
    return text[:max_len]


def _get_client_ip() -> str:
    forwarded_for = request.headers.get("X-Forwarded-For", "")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.remote_addr or ""


def _should_persist(status_code: int) -> bool:
    return status_code >= _min_audit_status()


def _persist_to_application_errors(error_record: Dict[str, Any]) -> bool:
    """Try to persist to Application_Errors table. Returns True on success."""
    try:
        from config import TABLES
        from repositories.cloudscale_repository import cloudscale_repo

        table_name = TABLES.get("application_errors")
        if not table_name:
            return False

        result = cloudscale_repo.create_record(table_name, error_record)
        if result.get("success"):
            return True

        logger.warning("Application_Errors write failed: %s", result.get("error"))
        return False
    except Exception as exc:
        logger.warning("Application_Errors persistence error: %s", exc)
        return False


def record_application_error(
    exc: Exception,
    status_code: int,
    error_code: str,
    user_message: str,
) -> None:
    """
    Persist standardized error context to Session_Audit_Log.

    Uses lazy import to avoid heavy import/cycle at app startup.
    """
    if not has_request_context() or not _should_persist(status_code):
        return

    request_id = get_request_id()
    details: Dict[str, Any] = {
        "request_id": request_id,
        "status_code": status_code,
        "error_code": _safe_text(error_code, 100),
        "message": _safe_text(user_message, 500),
        "exception_type": type(exc).__name__,
        "exception": _safe_text(exc, 500),
        "method": request.method,
        "path": request.path,
        "endpoint": request.endpoint,
        "user_agent": _safe_text(request.headers.get("User-Agent", ""), 300),
    }

    error_record = {
        "Request_ID": _safe_text(request_id, 64),
        "Error_Code": _safe_text(error_code, 100),
        "Status_Code": int(status_code),
        "Message": _safe_text(user_message, 500),
        "Exception_Type": _safe_text(type(exc).__name__, 100),
        "Exception_Message": _safe_text(exc, 1000),
        "Request_Method": _safe_text(request.method, 10),
        "Request_Path": _safe_text(request.path, 500),
        "Endpoint": _safe_text(request.endpoint or "", 200),
        "User_ID": _safe_text(getattr(g, "user_id", ""), 50),
        "User_Email": _safe_text(getattr(g, "user_email", ""), 200),
        "Session_ID": _safe_text(getattr(g, "session_id", ""), 80),
        "IP_Address": _safe_text(_get_client_ip(), 64),
        "User_Agent": _safe_text(request.headers.get("User-Agent", ""), 300),
        "Severity": _severity_from_status(status_code),
        "Error_Details": _safe_text(json.dumps(details, default=str), 4000),
        "Created_At": datetime.now(timezone.utc).isoformat(),
    }

    if _persist_to_application_errors(error_record):
        return

    try:
        from services.session_service import log_audit_event

        log_audit_event(
            event_type="APPLICATION_ERROR",
            user_email=_safe_text(getattr(g, "user_email", ""), 200),
            user_id=_safe_text(getattr(g, "user_id", ""), 50),
            ip_address=_get_client_ip(),
            session_id=_safe_text(getattr(g, "session_id", ""), 80),
            details=details,
            severity=_severity_from_status(status_code),
        )
    except Exception as log_exc:
        logger.warning("Failed to persist application error audit event: %s", log_exc)
