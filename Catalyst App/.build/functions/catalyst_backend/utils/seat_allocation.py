"""
Seat allocation engine for the Railway Ticketing System.
Implements IRCTC-style Confirmed, RAC, and Waitlist logic using Train_Inventory.
Also includes IRCTC cancellation refund calculation.
"""

import json
import logging
from datetime import datetime
from config import (
    COACH_PREFIX, COACH_CAPACITY, BERTH_CYCLE, get_form_config,
    CANCEL_MIN_DEDUCTION, AC_CLASSES, NON_AC_CLASSES
)
from repositories.cache_manager import cache
from repositories.cloudscale_repository import zoho_repo
from services.zoho_service import zoho
from config import SEAT_CLASS_MAP

logger = logging.getLogger(__name__)


def _update_train_available_seats(train_id, cls, confirmed_count, total_capacity):
    """
    Update the Available_Seats_{Class} field on the Trains record.
    available = total_capacity - confirmed_count
    """
    field_name = SEAT_CLASS_MAP.get(cls)
    if not field_name:
        return
    available = max(0, total_capacity - confirmed_count)
    try:
        zoho.update_record(
            get_form_config()['reports']['trains'],
            train_id,
            {field_name: available}
        )
        logger.info(f"Updated {field_name}={available} for train {train_id}")
    except Exception as exc:
        logger.warning(f"Failed to update train available seats: {exc}")


def get_train_inventory(train_id, journey_date, cls):
    """
    Fetches or creates a Train_Inventory record for a specific train, date, and class.

    This is a critical function that ensures an inventory record exists before any
    seat allocation or de-allocation is attempted. If a record for the given
    train, date, and class combination doesn't exist, it creates one by
    fetching the default capacity from the parent `Trains` record.

    Args:
        train_id (str): The ID of the train.
        journey_date (str): The date of the journey in 'YYYY-MM-DD' format.
        cls (str): The travel class (e.g., 'SL', '3A').

    Returns:
        dict: The fetched or newly created Train_Inventory record, or None if
              the parent train or its capacity cannot be determined.
    """
    try:
        # Standardize date format for Zoho criteria
        dt = datetime.strptime(journey_date, '%Y-%m-%d')
        date_criteria = dt.strftime('%d-%b-%Y')
    except (ValueError, TypeError):
        logger.error(f"Invalid journey_date format: {journey_date}. Expected YYYY-MM-DD.")
        # Fallback for other potential date formats, though YYYY-MM-DD is standard
        try:
            dt = datetime.strptime(journey_date, '%d-%b-%Y')
            date_criteria = journey_date
        except (ValueError, TypeError):
            logger.error(f"Could not parse date: {journey_date}. Aborting inventory fetch.")
            return None

    inv_report = get_form_config()['reports']['train_inventory']
    
    # First, try to get from cache
    cache_key = f"inventory:{train_id}:{date_criteria}:{cls}"
    cached_inv = cache.get(cache_key)
    if cached_inv:
        logger.debug(f"Inventory cache hit for {cache_key}")
        return cached_inv

    # If not in cache, fetch from Zoho
    logger.info(f"Fetching inventory for Train={train_id}, Date={date_criteria}, Class={cls}")
    criteria = (f'(Train == "{train_id}") && (Journey_Date == "{date_criteria}") && '
                f'(Class == "{cls}")')
    
    res = zoho.get_all_records(inv_report, criteria=criteria, limit=1)

    if res.get('success'):
        records = res.get('data', {}).get('data', [])
        if records:
            inventory_record = records[0]
            logger.info(f"Found existing inventory record: {inventory_record.get('ID')}")
            cache.set(cache_key, inventory_record, ttl=3600) # Cache for 1 hour
            return inventory_record

    # If no record exists, create one
    logger.warning(f"No inventory record found. Creating a new one for {train_id} on {date_criteria}.")
    
    # Fetch the parent train to get its total capacity for the class
    train_record = zoho_repo.get_train_cached(train_id)
    if not train_record:
        logger.error(f"Cannot create inventory: Parent train {train_id} not found.")
        return None

    # Map class to the correct capacity field in the Trains record
    capacity_field_map = {
        'SL': 'Total_Seats_SL', '3A': 'Total_Seats_3A', '2A': 'Total_Seats_2A',
        '1A': 'Total_Seats_1A', 'CC': 'Total_Seats_CC', 'EC': 'Total_Seats_EC',
        '2S': 'Total_Seats_2S', 'FC': 'Total_Seats_FC'
    }
    capacity_field = capacity_field_map.get(cls.upper())
    layout_field = f"Layout_{cls.upper()}"
    
    if not capacity_field:
        logger.error(f"Invalid class '{cls}' provided for inventory creation.")
        return None
        
    capacity = int(train_record.get(capacity_field) or 0)

    if capacity <= 0:
        logger.warning(f"Train {train_id} has 0 capacity for class {cls}. Cannot create inventory.")
        return None

    layout_name = train_record.get(layout_field)

    # Payload for the new inventory record
    payload = {
        "Train": train_id,
        "Journey_Date": date_criteria,
        "Class": cls,
        "Total_Capacity": capacity,
        "Layout_Name": layout_name,
        "Confirmed_Seats_JSON": "[]",
        "RAC_Count": 0,
        "Waitlist_Count": 0,
        "Chart_Prepared": "false"
    }

    inv_form = get_form_config()['forms']['train_inventory']
    create_res = zoho.add_record(inv_form, payload)
    
    if create_res.get('success') and 'data' in create_res:
        # The response from Zoho for a new record includes the ID
        new_record_details = create_res['data'].get('data', [{}])[0].get('Details', {})
        payload['ID'] = new_record_details.get('ID')
        logger.info(f"Successfully created new inventory record {payload['ID']} with capacity {capacity}.")
        cache.set(cache_key, payload, ttl=3600) # Cache the new record
        return payload

    logger.error(f"Failed to create inventory record: {create_res.get('error')}")
    return None


