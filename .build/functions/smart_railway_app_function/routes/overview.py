"""
Overview Routes - Dashboard statistics and system overview.
"""

import logging
from flask import Blueprint, jsonify
from datetime import datetime, timedelta

from repositories.cloudscale_repository import cloudscale_repo
from config import TABLES
from core.security import require_admin

logger = logging.getLogger(__name__)
overview_bp = Blueprint('overview', __name__)


def _safe_count(query: str) -> int:
    """Execute a COUNT query and return the count safely."""
    try:
        result = cloudscale_repo.execute_query(query)
        if result.get('success'):
            rows = result.get('data', {}).get('data', [])
            if rows:
                # Handle both 'count' and 'COUNT(ROWID)' keys
                row = rows[0]
                return row.get('count', row.get('COUNT(ROWID)', 0)) or 0
        return 0
    except Exception as e:
        logger.warning(f'Count query failed: {e}')
        return 0


def _safe_sum(query: str, field: str = 'total') -> float:
    """Execute a SUM query and return the sum safely."""
    try:
        result = cloudscale_repo.execute_query(query)
        if result.get('success'):
            rows = result.get('data', {}).get('data', [])
            if rows:
                return float(rows[0].get(field, 0) or 0)
        return 0.0
    except Exception as e:
        logger.warning(f'Sum query failed: {e}')
        return 0.0


@overview_bp.route('/overview/stats', methods=['GET'])
@require_admin
def get_stats():
    """Get dashboard statistics."""
    try:
        # Get counts for main entities
        users_count = _safe_count(f"SELECT COUNT(ROWID) as count FROM {TABLES['users']}")
        admins_count = _safe_count(f"SELECT COUNT(ROWID) as count FROM {TABLES['users']} WHERE Role = 'Admin'")
        trains_count = _safe_count(f"SELECT COUNT(ROWID) as count FROM {TABLES['trains']}")
        stations_count = _safe_count(f"SELECT COUNT(ROWID) as count FROM {TABLES['stations']}")
        
        # Booking stats
        total_bookings = _safe_count(f"SELECT COUNT(ROWID) as count FROM {TABLES['bookings']}")
        confirmed_bookings = _safe_count(
            f"SELECT COUNT(ROWID) as count FROM {TABLES['bookings']} WHERE Booking_Status = 'Confirmed'"
        )
        cancelled_bookings = _safe_count(
            f"SELECT COUNT(ROWID) as count FROM {TABLES['bookings']} WHERE Booking_Status = 'Cancelled'"
        )
        pending_bookings = _safe_count(
            f"SELECT COUNT(ROWID) as count FROM {TABLES['bookings']} WHERE Booking_Status = 'Pending'"
        )
        
        # Today's bookings
        today = datetime.utcnow().strftime('%Y-%m-%d')
        todays_bookings = _safe_count(
            f"SELECT COUNT(ROWID) as count FROM {TABLES['bookings']} WHERE Created_At LIKE '{today}%'"
        )
        
        # Revenue (sum of Total_Fare for confirmed bookings)
        total_revenue = _safe_sum(
            f"SELECT SUM(Total_Fare) as total FROM {TABLES['bookings']} WHERE Booking_Status = 'Confirmed'",
            'total'
        )
        
        # Today's revenue
        todays_revenue = _safe_sum(
            f"SELECT SUM(Total_Fare) as total FROM {TABLES['bookings']} "
            f"WHERE Booking_Status = 'Confirmed' AND Created_At LIKE '{today}%'",
            'total'
        )
        
        # Passenger count
        passengers_count = _safe_count(f"SELECT COUNT(ROWID) as count FROM {TABLES['passengers']}")
        
        # Active trains (with Running_Status)
        active_trains = _safe_count(
            f"SELECT COUNT(ROWID) as count FROM {TABLES['trains']} WHERE Status = 'Active'"
        )
        
        # Recent bookings (last 7 days trend)
        booking_trend = []
        for i in range(7):
            date = (datetime.utcnow() - timedelta(days=i)).strftime('%Y-%m-%d')
            count = _safe_count(
                f"SELECT COUNT(ROWID) as count FROM {TABLES['bookings']} WHERE Created_At LIKE '{date}%'"
            )
            booking_trend.append({'date': date, 'count': count})
        
        booking_trend.reverse()  # Chronological order
        
        return jsonify({
            'status': 'success',
            'data': {
                'users': {
                    'total': users_count,
                    'admins': admins_count,
                    'passengers': users_count - admins_count,
                },
                'trains': {
                    'total': trains_count,
                    'active': active_trains,
                },
                'stations': {
                    'total': stations_count,
                },
                'bookings': {
                    'total': total_bookings,
                    'confirmed': confirmed_bookings,
                    'cancelled': cancelled_bookings,
                    'pending': pending_bookings,
                    'today': todays_bookings,
                },
                'passengers': {
                    'total': passengers_count,
                },
                'revenue': {
                    'total': total_revenue,
                    'today': todays_revenue,
                },
                'trends': {
                    'bookings': booking_trend,
                },
            }
        }), 200

    except Exception as e:
        logger.exception(f'Get stats error: {e}')
        return jsonify({'status': 'error', 'message': 'Failed to fetch statistics'}), 500


@overview_bp.route('/overview/recent-bookings', methods=['GET'])
@require_admin
def get_recent_bookings():
    """Get recent bookings for dashboard."""
    try:
        query = f"""
            SELECT ROWID, PNR, User_ID, Train_ID, Source_Station, Destination_Station, 
                   Journey_Date, Total_Fare, Booking_Status, Created_At
            FROM {TABLES['bookings']}
            ORDER BY Created_At DESC
            LIMIT 10
        """
        result = cloudscale_repo.execute_query(query)
        
        if result.get('success'):
            bookings = result.get('data', {}).get('data', [])
            return jsonify({'status': 'success', 'data': bookings}), 200
        
        return jsonify({'status': 'error', 'message': 'Failed to fetch recent bookings'}), 500

    except Exception as e:
        logger.exception(f'Get recent bookings error: {e}')
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


@overview_bp.route('/overview/system-health', methods=['GET'])
@require_admin
def get_system_health():
    """Get system health status."""
    try:
        # Test database connection
        db_ok = False
        try:
            probe = cloudscale_repo.execute_query("SELECT 1 as test")
            db_ok = probe.get('success', False)
        except Exception:
            pass
        
        return jsonify({
            'status': 'success',
            'data': {
                'database': 'healthy' if db_ok else 'unhealthy',
                'api': 'healthy',
                'timestamp': datetime.utcnow().isoformat(),
            }
        }), 200

    except Exception as e:
        logger.exception(f'System health error: {e}')
        return jsonify({'status': 'error', 'message': 'Health check failed'}), 500
