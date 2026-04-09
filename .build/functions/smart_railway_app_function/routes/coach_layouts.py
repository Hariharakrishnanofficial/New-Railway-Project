"""
Coach Layouts Routes - Coach configuration and layout management.
"""

import logging
from flask import Blueprint, jsonify, request

from repositories.cloudscale_repository import cloudscale_repo, CriteriaBuilder
from config import TABLES
from core.security import require_auth, require_admin

logger = logging.getLogger(__name__)
coach_layouts_bp = Blueprint('coach_layouts', __name__)


@coach_layouts_bp.route('/coach-layouts', methods=['GET'])
def get_all_coach_layouts():
    """Get all coach layouts."""
    try:
        train_id = request.args.get('trainId')
        coach_type = request.args.get('coachType')

        cb = CriteriaBuilder()
        if train_id:
            cb.id_eq('Train_ID', train_id)
        if coach_type:
            cb.eq('Coach_Type', coach_type)

        criteria = cb.build()
        result = cloudscale_repo.get_all_records(TABLES['coach_layouts'], criteria=criteria, limit=200)

        if result.get('success'):
            return jsonify({'status': 'success', 'data': result.get('data', {}).get('data', [])}), 200
        return jsonify({'status': 'error', 'message': 'Failed to fetch coach layouts'}), 500
    except Exception as e:
        logger.exception(f'Get coach layouts error: {e}')
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


@coach_layouts_bp.route('/coach-layouts/<layout_id>', methods=['GET'])
def get_coach_layout(layout_id):
    """Get coach layout by ID."""
    try:
        result = cloudscale_repo.get_record_by_id(TABLES['coach_layouts'], layout_id)
        if result.get('success') and result.get('data'):
            return jsonify({'status': 'success', 'data': result['data']}), 200
        return jsonify({'status': 'error', 'message': 'Coach layout not found'}), 404
    except Exception as e:
        logger.exception(f'Get coach layout error: {e}')
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


@coach_layouts_bp.route('/coach-layouts', methods=['POST'])
@require_admin
def create_coach_layout():
    """Create new coach layout (admin only)."""
    data = request.get_json(silent=True) or {}
    try:
        layout_data = {
            'Train_ID': data.get('trainId') or data.get('Train_ID'),
            'Coach_Type': data.get('coachType') or data.get('Coach_Type') or '',
            'Coach_Number': data.get('coachNumber') or data.get('Coach_Number') or '',
            'Total_Seats': data.get('totalSeats') or data.get('Total_Seats') or 0,
            'Seat_Configuration': data.get('seatConfiguration') or data.get('Seat_Configuration') or '',
            'Facilities': data.get('facilities') or data.get('Facilities') or '',
            'Position': data.get('position') or data.get('Position') or 1,
        }
        result = cloudscale_repo.create_record(TABLES['coach_layouts'], layout_data)
        if result.get('success'):
            return jsonify({'status': 'success', 'data': result.get('data')}), 201
        return jsonify({'status': 'error', 'message': 'Failed to create coach layout'}), 500
    except Exception as e:
        logger.exception(f'Create coach layout error: {e}')
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


@coach_layouts_bp.route('/coach-layouts/<layout_id>', methods=['PUT'])
@require_admin
def update_coach_layout(layout_id):
    """Update coach layout (admin only)."""
    data = request.get_json(silent=True) or {}
    try:
        update_data = {}
        field_mapping = {
            'coachType': 'Coach_Type',
            'coachNumber': 'Coach_Number',
            'totalSeats': 'Total_Seats',
            'seatConfiguration': 'Seat_Configuration',
            'facilities': 'Facilities',
            'position': 'Position',
        }

        for client_key, db_key in field_mapping.items():
            if client_key in data:
                update_data[db_key] = data[client_key]

        if not update_data:
            return jsonify({'status': 'error', 'message': 'No fields to update'}), 400

        result = cloudscale_repo.update_record(TABLES['coach_layouts'], layout_id, update_data)
        if result.get('success'):
            return jsonify({'status': 'success', 'message': 'Coach layout updated'}), 200
        return jsonify({'status': 'error', 'message': 'Failed to update coach layout'}), 500
    except Exception as e:
        logger.exception(f'Update coach layout error: {e}')
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


@coach_layouts_bp.route('/coach-layouts/<layout_id>', methods=['DELETE'])
@require_admin
def delete_coach_layout(layout_id):
    """Delete coach layout (admin only)."""
    try:
        result = cloudscale_repo.delete_record(TABLES['coach_layouts'], layout_id)
        if result.get('success'):
            return jsonify({'status': 'success', 'message': 'Coach layout deleted'}), 200
        return jsonify({'status': 'error', 'message': 'Failed to delete coach layout'}), 500
    except Exception as e:
        logger.exception(f'Delete coach layout error: {e}')
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


@coach_layouts_bp.route('/coach-layouts/train/<train_id>', methods=['GET'])
def get_layouts_by_train(train_id):
    """Get all coach layouts for a specific train."""
    try:
        result = cloudscale_repo.get_train_coach_layouts(train_id)
        if result:
            return jsonify({'status': 'success', 'data': result}), 200
        return jsonify({'status': 'error', 'message': 'No coach layouts found for this train'}), 404
    except Exception as e:
        logger.exception(f'Get train coach layouts error: {e}')
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


@coach_layouts_bp.route('/coach-layouts/template/<coach_type>', methods=['GET'])
def get_layout_template(coach_type):
    """Get standard layout template for coach type."""
    try:
        templates = {
            'SL': {'totalSeats': 72, 'configuration': '3+3', 'facilities': 'Fan, Charging Point'},
            '3A': {'totalSeats': 64, 'configuration': '2+2', 'facilities': 'AC, Charging Point, Reading Light'},
            '2A': {'totalSeats': 48, 'configuration': '2+2', 'facilities': 'AC, Charging Point, Reading Light, Curtains'},
            '1A': {'totalSeats': 24, 'configuration': '2+0', 'facilities': 'AC, Charging Point, Reading Light, Curtains, TV'},
            'CC': {'totalSeats': 80, 'configuration': '3+2', 'facilities': 'AC, Ergonomic Seats'}
        }

        template = templates.get(coach_type)
        if template:
            return jsonify({'status': 'success', 'data': template}), 200
        return jsonify({'status': 'error', 'message': 'Template not found for this coach type'}), 404
    except Exception as e:
        logger.exception(f'Get layout template error: {e}')
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500