def _get_layout_data(layout_name):
    """
    Fetches coach layout data from the Coach_Layouts record.
    
    Layout JSON should contain a 2D array of seats with structure:
    [
      [
        {"coach": "S1", "seat_number": 1, "is_seat": true, "berth_type": "LOWER"},
        {"coach": "S1", "seat_number": 2, "is_seat": true, "berth_type": "MIDDLE"},
        ...
      ],
      ...
    ]
    """
    if not layout_name:
        logger.debug("Layout name not provided, cannot fetch layout data.")
        return None
    
    try:
        forms = get_form_config()
        criteria = f'(Layout_Name == "{layout_name}")'
        result = zoho.get_all_records(forms['reports']['coach_layouts'], criteria=criteria, limit=1)
        
        if not result.get('success'):
            logger.warning(f"Failed to fetch coach layout '{layout_name}': {result.get('error')}")
            return None
        
        records = result.get('data', {}).get('data', [])
        if not records:
            logger.warning(f"Coach layout '{layout_name}' not found in database.")
            return None
        
        layout_record = records[0]
        layout_json_str = layout_record.get('Layout_JSON')
        
        if not layout_json_str:
            logger.warning(f"Layout_JSON is empty for layout '{layout_name}'.")
            return None
        
        layout_data = json.loads(layout_json_str)
        logger.debug(f"Successfully loaded layout '{layout_name}' with structure: {json.dumps(layout_data)[:100]}...")
        return layout_data
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse Layout_JSON for '{layout_name}': {e}")
        return None
    except Exception as e:
        logger.error(f"Failed to fetch layout data for '{layout_name}': {e}", exc_info=True)
        return None


