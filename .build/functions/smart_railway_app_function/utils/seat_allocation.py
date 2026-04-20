"""
Seat allocation engine for Railway Ticketing System.

Implements IRCTC-style booking allocation:
  - CNF (Confirmed): Seat/berth assigned
  - RAC (Reservation Against Cancellation): Shared berth
  - WL (Waitlisted): Queue position

Also handles cancellation refund calculation and waitlist promotion.
"""

import json
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple, Set

from repositories.cloudscale_repository import cloudscale_repo
from repositories.cache_manager import cache
from config import (
    TABLES,
    COACH_PREFIX,
    COACH_CAPACITY,
    BERTH_CYCLE,
    SEAT_CLASS_MAP,
    CANCEL_MIN_DEDUCTION,
    AC_CLASSES,
    NON_AC_CLASSES,
    RAC_LIMIT_PER_COACH,
    WAITLIST_LIMIT_PER_TRAIN,
)
from utils.date_helpers import get_zoho_date_criteria, parse_date

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════════════════════
#  INVENTORY MANAGEMENT
# ══════════════════════════════════════════════════════════════════════════════

def get_train_inventory(
    train_id: str,
    journey_date: str,
    travel_class: str
) -> Optional[Dict[str, Any]]:
    """
    Fetch or create Train_Inventory record for a specific train/date/class.
    
    Args:
        train_id: Train ROWID
        journey_date: Journey date (YYYY-MM-DD or DD-MMM-YYYY)
        travel_class: Class code (SL, 3A, 2A, etc.)
    
    Returns:
        Inventory record dict, or None if unable to fetch/create
    """
    cls = _normalize_class(travel_class)
    date_criteria = get_zoho_date_criteria(journey_date)
    
    if not date_criteria:
        logger.error(f"Invalid journey_date format: {journey_date}")
        return None
    
    # Check cache first
    cache_key = f"inventory:{train_id}:{date_criteria}:{cls}"
    cached = cache.get(cache_key)
    if cached:
        logger.debug(f"Inventory cache hit for {cache_key}")
        return cached
    
    # Fetch from database
    logger.info(f"Fetching inventory: Train={train_id}, Date={date_criteria}, Class={cls}")
    
    criteria = f'Train = {train_id} AND Journey_Date = \'{date_criteria}\' AND Class = \'{cls}\''
    result = cloudscale_repo.get_all_records(TABLES['train_inventory'], criteria=criteria, limit=1)
    
    if result.get('success'):
        records = result.get('data', {}).get('data', [])
        if records:
            inventory = records[0]
            logger.info(f"Found existing inventory record: {inventory.get('ROWID')}")
            cache.set(cache_key, inventory, ttl=3600)
            return inventory
    
    # Create new inventory record
    logger.warning(f"No inventory record found. Creating new for train {train_id}")
    return _create_inventory_record(train_id, date_criteria, cls, cache_key)


def _create_inventory_record(
    train_id: str,
    date_criteria: str,
    cls: str,
    cache_key: str
) -> Optional[Dict[str, Any]]:
    """Create a new inventory record from train capacity."""
    train_record = cloudscale_repo.get_train_cached(train_id)
    if not train_record:
        logger.error(f"Cannot create inventory: Train {train_id} not found")
        return None
    
    # Get capacity from train record
    capacity_field_map = {
        'SL': 'Total_Seats_SL',
        '3A': 'Total_Seats_3A',
        '2A': 'Total_Seats_2A',
        '1A': 'Total_Seats_1A',
        'CC': 'Total_Seats_CC',
        'EC': 'Total_Seats_EC',
        '2S': 'Total_Seats_2S',
    }
    
    capacity_field = capacity_field_map.get(cls)
    if not capacity_field:
        logger.error(f"Invalid class '{cls}' for inventory creation")
        return None
    
    capacity = int(train_record.get(capacity_field) or 0)
    
    if capacity <= 0:
        # Use default capacity from COACH_CAPACITY
        capacity = COACH_CAPACITY.get(cls, 72)
        logger.info(f"Using default capacity {capacity} for class {cls}")
    
    # Create inventory record
    payload = {
        "Train": train_id,
        "Journey_Date": date_criteria,
        "Class": cls,
        "Total_Capacity": capacity,
        "Confirmed_Count": 0,
        "Confirmed_Seats_JSON": "[]",
        "RAC_Count": 0,
        "Waitlist_Count": 0,
        "Chart_Prepared": "false"
    }
    
    result = cloudscale_repo.create_record(TABLES['train_inventory'], payload)
    
    if result.get('success'):
        payload['ROWID'] = result.get('data', {}).get('ROWID')
        logger.info(f"Created inventory record {payload.get('ROWID')} with capacity {capacity}")
        cache.set(cache_key, payload, ttl=3600)
        return payload
    
    logger.error(f"Failed to create inventory: {result.get('error')}")
    return None


