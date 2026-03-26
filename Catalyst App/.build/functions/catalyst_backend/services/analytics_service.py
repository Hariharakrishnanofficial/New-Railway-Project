"""
Analytics Service — booking trends, occupancy, revenue, and user insights.
Uses CloudScale (ZCQL) for all database operations with caching.
"""

import logging
from datetime import datetime, timedelta
from collections import defaultdict

from config import TABLES
from repositories.cloudscale_repository import cloudscale_repo
from repositories.cache_manager import cache

logger = logging.getLogger(__name__)

# Cache TTL constants
TTL_OVERVIEW = 600  # 10 minutes


class AnalyticsService:
    """Analytics service using CloudScale queries."""

    def __init__(self):
        self.tables = TABLES

    def get_overview_stats(self) -> dict:
        """Aggregated dashboard stats — cached 10 min."""
        cache_key = "analytics:overview"
        cached    = cache.get(cache_key)
        if cached:
            return cached

        # Fetch all counts in parallel-ish (sequential but cached)
        stations_count = len(cloudscale_repo.get_all_stations_cached())
        trains_count   = len(cloudscale_repo.get_all_trains_cached())
        users_count    = len(cloudscale_repo.get_records(TABLES['users'], limit=500))
        all_bookings   = cloudscale_repo.get_records(TABLES['bookings'], limit=1000)

        today_str = datetime.now().strftime("%d-%b-%Y")
        today_ymd = datetime.now().strftime("%Y-%m-%d")

        bookings_today  = 0
        revenue_today   = 0.0
        revenue_total   = 0.0
        status_breakdown = defaultdict(int)
        class_breakdown  = defaultdict(int)

        for b in all_bookings:
            status = (b.get("Booking_Status") or "unknown").lower()
            cls    = b.get("Class", "Unknown")
            fare   = float(b.get("Total_Fare") or 0)

            status_breakdown[status] += 1
            class_breakdown[cls]     += 1

            if status != "cancelled":
                revenue_total += fare

            bt = str(b.get("Booking_Time") or b.get("Added_Time") or "").strip()
            if bt.startswith(today_str) or bt[:10] == today_ymd:
                bookings_today += 1
                if status != "cancelled":
                    revenue_today += fare

        stats = {
            "total_stations":      stations_count,
            "total_trains":        trains_count,
            "total_users":         users_count,
            "total_bookings":      len(all_bookings),
            "bookings_today":      bookings_today,
            "revenue_today":       round(revenue_today, 2),
            "revenue_total":       round(revenue_total, 2),
            "bookings_by_status":  dict(status_breakdown),
            "bookings_by_class":   dict(class_breakdown),
        }

        cache.set(cache_key, stats, ttl=TTL_OVERVIEW)
        return stats

    def get_booking_trends(self, days: int = 30) -> dict:
        """Day-wise booking counts for last N days."""
        cache_key = f"analytics:trends:{days}"
        cached    = cache.get(cache_key)
        if cached:
            return cached

        all_bookings = cloudscale_repo.get_records(TABLES['bookings'], limit=1000)
        cutoff       = datetime.now() - timedelta(days=days)
        daily        = defaultdict(lambda: {"confirmed": 0, "cancelled": 0, "revenue": 0.0})

        for b in all_bookings:
            bt  = str(b.get("Booking_Time") or b.get("Added_Time") or "")
            try:
                dt = datetime.strptime(bt.split(" ")[0], "%d-%b-%Y")
            except Exception:
                continue
            if dt < cutoff:
                continue
            date_key = dt.strftime("%Y-%m-%d")
            status   = (b.get("Booking_Status") or "").lower()
            fare     = float(b.get("Total_Fare") or 0)
            if status == "cancelled":
                daily[date_key]["cancelled"] += 1
            else:
                daily[date_key]["confirmed"] += 1
                daily[date_key]["revenue"]   += fare

        result = {"days": days, "daily": dict(daily)}
        cache.set(cache_key, result, ttl=600)
        return result

    def get_top_trains(self, top_n: int = 10) -> list:
        """Most booked trains by total booking count."""
        cache_key = f"analytics:top_trains:{top_n}"
        cached    = cache.get(cache_key)
        if cached:
            return cached

        all_bookings = cloudscale_repo.get_records(TABLES['bookings'], limit=1000)
        train_counts = defaultdict(lambda: {"count": 0, "revenue": 0.0, "name": ""})

        for b in all_bookings:
            if (b.get("Booking_Status") or "").lower() == "cancelled":
                continue
            t_field   = b.get("Trains", {})
            t_id      = t_field.get("ID", "") if isinstance(t_field, dict) else str(t_field or "")
            t_name    = t_field.get("display_value", t_id) if isinstance(t_field, dict) else t_id
            fare      = float(b.get("Total_Fare") or 0)
            train_counts[t_id]["count"]   += 1
            train_counts[t_id]["revenue"] += fare
            if not train_counts[t_id]["name"]:
                train_counts[t_id]["name"] = t_name

        top = sorted(train_counts.items(), key=lambda x: x[1]["count"], reverse=True)[:top_n]
        result = [{"train_id": tid, **data} for tid, data in top]

        cache.set(cache_key, result, ttl=TTL_OVERVIEW)
        return result

    def get_route_popularity(self) -> list:
        """Top origin-destination pairs by booking volume."""
        cache_key = "analytics:routes"
        cached    = cache.get(cache_key)
        if cached:
            return cached

        all_bookings = cloudscale_repo.get_records(TABLES['bookings'], limit=1000)
        trains_map   = {t.get("ID"): t for t in cloudscale_repo.get_all_trains_cached()}

        route_counts = defaultdict(int)
        for b in all_bookings:
            if (b.get("Booking_Status") or "").lower() == "cancelled":
                continue
            t_field = b.get("Trains", {})
            t_id    = t_field.get("ID", "") if isinstance(t_field, dict) else str(t_field or "")
            train   = trains_map.get(t_id, {})
            def get_code(f):
                if isinstance(f, dict):
                    dv = f.get("display_value", "")
                    return dv.split("-")[0].strip().upper()
                return str(f or "").split("-")[0].strip().upper()
            src = get_code(train.get("From_Station", {}))
            dst = get_code(train.get("To_Station", {}))
            if src and dst:
                route_counts[f"{src} → {dst}"] += 1

        result = sorted(
            [{"route": r, "count": c} for r, c in route_counts.items()],
            key=lambda x: x["count"],
            reverse=True
        )[:20]

        cache.set(cache_key, result, ttl=TTL_OVERVIEW)
        return result

    def get_class_revenue(self) -> dict:
        """Revenue breakdown by travel class."""
        all_bookings = cloudscale_repo.get_records(TABLES['bookings'], limit=1000)
        class_rev    = defaultdict(float)
        class_cnt    = defaultdict(int)

        for b in all_bookings:
            if (b.get("Booking_Status") or "").lower() == "cancelled":
                continue
            cls  = b.get("Class", "Unknown")
            fare = float(b.get("Total_Fare") or 0)
            class_rev[cls] += fare
            class_cnt[cls] += 1

        return {
            "revenue_by_class": {k: round(v, 2) for k, v in class_rev.items()},
            "bookings_by_class": dict(class_cnt),
        }


# Singleton
analytics_service = AnalyticsService()