def process_booking_allocation(train_id, cls, journey_date, passengers):
    """
    Allocates seats (CNF/RAC/WL) for a list of passengers using a coach layout
    and updates inventory.
    
    Uses the Layout_Name from the Train_Inventory to fetch the coach layout,
    then assigns seats based on availability and passenger preferences.
    """
    cls_map = {'SLEEPER': 'SL', '3A': '3AC', '2A': '2AC', '1A': '1AC'}
    cls = cls_map.get(cls.upper(), cls.upper())

    inv = get_train_inventory(train_id, journey_date, cls)
    if not inv:
        logger.error(f"Inventory unavailable for train {train_id}, class {cls}. Assigning WL.")
        for i, p in enumerate(passengers):
            p.update({'Current_Status': f"WL/{i + 1}", 'Coach': '', 'Seat_Number': '', 'Berth': ''})
        return passengers, "waitlisted"

    total_cap = int(inv.get('Total_Capacity', 0))
    rac_count = int(inv.get('RAC_Count', 0))
    wl_count = int(inv.get('Waitlist_Count', 0))
    layout_name = inv.get('Layout_Name')
    
    logger.info(f"Processing allocation: train={train_id}, class={cls}, layout={layout_name}, "
                f"total_cap={total_cap}, current_rac={rac_count}, current_wl={wl_count}")

    try:
        confirmed_seats = json.loads(inv.get('Confirmed_Seats_JSON', '[]'))
        if not isinstance(confirmed_seats, list): 
            confirmed_seats = []
    except (json.JSONDecodeError, TypeError):
        confirmed_seats = []
    
    current_confirmed = len(confirmed_seats)
    
    # Fetch layout data using the layout name from the inventory
    layout_data = _get_layout_data(layout_name) if layout_name else None
    
    if not layout_data:
        logger.warning(f"Layout data not available for '{layout_name}'. Passengers will be waitlisted.")
    
    occupied_seats = {f"{s['coach']}-{s['seat_number']}" for s in confirmed_seats}

    max_rac = total_cap // 8
    overall_status = "confirmed"

    # --- Allocate status and seats for each passenger ---
    for i, p in enumerate(passengers):
        if current_confirmed < total_cap:
            # --- CNF (Confirmed) Allocation ---
            berth_preference = p.get('Berth_Preference')
            seat_info = find_available_seat(layout_data, occupied_seats, berth_preference)
            
            if seat_info:
                confirmed_seats.append(seat_info)
                occupied_seats.add(f"{seat_info['coach']}-{seat_info['seat_number']}")
                p.update({
                    'Current_Status': f"CNF/{seat_info['coach']}/{seat_info['seat_number']}",
                    'Coach': seat_info['coach'],
                    'Seat_Number': str(seat_info['seat_number']),
                    'Berth': seat_info['berth']
                })
                current_confirmed += 1
                logger.debug(f"Passenger {i+1} confirmed: {seat_info['coach']}/{seat_info['seat_number']}")
            else:
                # Fallback to RAC or WL if no seat available
                if rac_count < max_rac:
                    rac_count += 1
                    p.update({'Current_Status': f"RAC/{rac_count}", 'Coach': '', 'Seat_Number': '', 'Berth': ''})
                    overall_status = "rac"
                    logger.debug(f"Passenger {i+1} RAC: {rac_count}")
                else:
                    wl_count += 1
                    p.update({'Current_Status': f"WL/{wl_count}", 'Coach': '', 'Seat_Number': '', 'Berth': ''})
                    overall_status = "waitlisted"
                    logger.debug(f"Passenger {i+1} WL: {wl_count}")

        elif rac_count < max_rac:
            # --- RAC (Reservation Against Cancellation) Allocation ---
            rac_count += 1
            p.update({'Current_Status': f"RAC/{rac_count}", 'Coach': '', 'Seat_Number': '', 'Berth': ''})
            if overall_status == "confirmed": 
                overall_status = "rac"
            logger.debug(f"Passenger {i+1} RAC: {rac_count}")
        
        else:
            # --- WL (Waitlisted) Allocation ---
            wl_count += 1
            p.update({'Current_Status': f"WL/{wl_count}", 'Coach': '', 'Seat_Number': '', 'Berth': ''})
            overall_status = "waitlisted"
            logger.debug(f"Passenger {i+1} WL: {wl_count}")

    # --- Update Inventory Record in Zoho ---
    update_payload = {
        "Confirmed_Seats_JSON": json.dumps(confirmed_seats),
        "RAC_Count": rac_count,
        "Waitlist_Count": wl_count
    }
    
    zoho.update_record(get_form_config()['reports']['train_inventory'], inv['ID'], update_payload)
    logger.info(f"Updated inventory {inv['ID']}: Confirmed={len(confirmed_seats)}, RAC={rac_count}, WL={wl_count}, Status={overall_status}")

    cache.delete(f"inventory:{train_id}:{inv.get('Journey_Date')}:{cls}")
    _update_train_available_seats(train_id, cls, len(confirmed_seats), total_cap)

    return passengers, overall_status

