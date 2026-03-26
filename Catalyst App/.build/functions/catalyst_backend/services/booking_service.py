"""
Booking Service — orchestrates the full booking workflow.
Uses CloudScale (ZCQL) for all database operations.
"""

import json
import random
import string
import logging
from datetime import datetime, timedelta

from config import TABLES, BOOKING_ADVANCE_DAYS
from repositories.cloudscale_repository import zoho_repo, CriteriaBuilder
from repositories.cache_manager import cache
from utils.seat_allocation import process_booking_allocation, process_booking_cancellation, calculate_refund, promote_waitlist
from utils.date_helpers import to_zoho_date_only, to_zoho_datetime
from utils.fare_helper import get_fare_for_journey
from core.exceptions import (
    BookingNotFoundError, TrainNotFoundError, DuplicateBookingError,
    BookingLimitError, InvalidDateError, BookingAlreadyCancelledError, ValidationError
)

logger = logging.getLogger(__name__)


def _generate_pnr() -> str:
    """
    Generate PNR in IRCTC format: PNR + 8 uppercase alphanumeric = 11 chars total.
    Example: PNRX7K2P9W1
    Checks database for uniqueness before returning.
    """
    for _ in range(10):  # max 10 attempts
        suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=8))
        pnr = f"PNR{suffix}"
        # Check uniqueness using ZCQL criteria
        try:
            criteria = CriteriaBuilder().eq("PNR", pnr).build()
            existing = zoho_repo.get_records(TABLES['bookings'], criteria=criteria, limit=1)
            if not existing:
                return pnr
        except Exception:
            # On error, still return (collision risk very low)
            logger.warning(f"Could not verify PNR uniqueness for {pnr}. Proceeding anyway.")
            return pnr
    # Fallback: highly unlikely to reach here
    final_pnr = f"PNR{''.join(random.choices(string.ascii_uppercase + string.digits, k=8))}"
    logger.error(f"Failed to generate a unique PNR after 10 attempts. Using fallback: {final_pnr}")
    return final_pnr


