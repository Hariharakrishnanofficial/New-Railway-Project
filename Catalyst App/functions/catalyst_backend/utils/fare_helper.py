"""
Fare calculation utility.
Handles:
  1. Dynamic fare from Fares table (with Is_Active filter)
  2. Fallback to Train record default fare
  3. Tatkal surcharge from Quotas table or Fares.Tatkal_Fare
  4. Chargeable passengers (excludes children)
Uses ZohoRepository with caching for the fare matrix lookup.
"""
import logging
from repositories.cloudscale_repository import zoho_repo, CriteriaBuilder
from repositories.cache_manager import cache, TTL_FARES
from config import TABLES

logger = logging.getLogger(__name__)


def get_fare_for_journey(train_id, from_station_id, to_station_id, cls,
                         train_record=None, quota="General") -> float:
    """
    Calculates the fare for a specific journey with full IRCTC-style logic.
    
    Fare Priority:
    1.  **Dynamic Fare**: Looks for an active record in the `Fares` table matching
        the exact train, from/to stations, and class.
        - If `Dynamic_Fare` is set and > 0, it is used.
        - Otherwise, `Base_Fare` from the same record is used.
    2.  **Train Default Fare**: If no matching `Fares` record is found, it falls
        back to the default fare stored on the `Trains` record (e.g., `Fare_SL`).
        
    Surcharge Logic:
    - **Tatkal**: If the quota is 'Tatkal' or 'Premium Tatkal':
        - It first checks for a specific `Tatkal_Fare` in the `Fares` record.
        - If not found, it fetches the `Surcharge_Percentage` from the `Quotas`
          table and applies it to the base fare.
        - If no surcharge is configured, a default of 30% is applied as a fallback.
    """
    cache_key = f'fare:{train_id}:{from_station_id}:{to_station_id}:{cls}:{quota}'
    cached = cache.get(cache_key)
    if cached is not None:
        logger.debug(f"Fare cache hit for key: {cache_key}")
        return cached

    base_fare = 0.0
    tatkal_fare_from_record = 0.0
    fare_record_found = False

    # Step 1 & 2: Query Fares table for dynamic/base fare
    try:
        criteria = (CriteriaBuilder()
                    .eq('Train', train_id)
                    .eq('From_Station', from_station_id)
                    .eq('To_Station', to_station_id)
                    .eq('Class', cls)
                    .eq('Is_Active', 'true')
                    .build())
        
        records = zoho_repo.get_records(TABLES['fares'], criteria=criteria, limit=1)
        
        if records:
            fare_record = records[0]
            logger.info(f"Found matching fare record: {fare_record.get('ID')}")
            dynamic_fare = float(fare_record.get('Dynamic_Fare') or 0)
            base_fare_val = float(fare_record.get('Base_Fare') or 0)
            
            base_fare = dynamic_fare if dynamic_fare > 0 else base_fare_val
            tatkal_fare_from_record = float(fare_record.get('Tatkal_Fare') or 0)
            
            if base_fare > 0:
                fare_record_found = True
            else:
                logger.warning(f"Fare record {fare_record.get('ID')} found but has zero base fare.")

    except Exception as exc:
        logger.error(f'Fares table lookup failed for train {train_id}: {exc}', exc_info=True)

    # Step 3: Fallback to Train record's default fare
    if not fare_record_found:
        logger.warning(f"No active fare record found for {train_id} from {from_station_id} to {to_station_id}. Falling back to train default.")
        if not train_record:
            train_record = zoho_repo.get_train_cached(train_id)

        if not train_record:
            logger.error(f"Cannot calculate fare. Train record {train_id} not found.")
            return 0.0

        fare_map = {
            'SL': 'Fare_SL', '2S': 'Fare_2S',
            '3A': 'Fare_3A', '3AC': 'Fare_3A',
            '2A': 'Fare_2A', '2AC': 'Fare_2A',
            '1A': 'Fare_1A', '1AC': 'Fare_1A',
            'CC': 'Fare_CC', 'EC': 'Fare_EC',
            'FC': 'Fare_1A', # Assuming FC maps to 1A fare
        }
        field = fare_map.get(str(cls).upper(), 'Fare_SL')
        base_fare = float((train_record or {}).get(field) or 0)
        logger.info(f"Using fallback fare from Train.{field}: {base_fare}")

    # Step 4: Apply Tatkal surcharge if applicable
    total_fare = base_fare
    if str(quota or '').lower().strip() in ('tatkal', 'premium tatkal', 'tq', 'pt'):
        logger.info(f"Applying Tatkal surcharge for quota '{quota}'")
        if tatkal_fare_from_record > 0:
            total_fare += tatkal_fare_from_record
            logger.info(f"Used specific Tatkal_Fare from Fares record: {tatkal_fare_from_record}")
        else:
            surcharge_pct = _get_tatkal_surcharge(quota)
            if surcharge_pct > 0:
                surcharge_amount = base_fare * (surcharge_pct / 100.0)
                total_fare += surcharge_amount
                logger.info(f"Applied {surcharge_pct}% surcharge from Quotas table: {surcharge_amount}")
            else:
                # Fallback to a default surcharge if not configured
                surcharge_amount = base_fare * 0.30 
                total_fare += surcharge_amount
                logger.warning(f"No Tatkal surcharge configured. Applying default 30%: {surcharge_amount}")

    logger.info(f"Final calculated fare for journey: {total_fare}")
    cache.set(cache_key, total_fare, ttl=TTL_FARES)
    return total_fare


def _get_tatkal_surcharge(quota) -> float:
    """Fetch Tatkal surcharge percentage from Quotas table."""
    cache_key = f'tatkal_surcharge:{quota}'
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    try:
        criteria = CriteriaBuilder().eq('Quota_Name', quota).build()
        quotas = zoho_repo.get_records(TABLES['quotas'], criteria=criteria, limit=1)
        if quotas:
            pct = float(quotas[0].get('Surcharge_Percentage') or 0)
            cache.set(cache_key, pct, ttl=TTL_FARES)
            return pct
    except Exception as exc:
        logger.warning(f'Quotas lookup error: {exc}')

    cache.set(cache_key, 0.0, ttl=TTL_FARES)
    return 0.0
