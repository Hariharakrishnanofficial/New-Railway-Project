"""
Fare calculation utility for Railway Ticketing System.

Implements IRCTC-style fare calculation:
  1. Base fare from Fares table or Train default
  2. Reservation charges
  3. Superfast surcharge
  4. Tatkal premium
  5. GST (AC classes only)
  6. Concession discounts
"""

import logging
from typing import Optional, Dict, Any, List

from repositories.cloudscale_repository import cloudscale_repo, CriteriaBuilder
from repositories.cache_manager import cache
from config import (
    TABLES,
    BASE_FARE_PER_KM,
    RESERVATION_CHARGE,
    SUPERFAST_SURCHARGE,
    TATKAL_PREMIUM_PERCENT,
    TATKAL_MIN_CHARGE,
    TATKAL_MAX_CHARGE,
    GST_RATE,
    AC_CLASSES,
    CONCESSION_RATES,
    SUPERFAST_TRAIN_TYPES,
)

logger = logging.getLogger(__name__)

# Cache TTL for fares (5 minutes)
TTL_FARES = 300


def get_fare_for_journey(
    train_id: str,
    from_station_id: str,
    to_station_id: str,
    travel_class: str,
    train_record: Optional[Dict] = None,
    quota: str = "General",
    distance_km: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Calculate the total fare for a journey with full IRCTC-style breakdown.
    
    Args:
        train_id: Train ROWID
        from_station_id: Source station ROWID
        to_station_id: Destination station ROWID
        travel_class: Class code (SL, 3A, 2A, 1A, CC, EC, 2S)
        train_record: Optional pre-fetched train record
        quota: Booking quota (General, Tatkal, Premium Tatkal)
        distance_km: Optional distance override
    
    Returns:
        Dict with: total_fare, base_fare, breakdown, and components
    """
    cls = _normalize_class(travel_class)
    
    # Cache key for fare lookup
    cache_key = f'fare:{train_id}:{from_station_id}:{to_station_id}:{cls}:{quota}'
    cached = cache.get(cache_key)
    if cached is not None:
        logger.debug(f"Fare cache hit for key: {cache_key}")
        return cached
    
    # Step 1: Get base fare
    base_fare = _get_base_fare(train_id, from_station_id, to_station_id, cls, train_record, distance_km)
    
    if base_fare <= 0:
        logger.warning(f"Could not determine base fare for train {train_id}, class {cls}")
        return {
            'total_fare': 0.0,
            'base_fare': 0.0,
            'breakdown': [],
            'error': 'Unable to calculate fare'
        }
    
    # Build fare breakdown
    breakdown = []
    breakdown.append({'component': 'Base Fare', 'amount': base_fare})
    
    total = base_fare
    
    # Step 2: Reservation charge
    reservation = RESERVATION_CHARGE.get(cls, 20)
    breakdown.append({'component': 'Reservation Charge', 'amount': reservation})
    total += reservation
    
    # Step 3: Superfast surcharge (if applicable)
    superfast_charge = 0.0
    if train_record:
        train_type = (train_record.get('Train_Type') or '').strip()
        if train_type in SUPERFAST_TRAIN_TYPES:
            superfast_charge = SUPERFAST_SURCHARGE.get(cls, 30)
            breakdown.append({'component': 'Superfast Surcharge', 'amount': superfast_charge})
            total += superfast_charge
    
    # Step 4: Tatkal premium
    tatkal_charge = 0.0
    quota_upper = (quota or '').upper().strip()
    if quota_upper in ('TATKAL', 'TQ', 'TK', 'PREMIUM TATKAL', 'PT'):
        tatkal_charge = _calculate_tatkal_charge(base_fare, cls, quota_upper)
        breakdown.append({'component': 'Tatkal Premium', 'amount': tatkal_charge})
        total += tatkal_charge
    
    # Step 5: GST (AC classes only)
    gst = 0.0
    if cls in AC_CLASSES:
        gst = round(total * GST_RATE, 2)
        breakdown.append({'component': f'GST ({int(GST_RATE * 100)}%)', 'amount': gst})
        total += gst
    
    # Round total
    total = round(total, 2)
    
    result = {
        'total_fare': total,
        'base_fare': base_fare,
        'reservation_charge': reservation,
        'superfast_charge': superfast_charge,
        'tatkal_charge': tatkal_charge,
        'gst': gst,
        'travel_class': cls,
        'quota': quota,
        'breakdown': breakdown,
    }
    
    cache.set(cache_key, result, ttl=TTL_FARES)
    logger.info(f"Calculated fare: {total} for train {train_id}, class {cls}, quota {quota}")
    
    return result


def calculate_fare_for_passengers(
    fare_per_passenger: float,
    passengers: List[Dict],
    travel_class: str
) -> Dict[str, Any]:
    """
    Calculate total fare for all passengers with concessions.
    
    Args:
        fare_per_passenger: Base fare per adult passenger
        passengers: List of passenger dicts with age, gender, concession_type
        travel_class: Class code
    
    Returns:
        Dict with total_fare, per_passenger_fares, summary
    """
    cls = _normalize_class(travel_class)
    
    per_passenger_fares = []
    chargeable_count = 0
    free_count = 0
    total = 0.0
    
    for p in passengers:
        age = int(p.get('age') or p.get('Age') or 0)
        gender = (p.get('gender') or p.get('Gender') or '').lower()
        concession = (p.get('concession_type') or p.get('Concession_Type') or '').lower()
        
        # Children under 5 travel free
        if age < 5:
            per_passenger_fares.append({
                'name': p.get('name') or p.get('Name', 'Child'),
                'fare': 0.0,
                'note': 'Free (under 5)'
            })
            free_count += 1
            continue
        
        # Calculate discount
        discount_rate = 0.0
        note = ''
        
        if age >= 60 and gender == 'male':
            discount_rate = CONCESSION_RATES.get('senior_male', 0.40)
            note = 'Senior Citizen (Male 60+)'
        elif age >= 58 and gender == 'female':
            discount_rate = CONCESSION_RATES.get('senior_female', 0.50)
            note = 'Senior Citizen (Female 58+)'
        elif 5 <= age <= 12:
            discount_rate = CONCESSION_RATES.get('child', 0.50)
            note = 'Child (5-12 years)'
        elif concession == 'student':
            discount_rate = CONCESSION_RATES.get('student', 0.50)
            note = 'Student Concession'
        elif concession == 'disabled':
            discount_rate = CONCESSION_RATES.get('disabled', 0.50)
            note = 'Disability Concession'
        
        passenger_fare = fare_per_passenger * (1 - discount_rate)
        passenger_fare = round(passenger_fare, 2)
        
        per_passenger_fares.append({
            'name': p.get('name') or p.get('Name', 'Passenger'),
            'fare': passenger_fare,
            'discount_percent': int(discount_rate * 100),
            'note': note or 'Full Fare'
        })
        
        total += passenger_fare
        chargeable_count += 1
    
    return {
        'total_fare': round(total, 2),
        'per_passenger_fares': per_passenger_fares,
        'chargeable_passengers': chargeable_count,
        'free_passengers': free_count,
        'fare_per_adult': fare_per_passenger,
    }


def _normalize_class(cls: str) -> str:
    """Normalize class code to standard format."""
    cls = (cls or 'SL').upper().strip()
    # Map alternate codes
    mapping = {
        'SLEEPER': 'SL',
        '3AC': '3A',
        '2AC': '2A',
        '1AC': '1A',
        'FIRST CLASS': '1A',
        'CHAIR CAR': 'CC',
        'EXECUTIVE': 'EC',
        'SECOND SITTING': '2S',
    }
    return mapping.get(cls, cls)


def _get_base_fare(
    train_id: str,
    from_station_id: str,
    to_station_id: str,
    cls: str,
    train_record: Optional[Dict] = None,
    distance_km: Optional[float] = None
) -> float:
    """
    Get base fare from Fares table or Train record.
    
    Priority:
      1. Dynamic fare from Fares table
      2. Default fare from Train record
      3. Calculate from distance if available
    """
    # Try Fares table first
    try:
        criteria = (CriteriaBuilder()
                    .eq('Train', train_id)
                    .eq('From_Station', from_station_id)
                    .eq('To_Station', to_station_id)
                    .eq('Class', cls)
                    .eq('Is_Active', 'true')
                    .build())
        
        records = cloudscale_repo.get_records(TABLES['fares'], criteria=criteria, limit=1)
        
        if records:
            fare_record = records[0]
            dynamic_fare = float(fare_record.get('Dynamic_Fare') or 0)
            base_fare = float(fare_record.get('Base_Fare') or 0)
            
            if dynamic_fare > 0:
                logger.info(f"Using dynamic fare from Fares table: {dynamic_fare}")
                return dynamic_fare
            if base_fare > 0:
                logger.info(f"Using base fare from Fares table: {base_fare}")
                return base_fare
    
    except Exception as exc:
        logger.warning(f"Fares table lookup failed: {exc}")
    
    # Fallback to Train record default fare
    if not train_record:
        train_record = cloudscale_repo.get_train_cached(train_id)
    
    if train_record:
        fare_field_map = {
            'SL': 'Fare_SL',
            '2S': 'Fare_2S',
            '3A': 'Fare_3A',
            '2A': 'Fare_2A',
            '1A': 'Fare_1A',
            'CC': 'Fare_CC',
            'EC': 'Fare_EC',
            'FC': 'Fare_1A',
        }
        field = fare_field_map.get(cls, 'Fare_SL')
        train_fare = float(train_record.get(field) or 0)
        
        if train_fare > 0:
            logger.info(f"Using fallback fare from Train.{field}: {train_fare}")
            return train_fare
    
    # Last resort: calculate from distance
    if distance_km and distance_km > 0:
        rate_per_km = BASE_FARE_PER_KM.get(cls, 0.60)
        calculated = round(distance_km * rate_per_km, 2)
        logger.info(f"Calculated fare from distance: {calculated} ({distance_km}km x {rate_per_km}/km)")
        return calculated
    
    return 0.0


def _calculate_tatkal_charge(base_fare: float, cls: str, quota: str) -> float:
    """Calculate Tatkal premium charge."""
    # Calculate percentage-based premium
    premium = base_fare * (TATKAL_PREMIUM_PERCENT / 100.0)
    
    # Apply min/max caps
    min_charge = TATKAL_MIN_CHARGE.get(cls, 100)
    max_charge = TATKAL_MAX_CHARGE.get(cls, 400)
    
    # Premium Tatkal has higher charges
    if quota in ('PT', 'PREMIUM TATKAL'):
        min_charge = int(min_charge * 1.5)
        max_charge = int(max_charge * 1.5)
    
    premium = max(min_charge, min(premium, max_charge))
    
    return round(premium, 2)


def _get_tatkal_surcharge_from_quota(quota_name: str) -> float:
    """Fetch Tatkal surcharge percentage from Quotas table."""
    cache_key = f'tatkal_surcharge:{quota_name}'
    cached = cache.get(cache_key)
    if cached is not None:
        return cached
    
    try:
        criteria = CriteriaBuilder().eq('Quota_Name', quota_name).build()
        records = cloudscale_repo.get_records(TABLES['quotas'], criteria=criteria, limit=1)
        if records:
            pct = float(records[0].get('Surcharge_Percentage') or 0)
            cache.set(cache_key, pct, ttl=TTL_FARES)
            return pct
    except Exception as exc:
        logger.warning(f'Quotas lookup error: {exc}')
    
    cache.set(cache_key, 0.0, ttl=TTL_FARES)
    return 0.0


def calculate_distance_fare(
    distance_km: float,
    travel_class: str,
    quota: str = "General",
    is_superfast: bool = False
) -> Dict[str, Any]:
    """
    Calculate fare based purely on distance.
    
    This is a simplified fare calculation used when no train-specific
    fare data is available.
    
    Args:
        distance_km: Journey distance in kilometers
        travel_class: Class code (SL, 3A, 2A, 1A, CC, EC, 2S)
        quota: Booking quota (General, Tatkal, Premium Tatkal)
        is_superfast: Whether train is superfast category
    
    Returns:
        Dict with: total_fare, base_fare, breakdown
    """
    cls = _normalize_class(travel_class)
    
    # Calculate base fare from distance
    rate_per_km = BASE_FARE_PER_KM.get(cls, 0.60)
    base_fare = round(distance_km * rate_per_km, 2)
    
    if base_fare <= 0:
        return {
            'total_fare': 0.0,
            'base_fare': 0.0,
            'breakdown': [],
            'error': 'Invalid distance'
        }
    
    breakdown = []
    breakdown.append({'component': 'Base Fare', 'amount': base_fare})
    
    total = base_fare
    
    # Reservation charge
    reservation = RESERVATION_CHARGE.get(cls, 20)
    breakdown.append({'component': 'Reservation Charge', 'amount': reservation})
    total += reservation
    
    # Superfast surcharge
    superfast_charge = 0.0
    if is_superfast:
        superfast_charge = SUPERFAST_SURCHARGE.get(cls, 30)
        breakdown.append({'component': 'Superfast Surcharge', 'amount': superfast_charge})
        total += superfast_charge
    
    # Tatkal premium
    tatkal_charge = 0.0
    quota_upper = (quota or '').upper().strip()
    if quota_upper in ('TATKAL', 'TQ', 'TK', 'PREMIUM TATKAL', 'PT'):
        tatkal_charge = _calculate_tatkal_charge(base_fare, cls, quota_upper)
        breakdown.append({'component': 'Tatkal Premium', 'amount': tatkal_charge})
        total += tatkal_charge
    
    # GST (AC classes only)
    gst = 0.0
    if cls in AC_CLASSES:
        gst = round(total * GST_RATE, 2)
        breakdown.append({'component': f'GST ({int(GST_RATE * 100)}%)', 'amount': gst})
        total += gst
    
    total = round(total, 2)
    
    return {
        'total_fare': total,
        'base_fare': base_fare,
        'reservation_charge': reservation,
        'superfast_charge': superfast_charge,
        'tatkal_charge': tatkal_charge,
        'gst': gst,
        'travel_class': cls,
        'quota': quota,
        'distance_km': distance_km,
        'rate_per_km': rate_per_km,
        'breakdown': breakdown,
    }
