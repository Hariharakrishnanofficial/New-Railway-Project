"""
Announcements Routes - System announcements.
"""

import logging
import json
from datetime import datetime
from flask import Blueprint, jsonify, request

from repositories.cloudscale_repository import cloudscale_repo, CriteriaBuilder
from config import TABLES
from core.permission_validator import require_permission
from services.notification_service import create_announcement_notifications

logger = logging.getLogger(__name__)
announcements_bp = Blueprint('announcements', __name__)


@announcements_bp.route('/announcements', methods=['GET'])
def get_all_announcements():
    """Get all announcements."""
    try:
        result = cloudscale_repo.get_all_records(TABLES['announcements'], limit=100, order_by='ROWID DESC')
        if result.get('success'):
            return jsonify({'status': 'success', 'data': result.get('data', {}).get('data', [])}), 200
        return jsonify({'status': 'error', 'message': 'Failed to fetch announcements'}), 500
    except Exception as e:
        logger.exception(f'Get announcements error: {e}')
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


@announcements_bp.route('/announcements/active', methods=['GET'])
def get_active_announcements():
    """Get active announcements."""
    try:
        criteria = CriteriaBuilder().eq('Is_Active', 'true').build()
        result = cloudscale_repo.get_all_records(TABLES['announcements'], criteria=criteria, limit=50)
        if result.get('success'):
            return jsonify({'status': 'success', 'data': result.get('data', {}).get('data', [])}), 200
        return jsonify({'status': 'error', 'message': 'Failed to fetch announcements'}), 500
    except Exception as e:
        logger.exception(f'Get active announcements error: {e}')
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


@announcements_bp.route('/announcements/<announcement_id>', methods=['GET'])
def get_announcement(announcement_id):
    """Get announcement by ID."""
    try:
        result = cloudscale_repo.get_record_by_id(TABLES['announcements'], announcement_id)
        if result.get('success') and result.get('data'):
            return jsonify({'status': 'success', 'data': result['data']}), 200
        return jsonify({'status': 'error', 'message': 'Announcement not found'}), 404
    except Exception as e:
        logger.exception(f'Get announcement error: {e}')
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


@announcements_bp.route('/announcements', methods=['POST'])
@require_permission('announcements', 'create')
def create_announcement():
    """Create announcement (admin only)."""
    data = request.get_json(silent=True) or {}
    try:
        raw_roles = data.get('audienceRoles') or data.get('Audience_Roles') or []
        if isinstance(raw_roles, str):
            try:
                parsed_roles = json.loads(raw_roles)
                audience_roles = parsed_roles if isinstance(parsed_roles, list) else [raw_roles]
            except Exception:
                audience_roles = [p.strip() for p in raw_roles.split(',') if p.strip()]
        elif isinstance(raw_roles, list):
            audience_roles = [str(role).strip() for role in raw_roles if str(role).strip()]
        else:
            audience_roles = []

        audience_type = (data.get('audienceType') or data.get('Audience_Type') or 'both').strip().lower()
        if audience_type not in {'user', 'employee', 'both'}:
            audience_type = 'both'

        announcement_data = {
            'Title': data.get('title') or data.get('Title') or '',
            'Message': data.get('message') or data.get('Message') or '',
            'Type': data.get('type') or data.get('Type') or 'info',
            'Priority': data.get('priority') or data.get('Priority') or 'normal',
            'Is_Active': 'true',
            'Audience_Type': audience_type,
            'Audience_Roles': json.dumps(audience_roles) if audience_roles else '',
            'Created_At': datetime.utcnow().isoformat(),
        }
        result = cloudscale_repo.create_record(TABLES['announcements'], announcement_data)
        if result.get('success'):
            created_row = result.get('data') or {}
            announcement_id = created_row.get('ROWID')
            if announcement_id:
                fanout_result = create_announcement_notifications(
                    announcement_id=announcement_id,
                    title=announcement_data['Title'],
                    message=announcement_data['Message'],
                    audience_type=audience_type,
                    audience_roles=audience_roles,
                )
                if not fanout_result.get('success'):
                    logger.warning('Announcement fanout failed for %s: %s', announcement_id, fanout_result.get('error'))
            return jsonify({'status': 'success', 'data': created_row}), 201
        return jsonify({'status': 'error', 'message': 'Failed to create announcement'}), 500
    except Exception as e:
        logger.exception(f'Create announcement error: {e}')
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


@announcements_bp.route('/announcements/<announcement_id>', methods=['PUT'])
@require_permission('announcements', 'edit')
def update_announcement(announcement_id):
    """Update announcement (admin only)."""
    data = request.get_json(silent=True) or {}
    try:
        update_data = {}
        field_mapping = {
            'title': 'Title',
            'message': 'Message',
            'type': 'Type',
            'priority': 'Priority',
            'isActive': 'Is_Active',
            'audienceType': 'Audience_Type',
        }
        for client_key, db_key in field_mapping.items():
            if client_key in data:
                value = data[client_key]
                if client_key == 'isActive':
                    value = 'true' if value else 'false'
                if client_key == 'audienceType':
                    normalized = str(value).strip().lower()
                    value = normalized if normalized in {'user', 'employee', 'both'} else 'both'
                update_data[db_key] = value

        if 'audienceRoles' in data:
            roles = data.get('audienceRoles')
            if isinstance(roles, list):
                update_data['Audience_Roles'] = json.dumps([str(role).strip() for role in roles if str(role).strip()])
            elif isinstance(roles, str):
                try:
                    parsed = json.loads(roles)
                    if isinstance(parsed, list):
                        update_data['Audience_Roles'] = json.dumps([str(role).strip() for role in parsed if str(role).strip()])
                    else:
                        update_data['Audience_Roles'] = ''
                except Exception:
                    update_data['Audience_Roles'] = json.dumps([p.strip() for p in roles.split(',') if p.strip()])
            else:
                update_data['Audience_Roles'] = ''

        if not update_data:
            return jsonify({'status': 'error', 'message': 'No fields to update'}), 400

        result = cloudscale_repo.update_record(TABLES['announcements'], announcement_id, update_data)
        if result.get('success'):
            return jsonify({'status': 'success', 'message': 'Announcement updated'}), 200
        return jsonify({'status': 'error', 'message': 'Failed to update announcement'}), 500
    except Exception as e:
        logger.exception(f'Update announcement error: {e}')
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


@announcements_bp.route('/announcements/<announcement_id>', methods=['DELETE'])
@require_permission('announcements', 'delete')
def delete_announcement(announcement_id):
    """Delete announcement (admin only)."""
    try:
        result = cloudscale_repo.delete_record(TABLES['announcements'], announcement_id)
        if result.get('success'):
            return jsonify({'status': 'success', 'message': 'Announcement deleted'}), 200
        return jsonify({'status': 'error', 'message': 'Failed to delete announcement'}), 500
    except Exception as e:
        logger.exception(f'Delete announcement error: {e}')
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500
