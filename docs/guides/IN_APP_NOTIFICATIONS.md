# In‑App Notifications (Bell Icon) — Explained Process

## 1) What we’re building
We’re adding **in‑app notifications** for both:
- **Passengers (Users)**
- **Employees/Admins**

UX requirement: show a **bell icon** with an **unread badge** in the main layouts, plus a page to manage notifications.

v1 uses **polling** (not realtime sockets).

---

## 2) Key constraints from current system
### Backend security model (must follow)
The backend is **session-based** and uses HttpOnly cookies + CSRF. The central pattern is in:
- `functions\smart_railway_app_function\core\session_middleware.py`

`@require_session` establishes:
- `g.user_id`
- `g.user_type` (`'user'` or `'employee'`)
- `g.user_email`, `g.user_role`

**Rule:** Notifications APIs must never accept `recipientId`/`recipientType` from the client. Recipient is always derived from the session (`g.*`).

### Backend response envelope
Keep responses consistent:
- Success: `{ "status": "success", "data": ... }`
- Error: `{ "status": "error", "message": "...", "code": "..." }`

### CloudScale quirks
CloudScale booleans are often stored as strings (`'true'/'false'`). Code should be defensive.

### API base URL (Catalyst hosting)
In this project the frontend calls the Catalyst Function through the Catalyst domain using this base:

- Base: `https://<your-app>.development.catalystserverless.in/server/smart_railway_app_function`
- Example full path: `.../server/smart_railway_app_function/notifications`

In React, this is already centralized in `railway-app/src/services/sessionApi.js`.

### Auth model + CSRF header
All in-app notifications APIs are designed to work with the existing **session cookie + CSRF** pattern:

- Auth: HttpOnly session cookie (sent automatically by `fetch` with `credentials: 'include'`)
- CSRF header: `X-CSRF-Token` (from `functions/smart_railway_app_function/config.py`)
- Read-only GET endpoints can be CSRF-free; state-changing endpoints should require CSRF.

---

## 3) Database design (CloudScale)
### 3.1 New table: `Notifications`
Single table, polymorphic recipient (user/employee).

**Recommended columns**
- `Recipient_Type` (string): `user | employee`
- `Recipient_ID` (number): ROWID of recipient
- `Title` (string)
- `Message` (text)
- `Type` (string): `booking | refund | train | announcement | security | employee | system`
- `Priority` (string): `low | normal | high | critical`
- `Is_Read` (string/boolean): `'true'/'false'`
- `Read_At` (datetime, nullable)
- `Created_At` (datetime)

**Optional (recommended for deep-linking)**
- `Action_Path` (string): e.g. `#/my-bookings` or `#/admin/invitations`
- `Related_Entity_Type` (string)
- `Related_Entity_ID` (string)
- `Metadata` (json/text)
- `Expires_At` (datetime)

**Indexes**
- `(Recipient_Type, Recipient_ID, Is_Read, Created_At desc)`
- `(Recipient_Type, Recipient_ID, Created_At desc)`

#### Suggested full column list (CloudScale)
Use **PascalCase with underscores** consistently (matches existing tables and makes ZCQL predictable):

- `Notification_ID` (string/UUID, optional if you rely on ROWID)
- `Recipient_Type` (`'user' | 'employee'`)
- `Recipient_ID` (numeric ROWID from Users/Employees)
- `Audience_Source` (`'system' | 'announcement' | 'booking' | 'payment' | ...'`)
- `Source_ID` (string, optional; e.g., `Announcement.ROWID` or `Booking.ROWID`)
- `Title` (string)
- `Message` (string)
- `Notification_Type` (`'info' | 'success' | 'warning' | 'error'`)
- `Action_URL` (string, optional; a HashRouter URL like `#/announcements` or `#/tickets/123`)
- `Is_Read` (`'true'/'false'` string or boolean depending on CloudScale config)
- `Read_At` (ISO datetime string, nullable)
- `Created_At` (ISO datetime string, always UTC)
- `Expires_At` (ISO datetime string, optional)

Notes:
- Always store times in UTC ISO format (e.g., `2026-04-09T08:21:11.545807+00:00`).
- For large-scale fanout, `Source_ID` + `Audience_Source` makes it easy to dedupe and audit.

### 3.2 Retention / cleanup
Decide a retention policy (example: 90 days). Implement a periodic cleanup job later if needed.

### 3.3 Targeting (who receives a notification)
We support targeting by **recipient type** and optionally by **role**:

**Recipient type**
- `user` → passengers
- `employee` → employees/admins

**Role-based targeting (employees)**
For broadcast-style notifications (especially announcements), we can target:
- all employees, or
- a subset of roles (example: `Admin`, `Ticket_Inspector`, `Station_Manager`).

**How targeting is stored**
- The **Notifications** table remains **per-recipient rows** (one row per recipient).
- The targeting rules should be stored on the **source event** (example: Announcement) as:
  - `Audience_Type`: `user | employee | both`
  - `Audience_Roles`: optional list (employees only)