def find_available_seat(layout_data, occupied_seats, preference):
    """
    Finds an available seat in the layout, trying to match preference first.
    
    Args:
        layout_data (list): 2D array of seat objects from coach layout
        occupied_seats (set): Set of occupied seat IDs in format "coach-seat_number"
        preference (str): Berth preference (e.g., "LOWER", "MIDDLE", "UPPER")
    
    Returns:
        dict: Seat info with keys: coach, seat_number, berth
        None: If no available seat found or layout is invalid
    """
    if not layout_data:
        logger.debug("Layout data is None or empty, cannot allocate seat.")
        return None
    
    # First pass: try to find a seat matching the preference
    if preference:
        for row in layout_data:
            if not isinstance(row, list):
                continue
            for seat in row:
                if not isinstance(seat, dict):
                    continue
                if seat.get('is_seat', False):
                    seat_id = f"{seat.get('coach', '')}-{seat.get('seat_number', '')}"
                    if seat_id not in occupied_seats and seat.get('berth_type') == preference:
                        logger.debug(f"Allocated seat: {seat_id} (berth: {preference})")
                        return {
                            'coach': seat['coach'],
                            'seat_number': seat['seat_number'],
                            'berth': seat['berth_type']
                        }
    
    # Second pass: find any available seat regardless of preference
    for row in layout_data:
        if not isinstance(row, list):
            continue
        for seat in row:
            if not isinstance(seat, dict):
                continue
            if seat.get('is_seat', False):
                seat_id = f"{seat.get('coach', '')}-{seat.get('seat_number', '')}"
                if seat_id not in occupied_seats:
                    logger.debug(f"Allocated seat: {seat_id} (no preference match, berth: {seat.get('berth_type')})")
                    return {
                        'coach': seat['coach'],
                        'seat_number': seat['seat_number'],
                        'berth': seat.get('berth_type', 'UNKNOWN')
                    }
    
    logger.warning(f"No available seats found in layout (occupied: {len(occupied_seats)})")
    return None


def process_booking_cancellation(train_id, cls, journey_date, passengers_to_cancel):
    """
    Processes the cancellation of seats, updating inventory and freeing up spots.

    This function handles the logic for removing passengers from CNF, RAC, or WL
    lists. It updates the `Train_Inventory` record to reflect the new availability.

    Args:
        train_id (str): The ID of the train.
        cls (str): The travel class.
        journey_date (str): The journey date in 'YYYY-MM-DD' format.
        passengers_to_cancel (list): A list of passenger dictionaries for whom
                                     the booking is being cancelled.
    """
    cls_map = {'SLEEPER': 'SL', '3A': '3AC', '2A': '2AC', '1A': '1AC'}
    cls = cls_map.get(cls.upper(), cls.upper())

    inv = get_train_inventory(train_id, journey_date, cls)
    if not inv:
        logger.error(f"Cannot process cancellation: Inventory not found for train {train_id}, class {cls}.")
        return

    rac_count = int(inv.get('RAC_Count') or 0)
    wl_count = int(inv.get('Waitlist_Count') or 0)
    
    try:
        confirmed_seats = json.loads(inv.get('Confirmed_Seats_JSON', '[]'))
        if not isinstance(confirmed_seats, list):
            confirmed_seats = []
    except (json.JSONDecodeError, TypeError):
        confirmed_seats = []

    freed_confirmed_seats = 0

    for p in passengers_to_cancel:
        # Use 'Previous_Status' for partial cancels, otherwise 'Current_Status'
        status = p.get('Previous_Status') or p.get('Current_Status', '')
        
        if status.startswith('CNF/'):
            seat_str_to_remove = status.replace('CNF/', '').strip()
            # The format of seat_str is now "S1/34", we need to find the dict
            # in confirmed_seats that matches this.
            seat_parts = seat_str_to_remove.split('/')
            if len(seat_parts) >= 2:
                coach_to_remove, num_to_remove = seat_parts[0], seat_parts[1]
                
                original_len = len(confirmed_seats)
                confirmed_seats = [
                    s for s in confirmed_seats 
                    if not (s.get('coach') == coach_to_remove and str(s.get('seat_number')) == num_to_remove)
                ]
                
                if len(confirmed_seats) < original_len:
                    freed_confirmed_seats += 1
                    logger.info(f"Freed confirmed seat: {seat_str_to_remove}")
                else:
                    logger.warning(f"Seat {seat_str_to_remove} not found in confirmed list for cancellation.")
            else:
                logger.warning(f"Could not parse seat to remove from status: {status}")
        
        elif status.startswith('RAC/'):
            rac_count = max(0, rac_count - 1)
            logger.info("Decremented RAC count.")
            
        elif status.startswith('WL/'):
            wl_count = max(0, wl_count - 1)
            logger.info("Decremented WL count.")

    # --- Update Inventory Record ---
    update_payload = {
        "Confirmed_Seats_JSON": json.dumps(confirmed_seats),
        "RAC_Count": rac_count,
        "Waitlist_Count": wl_count
    }
    zoho.update_record(get_form_config()['reports']['train_inventory'], inv['ID'], update_payload)
    logger.info(f"Updated inventory {inv['ID']} after cancellation: Confirmed={len(confirmed_seats)}, RAC={rac_count}, WL={wl_count}")

    # Invalidate cache
    cache.delete(f"inventory:{train_id}:{inv.get('Journey_Date')}:{cls}")

    # --- Update Available Seats on Train Record ---
    total_cap = int(inv.get('Total_Capacity') or 0)
    _update_train_available_seats(train_id, cls, len(confirmed_seats), total_cap)

    # --- Promote Waitlisted Passengers ---
    if freed_confirmed_seats > 0:
        logger.info(f"{freed_confirmed_seats} confirmed seats freed. Attempting to promote from RAC/WL.")
        promote_waitlist(train_id, cls, journey_date, freed_confirmed_seats)


