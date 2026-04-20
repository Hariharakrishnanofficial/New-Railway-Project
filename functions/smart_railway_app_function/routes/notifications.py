"""
Notifications Routes - In-app notifications APIs for session-authenticated users.
"""

from __future__ import annotations

import logging

from flask import Blueprint, jsonify, request, g

from core.session_middleware import require_session
from services.notification_service import (
    list_notifications,
    get_unread_count,
    mark_notification_read,
    mark_all_read,
    delete_notification,
)

logger = logging.getLogger(__name__)
notifications_bp = Blueprint("notifications", __name__)


def _param_int(name: str, default: int) -> int:
    raw = request.args.get(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except (TypeError, ValueError):
        return default


def _param_bool(name: str, default: bool = False) -> bool:
    raw = request.args.get(name)
    if raw is None:
        return default
    return str(raw).strip().lower() in {"1", "true", "yes", "y"}


@notifications_bp.route("/notifications", methods=["GET"])
@require_session
def get_notifications():
    try:
        days = _param_int("days", 30)
        limit = _param_int("limit", 10)
        offset = _param_int("offset", 0)
        unread_only = _param_bool("unreadOnly", False)
        source_type = (request.args.get("type") or "").strip() or None

        result = list_notifications(
            recipient_type=g.user_type,
            recipient_id=int(g.user_id),
            days=days,
            limit=limit,
            offset=offset,
            unread_only=unread_only,
            source_type=source_type,
        )
        if not result.get("success"):
            return jsonify({"status": "error", "message": result.get("error", "Failed to fetch notifications")}), 500

        return jsonify({"status": "success", "data": result["data"]}), 200
    except Exception as exc:
        logger.exception("Get notifications error: %s", exc)
        return jsonify({"status": "error", "message": "Internal server error"}), 500


@notifications_bp.route("/notifications/unread-count", methods=["GET"])
@require_session
def get_notifications_unread_count():
    try:
        days = _param_int("days", 30)
        result = get_unread_count(
            recipient_type=g.user_type,
            recipient_id=int(g.user_id),
            days=days,
        )
        if not result.get("success"):
            return jsonify({"status": "error", "message": result.get("error", "Failed to fetch unread count")}), 500

        return jsonify({"status": "success", "data": result["data"]}), 200
    except Exception as exc:
        logger.exception("Unread count error: %s", exc)
        return jsonify({"status": "error", "message": "Internal server error"}), 500


@notifications_bp.route("/notifications/<notification_id>/read", methods=["PUT"])
@require_session
def mark_read(notification_id: str):
    try:
        result = mark_notification_read(
            recipient_type=g.user_type,
            recipient_id=int(g.user_id),
            notification_id=int(notification_id),
        )
        if not result.get("success"):
            status_code = int(result.get("status_code") or 500)
            message = result.get("error", "Failed to mark as read")
            return jsonify({"status": "error", "message": message}), status_code

        return jsonify({"status": "success", "message": "Marked as read"}), 200
    except ValueError:
        return jsonify({"status": "error", "message": "Invalid notification id"}), 400
    except Exception as exc:
        logger.exception("Mark read error: %s", exc)
        return jsonify({"status": "error", "message": "Internal server error"}), 500


@notifications_bp.route("/notifications/read-all", methods=["PUT"])
@require_session
def mark_all_read_endpoint():
    try:
        days = _param_int("days", 30)
        result = mark_all_read(
            recipient_type=g.user_type,
            recipient_id=int(g.user_id),
            days=days,
        )
        if not result.get("success"):
            return jsonify({"status": "error", "message": result.get("error", "Failed to mark all as read")}), 500

        return jsonify({"status": "success", "data": result["data"]}), 200
    except Exception as exc:
        logger.exception("Mark all read error: %s", exc)
        return jsonify({"status": "error", "message": "Internal server error"}), 500


@notifications_bp.route("/notifications/<notification_id>", methods=["DELETE"])
@require_session
def delete_notification_endpoint(notification_id: str):
    try:
        result = delete_notification(
            recipient_type=g.user_type,
            recipient_id=int(g.user_id),
            notification_id=int(notification_id),
        )
        if not result.get("success"):
            status_code = int(result.get("status_code") or 500)
            message = result.get("error", "Failed to delete notification")
            return jsonify({"status": "error", "message": message}), status_code

        return jsonify({"status": "success", "message": "Deleted"}), 200
    except ValueError:
        return jsonify({"status": "error", "message": "Invalid notification id"}), 400
    except Exception as exc:
        logger.exception("Delete notification error: %s", exc)
        return jsonify({"status": "error", "message": "Internal server error"}), 500
