"""
log_helper.py
Helper function to log admin actions to the Admin_Logs Zoho form.
"""
from services.zoho_service import zoho
from config import get_form_config
from flask import g, request
import logging
import json
from datetime import datetime

logger = logging.getLogger(__name__)

def log_admin_action(action, record_id=None, summary=None, details=None):
    """
    Logs an admin action to the Admin_Logs form in Zoho.

    Args:
        action (str): A short string identifying the action (e.g., 'create_train').
        record_id (str, optional): The ID of the Zoho record that was affected.
        summary (str, optional): A human-readable summary of the action.
        details (dict, optional): A dictionary with extra details to be stored as JSON.
    """
    try:
        if not hasattr(g, 'user') or not g.user:
            logger.warning("Cannot log admin action: No user in Flask global context 'g'.")
            return

        user_id = g.user.get('ID')
        user_name = g.user.get('Full_Name', 'Unknown User')
        forms = get_form_config()
        
        if not summary:
            summary = f"User '{user_name}' performed action '{action}'"
            if record_id:
                summary += f" on record '{record_id}'"

        payload = {
            "User_ID": str(user_id),
            "User_Name": user_name,
            "Action": action,
            "Timestamp": datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S'),
            "Affected_Record_ID": str(record_id) if record_id else None,
            "Summary": summary,
            "Details_JSON": json.dumps(details) if details else None,
            "Source_IP": request.remote_addr,
        }

        result = zoho.create_record(forms['forms']['admin_logs'], payload)
        if not result.get('success'):
            logger.error(f"Failed to log admin action to Zoho: {result.get('error')}")

    except Exception as e:
        logger.error(f"Exception in log_admin_action: {e}", exc_info=True)

