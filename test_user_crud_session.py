#!/usr/bin/env python3
""" 
Authenticated Users CRUD smoke test (session-cookie + CSRF).

Flow:
1) Ensure an admin employee exists (data-seed)
2) Admin login (employee session)
3) Admin creates a passenger user (POST /users)
4) Admin reads + updates the passenger user
5) Passenger logs in and exercises /users/me (GET/PUT/DELETE)
6) Admin verifies passenger is Suspended after delete

Run:
  python test_user_crud_session.py

Env overrides:
  BASE_URL=http://localhost:3000/server/smart_railway_app_function
  TEST_ADMIN_EMAIL=admin@railway.com
  TEST_ADMIN_PASSWORD=Admin@123
"""

import json
import os
import time
from typing import Any, Dict, Optional

import requests

BASE_URL = os.getenv("BASE_URL", "http://localhost:3000/server/smart_railway_app_function").rstrip("/")
ADMIN_EMAIL = os.getenv("TEST_ADMIN_EMAIL", "admin@railway.com").strip().lower()
ADMIN_PASSWORD = os.getenv("TEST_ADMIN_PASSWORD", "Admin@123")


def _pretty(obj: Any) -> str:
    try:
        return json.dumps(obj, indent=2)
    except Exception:
        return str(obj)


def _fail(msg: str) -> None:
    print(f"FAIL: {msg}")
    raise SystemExit(1)


def _extract_csrf(payload: Dict[str, Any]) -> Optional[str]:
    data = payload.get("data") or {}
    if not isinstance(data, dict):
        return None
    return data.get("csrfToken") or data.get("csrf_token")


def _extract_user_rowid(payload: Dict[str, Any]) -> Optional[str]:
    data = payload.get("data") or {}
    if not isinstance(data, dict):
        return None
    return str(data.get("ROWID") or data.get("rowid") or data.get("id") or "").strip() or None


def _require_status(resp: requests.Response, allowed_statuses) -> Dict[str, Any]:
    if resp.status_code not in allowed_statuses:
        try:
            body = resp.json()
        except Exception:
            body = resp.text
        _fail(f"Unexpected status {resp.status_code} for {resp.request.method} {resp.request.url}\n{_pretty(body)}")

    try:
        return resp.json()
    except Exception:
        return {}


def main() -> None:
    print(f"BASE_URL: {BASE_URL}")

    admin = requests.Session()

    # 1) Ensure admin employee exists
    seed_payload = {
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD,
        "full_name": "System Admin",
        "department": "Administration",
        "designation": "System Administrator",
    }
    seed_resp = admin.post(f"{BASE_URL}/data-seed/admin-employee", json=seed_payload)
    _require_status(seed_resp, (201, 409))

    # 2) Admin login (employee)
    login_resp = admin.post(
        f"{BASE_URL}/session/employee/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        headers={"Content-Type": "application/json"},
    )
    login_json = _require_status(login_resp, (200,))
    admin_csrf = _extract_csrf(login_json)
    if not admin_csrf:
        _fail(f"Admin login missing csrfToken: {_pretty(login_json)}")

    admin_headers = {"Content-Type": "application/json", "X-CSRF-Token": admin_csrf}

    # 3) Admin creates passenger user
    suffix = str(int(time.time()))
    passenger_email = f"crud_passenger_{suffix}@example.com"
    passenger_password = "SecurePass123!"

    create_resp = admin.post(
        f"{BASE_URL}/users",
        json={
            "fullName": "CRUD Passenger",
            "email": passenger_email,
            "password": passenger_password,
            "phoneNumber": "+91-9000000009",
            "role": "USER",
        },
        headers=admin_headers,
    )
    create_json = _require_status(create_resp, (201,))
    passenger_rowid = _extract_user_rowid(create_json)
    if not passenger_rowid:
        _fail(f"Create user missing ROWID: {_pretty(create_json)}")

    print(f"Created passenger user ROWID={passenger_rowid}, email={passenger_email}")

    # 4) Admin READ + UPDATE
    read_resp = admin.get(f"{BASE_URL}/users/{passenger_rowid}")
    read_json = _require_status(read_resp, (200,))
    if (read_json.get("data") or {}).get("Password") is not None:
        _fail("Password leaked in GET /users/<id> response")

    upd_resp = admin.put(
        f"{BASE_URL}/users/{passenger_rowid}",
        json={"address": "Test Address", "phoneNumber": "+91-9111111111"},
        headers=admin_headers,
    )
    _require_status(upd_resp, (200,))

    # 5) Passenger login and /users/me CRUD
    passenger = requests.Session()
    p_login_resp = passenger.post(
        f"{BASE_URL}/session/login",
        json={"email": passenger_email, "password": passenger_password},
        headers={"Content-Type": "application/json"},
    )
    p_login_json = _require_status(p_login_resp, (200,))
    passenger_csrf = _extract_csrf(p_login_json)
    if not passenger_csrf:
        _fail(f"Passenger login missing csrfToken: {_pretty(p_login_json)}")

    passenger_headers = {"Content-Type": "application/json", "X-CSRF-Token": passenger_csrf}

    me_resp = passenger.get(f"{BASE_URL}/users/me")
    me_json = _require_status(me_resp, (200,))
    me_id = str((me_json.get("data") or {}).get("id") or "")

    if me_id and me_id != str(passenger_rowid):
        _fail(f"/users/me returned different user. expected={passenger_rowid} got={me_id}")

    me_upd = passenger.put(
        f"{BASE_URL}/users/me",
        json={"address": "Passenger Self Updated Address"},
        headers=passenger_headers,
    )
    _require_status(me_upd, (200,))

    me_del = passenger.delete(
        f"{BASE_URL}/users/me",
        headers=passenger_headers,
    )
    _require_status(me_del, (200,))

    # 6) Admin verifies Suspended
    verify_resp = admin.get(f"{BASE_URL}/users/{passenger_rowid}")
    verify_json = _require_status(verify_resp, (200,))
    status = (verify_json.get("data") or {}).get("accountStatus")
    if status != "Suspended":
        _fail(f"Expected accountStatus='Suspended' after delete, got: {status}\n{_pretty(verify_json)}")

    print("OK: authenticated user CRUD flow passed")


if __name__ == "__main__":
    main()