This lets us create notifications for **all users + employees** by default, but still support role filtering when needed.

---

## 4) Backend implementation
### 4.1 Add table mapping
Add to `functions\smart_railway_app_function\config.py`:
- `TABLES['NOTIFICATIONS'] = '<CloudScale_table_name>'`

(Use the existing `TABLES` pattern; never hardcode table names.)

### 4.2 Create backend modules
**New blueprint**: `routes\notifications.py`

**New service layer** (recommended): `services\notification_service.py`
- `create_notification(recipient_type, recipient_id, ...)`
- `list_notifications(recipient_type, recipient_id, limit, offset, filters)`
- `get_unread_count(recipient_type, recipient_id)`
- `mark_read(recipient_type, recipient_id, notification_id)`
- `mark_all_read(recipient_type, recipient_id)`
- `delete_notification(recipient_type, recipient_id, notification_id)`

**DB access**
Use `CloudScaleRepository` and ZCQL patterns (CriteriaBuilder) as used elsewhere in the project.

### 4.3 API endpoints (full contract)
All endpoints require `@require_session`. Recipient scoping is **always derived from the session** (never from client params):

- `Recipient_Type = g.user_type` (`user|employee`)
- `Recipient_ID = g.user_id`

**CSRF rule**
- `GET` endpoints: CSRF not required
- `PUT/POST/DELETE` endpoints: require `X-CSRF-Token`

#### A) List notifications (bell dropdown + inbox)
`GET /notifications?days=30&limit=10&offset=0&unreadOnly=false&type=announcement`

Query params:
- `days` (int, default `30`) → only items created within the last N days
- `limit` (int, default `10`, max `50`)
- `offset` (int, default `0`)
- `unreadOnly` (`true|false`, optional)
- `type` (optional) → maps to `Audience_Source` / `Notification_Type` depending on final naming

**200 response (recommended shape)**
```json
{
  "status": "success",
  "data": {
    "items": [
      {
        "id": 123,
        "title": "Announcement",
        "message": "New timetable updated",
        "notificationType": "info",
        "audienceSource": "announcement",
        "sourceId": "55",
        "actionUrl": "#/announcements",
        "isRead": false,
        "createdAt": "2026-04-09T08:21:11.545807+00:00"
      }
    ],
    "limit": 10,
    "offset": 0,
    "hasMore": false
  }
}
```

#### B) Unread count (badge)
`GET /notifications/unread-count?days=30`

**200 response**
```json
{ "status": "success", "data": { "unread": 3 } }
```

#### C) Mark one as read
`PUT /notifications/<id>/read`

Rules:
- Validate the record exists for **this** session user (id-only is not enough)
- Update `Is_Read=true` and set `Read_At=now()`

**200 response**
```json
{ "status": "success", "message": "Marked as read" }
```

Errors:
- `404` → notification not found for this user
- `403` → (optional) if you want to distinguish ownership vs missing

#### D) Mark all as read (within time window)
`PUT /notifications/read-all?days=30`

- Marks all unread notifications for the current session recipient within the time filter

**200 response**
```json
{ "status": "success", "data": { "updated": 12 } }
```

#### E) Delete (dismiss)
`DELETE /notifications/<id>`

- Prefer soft delete later (add `Is_Archived`) if you need audit/history.
- For now, hard delete is acceptable if product doesn’t require history.

**200 response**
```json
{ "status": "success", "message": "Deleted" }
```

### 4.4 Query + backend logic details (ZCQL-safe)
Use `CloudScaleRepository` + `CriteriaBuilder` (no f-string value injection) and always scope queries to the session recipient.

#### A) Days cutoff filter
- Compute `cutoff_iso = now_utc - timedelta(days=days)`
- Add criteria: `Created_At >= cutoff_iso`

Example criteria (conceptual):
- `Recipient_Type = g.user_type`
- `Recipient_ID = g.user_id`
- `Created_At >= cutoff_iso`
- If `unreadOnly=true`: `Is_Read = 'false'`

#### B) Unread count
Run a `COUNT(*)` with the same recipient + cutoff criteria.

#### C) Ownership enforcement
For `PUT /notifications/<id>/read` and `DELETE /notifications/<id>`:
- Never update/delete by id alone.
- Always include: `ROWID = <id> AND Recipient_Type = g.user_type AND Recipient_ID = g.user_id`.

#### D) Sorting + pagination
- Order by `Created_At DESC`
- Always use `LIMIT` + `OFFSET`

### 4.5 Event producers (where notifications come from)
Notifications should be created **after** the main operation succeeds. If notification creation fails, log it but do not break core operations (best-effort).

#### Core events
**Passenger/User**
- Booking confirmed
- Booking cancelled
- Refund updated
- Train schedule change impacting a booking

**Employee/Admin**
- Employee invitation created/resend
- Employee status change
- Admin operational actions (optional)

