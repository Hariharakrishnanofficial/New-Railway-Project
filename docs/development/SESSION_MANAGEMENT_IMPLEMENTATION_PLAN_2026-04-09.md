# Session Management Implementation Plan and Changes
Date: 2026-04-09
Scope: Backend session lifecycle hardening with backward-compatible behavior.

## Goal
Implement session-ID flow hardening without changing public API contracts or breaking existing login/session workflows.

## Implemented Plan (Status)
1. Normalize session identifier handling (signed cookie vs raw DB Session_ID): Implemented
2. Ensure CSRF/session operations always use raw Session_ID internally: Implemented
3. Fix logout revocation path to revoke server-side record reliably: Implemented
4. Harden session secret configuration in production only: Implemented
5. Increase session ID entropy within BIGINT schema constraints: Implemented
6. Preserve compatibility for existing cookie/header flows: Implemented

## Files Changed
- functions/smart_railway_app_function/services/session_service.py
- functions/smart_railway_app_function/core/session_middleware.py
- functions/smart_railway_app_function/config.py

## Detailed Changes

### 1) Session ID Normalization (Core Fix)
Problem:
- Session cookie stores signed value: value.signature
- Database stores raw Session_ID
- Some operations used signed value against DB fields expecting raw value

Implementation:
- Added extract_raw_session_id(session_id_or_signed) in session_service.py.
- Behavior:
  - If input looks signed (contains '.'), verify + unsign.
  - If input is raw (legacy/header fallback), pass through.
  - Return None if invalid.

Why this is safe:
- No endpoint contract changed.
- Existing signed cookie flow continues.
- Legacy Authorization: Session <raw_id> remains functional.

### 2) Validate Session Uses Normalization
Problem:
- validate_session previously always unsign_cookie(input), which rejects raw fallback values.

Implementation:
- validate_session now uses extract_raw_session_id.
- It accepts both signed and raw input formats.
- Returns same response shape, with session_id as raw DB Session_ID.

### 3) CSRF Validation Uses Raw Session_ID
Problem:
- Middleware sometimes passed signed session string to validate_csrf_token.
- validate_csrf_token query uses Session_ID in DB (raw), causing mismatch risk.

Implementation:
- Middleware now derives raw_session_id from validated session_data.
- Middleware passes raw_session_id into validate_csrf_token.
- validate_csrf_token also defensively normalizes input using extract_raw_session_id.

Impact:
- State-changing requests (POST/PUT/DELETE/PATCH) validate reliably.

### 4) Request Context Stores Raw Session_ID
Problem:
- g.session_id previously held signed cookie string.
- Session management endpoints compare against raw Session_ID in DB records.

Implementation:
- In require_session/require_session_admin/require_session_employee/optional_session, g.session_id now stores raw Session_ID.

Impact:
- Current-session detection is accurate.
- Revoke-all excluding current session works correctly.
- CSRF regeneration endpoint works reliably with current context ID.

### 5) Logout Revocation Reliability
Problem:
- Logout path passed cookie value directly to revoke_session.
- If cookie value is signed and revoke path expects raw DB ID, record may not be revoked.

Implementation:
- revoke_session now normalizes input (signed or raw) before revoking.

Impact:
- Logout reliably revokes server-side session record and still clears browser cookie.

### 6) SESSION_SECRET Hardening (Production)
Problem:
- Weak/default fallback secret could be used if environment is misconfigured.

Implementation:
- In config.py, production startup now enforces SESSION_SECRET:
  - Must be present
  - Must not be default string
  - Must be at least 32 characters
- Development behavior remains unchanged.

Impact:
- Prevents weak-signature deployment in production.

### 7) Session ID Entropy Increase (Within BIGINT)
Problem:
- Session ID generation used 62 random bits.

Implementation:
- Increased to 63 random bits (max signed BIGINT-safe range 0..2^63-1).

Impact:
- Entropy doubled from 2^62 to 2^63 possibilities.
- No schema change required.

## Double Flow (Two End-to-End Examples)

### Flow A: Passenger Login + Protected Update
1. Client POST /session/login with email/password.
2. Backend creates raw Session_ID in DB and returns signed cookie value.
3. Client later sends POST /session/profile with cookie + X-CSRF-Token.
4. Middleware validates signed cookie, extracts raw Session_ID, validates CSRF with raw ID.
5. Update succeeds.

Example:
- Cookie received by client: railway_sid=1234567890.abcd1234...
- Raw ID in DB: 1234567890
- CSRF lookup uses raw DB ID 1234567890 (not signed string).

### Flow B: Employee Login + Revoke-All-Except-Current
1. Client POST /session/employee/login.
2. Backend sets signed session cookie, stores raw Session_ID in Sessions table.
3. Employee calls POST /session/sessions/revoke-all.
4. Middleware stores raw Session_ID in request context.
5. Service revokes all sessions for user except current raw Session_ID.

Example:
- Current cookie: 9876543210.ffffeeee...
- Context current session: 9876543210
- Revoke loop compares DB Session_ID values against 9876543210.
- Current session remains active; others revoked.

## Compatibility Notes
- No route names changed.
- No response payload contract changed.
- No frontend API surface change required.
- Legacy raw session fallback remains supported.

## Risk and Rollback
- Risk level: Low-to-medium (auth-sensitive paths, but compatibility-preserving).
- Rollback strategy:
  - Revert the three changed files to previous commit if needed.
  - No data migration required.

## Validation Checklist
- Signed cookie login still works for passengers and employees.
- Protected POST/PUT/PATCH/DELETE with CSRF token works.
- Logout revokes server-side session and clears cookie.
- Revoke-all keeps current session active.
- Production fails fast on weak SESSION_SECRET.
- Development startup remains unaffected.
