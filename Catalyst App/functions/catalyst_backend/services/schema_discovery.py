"""
schema_discovery.py — Dynamic schema discovery for CloudScale.

Automatically discovers all tables and their fields from CloudScale ZCQL.
Builds MCP query prompts dynamically at runtime.

Features:
- Fetches all tables from CloudScale
- Gets field metadata via ZCQL introspection
- Caches schema for performance (refreshes hourly)
- Generates MCP prompt dynamically
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from config import TABLES
from repositories.cache_manager import cache
from repositories.cloudscale_repository import cloudscale_repo, get_catalyst_app

logger = logging.getLogger(__name__)


class SchemaDiscovery:
    """
    Dynamically discovers CloudScale schema (tables, fields).
    """

    CACHE_TTL = 3600  # 1 hour cache for schema

    def __init__(self):
        self._schema_cache: Optional[Dict] = None
        self._last_refresh: Optional[datetime] = None

    def _get_zcql(self):
        """Get ZCQL service from Catalyst app."""
        app = get_catalyst_app()
        if not app:
            raise RuntimeError("Catalyst app not initialized")
        return app.zcql()

    def get_all_tables(self) -> List[str]:
        """
        Get all configured CloudScale tables.
        Returns list of table names.
        """
        cache_key = "schema:tables"
        cached = cache.get(cache_key)
        if cached:
            return cached

        # Use configured tables from config.py
        tables = list(TABLES.values())
        cache.set(cache_key, tables, ttl=self.CACHE_TTL)
        return tables

    def get_table_fields(self, table_name: str) -> List[Dict]:
        """
        Fetch field metadata for a specific table by sampling a record.
        Returns list of field definitions.
        """
        cache_key = f"schema:fields:{table_name}"
        cached = cache.get(cache_key)
        if cached:
            return cached

        try:
            # Sample one record to discover fields
            query = f"SELECT * FROM {table_name} LIMIT 1"
            result = cloudscale_repo.execute_query(query)

            if result.get("success"):
                records = result.get("data", {}).get("data", [])
                if records and len(records) > 0:
                    sample = records[0]
                    fields = []
                    for key in sample.keys():
                        # Skip system fields
                        if key.startswith("zc_") or key == "ROWID":
                            continue
                        fields.append({
                            "name": key,
                            "link_name": key,
                            "type": self._infer_type(sample.get(key))
                        })
                    cache.set(cache_key, fields, ttl=self.CACHE_TTL)
                    return fields

            # If no records, return common fields based on table name
            return self._get_default_fields(table_name)

        except Exception as e:
            logger.warning(f"Failed to get fields for {table_name}: {e}")
            return self._get_default_fields(table_name)

    def _infer_type(self, value: Any) -> str:
        """Infer field type from sample value."""
        if value is None:
            return "text"
        if isinstance(value, bool):
            return "boolean"
        if isinstance(value, int):
            return "number"
        if isinstance(value, float):
            return "decimal"
        return "text"

    def _get_default_fields(self, table_name: str) -> List[Dict]:
        """Return default fields based on table name."""
        # Common fields for each table type
        defaults = {
            "Users": ["Email", "Full_Name", "Phone", "Role", "Account_Status", "Created_At"],
            "Stations": ["Station_Code", "Station_Name", "City", "State", "Zone"],
            "Trains": ["Train_Number", "Train_Name", "Train_Type", "From_Station", "To_Station", "Departure_Time", "Arrival_Time", "Is_Active"],
            "Train_Routes": ["Train_ID", "Notes"],
            "Route_Stops": ["Sequence", "Station_Name", "Station_Code", "Arrival_Time", "Departure_Time", "Distance_KM", "Day_Count"],
            "Coach_Layouts": ["Class_Code", "Class_Name", "Total_Seats", "Berth_Types"],
            "Train_Inventory": ["Train_ID", "Journey_Date", "Available_Seats_SL", "Available_Seats_3A", "Available_Seats_2A", "Available_Seats_1A"],
            "Fares": ["Train_ID", "Class_Code", "From_Station_ID", "To_Station_ID", "Base_Fare", "Reservation_Fee"],
            "Quotas": ["Quota_Code", "Quota_Name", "Description", "Max_Percentage"],
            "Bookings": ["PNR", "User_ID", "Train_ID", "Journey_Date", "Source_Station_ID", "Destination_Station_ID", "Class_Code", "Quota_Type", "Passenger_Count", "Total_Fare", "Booking_Status", "Payment_Status"],
            "Passengers": ["Booking_ID", "Passenger_Name", "Age", "Gender", "Seat_Number", "Coach", "Berth_Type", "Status"],
            "Announcements": ["Title", "Message", "Type", "Is_Active", "Start_Date", "End_Date"],
            "Admin_Logs": ["Admin_Email", "Action", "Entity_Type", "Entity_ID", "Details", "Timestamp"],
            "Settings": ["Key", "Value", "Description"],
            "Password_Reset_Tokens": ["User_ID", "Token", "Expires_At"],
        }

        fields = defaults.get(table_name, ["ID", "Name", "Status", "Created_At"])
        return [{"name": f, "link_name": f, "type": "text"} for f in fields]

    def discover_all_schemas(self, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Discover complete schema: all tables and their fields.
        Returns structured schema dictionary.
        """
        cache_key = "schema:complete"

        # Check cache first (unless force refresh)
        if not force_refresh:
            cached = cache.get(cache_key)
            if cached:
                logger.debug("Using cached schema")
                return cached

        logger.info("Discovering CloudScale schema...")

        schema = {
            "tables": {},
            "discovered_at": datetime.now().isoformat(),
            "discovery_method": "cloudscale_zcql",
        }

        # Discover each configured table
        for key, table_name in TABLES.items():
            try:
                fields = self.get_table_fields(table_name)
                display_name = key.replace("_", " ").title()

                schema["tables"][table_name] = {
                    "display_name": display_name,
                    "table_name": table_name,
                    "key": key,
                    "fields": fields,
                }
                logger.debug(f"Discovered {len(fields)} fields for {table_name}")

            except Exception as e:
                logger.warning(f"Failed to discover {table_name}: {e}")
                continue

        # Cache the complete schema
        cache.set(cache_key, schema, ttl=self.CACHE_TTL)
        logger.info(f"Schema discovered: {len(schema['tables'])} tables")

        return schema

    def get_queryable_modules(self) -> Dict[str, List[str]]:
        """
        Get a simplified mapping of module names to their field names.
        This is what the MCP query generator needs.
        """
        cache_key = "schema:queryable"
        cached = cache.get(cache_key)
        if cached:
            return cached

        schema = self.discover_all_schemas()

        modules = {}
        for table_name, table_data in schema.get("tables", {}).items():
            display_name = table_data.get("display_name", table_name)
            fields = table_data.get("fields", [])

            field_names = [f.get("link_name") or f.get("name", "") for f in fields]
            field_names = [f for f in field_names if f]

            if field_names:
                modules[display_name] = field_names

        cache.set(cache_key, modules, ttl=self.CACHE_TTL)
        return modules

    def get_table_for_module(self, module_name: str) -> Optional[str]:
        """
        Find the table name for a given module/display name.
        Handles both display names and table names.
        """
        schema = self.discover_all_schemas()
        module_lower = module_name.lower().replace(" ", "_")

        # Try exact match in tables
        for table_name, table_data in schema.get("tables", {}).items():
            display_name = table_data.get("display_name", "")
            key = table_data.get("key", "")

            # Match by display name
            if display_name.lower() == module_name.lower():
                return table_name

            # Match by key
            if key.lower() == module_lower:
                return table_name

            # Match by table name
            if table_name.lower() == module_lower or table_name.lower() == module_name.lower():
                return table_name

        # Try direct table name from config
        if module_name in TABLES.values():
            return module_name

        # Try key lookup
        if module_lower in TABLES:
            return TABLES[module_lower]

        return None

    def build_mcp_prompt(self) -> str:
        """
        Dynamically build the MCP query prompt based on discovered schema.
        """
        modules = self.get_queryable_modules()

        # Build module descriptions
        module_lines = []
        for module_name, fields in sorted(modules.items()):
            field_str = ", ".join(fields[:15])
            if len(fields) > 15:
                field_str += ", ..."
            module_lines.append(f"**{module_name}** — {field_str}")

        modules_section = "\n".join(module_lines)

        prompt = f"""You are a query generator for a Railway Ticketing System database (CloudScale).
Convert the user's natural language query into a structured MCP query.

Available modules and their fields (dynamically discovered):

{modules_section}

User query: "{{USER_QUERY}}"

Output ONLY valid JSON in this format:
{{"method":"GET","module":"<module_name>","filters":{{<field>:<value>}}}}

Use empty filters {{}} to get all records.
Only use GET method.

IMPORTANT: Match the module name EXACTLY as shown above (case-sensitive).

Examples:
- "Show all stations" → {{"method":"GET","module":"Stations","filters":{{}}}}
- "Find trains from Chennai" → {{"method":"GET","module":"Trains","filters":{{"From_Station":"Chennai"}}}}
- "Show all users" → {{"method":"GET","module":"Users","filters":{{}}}}

If the query cannot be converted to a database query, output:
{{"method":"NONE","reason":"<explanation>"}}
"""
        return prompt

    def get_module_for_query(self, user_query: str) -> Optional[str]:
        """
        Find the best matching module for a user query.
        Uses fuzzy matching against module names.
        """
        modules = self.get_queryable_modules()
        query_lower = user_query.lower()

        # Direct match
        for module_name in modules.keys():
            if module_name.lower() in query_lower:
                return module_name

        # Partial match - check words
        for module_name in modules.keys():
            for word in module_name.lower().replace("_", " ").split():
                if len(word) > 3 and word in query_lower:
                    return module_name

        return None

    def refresh_schema(self):
        """Force refresh the schema cache."""
        cache.delete("schema:complete")
        cache.delete("schema:queryable")
        cache.delete("schema:tables")
        # Clear all field caches
        for table_name in TABLES.values():
            cache.delete(f"schema:fields:{table_name}")
        return self.discover_all_schemas(force_refresh=True)


# Global singleton
schema_discovery = SchemaDiscovery()