def calculate_refund(total_fare, cls, quota, departure_datetime):
    """
    IRCTC cancellation refund calculation.

    Rules:
    - Tatkal (TQ/PT): No refund
    - AC classes: 25% deduction (>48h), 50% (12-48h), 100% (<12h)
    - Non-AC (SL/2S): ₹60 flat (>48h), 25% min ₹60 (12-48h), 100% (<12h)

    Returns dict with refund, deduction, rule, hours_before.
    """
    total_fare = float(total_fare or 0)

    # Tatkal — no refund
    if str(quota or '').upper() in ('TQ', 'PT'):
        return {
            'refund': 0.0,
            'deduction': total_fare,
            'rule': 'Tatkal tickets — No refund under any condition',
            'hours_before': None
        }

    # Calculate hours before departure
    now = datetime.now()
    if isinstance(departure_datetime, str):
        try:
            dep_dt = datetime.strptime(departure_datetime, '%d-%b-%Y %H:%M:%S')
        except Exception:
            try:
                dep_dt = datetime.strptime(departure_datetime, '%Y-%m-%d %H:%M:%S')
            except Exception:
                try:
                    dep_dt = datetime.strptime(departure_datetime.split(' ')[0], '%d-%b-%Y')
                    dep_dt = dep_dt.replace(hour=0, minute=0)
                except Exception:
                    dep_dt = now
    elif isinstance(departure_datetime, datetime):
        dep_dt = departure_datetime
    else:
        dep_dt = now

    hours_before = (dep_dt - now).total_seconds() / 3600

    cls_upper = (cls or 'SL').upper()
    # Normalize class
    norm_map = {'3AC': '3A', '2AC': '2A', '1AC': '1A'}
    cls_norm = norm_map.get(cls_upper, cls_upper)

    if cls_norm in AC_CLASSES or cls_upper in AC_CLASSES:
        # AC Class cancellation rules
        if hours_before > 48:
            deduction_pct = 0.25
            min_deduction = CANCEL_MIN_DEDUCTION.get(cls_norm, CANCEL_MIN_DEDUCTION.get(cls_upper, 90))
            deduction = max(total_fare * deduction_pct, min_deduction)
            rule = f"AC class — >48h before departure: 25% deduction (min ₹{min_deduction})"
        elif hours_before >= 12:
            deduction = total_fare * 0.50
            rule = "AC class — 12-48h before departure: 50% deduction"
        else:
            deduction = total_fare
            rule = "AC class — <12h before departure: No refund"
    else:
        # Non-AC (SL/2S) cancellation rules
        if hours_before > 48:
            deduction = 60.0  # Flat ₹60 per booking
            rule = "Non-AC class — >48h before departure: ₹60 flat deduction"
        elif hours_before >= 12:
            deduction = max(total_fare * 0.25, 60.0)
            rule = "Non-AC class — 12-48h before departure: 25% deduction (min ₹60)"
        else:
            deduction = total_fare
            rule = "Non-AC class — <12h before departure: No refund"

    deduction = min(deduction, total_fare)
    refund = total_fare - deduction

    return {
        'refund': round(refund, 2),
        'deduction': round(deduction, 2),
        'rule': rule,
        'hours_before': round(hours_before, 1) if hours_before else None
    }


