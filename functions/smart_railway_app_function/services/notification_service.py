"""
Notification Service - Smart Railway Ticketing System

Handles in-app notifications (bell + inbox) for both users and employees.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Set

from config import TABLES
from repositories.cloudscale_repository import cloudscale_repo, CriteriaBuilder

logger = logging.getLogger(__name__)


def _now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _safe_int(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _build_cutoff(days: int) -> str:
    if days < 1:
        days = 1
    return (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()


def _recipient_row_to_id(recipient: Dict[str, Any]) -> Optional[int]:
    rowid = recipient.get("ROWID")
    if rowid is None:
        return None
    try:
        return int(rowid)
    except (TypeError, ValueError):
        return None


def _normalize_roles(audience_roles: Any) -> List[str]:
    if audience_roles is None:
        return []
    if isinstance(audience_roles, list):
        vals = audience_roles
    elif isinstance(audience_roles, str):
        raw = audience_roles.strip()
        if not raw:
            return []
        try:
            parsed = json.loads(raw)
            vals = parsed if isinstance(parsed, list) else [raw]
        except Exception:
            vals = [p.strip() for p in raw.split(",") if p.strip()]
    else:
        return []

    out: List[str] = []
    seen: Set[str] = set()
    for role in vals:
        v = str(role).strip()
        if not v:
            continue
        key = v.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(v)
    return out


def _notification_to_response(row: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": row.get("ROWID"),
        "title": row.get("Title", ""),
        "message": row.get("Message", ""),
        "notificationType": row.get("Notification_Type", "info"),
        "audienceSource": row.get("Audience_Source", "system"),
        "sourceId": row.get("Source_ID"),
        "actionUrl": row.get("Action_URL"),
        "isRead": _normalize_bool(row.get("Is_Read")),
        "createdAt": row.get("Created_At"),
        "readAt": row.get("Read_At"),
        "expiresAt": row.get("Expires_At"),
    }


def create_notification(
    *,
    recipient_type: str,
    recipient_id: int,
    title: str,
    message: str,
    notification_type: str = "info",
    audience_source: str = "system",
    source_id: Optional[str] = None,
    action_url: Optional[str] = None,
    expires_at: Optional[str] = None,
) -> Dict[str, Any]:
    now_iso = _now_utc_iso()
    payload: Dict[str, Any] = {
        "Recipient_Type": recipient_type,
        "Recipient_ID": int(recipient_id),
        "Audience_Source": audience_source,
        "Title": title,
        "Message": message,
        "Notification_Type": notification_type,
        "Is_Read": "false",
        "Created_At": now_iso,
    }
    if source_id:
        payload["Source_ID"] = str(source_id)
    if action_url:
        payload["Action_URL"] = action_url
    if expires_at:
        payload["Expires_At"] = expires_at

    return cloudscale_repo.create_record(TABLES["notifications"], payload)


def list_notifications(
    *,
    recipient_type: str,
    recipient_id: int,
    days: int = 30,
    limit: int = 10,
    offset: int = 0,
    unread_only: bool = False,
    source_type: Optional[str] = None,
) -> Dict[str, Any]:
    days = max(1, min(_safe_int(days, 30), 365))
    limit = max(1, min(_safe_int(limit, 10), 50))
    offset = max(0, _safe_int(offset, 0))
    cutoff_iso = _build_cutoff(days)

    criteria = CriteriaBuilder() \
        .eq("Recipient_Type", recipient_type) \
        .id_eq("Recipient_ID", int(recipient_id)) \
        .gte("Created_At", cutoff_iso)

    if unread_only:
        criteria.eq("Is_Read", "false")
    if source_type:
        criteria.eq("Audience_Source", source_type)

    where = criteria.build() or "1 = 1"
    table = TABLES["notifications"]
    query = (
        "SELECT ROWID, Recipient_Type, Recipient_ID, Audience_Source, Source_ID, Title, Message, "
        "Notification_Type, Action_URL, Is_Read, Read_At, Created_At, Expires_At "
        f"FROM {table} WHERE {where} ORDER BY Created_At DESC LIMIT {limit} OFFSET {offset}"
    )

    result = cloudscale_repo.execute_query(query)
    if not result.get("success"):
        return {"success": False, "error": result.get("error", "Failed to list notifications")}

    rows = result.get("data", {}).get("data", []) or []
    items = [_notification_to_response(row) for row in rows]
    has_more = len(items) == limit
    return {"success": True, "data": {"items": items, "limit": limit, "offset": offset, "hasMore": has_more}}


def get_unread_count(*, recipient_type: str, recipient_id: int, days: int = 30) -> Dict[str, Any]:
    days = max(1, min(_safe_int(days, 30), 365))
    cutoff_iso = _build_cutoff(days)
    table = TABLES["notifications"]
    criteria = CriteriaBuilder() \
        .eq("Recipient_Type", recipient_type) \
        .id_eq("Recipient_ID", int(recipient_id)) \
        .eq("Is_Read", "false") \
        .gte("Created_At", cutoff_iso) \
        .build()
    query = f"SELECT COUNT(ROWID) as count FROM {table} WHERE {criteria}"
    result = cloudscale_repo.execute_query(query)
    if not result.get("success"):
        return {"success": False, "error": result.get("error", "Failed to count unread notifications")}

    rows = result.get("data", {}).get("data", []) or []
    count = _safe_int(rows[0].get("count"), 0) if rows else 0
    return {"success": True, "data": {"unread": count}}


def mark_notification_read(*, recipient_type: str, recipient_id: int, notification_id: int) -> Dict[str, Any]:
    criteria = CriteriaBuilder() \
        .id_eq("ROWID", int(notification_id)) \
        .eq("Recipient_Type", recipient_type) \
        .id_eq("Recipient_ID", int(recipient_id)) \
        .build()
    table = TABLES["notifications"]
    query = f"SELECT ROWID, Is_Read FROM {table} WHERE {criteria} LIMIT 1"
    result = cloudscale_repo.execute_query(query)
    if not result.get("success"):
        return {"success": False, "error": result.get("error", "Failed to find notification")}

    rows = result.get("data", {}).get("data", []) or []
    if not rows:
        return {"success": False, "status_code": 404, "error": "Notification not found"}

    update = {
        "Is_Read": "true",
        "Read_At": _now_utc_iso(),
    }
    return cloudscale_repo.update_record(table, str(notification_id), update)


def mark_all_read(*, recipient_type: str, recipient_id: int, days: int = 30) -> Dict[str, Any]:
    days = max(1, min(_safe_int(days, 30), 365))
    cutoff_iso = _build_cutoff(days)
    table = TABLES["notifications"]
    criteria = CriteriaBuilder() \
        .eq("Recipient_Type", recipient_type) \
        .id_eq("Recipient_ID", int(recipient_id)) \
        .eq("Is_Read", "false") \
        .gte("Created_At", cutoff_iso) \
        .build()

    query = f"SELECT ROWID FROM {table} WHERE {criteria} LIMIT 500"
    result = cloudscale_repo.execute_query(query)
    if not result.get("success"):
        return {"success": False, "error": result.get("error", "Failed to load unread notifications")}

    rows = result.get("data", {}).get("data", []) or []
    updated = 0
    read_at = _now_utc_iso()
    for row in rows:
        rid = row.get("ROWID")
        if rid is None:
            continue
        upd = cloudscale_repo.update_record(table, str(rid), {"Is_Read": "true", "Read_At": read_at})
        if upd.get("success"):
            updated += 1

    return {"success": True, "data": {"updated": updated}}


def delete_notification(*, recipient_type: str, recipient_id: int, notification_id: int) -> Dict[str, Any]:
    table = TABLES["notifications"]
    criteria = CriteriaBuilder() \
        .id_eq("ROWID", int(notification_id)) \
        .eq("Recipient_Type", recipient_type) \
        .id_eq("Recipient_ID", int(recipient_id)) \
        .build()
    query = f"SELECT ROWID FROM {table} WHERE {criteria} LIMIT 1"
    result = cloudscale_repo.execute_query(query)
    if not result.get("success"):
        return {"success": False, "error": result.get("error", "Failed to find notification")}

    rows = result.get("data", {}).get("data", []) or []
    if not rows:
        return {"success": False, "status_code": 404, "error": "Notification not found"}

    return cloudscale_repo.delete_record(table, str(notification_id))


def _get_target_user_ids() -> List[int]:
    query = (
        f"SELECT ROWID FROM {TABLES['users']} "
        "WHERE Account_Status = 'Active' ORDER BY ROWID DESC LIMIT 2000"
    )
    result = cloudscale_repo.execute_query(query)
    if not result.get("success"):
        logger.error("Failed to load users for notification fanout: %s", result.get("error"))
        return []
    rows = result.get("data", {}).get("data", []) or []
    out: List[int] = []
    for row in rows:
        rid = _recipient_row_to_id(row)
        if rid is not None:
            out.append(rid)
    return out


def _get_target_employee_ids(audience_roles: Optional[List[str]]) -> List[int]:
    criteria = CriteriaBuilder().eq("Account_Status", "Active")
    if audience_roles:
        criteria.is_in("Role", audience_roles)
    where = criteria.build() or "1 = 1"
    query = (
        f"SELECT ROWID FROM {TABLES['employees']} "
        f"WHERE {where} ORDER BY ROWID DESC LIMIT 2000"
    )
    result = cloudscale_repo.execute_query(query)
    if not result.get("success"):
        logger.error("Failed to load employees for notification fanout: %s", result.get("error"))
        return []
    rows = result.get("data", {}).get("data", []) or []
    out: List[int] = []
    for row in rows:
        rid = _recipient_row_to_id(row)
        if rid is not None:
            out.append(rid)
    return out


def create_announcement_notifications(
    *,
    announcement_id: Any,
    title: str,
    message: str,
    audience_type: str = "both",
    audience_roles: Optional[Any] = None,
) -> Dict[str, Any]:
    normalized_audience = (audience_type or "both").strip().lower()
    if normalized_audience not in {"user", "employee", "both"}:
        normalized_audience = "both"
    roles = _normalize_roles(audience_roles)

    user_ids: List[int] = []
    employee_ids: List[int] = []
    if normalized_audience in {"user", "both"}:
        user_ids = _get_target_user_ids()
    if normalized_audience in {"employee", "both"}:
        employee_ids = _get_target_employee_ids(roles)

    source_id = str(announcement_id)
    created = 0
    failed = 0

    for uid in user_ids:
        res = create_notification(
            recipient_type="user",
            recipient_id=uid,
            title=title,
            message=message,
            notification_type="info",
            audience_source="announcement",
            source_id=source_id,
            action_url="/admin/announcements",
        )
        if res.get("success"):
            created += 1
        else:
            failed += 1

    for eid in employee_ids:
        res = create_notification(
            recipient_type="employee",
            recipient_id=eid,
            title=title,
            message=message,
            notification_type="info",
            audience_source="announcement",
            source_id=source_id,
            action_url="/admin/announcements",
        )
        if res.get("success"):
            created += 1
        else:
            failed += 1

    return {
        "success": True,
        "data": {
            "created": created,
            "failed": failed,
            "audienceType": normalized_audience,
            "audienceRoles": roles,
        },
    }