def get_seat_availability(
    train_id: str,
    journey_date: str,
    travel_class: str
) -> Dict[str, Any]:
    """
    Get seat availability for a train/date/class.
    
    Returns:
        Dict with available, total, rac_available, waitlist_count, status
    """
    inv = get_train_inventory(train_id, journey_date, travel_class)
    
    if not inv:
        return {
            'available': 0,
            'total': 0,
            'rac_available': 0,
            'waitlist_count': 0,
            'status': 'unavailable'
        }
    
    total = int(inv.get('Total_Capacity') or 0)
    confirmed = int(inv.get('Confirmed_Count') or 0)
    rac_count = int(inv.get('RAC_Count') or 0)
    wl_count = int(inv.get('Waitlist_Count') or 0)
    
    # Try to get confirmed count from JSON if not directly stored
    if confirmed == 0:
        try:
            confirmed_seats = json.loads(inv.get('Confirmed_Seats_JSON') or '[]')
            confirmed = len(confirmed_seats)
        except Exception:
            pass
    
    available = max(0, total - confirmed)
    max_rac = total // 8  # RAC is typically 1/8 of capacity
    rac_available = max(0, max_rac - rac_count)
    
    # Determine status
    if available > 0:
        status = 'available'
    elif rac_available > 0:
        status = 'rac'
    elif wl_count < WAITLIST_LIMIT_PER_TRAIN:
        status = 'waitlist'
    else:
        status = 'full'
    
    return {
        'available': available,
        'total': total,
        'confirmed': confirmed,
        'rac_available': rac_available,
        'rac_count': rac_count,
        'waitlist_count': wl_count,
        'status': status
    }


# ══════════════════════════════════════════════════════════════════════════════
#  SEAT ALLOCATION
# ══════════════════════════════════════════════════════════════════════════════

