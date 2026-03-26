"""
Overview routes — delegates to AnalyticsService (cached, optimized).
"""
from flask import Blueprint, jsonify
from services.analytics_service import analytics_service

overview_bp = Blueprint('overview', __name__)


@overview_bp.route('/api/overview/stats', methods=['GET'])
def overview_stats():
    try:
        stats = analytics_service.get_overview_stats()
        return jsonify({'success': True, 'data': stats}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
