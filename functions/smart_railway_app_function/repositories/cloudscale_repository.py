"""
CloudScale Repository - Data access layer for Zoho Catalyst CloudScale.
Uses ZCQL (Zoho Catalyst Query Language) for all database operations.

Features:
  - ZCQL queries for all CRUD operations
  - CriteriaBuilder: safe query construction
  - Caching: TTL-based for read operations
  - Batch operations with rollback support
  - Unified table access
"""

from __future__ import annotations

import logging
import os
from typing import Optional, List, Dict, Any, Tuple

from repositories.cache_manager import cache, TTL_STATIONS, TTL_TRAINS, TTL_USER, TTL_INVENTORY
from config import TABLES, get_table

logger = logging.getLogger(__name__)

# Catalyst SDK - imported at function initialization
_catalyst_app = None


def _sanitize_tls_bundle_env() -> None:
    """Clear stale CA bundle env vars that point to deleted .build paths."""
    valid_bundle = None
    try:
        import certifi  # pylint: disable=import-outside-toplevel
        candidate = certifi.where()
        if candidate and os.path.exists(candidate):
            valid_bundle = candidate
    except Exception:
        valid_bundle = None

    for env_key in ('SSL_CERT_FILE', 'REQUESTS_CA_BUNDLE', 'CURL_CA_BUNDLE'):
        bundle_path = os.environ.get(env_key)
        if bundle_path:
            # Remove if path doesn't exist OR if it points to .build (often stale)
            if not os.path.exists(bundle_path) or '.build' in bundle_path:
                if valid_bundle:
                    logger.warning(
                        "Replacing invalid/stale TLS bundle path in %s: %s -> %s",
                        env_key,
                        bundle_path,
                        valid_bundle,
                    )
                    os.environ[env_key] = valid_bundle
                else:
                    logger.warning("Removing invalid TLS bundle path from %s: %s", env_key, bundle_path)
                    os.environ.pop(env_key, None)
    
    # Force set valid bundle if we have one
    if valid_bundle:
        os.environ['SSL_CERT_FILE'] = valid_bundle
        os.environ['REQUESTS_CA_BUNDLE'] = valid_bundle
        os.environ['CURL_CA_BUNDLE'] = valid_bundle


def init_catalyst(catalyst_app):
    """Initialize Catalyst SDK with the app instance from request context."""
    global _catalyst_app
    _catalyst_app = catalyst_app


def get_catalyst_app():
    """Get initialized Catalyst app instance."""
    global _catalyst_app
    return _catalyst_app


# ══════════════════════════════════════════════════════════════════════════════
#  CRITERIA BUILDER (ZCQL compatible)
# ══════════════════════════════════════════════════════════════════════════════

class CriteriaBuilder:
    """
    Builds safe ZCQL WHERE clause conditions.

    Example:
        CriteriaBuilder()
            .eq("Email", "user@example.com")
            .eq("Account_Status", "Active")
            .ne("Role", "Admin")
            .build()
        => "Email = 'user@example.com' AND Account_Status = 'Active' AND Role != 'Admin'"
    """

    def __init__(self):
        self._parts: List[str] = []

    @staticmethod
    def _esc(value: Any) -> str:
        """Escape single quotes in a string value for ZCQL."""
        if value is None:
            return "NULL"
        return str(value).replace("'", "''")

    def eq(self, field: str, value: Any) -> "CriteriaBuilder":
        """Equality condition."""
        if value is None:
            self._parts.append(f"{field} IS NULL")
        else:
            self._parts.append(f"{field} = '{self._esc(value)}'")
        return self

    def id_eq(self, field: str, value: Any) -> "CriteriaBuilder":
        """ID field equality (numeric, no quotes)."""
        self._parts.append(f"{field} = {value}")
        return self

    def ne(self, field: str, value: Any) -> "CriteriaBuilder":
        """Not equal condition."""
        if value is None:
            self._parts.append(f"{field} IS NOT NULL")
        else:
            self._parts.append(f"{field} != '{self._esc(value)}'")
        return self

    def gt(self, field: str, value: Any) -> "CriteriaBuilder":
        """Greater than."""
        self._parts.append(f"{field} > '{self._esc(value)}'")
        return self

    def gte(self, field: str, value: Any) -> "CriteriaBuilder":
        """Greater than or equal."""
        self._parts.append(f"{field} >= '{self._esc(value)}'")
        return self

    def lt(self, field: str, value: Any) -> "CriteriaBuilder":
        """Less than."""
        self._parts.append(f"{field} < '{self._esc(value)}'")
        return self

    def lte(self, field: str, value: Any) -> "CriteriaBuilder":
        """Less than or equal."""
        self._parts.append(f"{field} <= '{self._esc(value)}'")
        return self

    def like(self, field: str, value: str) -> "CriteriaBuilder":
        """LIKE pattern match (use % wildcards)."""
        self._parts.append(f"{field} LIKE '{self._esc(value)}'")
        return self

    def contains(self, field: str, value: str) -> "CriteriaBuilder":
        """Contains substring (LIKE %value%)."""
        self._parts.append(f"{field} LIKE '%{self._esc(value)}%'")
        return self

    def is_in(self, field: str, values: List[Any]) -> "CriteriaBuilder":
        """IN clause for multiple values."""
        if not values:
            # Empty IN clause - always false
            self._parts.append("1 = 0")
        else:
            escaped = ", ".join([f"'{self._esc(v)}'" for v in values])
            self._parts.append(f"{field} IN ({escaped})")
        return self

    def id_in(self, field: str, values: List[Any]) -> "CriteriaBuilder":
        """IN clause for numeric IDs (no quotes)."""
        if not values:
            self._parts.append("1 = 0")
        else:
            vals = ", ".join([str(v) for v in values])
            self._parts.append(f"{field} IN ({vals})")
        return self

    def between(self, field: str, low: Any, high: Any) -> "CriteriaBuilder":
        """BETWEEN clause."""
        self._parts.append(f"{field} BETWEEN '{self._esc(low)}' AND '{self._esc(high)}'")
        return self

    def is_null(self, field: str) -> "CriteriaBuilder":
        """IS NULL condition."""
        self._parts.append(f"{field} IS NULL")
        return self

    def is_not_null(self, field: str) -> "CriteriaBuilder":
        """IS NOT NULL condition."""
        self._parts.append(f"{field} IS NOT NULL")
        return self

    def raw(self, expr: str) -> "CriteriaBuilder":
        """Add a raw SQL expression (use sparingly)."""
        self._parts.append(f"({expr})")
        return self

    def build(self) -> Optional[str]:
        """Build AND-joined WHERE clause."""
        if not self._parts:
            return None
        return " AND ".join(self._parts)

    def or_build(self) -> Optional[str]:
        """Build OR-joined WHERE clause."""
        if not self._parts:
            return None
        return " OR ".join(self._parts)