def process_booking_allocation(
    train_id: str,
    travel_class: str,
    journey_date: str,
    passengers: List[Dict]
) -> Tuple[List[Dict], str]:
    """
    Allocate seats (CNF/RAC/WL) for passengers and update inventory.
    
    Args:
        train_id: Train ROWID
        travel_class: Class code
        journey_date: Journey date
        passengers: List of passenger dicts
    
    Returns:
        Tuple of (updated passengers list, overall booking status)
    """
    cls = _normalize_class(travel_class)
    
    inv = get_train_inventory(train_id, journey_date, cls)
    if not inv:
        logger.error(f"Inventory unavailable for train {train_id}, class {cls}")
        # Assign all as waitlisted
        for i, p in enumerate(passengers):
            p.update({
                'Current_Status': f"WL/{i + 1}",
                'Coach': '',
                'Seat_Number': '',
                'Berth': ''
            })
        return passengers, "waitlisted"
    
    total_cap = int(inv.get('Total_Capacity') or 0)
    rac_count = int(inv.get('RAC_Count') or 0)
    wl_count = int(inv.get('Waitlist_Count') or 0)
    
    # Parse confirmed seats
    try:
        confirmed_seats = json.loads(inv.get('Confirmed_Seats_JSON') or '[]')
        if not isinstance(confirmed_seats, list):
            confirmed_seats = []
    except Exception:
        confirmed_seats = []
    
    current_confirmed = len(confirmed_seats)
    occupied_seats: Set[str] = {f"{s['coach']}-{s['seat_number']}" for s in confirmed_seats}
    
    max_rac = total_cap // 8
    overall_status = "confirmed"
    
    logger.info(f"Allocating {len(passengers)} passengers: cap={total_cap}, confirmed={current_confirmed}, rac={rac_count}, wl={wl_count}")
    
    # Allocate each passenger
    for i, p in enumerate(passengers):
        if current_confirmed < total_cap:
            # CNF allocation
            seat_info = _allocate_seat(cls, current_confirmed, p.get('Berth_Preference'))
            
            # Ensure seat is not already taken
            seat_id = f"{seat_info['coach']}-{seat_info['seat_number']}"
            while seat_id in occupied_seats:
                current_confirmed += 1
                seat_info = _allocate_seat(cls, current_confirmed, None)
                seat_id = f"{seat_info['coach']}-{seat_info['seat_number']}"
            
            confirmed_seats.append(seat_info)
            occupied_seats.add(seat_id)
            
            p.update({
                'Current_Status': f"CNF/{seat_info['coach']}/{seat_info['seat_number']}",
                'Coach': seat_info['coach'],
                'Seat_Number': str(seat_info['seat_number']),
                'Berth': seat_info['berth']
            })
            current_confirmed += 1
            logger.debug(f"Passenger {i+1} CNF: {seat_info['coach']}/{seat_info['seat_number']}")
        
        elif rac_count < max_rac:
            # RAC allocation
            rac_count += 1
            p.update({
                'Current_Status': f"RAC/{rac_count}",
                'Coach': '',
                'Seat_Number': '',
                'Berth': ''
            })
            if overall_status == "confirmed":
                overall_status = "rac"
            logger.debug(f"Passenger {i+1} RAC: {rac_count}")
        
        else:
            # Waitlist allocation
            wl_count += 1
            p.update({
                'Current_Status': f"WL/{wl_count}",
                'Coach': '',
                'Seat_Number': '',
                'Berth': ''
            })
            overall_status = "waitlisted"
            logger.debug(f"Passenger {i+1} WL: {wl_count}")
    
    # Update inventory record
    update_payload = {
        "Confirmed_Count": len(confirmed_seats),
        "Confirmed_Seats_JSON": json.dumps(confirmed_seats),
        "RAC_Count": rac_count,
        "Waitlist_Count": wl_count
    }
    
    cloudscale_repo.update_record(TABLES['train_inventory'], inv['ROWID'], update_payload)
    logger.info(f"Updated inventory: CNF={len(confirmed_seats)}, RAC={rac_count}, WL={wl_count}")
    
    # Invalidate cache
    date_criteria = get_zoho_date_criteria(journey_date)
    cache.delete(f"inventory:{train_id}:{date_criteria}:{cls}")
    
    # Update train available seats
    _update_train_available_seats(train_id, cls, len(confirmed_seats), total_cap)
    
    return passengers, overall_status


