"""
CloudScale Repository — Data access layer for Zoho Catalyst CloudScale.
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
from typing import Optional, List, Dict, Any, Tuple

from repositories.cache_manager import cache
from config import TABLES, get_table

logger = logging.getLogger(__name__)

# Catalyst SDK - imported at function initialization
_zcatalyst_sdk = None
_catalyst_app = None


def init_catalyst(catalyst_app):
    """Initialize Catalyst SDK with the app instance from request context."""
    global _catalyst_app
    _catalyst_app = catalyst_app


def get_catalyst_app():
    """Get initialized Catalyst app instance."""
    global _catalyst_app
    return _catalyst_app


# ════════════════════════════════════════════════════════════════════════════
#  CRITERIA BUILDER (ZCQL compatible)
# ════════════════════════════════════════════════════════════════════════════

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
        escaped = ", ".join([f"'{self._esc(v)}'" for v in values])
        self._parts.append(f"{field} IN ({escaped})")
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


# ════════════════════════════════════════════════════════════════════════════
#  TABLE CONFIGURATION (imported from config.py)
# ════════════════════════════════════════════════════════════════════════════

# TABLES imported from config.py - single source of truth


# ════════════════════════════════════════════════════════════════════════════
#  CLOUDSCALE REPOSITORY
# ════════════════════════════════════════════════════════════════════════════

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

    @property
    def forms(self) -> Dict[str, Dict[str, str]]:
        """
        Backward-compatible forms/reports config.
        Both 'forms' and 'reports' point to the same CloudScale tables.
        """
        return {
            'forms': self._tables,
            'reports': self._tables,
        }

    def _get_zcql(self):
        """Get ZCQL service from Catalyst app."""
        app = get_catalyst_app()
        if not app:
            raise RuntimeError("Catalyst app not initialized. Call init_catalyst() first.")
        return app.zcql()

    def _get_datastore(self):
        """Get Datastore service for row operations."""
        app = get_catalyst_app()
        if not app:
            raise RuntimeError("Catalyst app not initialized. Call init_catalyst() first.")
        return app.datastore()

    # ════════════════════════════════════════════════════════════════════════
    #  ZCQL QUERY EXECUTION
    # ════════════════════════════════════════════════════════════════════════

    def execute_query(self, query: str) -> Dict[str, Any]:
        """Execute a ZCQL SELECT query."""
        try:
            zcql = self._get_zcql()
            result = zcql.execute_query(query)

            # ZCQL returns list of dicts
            if isinstance(result, list):
                # Extract table name from nested response
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

    # ════════════════════════════════════════════════════════════════════════
    #  CRUD OPERATIONS
    # ════════════════════════════════════════════════════════════════════════

    def create_record(self, table_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a single record in a CloudScale table."""
        try:
            # Resolve table name
            actual_table = self._tables.get(table_name.lower(), table_name)

            datastore = self._get_datastore()
            table = datastore.table(actual_table)

            # Insert row
            result = table.insert_row(data)

            # Get the created row ID
            row_id = result.get('ROWID') if isinstance(result, dict) else None

            return {
                "success": True,
                "data": {"data": [{"Details": {"ID": row_id}, **data}]},
                "status_code": 201
            }

        except Exception as exc:
            logger.error(f"Create record error in {table_name}: {exc}")
            return {"success": False, "error": str(exc)}

    def get_all_records(
        self,
        table_name: str,
        criteria: Optional[str] = None,
        limit: int = 200,
        from_index: int = 1,
        order_by: Optional[str] = None
    ) -> Dict[str, Any]:
        """Fetch records from a CloudScale table with optional criteria filter."""
        try:
            # Resolve table name
            actual_table = self._tables.get(table_name.lower(), table_name)

            # Build ZCQL query
            query = f"SELECT * FROM {actual_table}"

            if criteria:
                query += f" WHERE {criteria}"

            if order_by:
                query += f" ORDER BY {order_by}"
            else:
                query += " ORDER BY ROWID DESC"

            query += f" LIMIT {limit}"

            if from_index > 1:
                query += f" OFFSET {from_index - 1}"

            return self.execute_query(query)

        except Exception as exc:
            logger.error(f"Get all records error from {table_name}: {exc}")
            return {"success": False, "error": str(exc)}

    def get_record_by_id(self, table_name: str, record_id: str) -> Dict[str, Any]:
        """Fetch a single record by ROWID."""
        try:
            actual_table = self._tables.get(table_name.lower(), table_name)

            query = f"SELECT * FROM {actual_table} WHERE ROWID = {record_id}"
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
            actual_table = self._tables.get(table_name.lower(), table_name)

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
            actual_table = self._tables.get(table_name.lower(), table_name)

            datastore = self._get_datastore()
            table = datastore.table(actual_table)

            table.delete_row(int(record_id))

            return {"success": True, "data": None, "status_code": 204}

        except Exception as exc:
            logger.error(f"Delete record error from {table_name}: {exc}")
            return {"success": False, "error": str(exc)}

    # ── Alias helpers (backward-compat) ───────────────────────────────────────

    def get_records(self, table_name: str, criteria: Optional[str] = None, limit: int = 200) -> List[Dict]:
        """Return list of data rows directly."""
        result = self.get_all_records(table_name, criteria=criteria, limit=limit)
        if result.get("success"):
            return result.get("data", {}).get("data", []) or []
        return []

    def add_record(self, table_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Alias for create_record."""
        return self.create_record(table_name, data)

    # ════════════════════════════════════════════════════════════════════════
    #  CACHED READ OPERATIONS
    # ════════════════════════════════════════════════════════════════════════

    def get_all_stations_cached(self, ttl: int = 86400) -> List[Dict]:
        """Stations list — cached 24h."""
        key = "stations:all"
        hit = cache.get(key)
        if hit is not None:
            return hit
        records = self.get_records(TABLES['stations'], limit=500)
        cache.set(key, records, ttl=ttl)
        return records

    def get_all_trains_cached(self, ttl: int = 3600) -> List[Dict]:
        """Trains list — cached 1h."""
        key = "trains:all"
        hit = cache.get(key)
        if hit is not None:
            return hit
        records = self.get_records(TABLES['trains'], limit=500)
        cache.set(key, records, ttl=ttl)
        return records

    def get_train_cached(self, train_id: str, ttl: int = 3600) -> Optional[Dict]:
        """Single train record — cached 1h."""
        key = f"train:{train_id}"
        hit = cache.get(key)
        if hit is not None:
            return hit
        result = self.get_record_by_id(TABLES['trains'], train_id)
        if result.get("success") and result.get("data"):
            cache.set(key, result["data"], ttl=ttl)
            return result["data"]
        return None

    def get_user_cached(self, user_id: str, ttl: int = 900) -> Optional[Dict]:
        """User record — cached 15 min."""
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

    # ════════════════════════════════════════════════════════════════════════
    #  BATCH OPERATIONS
    # ════════════════════════════════════════════════════════════════════════

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
                row_id = result.get("data", {}).get("data", [{}])[0].get("Details", {}).get("ID", f"row_{i}")
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

    # ════════════════════════════════════════════════════════════════════════
    #  OPTIMIZED QUERIES
    # ════════════════════════════════════════════════════════════════════════

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
            # For CloudScale, From_Station stores station ID
            # We need to join or filter differently
            cb.contains("From_Station", source.upper())

        if destination:
            cb.contains("To_Station", destination.upper())

        criteria = cb.build()
        return self.get_records(TABLES['trains'], criteria=criteria, limit=500)

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
        records = self.get_records(TABLES['bookings'], criteria=criteria, limit=100)
        return len(records)

    # ════════════════════════════════════════════════════════════════════════
    #  USER QUERIES (Authentication)
    # ════════════════════════════════════════════════════════════════════════

    def get_user_by_email(self, email: str) -> Optional[Dict]:
        """Find user by email address."""
        criteria = CriteriaBuilder().eq("Email", email.lower()).build()
        records = self.get_records(TABLES['users'], criteria=criteria, limit=1)
        return records[0] if records else None

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


# ── Global singleton ─────────────────────────────────────────────────────────
cloudscale_repo = CloudScaleRepository()

# Backward compatibility alias (for existing code that imports zoho_repo)
zoho_repo = cloudscale_repo