def promote_waitlist(train_id, cls, journey_date, num_seats_to_fill):
    """
    Promotes passengers from RAC and WL lists to fill newly available confirmed seats.

    This function is triggered after a cancellation frees up one or more confirmed
    seats. It first promotes RAC passengers to CNF, then WL passengers to RAC or CNF.

    Args:
        train_id (str): The ID of the train.
        cls (str): The travel class.
        journey_date (str): The journey date in 'YYYY-MM-DD' format.
        num_seats_to_fill (int): The number of confirmed seats that have become available.
    """
    if num_seats_to_fill <= 0:
        return

    logger.info(f"Attempting to promote {num_seats_to_fill} passengers for train {train_id} on {journey_date}.")

    # --- 1. Fetch all potentially affected bookings (RAC and WL) ---
    # We fetch all bookings for the train/date/class and filter in memory.
    # This is often more efficient than multiple complex Zoho queries.
    try:
        dt = datetime.strptime(journey_date, '%Y-%m-%d')
        date_criteria = dt.strftime('%d-%b-%Y')
    except (ValueError, TypeError):
        logger.error(f"Invalid date format for promotion: {journey_date}")
        return

    all_bookings = zoho_repo.get_records(
        get_form_config()['reports']['bookings'],
        criteria=(f'(Train == "{train_id}") && (Journey_Date == "{date_criteria}") && '
                  f'(Class == "{cls}") && (Booking_Status != "confirmed") && (Booking_Status != "cancelled")'),
        limit=200 # Fetch a reasonable number of non-confirmed bookings
    )

    if not all_bookings:
        logger.info("No RAC or WL bookings found to promote.")
        return

    # Separate bookings into RAC and WL lists and sort by booking time
    rac_bookings = sorted(
        [b for b in all_bookings if b.get('Booking_Status') == 'rac'],
        key=lambda b: b.get('Booking_Time', '')
    )
    wl_bookings = sorted(
        [b for b in all_bookings if b.get('Booking_Status') == 'waitlisted'],
        key=lambda b: b.get('Booking_Time', '')
    )

    # --- 2. Re-run allocation logic for each booking ---
    # This is a simplified promotion logic. A more robust system would
    # individually update passenger statuses. Here, we re-process the entire
    # booking to ensure consistency.
    
    promotable_bookings = rac_bookings + wl_bookings
    
    for booking in promotable_bookings:
        if num_seats_to_fill <= 0:
            break # No more seats to fill

        passengers = booking.get('Passengers', [])
        if not isinstance(passengers, list):
            try:
                passengers = json.loads(passengers)
            except:
                continue
        
        num_to_promote = len(passengers)
        
        if num_to_promote <= num_seats_to_fill:
            # Re-run allocation for the entire booking
            updated_passengers, new_status = process_booking_allocation(
                train_id, cls, journey_date, passengers
            )
            
            # Update the booking record
            update_payload = {
                'Passengers': json.dumps(updated_passengers),
                'Booking_Status': new_status
            }
            zoho.update_record(get_form_config()['reports']['bookings'], booking['ID'], update_payload)
            
            num_seats_to_fill -= num_to_promote
            logger.info(f"Promoted booking {booking['PNR']} to {new_status}. {num_seats_to_fill} seats left to fill.")
    
    logger.info("Promotion process complete.")