#### Announcement → Notification fanout (required)
When an announcement is created/published, also create per-recipient notification rows so the bell shows it.

**Audience rules**
- Default: `Audience_Type = both` (all users + all employees)
- Supported:
  - `Audience_Type`: `user | employee | both`
  - `Audience_Roles`: optional list (employees only). Example: `["Admin"]`.

**Fanout steps (sync, v1)**
1) Insert announcement (source of truth)
2) Resolve recipients by audience:
   - If includes users: query all active users
   - If includes employees: query all active employees; if `Audience_Roles` provided, filter by role
3) For each recipient, insert a notification row:
   - `Audience_Source='announcement'`
   - `Source_ID=<announcement ROWID>`
   - `Title=<announcement title>`
   - `Message=<short summary>`
   - `Action_URL="#/announcements"`
   - `Is_Read=false`

**Scaling notes**
- If recipient count is large, batch inserts (e.g., 200–500 rows per batch).
- If Catalyst execution time becomes an issue, move fanout to an async job later.

**Where to hook**
Use the existing modules:
- `routes\bookings.py` / related booking services
- `routes\employee_invitation_routes.py`
- `routes\admin_employees.py`
- `routes\announcements.py` (broadcast + fanout)

---

## 5) Frontend implementation (full behavior)
### 5.1 API client + auth assumptions
Use the existing API wrapper:
- `railway-app\src\services\sessionApi.js`

It already:
- targets the Catalyst base (`/server/smart_railway_app_function/...`)
- includes cookies (`credentials: 'include'`)
- attaches CSRF (`X-CSRF-Token`) for state-changing requests

### 5.2 NotificationContext (polling + caching)
Create `railway-app\src\context\NotificationContext.jsx` and expose a `useNotifications()` hook.

State:
- `unreadCount`
- `recentNotifications` (bell dropdown: `days=30`, `limit=10`)
- `loading` / `error`

Methods:
- `refreshUnreadCount({ days = 30 } = {})` → `GET /notifications/unread-count?days=30`
- `fetchRecent({ days = 30, limit = 10 } = {})` → `GET /notifications?days=30&limit=10&offset=0`
- `markRead(id)` → `PUT /notifications/<id>/read`
- `markAllRead({ days = 30 } = {})` → `PUT /notifications/read-all?days=30`
- `deleteNotification(id)` → `DELETE /notifications/<id>`

Polling:
- Poll `unreadCount` every 30–60 seconds while logged in.
- Stop polling on logout.
- Optional: only poll when `document.visibilityState === 'visible'`.

UX note:
- Don’t show a toast for background 401s from session checks. Only show a login prompt when a user action requires auth.

### 5.3 NotificationBell component
Create `railway-app\src\components\NotificationBell.jsx`.

Dropdown behavior:
- On open: call `fetchRecent({ days: 30, limit: 10 })`
- Render items with: title, message, timestamp, unread dot
- On item click:
  1) `markRead(id)` (best-effort)
  2) navigate to `actionUrl` (HashRouter URL like `#/announcements`)

Dropdown actions:
- “Mark all as read” → `markAllRead({ days: 30 })`
- “View all” → route to inbox page

### 5.4 Layout integration (passenger + admin)
Add the bell into both layouts:
- `railway-app\src\components\PassengerLayout.jsx`
- `railway-app\src\components\AdminLayout.jsx`

They can share the same `NotificationBell` because the backend auto-scopes by session user.

### 5.5 Inbox page + routing (HashRouter)
Create `railway-app\src\pages\NotificationsPage.jsx`.

Features:
- Pagination (`limit/offset`)
- Unread filter (toggle)
- Actions: mark read, mark all read, delete
- Optional time filter: offer 30 / 90 days

Routing in `railway-app\src\App.js`:
- Prefer a single route for all roles: `#/notifications`
- If you need layout separation, add `#/admin/notifications` for employees/admins.

### 5.6 Icons
Add a bell icon into `railway-app\src\components\UI.jsx` icon registry so UI is consistent.

---

## 6) Error handling (UX standard)
- If APIs return 401 due to expired session, redirect to login (do not spam toasts).
- For non-auth errors, show ToastContext messages.

---

## 7) Testing checklist
### Backend
- List returns only current user’s notifications.
- Unread count correct.
- Mark read/delete fails if notification belongs to another user.
- CSRF required for write actions.

### Frontend
- Badge updates after mark read.
- Page loads, pagination works.
- Handles 401 silently (route guard / redirect).

---

## 8) Rollout checklist
1. Create CloudScale `Notifications` table and indexes.
2. Deploy backend function updates.
3. Deploy frontend updates.
4. Verify both user and employee flows.

---

## 9) Related project todo items
This feature aligns with existing tracked items:
- `notif-schema`
- `notif-backend-core-apis`
- `notif-backend-event-producers`
- `notif-frontend-context-polling`
- `notif-frontend-ui-components-routes`
- `notif-testing-rollout`