class BookingService:
    """Service layer for all booking operations using CloudScale."""

    def __init__(self):
        self.tables = TABLES

    # ════════════════════════════════════════════════════════════════════════
    #  CREATE BOOKING
    # ════════════════════════════════════════════════════════════════════════

    def create(self, data: dict) -> dict:
        """
        Full booking creation workflow.
        Returns: { PNR, Booking_Status, Total_Fare, passengers, record }
        Raises: RailwayException subclasses on failure.
        """
        # ── Extract fields ──────────────────────────────────────────────────
        train_id     = data.get("train_id") or data.get("Trains") or data.get("Train", "")
        user_id      = data.get("user_id")  or data.get("Users", "")
        cls          = data.get("Class", "SL")
        journey_date = data.get("Journey_Date", "")
        passengers   = data.get("Passengers") or data.get("passengers", [])
        quota        = data.get("Quota", "General")

        if isinstance(train_id, dict): train_id = train_id.get("ID", "")
        if isinstance(user_id, dict):  user_id  = user_id.get("ID", "")

        if not train_id:      raise ValidationError("train_id is required")
        if not user_id:       raise ValidationError("user_id is required")
        if not journey_date:  raise ValidationError("Journey_Date is required")
        if not passengers:    raise ValidationError("At least one passenger is required")
        if len(passengers) > 6: raise ValidationError("Maximum 6 passengers per booking")

        # ── Normalize Passengers for Zoho ───────────────────────────────────
        normalized_passengers = []
        for p in passengers:
            np = {
                "Name":            p.get("name")      or p.get("Name", ""),
                "Age":             p.get("age")       or p.get("Age", ""),
                "Gender":          p.get("gender")    or p.get("Gender", "Male"),
                "Berth_Preference": p.get("berthPref") or p.get("Berth_Preference", "No Preference")
            }
            normalized_passengers.append(np)
        passengers = normalized_passengers

        # ── Date validation ─────────────────────────────────────────────────
        try:
            dt_jd = datetime.strptime(journey_date.split(" ")[0], "%Y-%m-%d")
        except Exception:
            try:
                dt_jd = datetime.strptime(journey_date.split(" ")[0], "%d-%b-%Y")
            except Exception:
                raise InvalidDateError("Invalid Journey_Date format. Use YYYY-MM-DD")

        today    = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        max_date = today + timedelta(days=BOOKING_ADVANCE_DAYS)

        if dt_jd < today:      raise InvalidDateError("Cannot book for past dates")
        if dt_jd > max_date:   raise InvalidDateError(f"Cannot book more than {BOOKING_ADVANCE_DAYS} days in advance")

        # ── Fetch train (cached) ─────────────────────────────────────────────
        train = zoho_repo.get_train_cached(train_id)
        if not train:
            raise TrainNotFoundError(train_id)

        # ── Fetch user (cached) + booking limit check ────────────────────────
        user = zoho_repo.get_user_cached(user_id)
        if not user:
            raise ValidationError("User not found")

        is_verified = str(user.get("Is_Aadhar_Verified", "false")).lower() == "true"
        max_limit   = 12 if is_verified else 6

        now         = datetime.now()
        start_month = now.replace(day=1).strftime("%d-%b-%Y %H:%M:%S")
        monthly_count = zoho_repo.count_monthly_bookings(user_id, start_month)
        if monthly_count >= max_limit:
            raise BookingLimitError(max_limit)

        # ── Duplicate booking check ─────────────────────────────────────────
        zoho_date = to_zoho_date_only(journey_date)
        dup_criteria = (
            CriteriaBuilder()
            .id_eq("User_ID", user_id)
            .id_eq("Train_ID", train_id)
            .eq("Journey_Date", zoho_date)
            .ne("Booking_Status", "Cancelled")
            .build()
        )
        existing = zoho_repo.get_records(TABLES['bookings'], criteria=dup_criteria, limit=1)
        if existing:
            raise DuplicateBookingError()

        # ── Fare calculation ─────────────────────────────────────────────────
        from_id = data.get("Boarding_Station") or (train.get("From_Station", {}).get("ID", "") if isinstance(train.get("From_Station"), dict) else "")
        to_id   = data.get("Deboarding_Station") or (train.get("To_Station", {}).get("ID", "") if isinstance(train.get("To_Station"), dict) else "")

        fare_per_person  = get_fare_for_journey(train_id, from_id, to_id, cls, train_record=train, quota=quota)
        chargeable_count = sum(1 for p in passengers if not p.get("Is_Child", False))
        total_fare       = fare_per_person * chargeable_count

        # ── Seat allocation ──────────────────────────────────────────────────
        passengers, booking_status = process_booking_allocation(train_id, cls, journey_date, passengers)

        pnr = _generate_pnr()
        for p in passengers:
            p['PNR'] = pnr

        payload = {
            "PNR":             pnr,
            "User_ID":         user_id,
            "Train_ID":        train_id,
            "Journey_Date":    zoho_date,
            "Class":           cls,
            "Quota":           quota,
            "Num_Passengers":  len(passengers),
            "Total_Fare":      total_fare,
            "Booking_Status":  booking_status,
            "Payment_Status":  "pending",
            "Payment_Method":  data.get("Payment_Method", "online"),
            "Passengers":      passengers,
            "Booking_Time":    to_zoho_datetime(None),
        }
        if data.get("Boarding_Station"):   payload["Boarding_Station_ID"]   = data["Boarding_Station"]
        if data.get("Deboarding_Station"): payload["Deboarding_Station_ID"] = data["Deboarding_Station"]

        result = zoho_repo.create_record(TABLES['bookings'], payload)
        if not result.get("success"):
            raise ValidationError(result.get("error", "Failed to create booking"))

        # ── Sync passengers to Passengers form ────────────────────────────────
        booking_id = ""
        try:
            # Extract new booking record ID from Zoho response
            res_data = result.get("data", {})
            if isinstance(res_data, dict):
                # Zoho response format can vary slightly
                data_list = res_data.get("data", [])
                if isinstance(data_list, list) and data_list:
                    # Standard create response: { data: [{ details: { ID: "..." } }] }
                    details = data_list[0].get("details", {})
                    if not details: # Fallback for other formats
                         details = data_list[0].get("Details", {})
                    booking_id = details.get("ID", "")
                elif isinstance(data_list, dict):
                    # Sometimes it's just the record dict
                    booking_id = data_list.get("ID", "")
        except (AttributeError, IndexError, TypeError) as e:
            logger.error(f"Could not extract booking ID from Zoho response: {e}. Response was: {result}")


        if booking_id:
            logger.info(f"New booking created with ID: {booking_id}. Syncing passengers to Passengers form.")
            self._sync_passengers_to_form(booking_id, passengers)
        else:
            logger.error("Failed to get new booking ID. Cannot sync passengers to Passengers form.")

        # Invalidate inventory cache for this train+date+class
        zoho_repo.invalidate_inventory_cache(train_id, zoho_date, cls)

        return {
            "PNR":            pnr,
            "Booking_Status": booking_status,
            "Total_Fare":     total_fare,
            "passengers":     passengers,
            "record":         result.get("data", {}),
        }

    def _sync_passengers_to_form(self, booking_id: str, passengers: list):
        """
        Creates a separate record in the 'Passengers' form for each passenger
        in a booking, linking them via a lookup field.
        
        Args:
            booking_id (str): The ID of the parent booking record.
            passengers (list): The list of passenger dictionaries from the booking.
        """
        passengers_table = TABLES['passengers']
        
        for i, p in enumerate(passengers):
            try:
                pax_payload = {
                    "Passenger_Name":  p.get("Name") or p.get("Passenger_Name", ""),
                    "Age":             p.get("Age", ""),
                    "Gender":          p.get("Gender", "Male"),
                    "Booking_ID":      booking_id, # Link to the booking record
                    "Berth_Preference": p.get("Berth_Preference") or p.get("berthPref", "No Preference"),
                    "Is_Child":        str(p.get("Is_Child", False)).lower(),
                    "Current_Status":  p.get("Current_Status", ""),
                    "Coach":           p.get("Coach", ""),
                    "Seat_Number":     p.get("Seat_Number") or p.get("Seat", ""),
                    "Berth_Type":      p.get("Berth", ""),
                }
                # Using a fire-and-forget approach for performance.
                # A more robust system might use a background queue.
                zoho_repo.create_record(passengers_table, pax_payload)
                logger.info(f"Queued sync for passenger {i+1} for booking {booking_id}")

            except Exception as pax_err:
                logger.error(f"Failed to queue sync for passenger {i+1} in booking {booking_id}: {pax_err}")

    # ════════════════════════════════════════════════════════════════════════
    #  CANCEL BOOKING
    # ════════════════════════════════════════════════════════════════════════

    def cancel(self, booking_id: str) -> dict:
        """Full cancellation with auto-refund and waitlist promotion."""
        bk = zoho_repo.get_record_by_id(TABLES['bookings'], booking_id)
        if not bk.get("success"):
            raise BookingNotFoundError(booking_id)

        booking = bk.get("data", {}).get("data") or bk.get("data") or {}

        if (booking.get("Booking_Status") or "").lower() == "cancelled":
            raise BookingAlreadyCancelledError()

        total_fare = float(booking.get("Total_Fare") or 0)
        cls        = booking.get("Class", "SL")
        quota      = booking.get("Quota", "General")
        jd         = booking.get("Journey_Date", "")
        dep_time   = booking.get("Departure_Time", "06:00")

        try:
            dt_jd = datetime.strptime(jd.split(" ")[0], "%d-%b-%Y")
        except Exception:
            try:
                dt_jd = datetime.strptime(jd.split(" ")[0], "%Y-%m-%d")
            except Exception:
                dt_jd = datetime.now() + timedelta(days=7)

        departure_str = dt_jd.strftime("%d-%b-%Y") + " " + str(dep_time or "06:00") + ":00"
        refund_info   = calculate_refund(total_fare, cls, quota, departure_str)

        cancel_payload = {
            "Booking_Status":    "cancelled",
            "Refund_Amount":     refund_info["refund"],
            "Cancellation_Time": to_zoho_datetime(None),
            "Departure_Time":    booking.get("Departure_Time"),  # Keep it synced
        }
        result = zoho_repo.update_record(TABLES['bookings'], booking_id, cancel_payload)
        if not result.get("success"):
            raise ValidationError("Failed to cancel booking")

        # Free seats
        passengers_raw = booking.get("Passengers", "[]")
        if isinstance(passengers_raw, str):
            try:
                passengers = json.loads(passengers_raw)
            except Exception:
                passengers = []
        else:
            passengers = passengers_raw or []

        # CloudScale stores Train_ID as raw ROWID string, not a lookup object
        train_id = str(booking.get("Train_ID", "") or "")

        journey_date_ymd = jd
        try:
            journey_date_ymd = datetime.strptime(jd.split(" ")[0], "%d-%b-%Y").strftime("%Y-%m-%d")
        except Exception:
            pass

        freed = sum(1 for p in passengers if (p.get("Current_Status") or "").startswith("CNF/"))
        process_booking_cancellation(train_id, cls, journey_date_ymd, passengers)

        if freed > 0:
            promote_waitlist(train_id, cls, journey_date_ymd, freed)

        # Invalidate caches
        zoho_repo.invalidate_inventory_cache(train_id, to_zoho_date_only(jd), cls)

        return {"refund": refund_info, "booking_id": booking_id}

    # ════════════════════════════════════════════════════════════════════════
    #  PARTIAL CANCEL
    # ════════════════════════════════════════════════════════════════════════

    def partial_cancel(self, booking_id: str, passenger_indices: list) -> dict:
        """Cancel specific passengers within a booking."""
        bk = zoho_repo.get_record_by_id(TABLES['bookings'], booking_id)
        if not bk.get("success"):
            raise BookingNotFoundError(booking_id)

        booking = bk.get("data", {}).get("data") or bk.get("data") or {}
        if (booking.get("Booking_Status") or "").lower() == "cancelled":
            raise BookingAlreadyCancelledError()

        passengers_raw = booking.get("Passengers", "[]")
        if isinstance(passengers_raw, str):
            try:
                passengers = json.loads(passengers_raw)
            except Exception:
                passengers = []
        else:
            passengers = passengers_raw or []

        if not passengers:
            raise ValidationError("No passengers in booking")

        for idx in passenger_indices:
            if idx < 0 or idx >= len(passengers):
                raise ValidationError(f"Invalid passenger index: {idx}")

        total_fare     = float(booking.get("Total_Fare") or 0)
        chargeable     = sum(1 for p in passengers if not p.get("Is_Child", False))
        fare_per_person = total_fare / max(chargeable, 1)

        cancel_passengers = []
        cancelled_fare    = 0.0

        for idx in passenger_indices:
            p = passengers[idx]
            if p.get("Cancelled", False):
                continue
            cancel_passengers.append(p)
            p["Cancelled"]        = True
            p["Previous_Status"]  = p.get("Current_Status", "")
            p["Current_Status"]   = "Cancelled"
            if not p.get("Is_Child", False):
                cancelled_fare += fare_per_person

        if not cancel_passengers:
            raise ValidationError("Selected passengers are already cancelled")

        cls        = booking.get("Class", "SL")
        quota      = booking.get("Quota", "General")
        jd         = booking.get("Journey_Date", "")
        dep_time   = booking.get("Departure_Time", "06:00")

        try:
            dt_jd = datetime.strptime(jd.split(" ")[0], "%d-%b-%Y")
        except Exception:
            try:
                dt_jd = datetime.strptime(jd.split(" ")[0], "%Y-%m-%d")
            except Exception:
                dt_jd = datetime.now() + timedelta(days=7)

        departure_str = dt_jd.strftime("%d-%b-%Y") + " " + str(dep_time or "06:00") + ":00"
        refund_info   = calculate_refund(cancelled_fare, cls, quota, departure_str)

        all_cancelled = all(p.get("Cancelled") or p.get("Current_Status") == "Cancelled" for p in passengers)
        new_status    = "cancelled" if all_cancelled else booking.get("Booking_Status")
        new_fare      = total_fare - cancelled_fare

        zoho_repo.update_record(TABLES['bookings'], booking_id, {
            "Passengers":     json.dumps(passengers),
            "Booking_Status": new_status,
            "Total_Fare":     new_fare,
            "Refund_Amount":  refund_info["refund"],
        })

        # CloudScale stores Train_ID as raw ROWID string, not a lookup object
        train_id         = str(booking.get("Train_ID", "") or "")
        journey_date_ymd = jd
        try:
            journey_date_ymd = datetime.strptime(jd.split(" ")[0], "%d-%b-%Y").strftime("%Y-%m-%d")
        except Exception:
            pass

        freed = sum(1 for p in cancel_passengers if (p.get("Previous_Status") or "").startswith("CNF/"))
        process_booking_cancellation(train_id, cls, journey_date_ymd, cancel_passengers)
        if freed > 0:
            promote_waitlist(train_id, cls, journey_date_ymd, freed)

        zoho_repo.invalidate_inventory_cache(train_id, to_zoho_date_only(jd), cls)

        return {
            "refund":               refund_info,
            "remaining_passengers": sum(1 for p in passengers if not p.get("Cancelled")),
            "new_fare":             new_fare,
            "booking_status":       new_status,
        }


# Singleton
booking_service = BookingService()