# ══════════════════════════════════════════════════════════════════════════════
#  CLOUDSCALE REPOSITORY
# ══════════════════════════════════════════════════════════════════════════════

class CloudScaleRepository:
    """
    Repository for Catalyst CloudScale database using ZCQL.
    """

    def __init__(self):
        self._tables = TABLES

    @property
    def tables(self) -> Dict[str, str]:
        """Get table configuration."""
        return self._tables

    def _get_zcql(self):
        """Get ZCQL service from Catalyst app."""
        _sanitize_tls_bundle_env()
        app = get_catalyst_app()
        if not app:
            # Check for local CLI login context if app is not initialized
            try:
                import zcatalyst_sdk
                # Use empty config to avoid "headers empty" error in local CLI
                app = zcatalyst_sdk.initialize({})
            except ImportError:
                raise RuntimeError("Catalyst app not initialized. Call init_catalyst() first.")
            except Exception:
                raise RuntimeError("Catalyst app not initialized. Call init_catalyst() first.")
        return app.zcql()

    def _get_datastore(self):
        """Get Datastore service for row operations."""
        _sanitize_tls_bundle_env()
        app = get_catalyst_app()
        if not app:
            try:
                import zcatalyst_sdk
                # Use empty config to avoid "headers empty" error in local CLI
                app = zcatalyst_sdk.initialize({})
            except ImportError:
                raise RuntimeError("Catalyst app not initialized. Call init_catalyst() first.")
            except Exception:
                raise RuntimeError("Catalyst app not initialized. Call init_catalyst() first.")
        return app.datastore()

    def _resolve_table(self, table_name: str) -> str:
        """Resolve table name from key or return as-is."""
        return self._tables.get(table_name.lower(), table_name)

    @staticmethod
    def _to_zcql_literal(value: Any) -> str:
        """Convert Python value to a safe ZCQL literal."""
        if value is None:
            return "NULL"
        if isinstance(value, bool):
            return "true" if value else "false"
        if isinstance(value, (int, float)):
            return str(value)
        escaped = str(value).replace("'", "''")
        return f"'{escaped}'"

    # ══════════════════════════════════════════════════════════════════════════
    #  ZCQL QUERY EXECUTION
    # ══════════════════════════════════════════════════════════════════════════

    def execute_query(self, query: str) -> Dict[str, Any]:
        """Execute a ZCQL SELECT query."""
        try:
            zcql = self._get_zcql()
            result = zcql.execute_query(query)

            # ZCQL returns list of dicts with table name as key
            if isinstance(result, list):
                data = []
                for row in result:
                    if isinstance(row, dict):
                        # CloudScale wraps results in table name
                        for key, value in row.items():
                            if isinstance(value, dict):
                                data.append(value)
                            else:
                                data.append(row)
                            break
                return {"success": True, "data": {"data": data}, "status_code": 200}

            return {"success": True, "data": {"data": result or []}, "status_code": 200}

        except Exception as exc:
            logger.error(f"ZCQL query error: {exc}")
            return {"success": False, "error": str(exc)}

    # ══════════════════════════════════════════════════════════════════════════
    #  CRUD OPERATIONS
    # ══════════════════════════════════════════════════════════════════════════

    def create_record(self, table_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a single record in a CloudScale table."""
        actual_table = self._resolve_table(table_name)

        try:
            datastore = self._get_datastore()
            table = datastore.table(actual_table)

            # Insert row
            result = table.insert_row(data)

            # Get the created row ID
            row_id = result.get('ROWID') if isinstance(result, dict) else None

            return {
                "success": True,
                "data": {"ROWID": row_id, **data},
                "status_code": 201
            }

        except Exception as exc:
            err_text = str(exc)
            logger.error(f"Create record error in {table_name}: {err_text}")
            
            # Log the data being inserted for debugging
            logger.debug(f"Insert data for {table_name}: {data}")

            # Fallback for environments where datastore row API is blocked.
            if "method not allowed" in err_text.lower():
                try:
                    zcql = self._get_zcql()
                    columns = ", ".join(data.keys())
                    values = ", ".join(self._to_zcql_literal(v) for v in data.values())
                    insert_query = f"INSERT INTO {actual_table} ({columns}) VALUES ({values})"
                    zcql.execute_query(insert_query)

                    # Best-effort ROWID lookup for user creation flows.
                    row_id = None
                    if actual_table == "Users" and data.get("Email"):
                        escaped_email = str(data["Email"]).replace("'", "''")
                        lookup_query = f"SELECT ROWID FROM {actual_table} WHERE Email = '{escaped_email}' ORDER BY ROWID DESC LIMIT 1"
                        lookup_result = zcql.execute_query(lookup_query)
                        if isinstance(lookup_result, list) and lookup_result:
                            first = lookup_result[0]
                            if isinstance(first, dict):
                                row = first.get(actual_table, {}) if actual_table in first else next(iter(first.values()), {})
                                if isinstance(row, dict):
                                    row_id = row.get("ROWID")
                    elif actual_table == "OTP_Tokens" and data.get("User_Email"):
                        escaped_email = str(data["User_Email"]).replace("'", "''")
                        lookup_query = f"SELECT ROWID FROM {actual_table} WHERE User_Email = '{escaped_email}' ORDER BY ROWID DESC LIMIT 1"
                        lookup_result = zcql.execute_query(lookup_query)
                        if isinstance(lookup_result, list) and lookup_result:
                            first = lookup_result[0]
                            if isinstance(first, dict):
                                row = first.get(actual_table, {}) if actual_table in first else next(iter(first.values()), {})
                                if isinstance(row, dict):
                                    row_id = row.get("ROWID")
                    elif actual_table == "Sessions" and data.get("Session_ID"):
                        # Use CriteriaBuilder for safe Session_ID query (BIGINT column)
                        session_id_val = data["Session_ID"]
                        criteria = CriteriaBuilder().id_eq("Session_ID", session_id_val).build()
                        lookup_query = f"SELECT ROWID FROM {actual_table} WHERE {criteria} ORDER BY ROWID DESC LIMIT 1"
                        lookup_result = zcql.execute_query(lookup_query)
                        if isinstance(lookup_result, list) and lookup_result:
                            first = lookup_result[0]
                            if isinstance(first, dict):
                                row = first.get(actual_table, {}) if actual_table in first else next(iter(first.values()), {})
                                if isinstance(row, dict):
                                    row_id = row.get("ROWID")

                    return {
                        "success": True,
                        "data": {"ROWID": row_id, **data},
                        "status_code": 201
                    }
                except Exception as fallback_exc:
                    logger.error(f"Create record fallback error in {table_name}: {fallback_exc}")
                    return {"success": False, "error": f"{err_text} | fallback: {fallback_exc}"}

            return {"success": False, "error": err_text}

    def get_all_records(
        self,
        table_name: str,
        criteria: Optional[str] = None,
        limit: int = 200,
        offset: int = 0,
        order_by: Optional[str] = None
    ) -> Dict[str, Any]:
        """Fetch records from a CloudScale table with optional criteria filter."""
        try:
            actual_table = self._resolve_table(table_name)

            # Build ZCQL query - avoid SELECT * as it's not supported in CloudScale Functions
            if actual_table == 'Stations':
                # Use specific fields for Stations to avoid SELECT * error
                query = f"SELECT ROWID, Station_Code, Station_Name, City, State, Zone, Division, Station_Type, Number_of_Platforms, Latitude, Longitude, Is_Active FROM {actual_table}"
            elif actual_table == 'Trains':
                # Use specific fields for Trains
                query = f"SELECT ROWID, Train_Number, Train_Name, Train_Type, From_Station, To_Station, Departure_Time, Arrival_Time, Duration, Distance, Run_Days, Is_Active FROM {actual_table}"
            elif actual_table == 'Users':
                # Users table requires auth-related fields for login/session flows
                query = (
                    f"SELECT ROWID, Full_Name, Email, Password, Phone_Number, Role, "
                    f"Account_Status, Date_of_Birth, Address, Last_Login FROM {actual_table}"
                )
            elif actual_table == 'OTP_Tokens':
                # OTP tokens for registration/password reset verification
                query = (
                    f"SELECT ROWID, User_Email, OTP, Purpose, Expires_At, Is_Used, Attempts, Created_At "
                    f"FROM {actual_table}"
                )
            elif actual_table == 'Sessions':
                # Session management table - use CREATEDTIME (Catalyst auto-field) not Created_At
                query = (
                    f"SELECT ROWID, Session_ID, User_ID, User_Email, User_Role, IP_Address, "
                    f"User_Agent, CSRF_Token, CREATEDTIME, Last_Accessed_At, Expires_At, Is_Active "
                    f"FROM {actual_table}"
                )
            elif actual_table == 'Employees':
                # Employee authentication - only use columns that exist in actual table
                # Based on schema: ROWID, Employee_ID, Full_Name, Email, Password, Phone_Number,
                # Account_Status, Aadhar_Verified, Date_of_Birth, ID_Proof_Type, ID_Proof_Number,
                # Address, Last_Login, Role, Department, Designation, Is_Active, Joined_At
                query = (
                    f"SELECT ROWID, Employee_ID, Full_Name, Email, Password, Role, "
                    f"Department, Designation, Account_Status, Joined_At, Is_Active, Phone_Number "
                    f"FROM {actual_table}"
                )
            else:
                # For other tables, use ROWID + a safe field to avoid SELECT *
                query = f"SELECT ROWID FROM {actual_table}"
                logger.warning(f"Using minimal field selection for table {actual_table} to avoid SELECT * error")

            if criteria:
                query += f" WHERE {criteria}"

            if order_by:
                query += f" ORDER BY {order_by}"
            else:
                query += " ORDER BY ROWID DESC"

            query += f" LIMIT {limit}"

            if offset > 0:
                query += f" OFFSET {offset}"

            return self.execute_query(query)

        except Exception as exc:
            logger.error(f"Get all records error from {table_name}: {exc}")
            return {"success": False, "error": str(exc)}

    def get_record_by_id(self, table_name: str, record_id: str) -> Dict[str, Any]:
        """Fetch a single record by ROWID."""
        try:
            actual_table = self._resolve_table(table_name)

            # Use specific fields instead of SELECT * (CloudScale Functions requirement)
            if actual_table == 'Stations':
                query = f"SELECT ROWID, Station_Code, Station_Name, City, State, Zone, Division, Station_Type, Number_of_Platforms, Latitude, Longitude, Is_Active FROM {actual_table} WHERE ROWID = {record_id}"
            elif actual_table == 'Trains':
                query = f"SELECT ROWID, Train_Number, Train_Name, Train_Type, From_Station, To_Station, Departure_Time, Arrival_Time, Duration, Distance, Run_Days, Is_Active FROM {actual_table} WHERE ROWID = {record_id}"
            elif actual_table == 'Users':
                query = (
                    f"SELECT ROWID, Full_Name, Email, Password, Phone_Number, Role, "
                    f"Account_Status, Date_of_Birth, Address, Last_Login "
                    f"FROM {actual_table} WHERE ROWID = {record_id}"
                )
            elif actual_table == 'OTP_Tokens':
                query = (
                    f"SELECT ROWID, User_Email, OTP, Purpose, Expires_At, Is_Used, Attempts, Created_At "
                    f"FROM {actual_table} WHERE ROWID = {record_id}"
                )
            elif actual_table == 'Sessions':
                query = (
                    f"SELECT ROWID, Session_ID, User_ID, User_Email, User_Role, IP_Address, "
                    f"User_Agent, CSRF_Token, Created_At, Last_Accessed_At, Expires_At, Is_Active "
                    f"FROM {actual_table} WHERE ROWID = {record_id}"
                )
            elif actual_table == 'Employees':
                query = (
                    f"SELECT ROWID, Employee_ID, Full_Name, Email, Password, Role, "
                    f"Department, Designation, Account_Status, Joined_At, Is_Active, Phone_Number "
                    f"FROM {actual_table} WHERE ROWID = {record_id}"
                )
            else:
                query = f"SELECT ROWID FROM {actual_table} WHERE ROWID = {record_id}"
            result = self.execute_query(query)

            if result.get("success"):
                data = result.get("data", {}).get("data", [])
                if data:
                    return {"success": True, "data": data[0], "status_code": 200}
                return {"success": True, "data": None, "status_code": 404}

            return result

        except Exception as exc:
            logger.error(f"Get record by ID error from {table_name}: {exc}")
            return {"success": False, "error": str(exc)}

    def update_record(self, table_name: str, record_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update a record by ROWID."""
        try:
            actual_table = self._resolve_table(table_name)

            datastore = self._get_datastore()
            table = datastore.table(actual_table)

            # Add ROWID to data for update
            data['ROWID'] = int(record_id)

            result = table.update_row(data)

            return {
                "success": True,
                "data": result,
                "status_code": 200
            }

        except Exception as exc:
            logger.error(f"Update record error in {table_name}: {exc}")
            return {"success": False, "error": str(exc)}

    def delete_record(self, table_name: str, record_id: str) -> Dict[str, Any]:
        """Delete a record by ROWID."""
        try:
            actual_table = self._resolve_table(table_name)

            datastore = self._get_datastore()
            table = datastore.table(actual_table)

            table.delete_row(int(record_id))

            return {"success": True, "data": None, "status_code": 204}

        except Exception as exc:
            logger.error(f"Delete record error from {table_name}: {exc}")
            return {"success": False, "error": str(exc)}

    # ── Alias helpers ─────────────────────────────────────────────────────────

    def get_records(self, table_name: str, criteria: Optional[str] = None, limit: int = 200) -> List[Dict]:
        """Return list of data rows directly."""
        result = self.get_all_records(table_name, criteria=criteria, limit=limit)
        if result.get("success"):
            return result.get("data", {}).get("data", []) or []
        return []

    def add_record(self, table_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Alias for create_record."""
        return self.create_record(table_name, data)

    def count_records(self, table_name: str, criteria: Optional[str] = None) -> int:
        """Count records matching criteria."""
        try:
            actual_table = self._resolve_table(table_name)
            query = f"SELECT COUNT(ROWID) as count FROM {actual_table}"
            if criteria:
                query += f" WHERE {criteria}"

            result = self.execute_query(query)
            if result.get("success"):
                data = result.get("data", {}).get("data", [])
                if data:
                    return int(data[0].get("count", 0))
            return 0
        except Exception as exc:
            logger.error(f"Count records error: {exc}")
            return 0

    # ══════════════════════════════════════════════════════════════════════════
    #  CACHED READ OPERATIONS
    # ══════════════════════════════════════════════════════════════════════════

    def get_all_stations_cached(self, ttl: int = TTL_STATIONS) -> List[Dict]:
        """Stations list - cached 24h."""
        key = "stations:all"
        hit = cache.get(key)
        if hit is not None:
            return hit
        records = self.get_records(TABLES['stations'], limit=500)
        cache.set(key, records, ttl=ttl)
        return records

    def get_all_trains_cached(self, ttl: int = TTL_TRAINS) -> List[Dict]:
        """Trains list - cached 1h."""
        key = "trains:all"
        hit = cache.get(key)
        if hit is not None:
            return hit
        records = self.get_records(TABLES['trains'], limit=500)
        cache.set(key, records, ttl=ttl)
        return records

    def get_train_cached(self, train_id: str, ttl: int = TTL_TRAINS) -> Optional[Dict]:
        """Single train record - cached 1h."""
        key = f"train:{train_id}"
        hit = cache.get(key)
        if hit is not None:
            return hit
        result = self.get_record_by_id(TABLES['trains'], train_id)
        if result.get("success") and result.get("data"):
            cache.set(key, result["data"], ttl=ttl)
            return result["data"]
        return None

    def get_user_cached(self, user_id: str, ttl: int = TTL_USER) -> Optional[Dict]:
        """User record - cached 15 min."""
        key = f"user:{user_id}"
        hit = cache.get(key)
        if hit is not None:
            return hit
        result = self.get_record_by_id(TABLES['users'], user_id)
        if result.get("success") and result.get("data"):
            cache.set(key, result["data"], ttl=ttl)
            return result["data"]
        return None

    def invalidate_train_cache(self, train_id: Optional[str] = None):
        """Invalidate train cache."""
        if train_id:
            cache.delete(f"train:{train_id}")
        cache.delete("trains:all")

    def invalidate_user_cache(self, user_id: str):
        """Invalidate user cache."""
        cache.delete(f"user:{user_id}")

    def invalidate_inventory_cache(self, train_id: str, journey_date: str, cls: str = ""):
        """Invalidate inventory cache."""
        prefix = f"inventory:{train_id}:{journey_date}"
        if cls:
            cache.delete(f"{prefix}:{cls}")
        else:
            cache.invalidate(prefix)

    # ══════════════════════════════════════════════════════════════════════════
    #  BATCH OPERATIONS
    # ══════════════════════════════════════════════════════════════════════════

    def batch_create(
        self,
        table_name: str,
        records: List[Dict],
        rollback_on_failure: bool = True
    ) -> Dict[str, Any]:
        """Create multiple records with optional rollback."""
        created_ids: List[str] = []
        errors: List[str] = []
        failed_indices: List[int] = []

        for i, record in enumerate(records):
            result = self.create_record(table_name, record)
            if result.get("success"):
                row_id = result.get("data", {}).get("ROWID", f"row_{i}")
                created_ids.append(str(row_id))
            else:
                errors.append(f"Row {i}: {result.get('error', 'unknown')}")
                failed_indices.append(i)
                if rollback_on_failure and created_ids:
                    logger.warning(f"Batch create: row {i} failed. Rolling back {len(created_ids)} record(s).")
                    for rid in created_ids:
                        self.delete_record(table_name, rid)
                    return {
                        "success": False,
                        "error": f"Batch failed at row {i}: {result.get('error')}. Rollback performed.",
                        "created_ids": [],
                        "failed_indices": failed_indices,
                        "errors": errors,
                    }

        return {
            "success": len(errors) == 0,
            "created_ids": created_ids,
            "failed_indices": failed_indices,
            "errors": errors,
        }

    def batch_update(self, table_name: str, updates: List[Tuple[str, Dict]]) -> Dict[str, Any]:
        """Update multiple records."""
        results = {"success_count": 0, "fail_count": 0, "errors": []}
        for record_id, data in updates:
            res = self.update_record(table_name, record_id, data)
            if res.get("success"):
                results["success_count"] += 1
            else:
                results["fail_count"] += 1
                results["errors"].append(f"{record_id}: {res.get('error', 'unknown')}")
        results["success"] = results["fail_count"] == 0
        return results

    # ══════════════════════════════════════════════════════════════════════════
    #  SPECIALIZED QUERIES
    # ══════════════════════════════════════════════════════════════════════════

    def get_user_by_email(self, email: str) -> Optional[Dict]:
        """Find user by email address."""
        criteria = CriteriaBuilder().eq("Email", email.lower()).build()
        records = self.get_records(TABLES['users'], criteria=criteria, limit=1)
        return records[0] if records else None

    # ══════════════════════════════════════════════════════════════════════════
    #  EMPLOYEE QUERIES (Staff: Admin/Employee roles)
    # ══════════════════════════════════════════════════════════════════════════

    def get_employee_by_email(self, email: str) -> Optional[Dict]:
        """Find employee by email address."""
        email_normalized = email.lower().strip()
        logger.info(f"[REPO] get_employee_by_email called with: '{email_normalized}'")
        criteria = CriteriaBuilder().eq("Email", email_normalized).build()
        logger.info(f"[REPO] Built criteria: {criteria}")
        records = self.get_records(TABLES['employees'], criteria=criteria, limit=1)
        logger.info(f"[REPO] Query returned {len(records)} records")
        if records:
            logger.info(f"[REPO] Found employee email: {records[0].get('Email')}")
        return records[0] if records else None

    def get_employee_by_id(self, employee_row_id: str) -> Optional[Dict]:
        """Find employee by ROWID."""
        result = self.get_record_by_id(TABLES['employees'], employee_row_id)
        if result.get("success") and result.get("data"):
            return result["data"]
        return None

    def get_employee_by_employee_id(self, employee_id: str) -> Optional[Dict]:
        """Find employee by Employee_ID (e.g., 'EMP001', 'ADM001')."""
        criteria = CriteriaBuilder().eq("Employee_ID", employee_id.upper()).build()
        records = self.get_records(TABLES['employees'], criteria=criteria, limit=1)
        return records[0] if records else None

    def get_employee_cached(self, employee_row_id: str, ttl: int = TTL_USER) -> Optional[Dict]:
        """Employee record - cached 15 min."""
        key = f"employee:{employee_row_id}"
        hit = cache.get(key)
        if hit is not None:
            return hit
        employee = self.get_employee_by_id(employee_row_id)
        if employee:
            cache.set(key, employee, ttl=ttl)
            return employee
        return None

    def invalidate_employee_cache(self, employee_row_id: str):
        """Invalidate employee cache."""
        cache.delete(f"employee:{employee_row_id}")

    def create_employee(self, employee_data: Dict) -> Dict[str, Any]:
        """
        Create a new employee record.
        
        Required fields:
        - Employee_ID: Unique staff ID (e.g., 'EMP001')
        - Full_Name: Employee name
        - Email: Unique email address
        - Password: Bcrypt hashed password
        - Role: 'Admin' or 'Employee'
        - Invited_By: ROWID of inviting admin
        - Account_Status: 'Active', 'Inactive', 'Suspended'
        """
        # Ensure email is lowercase
        if 'Email' in employee_data:
            employee_data['Email'] = employee_data['Email'].lower()
        return self.create_record(TABLES['employees'], employee_data)

    def update_employee(self, employee_row_id: str, update_data: Dict) -> Dict[str, Any]:
        """Update an employee record."""
        # Ensure email is lowercase if being updated
        if 'Email' in update_data:
            update_data['Email'] = update_data['Email'].lower()
        result = self.update_record(TABLES['employees'], employee_row_id, update_data)
        if result.get("success"):
            self.invalidate_employee_cache(employee_row_id)
        return result

    def delete_employee(self, employee_row_id: str) -> Dict[str, Any]:
        """Delete an employee record."""
        result = self.delete_record(TABLES['employees'], employee_row_id)
        if result.get("success"):
            self.invalidate_employee_cache(employee_row_id)
        return result

    def get_all_employees(
        self,
        role: str = None,
        department: str = None,
        status: str = "Active",
        limit: int = 100
    ) -> List[Dict]:
        """Get all employees with optional filters."""
        cb = CriteriaBuilder()
        if status:
            cb.eq("Account_Status", status)
        if role:
            cb.eq("Role", role)
        if department:
            cb.eq("Department", department)
        criteria = cb.build()
        return self.get_records(TABLES['employees'], criteria=criteria, limit=limit)

    def get_next_employee_id(self, role: str = "Employee") -> str:
        """
        Generate next sequential Employee_ID.
        Format: EMP001, EMP002... for Employee; ADM001, ADM002... for Admin
        """
        prefix = "ADM" if role == "Admin" else "EMP"
        # Get all employees with this prefix
        criteria = CriteriaBuilder().like("Employee_ID", f"{prefix}%").build()
        employees = self.get_records(TABLES['employees'], criteria=criteria, limit=1000)
        
        if not employees:
            return f"{prefix}001"
        
        # Find the highest number
        max_num = 0
        for emp in employees:
            emp_id = emp.get("Employee_ID", "")
            if emp_id.startswith(prefix):
                try:
                    num = int(emp_id[len(prefix):])
                    max_num = max(max_num, num)
                except ValueError:
                    continue
        
        return f"{prefix}{str(max_num + 1).zfill(3)}"

    def get_station_by_code(self, code: str) -> Optional[Dict]:
        """Find station by code."""
        criteria = CriteriaBuilder().eq("Station_Code", code.upper()).build()
        records = self.get_records(TABLES['stations'], criteria=criteria, limit=1)
        return records[0] if records else None

    def get_train_by_number(self, number: str) -> Optional[Dict]:
        """Find train by number."""
        criteria = CriteriaBuilder().eq("Train_Number", number).build()
        records = self.get_records(TABLES['trains'], criteria=criteria, limit=1)
        return records[0] if records else None

    def get_booking_by_pnr(self, pnr: str) -> Optional[Dict]:
        """Find booking by PNR."""
        criteria = CriteriaBuilder().eq("PNR", pnr).build()
        records = self.get_records(TABLES['bookings'], criteria=criteria, limit=1)
        return records[0] if records else None

    def get_passengers_by_booking(self, booking_id: str) -> List[Dict]:
        """Get all passengers for a booking."""
        criteria = CriteriaBuilder().id_eq("Booking_ID", booking_id).build()
        return self.get_records(TABLES['passengers'], criteria=criteria, limit=50)

    def get_active_bookings_for_train_date(self, train_id: str, date_str: str) -> List[Dict]:
        """Fetch active bookings for a specific train and date."""
        criteria = (
            CriteriaBuilder()
            .id_eq("Train_ID", train_id)
            .eq("Journey_Date", date_str)
            .ne("Booking_Status", "Cancelled")
            .build()
        )
        return self.get_records(TABLES['bookings'], criteria=criteria, limit=500)

    def count_monthly_bookings(self, user_id: str, start_of_month: str) -> int:
        """Count non-cancelled bookings for user since start of month."""
        criteria = (
            CriteriaBuilder()
            .id_eq("User_ID", user_id)
            .gte("Booking_Time", start_of_month)
            .ne("Booking_Status", "Cancelled")
            .build()
        )
        return self.count_records(TABLES['bookings'], criteria=criteria)

    def search_trains(
        self,
        source: str = "",
        destination: str = "",
        active_only: bool = True
    ) -> List[Dict]:
        """Search trains with ZCQL filtering."""
        cb = CriteriaBuilder()

        if active_only:
            cb.eq("Is_Active", "true")

        if source:
            cb.contains("From_Station", source.upper())

        if destination:
            cb.contains("To_Station", destination.upper())

        criteria = cb.build()
        return self.get_records(TABLES['trains'], criteria=criteria, limit=500)

    def get_route_stops(self, route_id: str) -> List[Dict]:
        """Get all stops for a route, ordered by sequence."""
        actual_table = self._resolve_table(TABLES['route_stops'])
        query = f"SELECT * FROM {actual_table} WHERE Route_ID = {route_id} ORDER BY Stop_Sequence ASC"
        result = self.execute_query(query)
        if result.get("success"):
            return result.get("data", {}).get("data", []) or []
        return []

    # ══════════════════════════════════════════════════════════════════════════
    #  PHASE 1: BOOKING INFRASTRUCTURE METHODS
    # ══════════════════════════════════════════════════════════════════════════

    def search_trains_by_route(
        self,
        from_station: str,
        to_station: str,
        journey_date: str = None,
        travel_class: str = None,
        active_only: bool = True
    ) -> List[Dict]:
        """
        Search trains between two stations on a specific date.
        
        Args:
            from_station: Source station code or ROWID
            to_station: Destination station code or ROWID
            journey_date: Journey date (DD-MMM-YYYY format for ZCQL)
            travel_class: Filter by class availability (SL, 3A, etc.)
            active_only: Only return active trains
        
        Returns:
            List of matching train records
        """
        cb = CriteriaBuilder()
        
        if active_only:
            cb.eq("Is_Active", "true")
        
        # Try to match by station code (string) or ROWID
        if from_station:
            if from_station.isdigit():
                cb.id_eq("From_Station", from_station)
            else:
                cb.eq("From_Station_Code", from_station.upper())
        
        if to_station:
            if to_station.isdigit():
                cb.id_eq("To_Station", to_station)
            else:
                cb.eq("To_Station_Code", to_station.upper())
        
        # Filter by day of week if journey_date provided
        if journey_date:
            day_name = self._get_day_from_date(journey_date)
            if day_name:
                cb.contains("Run_Days", day_name)
        
        criteria = cb.build()
        trains = self.get_records(TABLES['trains'], criteria=criteria, limit=100)
        
        # Filter by class availability if specified
        if travel_class and trains:
            class_field = self._get_capacity_field(travel_class)
            if class_field:
                trains = [t for t in trains if int(t.get(class_field) or 0) > 0]
        
        return trains

    def get_seat_availability_by_train(
        self,
        train_id: str,
        journey_date: str,
        travel_class: str = None
    ) -> Dict[str, Any]:
        """
        Get seat availability for a train on a date.
        
        Args:
            train_id: Train ROWID
            journey_date: Journey date (DD-MMM-YYYY format)
            travel_class: Specific class or None for all classes
        
        Returns:
            Dict with availability per class
        """
        classes = [travel_class] if travel_class else ['SL', '3A', '2A', '1A', 'CC', '2S']
        availability = {}
        
        for cls in classes:
            criteria = (
                CriteriaBuilder()
                .id_eq("Train", train_id)
                .eq("Journey_Date", journey_date)
                .eq("Class", cls)
                .build()
            )
            
            records = self.get_records(TABLES['train_inventory'], criteria=criteria, limit=1)
            
            if records:
                inv = records[0]
                total = int(inv.get('Total_Capacity') or 0)
                confirmed = int(inv.get('Confirmed_Count') or 0)
                rac = int(inv.get('RAC_Count') or 0)
                wl = int(inv.get('Waitlist_Count') or 0)
                
                available = max(0, total - confirmed)
                max_rac = total // 8
                rac_available = max(0, max_rac - rac)
                
                if available > 0:
                    status = 'AVAILABLE'
                elif rac_available > 0:
                    status = 'RAC'
                elif wl < 100:  # WAITLIST_LIMIT_PER_TRAIN
                    status = f'WL{wl + 1}'
                else:
                    status = 'REGRET'
                
                availability[cls] = {
                    'total': total,
                    'available': available,
                    'rac_available': rac_available,
                    'waitlist_count': wl,
                    'status': status
                }
            else:
                # No inventory - get from train capacity
                train = self.get_train_cached(train_id)
                if train:
                    capacity_field = f"Total_Seats_{cls}"
                    total = int(train.get(capacity_field) or 0)
                    availability[cls] = {
                        'total': total,
                        'available': total,
                        'rac_available': total // 8,
                        'waitlist_count': 0,
                        'status': 'AVAILABLE' if total > 0 else 'NA'
                    }
                else:
                    availability[cls] = {
                        'total': 0,
                        'available': 0,
                        'rac_available': 0,
                        'waitlist_count': 0,
                        'status': 'NA'
                    }
        
        return availability

    def create_booking_with_passengers(
        self,
        booking_data: Dict[str, Any],
        passengers: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Create a booking and its passengers atomically.
        
        Args:
            booking_data: Booking record data
            passengers: List of passenger records
        
        Returns:
            Dict with success status and created IDs
        """
        # Create booking first
        booking_result = self.create_record(TABLES['bookings'], booking_data)
        
        if not booking_result.get('success'):
            return {
                'success': False,
                'error': f"Failed to create booking: {booking_result.get('error')}"
            }
        
        booking_id = booking_result.get('data', {}).get('ROWID')
        
        if not booking_id:
            return {
                'success': False,
                'error': 'Booking created but no ID returned'
            }
        
        # Create passengers with booking reference
        passenger_ids = []
        errors = []
        
        for i, passenger in enumerate(passengers):
            passenger_data = {
                **passenger,
                'Booking_ID': booking_id
            }
            
            result = self.create_record(TABLES['passengers'], passenger_data)
            
            if result.get('success'):
                pid = result.get('data', {}).get('ROWID')
                passenger_ids.append(pid)
            else:
                errors.append(f"Passenger {i+1}: {result.get('error')}")
        
        if errors:
            logger.warning(f"Some passengers failed to create: {errors}")
        
        return {
            'success': True,
            'data': {
                'booking_id': booking_id,
                'pnr': booking_data.get('PNR'),
                'passenger_ids': passenger_ids,
                'errors': errors if errors else None
            }
        }

    def get_user_bookings(
        self,
        user_id: str,
        status: str = None,
        limit: int = 50
    ) -> List[Dict]:
        """
        Get bookings for a user.
        
        Args:
            user_id: User ROWID
            status: Filter by booking status (optional)
            limit: Max records to return
        
        Returns:
            List of booking records, newest first
        """
        cb = CriteriaBuilder().id_eq("User_ID", user_id)
        
        if status:
            cb.eq("Booking_Status", status)
        
        criteria = cb.build()
        
        # Execute with ORDER BY
        actual_table = self._resolve_table(TABLES['bookings'])
        query = f"SELECT * FROM {actual_table} WHERE {criteria} ORDER BY Booking_Time DESC LIMIT {limit}"
        
        result = self.execute_query(query)
        if result.get("success"):
            return result.get("data", {}).get("data", []) or []
        
        # Fallback without ordering
        return self.get_records(TABLES['bookings'], criteria=criteria, limit=limit)

    def get_booking_stats(self, days: int = 30) -> Dict[str, Any]:
        """
        Get booking statistics for dashboard.
        
        Args:
            days: Number of days to look back
        
        Returns:
            Dict with stats like total_bookings, revenue, etc.
        """
        from datetime import datetime, timedelta
        
        start_date = (datetime.now() - timedelta(days=days)).strftime('%d-%b-%Y')
        
        actual_table = self._resolve_table(TABLES['bookings'])
        
        # Total bookings in period
        total_query = f"SELECT COUNT(ROWID) as count FROM {actual_table} WHERE Booking_Time >= '{start_date}'"
        total_result = self.execute_query(total_query)
        total_bookings = 0
        if total_result.get('success'):
            data = total_result.get('data', {}).get('data', [])
            if data:
                total_bookings = int(data[0].get('count') or 0)
        
        # Confirmed bookings
        confirmed_query = f"SELECT COUNT(ROWID) as count FROM {actual_table} WHERE Booking_Status = 'confirmed' AND Booking_Time >= '{start_date}'"
        confirmed_result = self.execute_query(confirmed_query)
        confirmed_bookings = 0
        if confirmed_result.get('success'):
            data = confirmed_result.get('data', {}).get('data', [])
            if data:
                confirmed_bookings = int(data[0].get('count') or 0)
        
        # Cancelled bookings
        cancelled_query = f"SELECT COUNT(ROWID) as count FROM {actual_table} WHERE Booking_Status = 'cancelled' AND Booking_Time >= '{start_date}'"
        cancelled_result = self.execute_query(cancelled_query)
        cancelled_bookings = 0
        if cancelled_result.get('success'):
            data = cancelled_result.get('data', {}).get('data', [])
            if data:
                cancelled_bookings = int(data[0].get('count') or 0)
        
        return {
            'period_days': days,
            'total_bookings': total_bookings,
            'confirmed_bookings': confirmed_bookings,
            'cancelled_bookings': cancelled_bookings,
            'confirmation_rate': round(confirmed_bookings / max(total_bookings, 1) * 100, 1)
        }

    def _get_day_from_date(self, date_str: str) -> Optional[str]:
        """Get day name from date string."""
        from datetime import datetime
        
        # Try DD-MMM-YYYY format
        for fmt in ['%d-%b-%Y', '%Y-%m-%d', '%d/%m/%Y']:
            try:
                dt = datetime.strptime(date_str, fmt)
                return dt.strftime('%A')[:3]  # Mon, Tue, etc.
            except ValueError:
                continue
        return None

    def _get_capacity_field(self, travel_class: str) -> Optional[str]:
        """Get the capacity field name for a travel class."""
        mapping = {
            'SL': 'Total_Seats_SL',
            '3A': 'Total_Seats_3A',
            '2A': 'Total_Seats_2A',
            '1A': 'Total_Seats_1A',
            'CC': 'Total_Seats_CC',
            'EC': 'Total_Seats_EC',
            '2S': 'Total_Seats_2S',
        }
        return mapping.get(travel_class.upper())


# ── Global singleton ──────────────────────────────────────────────────────────
cloudscale_repo = CloudScaleRepository()
