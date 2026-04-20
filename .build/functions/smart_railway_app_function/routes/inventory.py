"""
Inventory Routes - Seat inventory management.
"""

import logging
from flask import Blueprint, jsonify, request

from repositories.cloudscale_repository import cloudscale_repo, CriteriaBuilder
from config import TABLES
from core.permission_validator import require_permission

logger = logging.getLogger(__name__)
inventory_bp = Blueprint('inventory', __name__)


@inventory_bp.route('/inventory', methods=['GET'])
def get_all_inventory():
    """Get all inventory records."""
    try:
        train_id = request.args.get('trainId')
        journey_date = request.args.get('journeyDate')

        cb = CriteriaBuilder()
        if train_id:
            cb.id_eq('Train_ID', train_id)
        if journey_date:
            cb.eq('Journey_Date', journey_date)

        criteria = cb.build()
        result = cloudscale_repo.get_all_records(TABLES['train_inventory'], criteria=criteria, limit=200)

        if result.get('success'):
            return jsonify({'status': 'success', 'data': result.get('data', {}).get('data', [])}), 200
        return jsonify({'status': 'error', 'message': 'Failed to fetch inventory'}), 500
    except Exception as e:
        logger.exception(f'Get inventory error: {e}')
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


@inventory_bp.route('/inventory/<inventory_id>', methods=['GET'])
def get_inventory(inventory_id):
    """Get inventory by ID."""
    try:
        result = cloudscale_repo.get_record_by_id(TABLES['train_inventory'], inventory_id)
        if result.get('success') and result.get('data'):
            return jsonify({'status': 'success', 'data': result['data']}), 200
        return jsonify({'status': 'error', 'message': 'Inventory not found'}), 404
    except Exception as e:
        logger.exception(f'Get inventory error: {e}')
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


@inventory_bp.route('/inventory', methods=['POST'])
@require_permission('trains', 'edit')
def create_inventory():
    """Create inventory record (admin only)."""
    data = request.get_json(silent=True) or {}
    try:
        inventory_data = {
            'Train_ID': data.get('trainId') or data.get('Train_ID'),
            'Journey_Date': data.get('journeyDate') or data.get('Journey_Date'),
            'Available_Seats_SL': data.get('availableSeatsSL') or 0,
            'Available_Seats_3A': data.get('availableSeats3A') or 0,
            'Available_Seats_2A': data.get('availableSeats2A') or 0,
            'Available_Seats_1A': data.get('availableSeats1A') or 0,
            'Available_Seats_CC': data.get('availableSeatsCC') or 0,
        }
        result = cloudscale_repo.create_record(TABLES['train_inventory'], inventory_data)
        if result.get('success'):
            return jsonify({'status': 'success', 'data': result.get('data')}), 201
        return jsonify({'status': 'error', 'message': 'Failed to create inventory'}), 500
    except Exception as e:
        logger.exception(f'Create inventory error: {e}')
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


@inventory_bp.route('/inventory/<inventory_id>', methods=['PUT'])
@require_permission('trains', 'edit')
def update_inventory(inventory_id):
    """Update inventory (admin only)."""
    data = request.get_json(silent=True) or {}
    try:
        update_data = {}
        field_mapping = {
            'availableSeatsSL': 'Available_Seats_SL',
            'availableSeats3A': 'Available_Seats_3A',
            'availableSeats2A': 'Available_Seats_2A',
            'availableSeats1A': 'Available_Seats_1A',
            'availableSeatsCC': 'Available_Seats_CC',
        }
        for client_key, db_key in field_mapping.items():
            if client_key in data:
                update_data[db_key] = data[client_key]

        if not update_data:
            return jsonify({'status': 'error', 'message': 'No fields to update'}), 400

        result = cloudscale_repo.update_record(TABLES['train_inventory'], inventory_id, update_data)
        if result.get('success'):
            return jsonify({'status': 'success', 'message': 'Inventory updated'}), 200
        return jsonify({'status': 'error', 'message': 'Failed to update inventory'}), 500
    except Exception as e:
        logger.exception(f'Update inventory error: {e}')
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


@inventory_bp.route('/inventory/<inventory_id>', methods=['DELETE'])
@require_permission('trains', 'delete')
def delete_inventory(inventory_id):
    """Delete inventory (admin only)."""
    try:
        result = cloudscale_repo.delete_record(TABLES['train_inventory'], inventory_id)
        if result.get('success'):
            return jsonify({'status': 'success', 'message': 'Inventory deleted'}), 200
        return jsonify({'status': 'error', 'message': 'Failed to delete inventory'}), 500
    except Exception as e:
        logger.exception(f'Delete inventory error: {e}')
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500
