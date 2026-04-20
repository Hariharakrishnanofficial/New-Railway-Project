# Dev Tables API (Development Only)

This project includes a **development-only** API for inspecting and performing basic CRUD operations on **any CloudScale (Datastore) table**.

> ⚠️ **Danger**: These endpoints can read/modify/delete data. They are intended for local debugging and schema inspection only.

## Availability / Safety

- Registered only when: `APP_ENVIRONMENT=development`
- Endpoint prefix: `/dev/tables/*`
- If `APP_ENVIRONMENT` is not `development`, the endpoints return **404**.

Blueprint implementation:
- `functions/smart_railway_app_function/routes/dev_tables.py`
- Registered from `functions/smart_railway_app_function/routes/__init__.py`

## Base URL (Catalyst local)

When running via `catalyst serve`, calls typically look like:

- `http://localhost:<port>/server/smart_railway_app_function/dev/tables/...`

## Table name resolution

`<table>` can be either:
- a key from `config.TABLES` (case-insensitive), e.g. `users`, `stations`
- or a literal table name, e.g. `Users`, `Stations`

## Endpoints

### List tables
`GET /dev/tables/`

Returns:
- `configured`: the `TABLES` mapping
- `discovered`: best-effort list from Catalyst Datastore `get_all_tables()`

### List columns
`GET /dev/tables/<table>/columns`

### List rows (paged)
`GET /dev/tables/<table>/rows?max_rows=200&next_token=<token>`

Uses Catalyst Datastore pagination.

### Get row by ROWID
`GET /dev/tables/<table>/rows/<row_id>`

### Insert row(s)
`POST /dev/tables/<table>/rows`

Body:
- JSON object (single insert) **or**
- JSON array of objects (bulk insert)

### Update row
`PATCH /dev/tables/<table>/rows/<row_id>`

Body:
- JSON object of fields to update

Notes:
- The handler injects `ROWID` from the path.

### Delete row
`DELETE /dev/tables/<table>/rows/<row_id>`

## Example curl

```bash
# list configured/discovered tables
curl -s "http://localhost:3000/server/smart_railway_app_function/dev/tables/"

# list columns for Users
curl -s "http://localhost:3000/server/smart_railway_app_function/dev/tables/users/columns"

# fetch first page of rows
curl -s "http://localhost:3000/server/smart_railway_app_function/dev/tables/users/rows?max_rows=50"
```
