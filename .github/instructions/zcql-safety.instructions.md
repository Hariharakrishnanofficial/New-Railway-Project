---
name: "ZCQL Safety & Patterns"
description: "Use when performing database operations, writing ZCQL queries, or modifying repositories. Enforces SQL injection prevention via CriteriaBuilder and the TABLES sync pattern."
applyTo: "functions/**/repositories/*.py"
---

# 🛡️ ZCQL Safety & Database Patterns

All database interactions in the Smart Railway project must use **Zoho Catalyst ZCQL** through the `CloudScaleRepository`. Follow these rules to prevent SQL injection and maintain schema consistency.

## 1. SQL Injection Prevention
**NEVER** use string formatting or f-strings to build ZCQL query filters.

### ✅ DO: Use `CriteriaBuilder`
The `CriteriaBuilder` automatically escapes values and handles type conversion.

```python
# GOOD: Safe and readable
criteria = CriteriaBuilder() \
    .eq("Email", user_email) \
    .eq("Account_Status", "Active") \
    .build()

query = f"SELECT ROWID, Email FROM {TABLES['USERS']} WHERE {criteria}"
```

### ❌ DON'T: Use string concatenation
```python
# BAD: Vulnerable to SQL injection
query = f"SELECT * FROM Users WHERE Email = '{user_email}'" 
```

## 2. Dynamic Table Names
**ALWAYS** use the `TABLES` dictionary from `config.py`. Never hardcode table names as strings.

```python
from config import TABLES

# ✅ Correct
table_name = TABLES['TICKET_BOOKINGS']
query = f"SELECT * FROM {table_name}"

# ❌ Incorrect
query = "SELECT * FROM Ticket_Bookings"
```

## 3. Query Execution Pattern
Always use `execute_query` from `CloudScaleRepository` for SELECT statements. It handles Catalyst app initialization and result normalization.

```python
repo = CloudScaleRepository()
result = repo.execute_query(query)

if result.get("success"):
    data = result["data"]["data"]
    # ... process data
```

## 4. Key ZCQL Constraints
*   **ROWID**: Always select `ROWID` if you need to update or delete the record later.
*   **Literals**: Use `_to_zcql_literal()` for any manual value conversion inside raw queries.
*   **Numeric IDs**: Use `.id_eq()` or `.id_in()` in `CriteriaBuilder` for numeric fields (ROWID, etc.) to skip unnecessary quotes.
*   **Pagination**: All list-returning queries MUST include `LIMIT` and `OFFSET`.

## 5. Error Handling
*   Wrap database calls in `try...except`.
*   Log the full error using `logger.exception()` for internal debugging.
*   Return a generic error message to the client; never leak ZCQL syntax errors.
