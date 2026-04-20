"""
Email automation routes for MailBot.
"""

from __future__ import annotations

import logging
import os

from flask import Blueprint, jsonify, request

from core.security import require_admin
from services.email_automation_service import email_automation_service

logger = logging.getLogger(__name__)

email_automation_bp = Blueprint("email_automation", __name__)


def _validate_webhook_secret() -> bool:
    expected = os.getenv("EMAIL_AUTOMATION_WEBHOOK_SECRET", "").strip()
    if not expected:
        return True

    supplied = (
        request.headers.get("X-Mailbot-Secret")
        or request.args.get("secret")
        or (request.get_json(silent=True) or {}).get("secret")
        or ""
    ).strip()
    return supplied == expected


@email_automation_bp.route("/api/email-automation/settings", methods=["GET"])
@require_admin
def get_email_automation_settings():
    settings = email_automation_service.load_settings()
    return jsonify({"success": True, "settings": settings}), 200


@email_automation_bp.route("/api/email-automation/settings", methods=["POST"])
@require_admin
def update_email_automation_settings():
    data = request.get_json(silent=True) or {}
    try:
        settings = email_automation_service.save_settings(data)
        return jsonify({"success": True, "settings": settings}), 200
    except Exception as exc:
        logger.exception(f"Email automation settings update failed: {exc}")
        return jsonify({"success": False, "error": str(exc)}), 500


@email_automation_bp.route("/api/email-automation/threads", methods=["GET"])
@require_admin
def list_email_automation_threads():
    limit = request.args.get("limit", 50, type=int)
    status = (request.args.get("status") or "").strip() or None
    result = email_automation_service.list_threads(limit=limit, status=status)
    return jsonify({"success": True, **result}), 200


@email_automation_bp.route("/api/email-automation/threads/<path:thread_key>", methods=["GET"])
@require_admin
def get_email_automation_thread(thread_key: str):
    thread = email_automation_service.get_thread(thread_key)
    if not thread:
        return jsonify({"success": False, "error": "Thread not found"}), 404
    return jsonify({"success": True, "thread": thread}), 200


@email_automation_bp.route("/api/email-automation/process", methods=["POST"])
@require_admin
def process_email_reply():
    data = request.get_json(silent=True) or {}
    force = bool(data.get("force", False))
    try:
        result = email_automation_service.process_inbound_reply(data, force=force)
        return jsonify(result), 200
    except Exception as exc:
        logger.exception(f"Email automation process failed: {exc}")
        return jsonify({"success": False, "error": str(exc)}), 500


@email_automation_bp.route("/api/email-automation/webhook/inbound", methods=["POST"])
def inbound_email_webhook():
    if not _validate_webhook_secret():
        return jsonify({"success": False, "error": "Invalid webhook secret"}), 401

    data = request.get_json(silent=True) or {}
    try:
        result = email_automation_service.process_inbound_reply(data, force=bool(data.get("force", False)))
        return jsonify(result), 200
    except Exception as exc:
        logger.exception(f"Email automation webhook failed: {exc}")
        return jsonify({"success": False, "error": str(exc)}), 500


@email_automation_bp.route("/api/email-automation/health", methods=["GET"])
@require_admin
def email_automation_health():
    settings = email_automation_service.load_settings()
    threads = email_automation_service.list_threads(limit=200)
    return jsonify({
        "success": True,
        "configured": bool(os.getenv("OPENAI_API_KEY", "").strip()),
        "enabled": bool(settings.get("enabled")),
        "model": settings.get("openai_model"),
        "threads": threads.get("stats", {}),
    }), 200
