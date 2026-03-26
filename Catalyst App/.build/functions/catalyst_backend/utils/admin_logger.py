"""
Admin Logging utility — provides a reusable helper to log admin actions.
Can be imported from any route file to auto-log admin operations.
"""

import logging
from datetime import datetime
from flask import request
from services.zoho_service import zoho
from config import get_form_config

logger = logging.getLogger(__name__)


def log_admin_action(
    admin_email: str,
    action: str,
    resource_type: str,
    resource_id: str = "",
    old_value: str = "",
    new_value: str = "",
) -> None:
    """
    Fire-and-forget admin action logging.
    Writes to the Admin_Logs table in Zoho.

    Usage:
        log_admin_action("admin@admin.com", "UPDATE", "Train", "12345",
                         old_value='{"Is_Active": "false"}',
                         new_value='{"Is_Active": "true"}')
    """
    try:
        forms = get_form_config()
        payload = {
            "Admin_User":    admin_email,
            "Action":        action,
            "Resource_Type": resource_type,
            "Resource_ID":   str(resource_id),
            "Old_Value":     str(old_value)[:2000] if old_value else "",
            "New_Value":     str(new_value)[:2000] if new_value else "",
            "Timestamp":     datetime.now().strftime("%d-%b-%Y %H:%M:%S"),
            "IP_Address":    request.headers.get("X-Forwarded-For", request.remote_addr or ""),
        }
        zoho.create_record(forms["forms"]["admin_logs"], payload)
        logger.debug(f"Admin log: {admin_email} {action} {resource_type}/{resource_id}")
    except Exception as exc:
        # Never fail silently but also never block the main operation
        logger.warning(f"Failed to write admin log: {exc}")
