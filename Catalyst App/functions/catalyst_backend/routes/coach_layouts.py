"""
Coach Layouts route — fetches visual seat map data.
"""
from flask import Blueprint, jsonify
from services.zoho_service import zoho
from config import TABLES
from core.security import require_admin
import json

coach_layouts_bp = Blueprint('coach_layouts', __name__, url_prefix='/api/coach-layouts')

@coach_layouts_bp.route('/<layout_name>', methods=['GET'])
@require_admin
def get_coach_layout(layout_name):
    criteria = f'(Layout_Name == "{layout_name}")'
    result = zoho.get_all_records(TABLES['coach_layouts'], criteria=criteria, limit=1)
    
    if not result.get('success'):
        return jsonify({'success': False, 'error': result.get('error', 'Failed to fetch coach layout')}), 500
    
    records = result.get('data', {}).get('data', [])
    if not records:
        return jsonify({'success': False, 'error': f'Coach layout "{layout_name}" not found'}), 404
        
    layout_record = records[0]
    layout_json_str = layout_record.get('Layout_JSON')
    
    if not layout_json_str:
        return jsonify({'success': False, 'error': 'Layout_JSON is empty for this layout'}), 404
        
    try:
        layout_data = json.loads(layout_json_str)
        return jsonify({'success': True, 'data': layout_data})
    except json.JSONDecodeError:
        return jsonify({'success': False, 'error': 'Failed to parse Layout_JSON'}), 500