def _allocate_seat(cls: str, seat_index: int, preference: Optional[str] = None) -> Dict[str, Any]:
    """
    Allocate a seat based on class configuration.
    
    Args:
        cls: Class code
        seat_index: Sequential seat number (0-based)
        preference: Berth preference (Lower, Upper, etc.)
    
    Returns:
        Dict with coach, seat_number, berth
    """
    coach_cap = COACH_CAPACITY.get(cls, 72)
    prefix = COACH_PREFIX.get(cls, 'S')
    berth_cycle = BERTH_CYCLE.get(cls, ['Lower', 'Middle', 'Upper', 'Side Lower', 'Side Upper'])
    
    # Calculate coach number and seat within coach
    coach_num = (seat_index // coach_cap) + 1
    seat_in_coach = (seat_index % coach_cap) + 1
    
    # Determine berth type
    berth_index = seat_index % len(berth_cycle)
    berth = berth_cycle[berth_index]
    
    # Try to honor preference if possible
    if preference and preference in berth_cycle:
        berth = preference
    
    coach = f"{prefix}{coach_num}"
    
    return {
        'coach': coach,
        'seat_number': seat_in_coach,
        'berth': berth
    }


def _update_train_available_seats(
    train_id: str,
    cls: str,
    confirmed_count: int,
    total_capacity: int
):
    """Update Available_Seats field on Train record."""
    field_name = SEAT_CLASS_MAP.get(cls)
    if not field_name:
        return
    
    available = max(0, total_capacity - confirmed_count)
    
    try:
        cloudscale_repo.update_record(
            TABLES['trains'],
            train_id,
            {field_name: available}
        )
        logger.info(f"Updated {field_name}={available} for train {train_id}")
    except Exception as exc:
        logger.warning(f"Failed to update train available seats: {exc}")


# ══════════════════════════════════════════════════════════════════════════════
#  CANCELLATION
# ══════════════════════════════════════════════════════════════════════════════

def process_booking_cancellation(
    train_id: str,
    travel_class: str,
    journey_date: str,
    passengers_to_cancel: List[Dict]
) -> Dict[str, Any]:
    """
    Process cancellation: free seats and update inventory.
    
    Args:
        train_id: Train ROWID
        travel_class: Class code
        journey_date: Journey date
        passengers_to_cancel: List of passengers being cancelled
    
    Returns:
        Dict with freed_seats count and promotion status
    """
    cls = _normalize_class(travel_class)
    
    inv = get_train_inventory(train_id, journey_date, cls)
    if not inv:
        logger.error(f"Cannot process cancellation: Inventory not found")
        return {'freed_seats': 0, 'error': 'Inventory not found'}
    
    rac_count = int(inv.get('RAC_Count') or 0)
    wl_count = int(inv.get('Waitlist_Count') or 0)
    
    try:
        confirmed_seats = json.loads(inv.get('Confirmed_Seats_JSON') or '[]')
        if not isinstance(confirmed_seats, list):
            confirmed_seats = []
    except Exception:
        confirmed_seats = []
    
    freed_confirmed = 0
    
    for p in passengers_to_cancel:
        status = p.get('Current_Status') or p.get('Previous_Status') or ''
        
        if status.startswith('CNF/'):
            # Remove from confirmed seats
            parts = status.replace('CNF/', '').split('/')
            if len(parts) >= 2:
                coach, seat_num = parts[0], parts[1]
                original_len = len(confirmed_seats)
                confirmed_seats = [
                    s for s in confirmed_seats
                    if not (s.get('coach') == coach and str(s.get('seat_number')) == seat_num)
                ]
                if len(confirmed_seats) < original_len:
                    freed_confirmed += 1
                    logger.info(f"Freed seat: {coach}/{seat_num}")
        
        elif status.startswith('RAC/'):
            rac_count = max(0, rac_count - 1)
            logger.info("Decremented RAC count")
        
        elif status.startswith('WL/'):
            wl_count = max(0, wl_count - 1)
            logger.info("Decremented WL count")
    
    # Update inventory
    update_payload = {
        "Confirmed_Count": len(confirmed_seats),
        "Confirmed_Seats_JSON": json.dumps(confirmed_seats),
        "RAC_Count": rac_count,
        "Waitlist_Count": wl_count
    }
    
    cloudscale_repo.update_record(TABLES['train_inventory'], inv['ROWID'], update_payload)
    logger.info(f"Updated inventory after cancellation: CNF={len(confirmed_seats)}, RAC={rac_count}, WL={wl_count}")
    
    # Invalidate cache
    date_criteria = get_zoho_date_criteria(journey_date)
    cache.delete(f"inventory:{train_id}:{date_criteria}:{cls}")
    
    # Update train available seats
    total_cap = int(inv.get('Total_Capacity') or 0)
    _update_train_available_seats(train_id, cls, len(confirmed_seats), total_cap)
    
    # Promote waitlisted passengers
    promoted = 0
    if freed_confirmed > 0:
        promoted = promote_waitlist(train_id, cls, journey_date, freed_confirmed)
    
    return {
        'freed_seats': freed_confirmed,
        'promoted_count': promoted,
        'new_confirmed': len(confirmed_seats),
        'new_rac': rac_count,
        'new_waitlist': wl_count
    }


def calculate_refund(
    total_fare: float,
    travel_class: str,
    quota: str,
    departure_datetime: str
) -> Dict[str, Any]:
    """
    Calculate cancellation refund based on IRCTC rules.
    
    Rules:
        - Tatkal (TQ/PT): No refund
        - AC classes: 25% (>48h), 50% (12-48h), 100% (<12h)
        - Non-AC: ₹60 flat (>48h), 25% min ₹60 (12-48h), 100% (<12h)
    
    Args:
        total_fare: Total booking fare
        travel_class: Class code
        quota: Booking quota
        departure_datetime: Departure datetime string
    
    Returns:
        Dict with refund, deduction, rule, hours_before
    """
    total_fare = float(total_fare or 0)
    cls = _normalize_class(travel_class)
    
    # Tatkal — no refund
    if str(quota or '').upper() in ('TQ', 'PT', 'TATKAL', 'PREMIUM TATKAL'):
        return {
            'refund': 0.0,
            'deduction': total_fare,
            'rule': 'Tatkal tickets — No refund',
            'hours_before': None
        }
    
    # Calculate hours before departure
    dep_dt = parse_date(departure_datetime)
    if not dep_dt:
        # If can't parse, assume recent booking
        dep_dt = datetime.now()
    
    hours_before = (dep_dt - datetime.now()).total_seconds() / 3600
    
    if cls in AC_CLASSES:
        # AC Class rules
        if hours_before > 48:
            min_deduction = CANCEL_MIN_DEDUCTION.get(cls, 90)
            deduction = max(total_fare * 0.25, min_deduction)
            rule = f"AC class — >48h: 25% deduction (min ₹{min_deduction})"
        elif hours_before >= 12:
            deduction = total_fare * 0.50
            rule = "AC class — 12-48h: 50% deduction"
        else:
            deduction = total_fare
            rule = "AC class — <12h: No refund"
    else:
        # Non-AC rules (SL/2S)
        if hours_before > 48:
            deduction = 60.0
            rule = "Non-AC — >48h: ₹60 flat deduction"
        elif hours_before >= 12:
            deduction = max(total_fare * 0.25, 60.0)
            rule = "Non-AC — 12-48h: 25% (min ₹60)"
        else:
            deduction = total_fare
            rule = "Non-AC — <12h: No refund"
    
    deduction = min(deduction, total_fare)
    refund = total_fare - deduction
    
    return {
        'refund': round(refund, 2),
        'deduction': round(deduction, 2),
        'rule': rule,
        'hours_before': round(hours_before, 1) if hours_before else None
    }


def promote_waitlist(
    train_id: str,
    travel_class: str,
    journey_date: str,
    num_seats: int
) -> int:
    """
    Promote passengers from RAC/WL when seats become available.
    
    Args:
        train_id: Train ROWID
        travel_class: Class code
        journey_date: Journey date
        num_seats: Number of seats to fill
    
    Returns:
        Number of passengers promoted
    """
    if num_seats <= 0:
        return 0
    
    cls = _normalize_class(travel_class)
    date_criteria = get_zoho_date_criteria(journey_date)
    
    logger.info(f"Promoting up to {num_seats} passengers for train {train_id}")
    
    # Fetch RAC and WL bookings
    try:
        criteria = f"Train_ID = {train_id} AND Journey_Date = '{date_criteria}' AND Class = '{cls}' AND Booking_Status IN ('rac', 'waitlisted')"
        bookings = cloudscale_repo.get_records(TABLES['bookings'], criteria=criteria, limit=50)
    except Exception as exc:
        logger.error(f"Failed to fetch bookings for promotion: {exc}")
        return 0
    
    if not bookings:
        logger.info("No RAC/WL bookings to promote")
        return 0
    
    # Sort by booking time (FIFO)
    rac_bookings = sorted(
        [b for b in bookings if b.get('Booking_Status') == 'rac'],
        key=lambda b: b.get('Booking_Time', '')
    )
    wl_bookings = sorted(
        [b for b in bookings if b.get('Booking_Status') == 'waitlisted'],
        key=lambda b: b.get('Booking_Time', '')
    )
    
    promoted = 0
    
    for booking in rac_bookings + wl_bookings:
        if num_seats <= 0:
            break
        
        passengers = booking.get('Passengers', [])
        if isinstance(passengers, str):
            try:
                passengers = json.loads(passengers)
            except Exception:
                continue
        
        num_passengers = len(passengers)
        
        if num_passengers <= num_seats:
            # Re-run allocation
            updated_passengers, new_status = process_booking_allocation(
                train_id, cls, journey_date, passengers
            )
            
            # Update booking
            cloudscale_repo.update_record(
                TABLES['bookings'],
                booking['ROWID'],
                {
                    'Passengers': json.dumps(updated_passengers),
                    'Booking_Status': new_status
                }
            )
            
            num_seats -= num_passengers
            promoted += num_passengers
            logger.info(f"Promoted booking {booking.get('PNR')} to {new_status}")
    
    logger.info(f"Promotion complete: {promoted} passengers promoted")
    return promoted


def _normalize_class(cls: str) -> str:
    """Normalize class code."""
    cls = (cls or 'SL').upper().strip()
    mapping = {
        'SLEEPER': 'SL',
        '3AC': '3A',
        '2AC': '2A',
        '1AC': '1A',
    }
    return mapping.get(cls, cls)
