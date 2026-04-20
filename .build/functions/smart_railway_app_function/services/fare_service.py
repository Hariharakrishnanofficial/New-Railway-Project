"""
Fare calculation service.

Provides high-level API for fare operations:
  - Calculate fare for train search results
  - Calculate fare for booking with passengers
  - Apply concessions and validate pricing
"""

import logging
from typing import Optional, Dict, Any, List, Union

from repositories.cloudscale_repository import cloudscale_repo
from repositories.cache_manager import cache
from config import TABLES, BASE_FARE_PER_KM
from utils.fare_helper import (
    get_fare_for_journey,
    calculate_fare_for_passengers,
    calculate_distance_fare,
)

logger = logging.getLogger(__name__)


class FareService:
    """
    Service for fare calculation operations.
    
    Wraps fare_helper utilities with caching, validation,
    and database integration.
    """
    
    def __init__(self):
        self.repo = cloudscale_repo
    
    def get_fare(
        self,
        train_id: str,
        from_station_id: str,
        to_station_id: str,
        travel_class: str,
        quota: str = 'GN',
        train_type: str = None,
        adults: int = 1,
        children: int = 0,
        seniors: int = 0,
        concession_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Calculate fare for a journey with all applicable charges.
        
        Args:
            train_id: Train ROWID
            from_station_id: Source station ROWID
            to_station_id: Destination station ROWID
            travel_class: Class code (SL, 3A, 2A, etc.)
            quota: Booking quota (GN, TQ, LD, etc.)
            train_type: Train type (Superfast, Express, etc.)
            adults: Number of adult passengers
            children: Number of children (5-12 years)
            seniors: Number of senior citizens (60+)
            concession_type: Concession type (Student, Disabled)
        
        Returns:
            Dict with fare breakdown and total
        """
        try:
            # Calculate distance
            distance = self._get_distance(from_station_id, to_station_id)
            
            if distance is None:
                # Try to get from train route
                distance = self._get_route_distance(train_id, from_station_id, to_station_id)
            
            if distance is None:
                logger.warning(f"Could not determine distance for journey")
                distance = 100  # Default fallback
            
            # Get train type if not provided
            if not train_type:
                train_type = self._get_train_type(train_id)
            
            # Check for fare rule in Fares table
            fare_rule = self._get_fare_rule(train_id, from_station_id, to_station_id, travel_class)
            
            if fare_rule:
                logger.info(f"Using fare rule from database")
                base_fare = float(fare_rule.get('Base_Fare') or 0)
            else:
                base_fare = None
            
            # Calculate fare using helper
            fare_breakdown = get_fare_for_journey(
                distance=distance,
                travel_class=travel_class,
                train_type=train_type,
                quota=quota,
                base_fare=base_fare
            )
            
            # Calculate total for all passengers
            total_passengers = adults + children + seniors
            
            passenger_fares = calculate_fare_for_passengers(
                per_passenger_fare=fare_breakdown['total'],
                adults=adults,
                children=children,
                seniors=seniors,
                concession_type=concession_type
            )
            
            return {
                'success': True,
                'data': {
                    'distance_km': distance,
                    'per_passenger': fare_breakdown,
                    'passengers': {
                        'adults': adults,
                        'children': children,
                        'seniors': seniors,
                        'concession': concession_type
                    },
                    'fare_summary': passenger_fares,
                    'total': passenger_fares['total'],
                    'currency': 'INR'
                }
            }
        
        except Exception as exc:
            logger.exception(f"Error calculating fare: {exc}")
            return {
                'success': False,
                'error': str(exc)
            }
    
    def get_quick_fare(
        self,
        distance: float,
        travel_class: str,
        train_type: str = 'Express',
        quota: str = 'GN'
    ) -> Dict[str, Any]:
        """
        Quick fare calculation without database lookup.
        
        Useful for search result display where only approximate
        fare is needed.
        """
        try:
            fare = get_fare_for_journey(
                distance=distance,
                travel_class=travel_class,
                train_type=train_type,
                quota=quota
            )
            
            return {
                'success': True,
                'data': {
                    'distance_km': distance,
                    'fare': fare['total'],
                    'breakdown': fare
                }
            }
        
        except Exception as exc:
            logger.error(f"Quick fare calculation failed: {exc}")
            return {
                'success': False,
                'error': str(exc),
                'data': {'fare': self._fallback_fare(distance, travel_class)}
            }
    
    def validate_fare(
        self,
        calculated_fare: float,
        submitted_fare: float,
        tolerance: float = 0.01
    ) -> bool:
        """
        Validate that submitted fare matches calculated fare.
        
        Used during booking confirmation to prevent fare manipulation.
        """
        diff = abs(calculated_fare - submitted_fare)
        allowed_diff = calculated_fare * tolerance
        
        if diff > allowed_diff:
            logger.warning(
                f"Fare mismatch: calculated={calculated_fare}, "
                f"submitted={submitted_fare}, diff={diff}"
            )
            return False
        
        return True
    
    def _get_distance(
        self,
        from_station_id: str,
        to_station_id: str
    ) -> Optional[float]:
        """Get distance between two stations."""
        cache_key = f"distance:{from_station_id}:{to_station_id}"
        cached = cache.get(cache_key)
        if cached:
            return cached
        
        # Try to calculate from station coordinates or route
        from_station = self._get_station(from_station_id)
        to_station = self._get_station(to_station_id)
        
        if from_station and to_station:
            from_km = float(from_station.get('Distance_From_Origin') or 0)
            to_km = float(to_station.get('Distance_From_Origin') or 0)
            
            if from_km and to_km:
                distance = abs(to_km - from_km)
                cache.set(cache_key, distance, ttl=86400)  # 24h cache
                return distance
        
        return None
    
    def _get_route_distance(
        self,
        train_id: str,
        from_station_id: str,
        to_station_id: str
    ) -> Optional[float]:
        """Get distance from train route stops."""
        try:
            # Fetch route stops for this train
            criteria = f"Train = {train_id}"
            result = self.repo.get_all_records(
                TABLES.get('route_stops', 'Route_Stops'),
                criteria=criteria
            )
            
            if not result.get('success'):
                return None
            
            stops = result.get('data', {}).get('data', [])
            
            from_km = None
            to_km = None
            
            for stop in stops:
                if str(stop.get('Station')) == str(from_station_id):
                    from_km = float(stop.get('Distance_From_Origin') or 0)
                if str(stop.get('Station')) == str(to_station_id):
                    to_km = float(stop.get('Distance_From_Origin') or 0)
            
            if from_km is not None and to_km is not None:
                return abs(to_km - from_km)
            
        except Exception as exc:
            logger.warning(f"Error getting route distance: {exc}")
        
        return None
    
    def _get_train_type(self, train_id: str) -> str:
        """Get train type (Superfast, Express, etc.)."""
        train = self.repo.get_train_cached(train_id)
        if train:
            return train.get('Train_Type', 'Express')
        return 'Express'
    
    def _get_station(self, station_id: str) -> Optional[Dict]:
        """Get station details."""
        cache_key = f"station:{station_id}"
        cached = cache.get(cache_key)
        if cached:
            return cached
        
        result = self.repo.get_record(TABLES['stations'], station_id)
        if result.get('success'):
            station = result.get('data', {}).get('data')
            if station:
                cache.set(cache_key, station, ttl=86400)
                return station
        
        return None
    
    def _get_fare_rule(
        self,
        train_id: str,
        from_station_id: str,
        to_station_id: str,
        travel_class: str
    ) -> Optional[Dict]:
        """Look up fare rule from Fares table."""
        try:
            criteria = (
                f"Train = {train_id} AND "
                f"Source_Station = {from_station_id} AND "
                f"Destination_Station = {to_station_id} AND "
                f"Class = '{travel_class}'"
            )
            
            result = self.repo.get_all_records(
                TABLES.get('fares', 'Fares'),
                criteria=criteria,
                limit=1
            )
            
            if result.get('success'):
                records = result.get('data', {}).get('data', [])
                if records:
                    return records[0]
        
        except Exception as exc:
            logger.debug(f"No fare rule found: {exc}")
        
        return None
    
    def _fallback_fare(self, distance: float, travel_class: str) -> float:
        """Calculate fallback fare when normal calculation fails."""
        rates = {
            'SL': 0.40,
            '3A': 0.90,
            '2A': 1.25,
            '1A': 2.10,
            'CC': 0.70,
            'EC': 1.50,
            '2S': 0.30,
        }
        rate = rates.get(travel_class.upper(), 0.50)
        return round(distance * rate, 0)


# Singleton instance
fare_service = FareService()
