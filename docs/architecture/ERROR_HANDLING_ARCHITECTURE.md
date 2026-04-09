# Error Handling Architecture

**Last Updated**: April 9, 2026  
**Status**: Implemented (Backend)

---

## Purpose

Define a standard, enterprise-style error handling architecture for the Smart Railway backend so that:

- every failed request returns a consistent API error payload,
- every request can be traced with a correlation ID,
- critical server-side failures are persisted for investigation,
- sensitive internals are not exposed to clients.

---

## Design Goals

1. Consistent client contract for all errors.
2. Request-level traceability with `request_id`.
3. Centralized error processing in one place.
4. Controlled persistence (store meaningful failures, avoid log noise).
5. Zero functional regression for existing routes.

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Incoming HTTP Request                        │
└─────────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
                  before_request: ensure_request_id()
                                 │
                                 ▼
                         Route / Service Logic
                                 │
                   ┌─────────────┴─────────────┐
                   │                           │
                   ▼                           ▼
              Success Path                 Exception Path
                   │                           │
                   │               Flask Error Handlers (Global)
                   │               - RailwayException handler
                   │               - Generic Exception handler
                   │               - 404 / 405 handlers
                   │                           │
                   │                           ▼
                   │         record_application_error(...)
                   │                           │
                   │                           ▼
                   │             Session_Audit_Log (APPLICATION_ERROR)
                   │
                   ▼
         after_request: attach X-Request-ID header
                                 │
                                 ▼
                       Standard JSON API Response
```

---

## Core Components

### 1) Global Error Handling Layer

Implemented in Flask app setup:

- Handles `RailwayException` with structured status + error_code.
- Handles unknown `Exception` as `INTERNAL_SERVER_ERROR` (HTTP 500).
- Handles 404 and 405 with standardized payload.

Standard response shape:

```json
{
  "status": "error",
  "message": "Internal server error",
  "error_code": "INTERNAL_SERVER_ERROR",
  "request_id": "9f71e3e5a4f648a8a7e07158fb5fb730"
}
```

### 2) Request Correlation (Traceability)

Centralized request ID management:

- `ensure_request_id()` creates/propagates per-request ID.
- `attach_request_id_header()` adds `X-Request-ID` to all responses.
- Error payload includes the same `request_id`.

This enables support/debug teams to trace a user error response to backend logs and audit entries quickly.

### 3) Central Error Tracking Utility

`core/error_tracking.py` provides:

- request ID lifecycle,
- severity derivation,
- safe payload truncation,
- persistence control threshold via `ERROR_AUDIT_MIN_STATUS`.

### 4) Persistence Strategy (Table Logging)

Critical errors are persisted as audit events using existing session audit infrastructure:

- Event type: `APPLICATION_ERROR`
- Storage table: `Session_Audit_Log` (via existing `log_audit_event` path)
- Default persistence threshold: HTTP `>= 500`

Stored details include:

- `request_id`, `status_code`, `error_code`
- route path, method, endpoint
- exception type and safe exception text
- user context when available (`user_id`, `user_email`, `session_id`)
- client metadata (`ip_address`, `user_agent`)

---

## Error Processing Flow (Step-by-Step)

1. Request enters API.
2. `before_request` ensures `request_id` exists.
3. Route/service executes.
4. If exception occurs, global error handler maps it to status + error_code.
5. Handler calls `record_application_error(...)`.
6. Utility writes `APPLICATION_ERROR` event to `Session_Audit_Log` (based on threshold).
7. API responds with standardized JSON body including `request_id`.
8. `after_request` adds `X-Request-ID` header.

---

## Enterprise Alignment

This architecture follows enterprise backend patterns:

1. **Centralized exception boundary** instead of scattered per-route handling.
2. **Correlation ID everywhere** (response, logs, persistence).
3. **Standard API contract** for frontends and support tooling.
4. **Controlled persistence policy** (not every client 4xx becomes a DB write by default).
5. **PII/secret safety** by storing safe summaries, not raw sensitive payloads.

---

## Configuration

Environment setting:

- `ERROR_AUDIT_MIN_STATUS`
  - Default: `500`
  - Meaning: only errors with status code >= this value are persisted.
  - Example: set to `400` if you want broader capture including client-side failures.

---

## Current File Map

- `functions/smart_railway_app_function/core/error_tracking.py`
- `functions/smart_railway_app_function/main.py`
- `functions/smart_railway_app_function/services/session_service.py` (existing audit write path)

---

## Operational Query Pattern

Typical production debugging workflow:

1. Collect `request_id` from client error response.
2. Search centralized logs by `request_id`.
3. Query `Session_Audit_Log` for `APPLICATION_ERROR` with matching details.
4. Use route, error_code, and exception_type for root-cause isolation.

---

## Future Enhancements

1. Add dedicated `Application_Errors` table for long-term analytics and deduplication.
2. Add alerting hooks for repeated `error_code` spikes.
3. Add admin endpoint to filter recent `APPLICATION_ERROR` events.
4. Add automated masking policy for additional sensitive fields.
