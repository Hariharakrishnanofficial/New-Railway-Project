"""Development-only table inspection & CRUD endpoints.

Registered only when APP_ENVIRONMENT=development.
"""

from __future__ import annotations

import os
from typing import Any, Dict, Optional

from flask import Blueprint, abort, jsonify, request

from config import TABLES
from repositories.cloudscale_repository import CloudScaleRepository


dev_tables_bp = Blueprint("dev_tables", __name__, url_prefix="/dev/tables")


@dev_tables_bp.before_request
def _dev_only_guard():
    if os.getenv("APP_ENVIRONMENT") != "development":
        abort(404)


def _resolve_table_name(name: str) -> str:
    candidate = (name or "").strip()
    if not candidate:
        abort(400)
    return TABLES.get(candidate.lower(), candidate)


def _get_table(table_name: str):
    repo = CloudScaleRepository()
    datastore = repo._get_datastore()
    return datastore.table(table_name)


@dev_tables_bp.get("/")
def list_tables():
    repo = CloudScaleRepository()
    configured = {k: v for k, v in TABLES.items()}

    discovered = []
    try:
        ds = repo._get_datastore()
        for t in ds.get_all_tables() or []:
            try:
                discovered.append(t.to_dict() if hasattr(t, "to_dict") else t)
            except Exception:
                discovered.append(str(t))
    except Exception as exc:
        return jsonify({
            "status": "partial",
            "configured": configured,
            "discovered": [],
            "message": f"Failed to list datastore tables: {exc}",
        }), 200

    return jsonify({
        "status": "success",
        "configured": configured,
        "discovered": discovered,
    }), 200


@dev_tables_bp.get("/<table>/columns")
def get_columns(table: str):
    actual = _resolve_table_name(table)
    t = _get_table(actual)
    cols = t.get_all_columns()
    return jsonify({"status": "success", "table": actual, "columns": cols}), 200


@dev_tables_bp.get("/<table>/rows")
def get_rows(table: str):
    actual = _resolve_table_name(table)
    t = _get_table(actual)

    next_token: Optional[str] = request.args.get("next_token")
    max_rows_raw = request.args.get("max_rows")
    max_rows = None
    if max_rows_raw not in (None, ""):
        try:
            max_rows = int(max_rows_raw)
        except Exception:
            return jsonify({"status": "error", "message": "max_rows must be an integer"}), 400

    out = t.get_paged_rows(next_token=next_token, max_rows=max_rows)
    return jsonify({"status": "success", "table": actual, **out}), 200


@dev_tables_bp.get("/<table>/rows/<row_id>")
def get_row(table: str, row_id: str):
    actual = _resolve_table_name(table)
    t = _get_table(actual)
    row = t.get_row(row_id)
    return jsonify({"status": "success", "table": actual, "row": row}), 200


@dev_tables_bp.post("/<table>/rows")
def insert_row(table: str):
    actual = _resolve_table_name(table)
    t = _get_table(actual)

    payload = request.get_json(silent=True)
    if not payload:
        return jsonify({"status": "error", "message": "JSON body required"}), 400

    if isinstance(payload, list):
        created = t.insert_rows(payload)
    elif isinstance(payload, dict):
        created = t.insert_row(payload)
    else:
        return jsonify({"status": "error", "message": "Body must be an object or array"}), 400

    return jsonify({"status": "success", "table": actual, "created": created}), 201


@dev_tables_bp.patch("/<table>/rows/<row_id>")
def update_row(table: str, row_id: str):
    actual = _resolve_table_name(table)
    t = _get_table(actual)

    payload = request.get_json(silent=True)
    if not isinstance(payload, dict) or not payload:
        return jsonify({"status": "error", "message": "JSON object body required"}), 400

    row: Dict[str, Any] = dict(payload)
    row["ROWID"] = row_id

    updated = t.update_row(row)
    return jsonify({"status": "success", "table": actual, "updated": updated}), 200


@dev_tables_bp.delete("/<table>/rows/<row_id>")
def delete_row(table: str, row_id: str):
    actual = _resolve_table_name(table)
    t = _get_table(actual)
    ok = t.delete_row(row_id)
    return jsonify({"status": "success", "table": actual, "deleted": bool(ok)}), 200
