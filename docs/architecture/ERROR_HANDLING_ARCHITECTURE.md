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

Critical errors are persisted to a dedicated error table:

- Primary table: `Application_Errors`
- Event code: `APPLICATION_ERROR`
- Default persistence threshold: HTTP `>= 500`

Fallback behavior:

- If `Application_Errors` is not available yet, system falls back to `Session_Audit_Log` using existing audit logging.

Stored details include:

- `request_id`, `status_code`, `error_code`
- route path, method, endpoint
- exception type and safe exception text
- user context when available (`user_id`, `user_email`, `session_id`)
- client metadata (`ip_address`, `user_agent`)

---

## Application_Errors Table Schema

Use the following schema when creating the dedicated error table in CloudScale.

```text
Table: Application_Errors

Required Columns:
- Request_ID        (TEXT, indexed)
- Error_Code        (TEXT, indexed)
- Status_Code       (NUMBER, indexed)
- Message           (TEXT)
- Severity          (TEXT, indexed)
- Created_At        (TEXT/DATETIME, indexed)

Optional Context Columns:
- Exception_Type    (TEXT)
- Exception_Message (TEXT)
- Request_Method    (TEXT)
- Request_Path      (TEXT, indexed)
- Endpoint          (TEXT)
- User_ID           (TEXT, indexed)
- User_Email        (TEXT)
- Session_ID        (TEXT)
- IP_Address        (TEXT)
- User_Agent        (TEXT)
- Error_Details     (TEXT)
```

### Recommended Indexes

1. `Request_ID`
2. `Error_Code`
3. `Status_Code`
4. `Severity`
5. `Request_Path`
6. `Created_At`
7. `User_ID`

### Notes

1. Keep `Error_Details` as JSON string text.
2. Store timestamps in ISO-8601 UTC (for example: `2026-04-09T14:20:11.123456+00:00`).
3. `Request_ID` should be the same value returned in API error responses and `X-Request-ID` header.

---

## Error Processing Flow (Step-by-Step)

1. Request enters API.
2. `before_request` ensures `request_id` exists.
3. Route/service executes.
4. If exception occurs, global error handler maps it to status + error_code.
5. Handler calls `record_application_error(...)`.
6. Utility writes to `Application_Errors` (based on threshold); if unavailable, it falls back to `Session_Audit_Log`.
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

Table migration/verification endpoints:

- `POST /admin/migrate/errors`
- `GET /admin/migrate/errors/schema`
- `POST /admin/migrate/errors/test`

---

## Current File Map

- `functions/smart_railway_app_function/core/error_tracking.py`
- `functions/smart_railway_app_function/main.py`
- `functions/smart_railway_app_function/routes/error_migration.py`
- `functions/smart_railway_app_function/services/session_service.py` (fallback audit write path)

---

## Operational Query Pattern

Typical production debugging workflow:

1. Collect `request_id` from client error response.
2. Search centralized logs by `request_id`.
3. Query `Application_Errors` for matching `Request_ID` / `Error_Code`.
4. If table not yet deployed, query `Session_Audit_Log` for `APPLICATION_ERROR` fallback events.
5. Use route, error_code, and exception_type for root-cause isolation.

---

## Future Enhancements

1. Add dedicated `Application_Errors` table for long-term analytics and deduplication.
2. Add alerting hooks for repeated `error_code` spikes.
3. Add admin endpoint to filter recent `APPLICATION_ERROR` events.
4. Add automated masking policy for additional sensitive fields.
