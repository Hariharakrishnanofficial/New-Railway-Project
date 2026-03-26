"""
Settings routes — CRUD for system settings.
"""

from flask import Blueprint, jsonify, request
from services.zoho_service import zoho
from config import TABLES
from utils.validators import validate_required

settings_bp = Blueprint('settings', __name__)


@settings_bp.route('/api/settings', methods=['POST'])
def create_setting():
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "error": "No data provided"}), 400

    mapped_data = {
        "Setting_Key":   (data.get("Setting_Key") or data.get("Key") or data.get("Type_field") or "").strip(),
        "Setting_Value": (data.get("Setting_Value") or data.get("Value") or "").strip(),
        "Setting_Type":  (data.get("Setting_Type") or data.get("Category") or "General").strip(),
        "Description":   (data.get("Description") or "").strip(),
        "Is_System":     data.get("Is_System", "false")
    }

    is_valid, missing = validate_required(mapped_data, ['Setting_Key', 'Setting_Value'])
    if not is_valid:
        return jsonify({
            "success": False,
            "error": f"Missing fields: {', '.join(missing)}"
        }), 400

    result = zoho.create_record(
        TABLES['settings'],
        mapped_data
    )

    print("Settings response:", result)
    return jsonify(result), result.get("status_code", 200)


@settings_bp.route('/api/settings', methods=['GET'])
def get_settings():
    # Frontend-friendly query params
    limit = request.args.get("limit", 200, type=int)
    type_filter = request.args.get("type")      # frontend sends ?type=Seat Class
    value_filter = request.args.get("value")    # frontend sends ?value=Economy

    # Build query criteria
    criteria_parts = []

    if type_filter:
        criteria_parts.append(f'(Setting_Key == "{type_filter}") || (Setting_Type == "{type_filter}")')

    if value_filter:
        criteria_parts.append(f'Setting_Value.contains("{value_filter}")')

    criteria = " && ".join(criteria_parts) if criteria_parts else None

    result = zoho.get_all_records(
        TABLES['settings'],
        criteria,
        limit
    )

    return jsonify(result), result.get("status_code", 200)


@settings_bp.route('/api/settings/<setting_id>', methods=['GET'])
def get_setting(setting_id):
    result = zoho.get_record_by_id(
        TABLES['settings'],
        setting_id
    )

    return jsonify(result), result.get("status_code", 200)


@settings_bp.route('/api/settings/key/<key>', methods=['GET'])
def get_setting_by_key(key):
    """Look up a setting by its Setting_Key field name (e.g., dropdown_class_types)."""
    from repositories.cloudscale_repository import CriteriaBuilder
    criteria = CriteriaBuilder().eq('Setting_Key', key).build()
    result = zoho.get_all_records(
        TABLES['settings'],
        criteria,
        limit=1
    )
    if not result.get('success'):
        return jsonify(result), result.get('status_code', 500)
    records = result.get('data', {}).get('data', [])
    if records:
        return jsonify({'success': True, 'data': records[0]}), 200
    return jsonify({'success': False, 'error': f'Setting with Setting_Key "{key}" not found'}), 404


@settings_bp.route('/api/settings/<setting_id>', methods=['PUT'])
def update_setting(setting_id):
    data = request.get_json()

    if not data:
        return jsonify({
            "success": False,
            "error": "No data provided"
        }), 400

    result = zoho.update_record(
        TABLES['settings'],
        setting_id,
        data
    )

    return jsonify(result), result.get("status_code", 200)


@settings_bp.route('/api/settings/<setting_id>', methods=['DELETE'])
def delete_setting(setting_id):
    result = zoho.delete_record(
        TABLES['settings'],
        setting_id
    )

    return jsonify(result), result.get("status_code", 200)
