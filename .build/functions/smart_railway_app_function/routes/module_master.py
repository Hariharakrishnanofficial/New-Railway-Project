"""
Module Master Routes - CRUD operations for Module Master table.

Endpoints:
- GET /modules - List all modules
- GET /modules/<id> - Get module by ID
- POST /modules - Create new module
- PUT /modules/<id> - Update module
- DELETE /modules/<id> - Delete module
"""

import logging
import re
from flask import Blueprint, jsonify, request

from repositories.cloudscale_repository import cloudscale_repo, CriteriaBuilder
from config import TABLES
from core.security import require_auth, require_admin, rate_limit

logger = logging.getLogger(__name__)
module_master_bp = Blueprint('module_master', __name__)

# Validation patterns
MODULE_CODE_PATTERN = re.compile(r'^[A-Z][A-Z0-9_]{1,19}$')


def _sanitize_string(value: str, max_length: int = 255) -> str:
    """Sanitize string input to prevent SQL injection."""
    if not value:
        return ''
    sanitized = value.replace("'", "''").replace('"', '').replace(';', '').replace('--', '')
    return sanitized[:max_length]


# ══════════════════════════════════════════════════════════════════════════════
#  GET ALL MODULES
# ══════════════════════════════════════════════════════════════════════════════

@module_master_bp.route('/modules', methods=['GET'])
@require_auth
def get_all_modules():
    """Get all modules with optional filtering."""
    try:
        # Query parameters
        limit = min(request.args.get('limit', 100, type=int), 500)
        offset = request.args.get('offset', 0, type=int)
        active_only = request.args.get('active', 'true').lower() == 'true'
        search = request.args.get('search', '').strip()

        # Build criteria
        cb = CriteriaBuilder()

        if active_only:
            cb.eq('Is_Active', 'true')

        if search:
            safe_search = _sanitize_string(search, 50)
            if safe_search:
                cb.contains('Module_Name', safe_search)

        criteria = cb.build()

        result = cloudscale_repo.get_all_records(
            TABLES.get('module_master', 'Module_Master'),
            criteria=criteria,
            limit=limit,
            offset=offset,
            order_by='Display_Order ASC, Module_Name ASC'
        )

        if result.get('success'):
            modules = result.get('data', {}).get('data', [])
            return jsonify({
                'status': 'success',
                'data': modules,
                'pagination': {
                    'limit': limit,
                    'offset': offset,
                    'count': len(modules)
                }
            }), 200

        return jsonify({
            'status': 'error',
            'message': 'Failed to fetch modules'
        }), 500

    except Exception as e:
        logger.exception(f'Get modules error: {e}')
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


# ══════════════════════════════════════════════════════════════════════════════
#  GET MODULE BY ID
# ══════════════════════════════════════════════════════════════════════════════

@module_master_bp.route('/modules/<module_id>', methods=['GET'])
@require_auth
def get_module(module_id):
    """Get module by ID."""
    try:
        result = cloudscale_repo.get_record_by_id(
            TABLES.get('module_master', 'Module_Master'),
            module_id
        )

        if result.get('success') and result.get('data'):
            return jsonify({
                'status': 'success',
                'data': result['data']
            }), 200

        return jsonify({
            'status': 'error',
            'message': 'Module not found'
        }), 404

    except Exception as e:
        logger.exception(f'Get module error: {e}')
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


# ══════════════════════════════════════════════════════════════════════════════
#  CREATE MODULE
# ══════════════════════════════════════════════════════════════════════════════

@module_master_bp.route('/modules', methods=['POST'])
@require_admin
@rate_limit(max_calls=50, window_seconds=3600)
def create_module():
    """Create a new module (admin only)."""
    data = request.get_json(silent=True) or {}

    # Extract and validate fields
    module_code = (data.get('moduleCode') or data.get('Module_Code') or '').strip().upper()
    module_name = (data.get('moduleName') or data.get('Module_Name') or '').strip()
    description = (data.get('description') or data.get('Description') or '').strip()
    display_order = data.get('displayOrder', data.get('Display_Order', 0))
    is_active = data.get('isActive', data.get('Is_Active', True))

    # Validation
    if not module_code:
        return jsonify({'status': 'error', 'message': 'Module code is required'}), 400

    if not MODULE_CODE_PATTERN.match(module_code):
        return jsonify({
            'status': 'error',
            'message': 'Module code must start with letter, contain only A-Z, 0-9, underscore, 2-20 chars'
        }), 400

    if not module_name:
        return jsonify({'status': 'error', 'message': 'Module name is required'}), 400

    if len(module_name) > 100:
        return jsonify({'status': 'error', 'message': 'Module name must be 100 chars or less'}), 400

    try:
        # Check for duplicate code
        existing = cloudscale_repo.get_records(
            TABLES.get('module_master', 'Module_Master'),
            criteria=CriteriaBuilder().eq('Module_Code', module_code).build(),
            limit=1
        )

        if existing:
            return jsonify({
                'status': 'error',
                'message': f'Module code {module_code} already exists'
            }), 409

        # Create module
        module_data = {
            'Module_Code': module_code,
            'Module_Name': _sanitize_string(module_name, 100),
            'Description': _sanitize_string(description, 500),
            'Display_Order': int(display_order) if display_order else 0,
            'Is_Active': bool(is_active),
        }

        result = cloudscale_repo.create_record(
            TABLES.get('module_master', 'Module_Master'),
            module_data
        )

        if result.get('success'):
            module_data['ROWID'] = result.get('data', {}).get('ROWID')
            return jsonify({
                'status': 'success',
                'message': 'Module created successfully',
                'data': module_data
            }), 201

        return jsonify({
            'status': 'error',
            'message': 'Failed to create module'
        }), 500

    except Exception as e:
        logger.exception(f'Create module error: {e}')
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


# ══════════════════════════════════════════════════════════════════════════════
#  UPDATE MODULE
# ══════════════════════════════════════════════════════════════════════════════

@module_master_bp.route('/modules/<module_id>', methods=['PUT'])
@require_admin
@rate_limit(max_calls=100, window_seconds=3600)
def update_module(module_id):
    """Update an existing module (admin only)."""
    data = request.get_json(silent=True) or {}

    try:
        # Check if module exists
        existing = cloudscale_repo.get_record_by_id(
            TABLES.get('module_master', 'Module_Master'),
            module_id
        )

        if not existing.get('success') or not existing.get('data'):
            return jsonify({'status': 'error', 'message': 'Module not found'}), 404

        # Build update data
        update_data = {}

        if 'moduleName' in data or 'Module_Name' in data:
            name = (data.get('moduleName') or data.get('Module_Name') or '').strip()
            if name:
                update_data['Module_Name'] = _sanitize_string(name, 100)

        if 'description' in data or 'Description' in data:
            desc = data.get('description') or data.get('Description') or ''
            update_data['Description'] = _sanitize_string(desc, 500)

        if 'displayOrder' in data or 'Display_Order' in data:
            order = data.get('displayOrder', data.get('Display_Order', 0))
            update_data['Display_Order'] = int(order)

        if 'isActive' in data or 'Is_Active' in data:
            active = data.get('isActive', data.get('Is_Active', True))
            update_data['Is_Active'] = bool(active)

        if not update_data:
            return jsonify({'status': 'error', 'message': 'No fields to update'}), 400

        result = cloudscale_repo.update_record(
            TABLES.get('module_master', 'Module_Master'),
            module_id,
            update_data
        )

        if result.get('success'):
            return jsonify({
                'status': 'success',
                'message': 'Module updated successfully',
                'data': update_data
            }), 200

        return jsonify({
            'status': 'error',
            'message': 'Failed to update module'
        }), 500

    except Exception as e:
        logger.exception(f'Update module error: {e}')
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


# ══════════════════════════════════════════════════════════════════════════════
#  DELETE MODULE
# ══════════════════════════════════════════════════════════════════════════════

@module_master_bp.route('/modules/<module_id>', methods=['DELETE'])
@require_admin
def delete_module(module_id):
    """Delete a module (admin only)."""
    try:
        # Check if module exists
        existing = cloudscale_repo.get_record_by_id(
            TABLES.get('module_master', 'Module_Master'),
            module_id
        )

        if not existing.get('success') or not existing.get('data'):
            return jsonify({'status': 'error', 'message': 'Module not found'}), 404

        result = cloudscale_repo.delete_record(
            TABLES.get('module_master', 'Module_Master'),
            module_id
        )

        if result.get('success'):
            return jsonify({
                'status': 'success',
                'message': 'Module deleted successfully'
            }), 200

        return jsonify({
            'status': 'error',
            'message': 'Failed to delete module'
        }), 500

    except Exception as e:
        logger.exception(f'Delete module error: {e}')
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500
