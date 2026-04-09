"""
Seat allocation service.

Provides high-level API for seat operations:
  - Check availability
  - Allocate seats for booking
  - Handle cancellation
  - Manage waitlist promotion
"""

import logging
from typing import Optional, Dict, Any, List

from repositories.cloudscale_repository import cloudscale_repo
from utils.seat_allocation import (
    get_train_inventory,
    get_seat_availability,
    process_booking_allocation,
    process_booking_cancellation,
    calculate_refund,
    promote_waitlist,
)

logger = logging.getLogger(__name__)


class SeatService:
    """
    Service for seat allocation operations.
    
    Wraps seat_allocation utilities with validation,
    logging, and high-level business logic.
    """
    
    def __init__(self):
        self.repo = cloudscale_repo
    
    def check_availability(
        self,
        train_id: str,
        journey_date: str,
        travel_class: str
    ) -> Dict[str, Any]:
        """
        Check seat availability for a train/date/class.
        
        Returns:
            Dict with availability status and counts
        """
        try:
            availability = get_seat_availability(train_id, journey_date, travel_class)
            
            return {
                'success': True,
                'data': {
                    'train_id': train_id,
                    'journey_date': journey_date,
                    'class': travel_class,
                    **availability
                }
            }
        
        except Exception as exc:
            logger.exception(f"Error checking availability: {exc}")
            return {
                'success': False,
                'error': str(exc)
            }
    
    def check_availability_bulk(
        self,
        train_id: str,
        journey_date: str,
        classes: List[str] = None
    ) -> Dict[str, Any]:
        """
        Check availability for multiple classes at once.
        
        Args:
            train_id: Train ROWID
            journey_date: Journey date
            classes: List of class codes (default: all classes)
        
        Returns:
            Dict with availability per class
        """
        if classes is None:
            classes = ['SL', '3A', '2A', '1A', 'CC', '2S']
        
        results = {}
        
        for cls in classes:
            try:
                availability = get_seat_availability(train_id, journey_date, cls)
                results[cls] = availability
            except Exception as exc:
                logger.warning(f"Error checking {cls} availability: {exc}")
                results[cls] = {
                    'available': 0,
                    'status': 'error',
                    'error': str(exc)
                }
        
        return {
            'success': True,
            'data': {
                'train_id': train_id,
                'journey_date': journey_date,
                'classes': results
            }
        }
    
    def allocate_seats(
        self,
        train_id: str,
        travel_class: str,
        journey_date: str,
        passengers: List[Dict],
        quota: str = 'GN'
    ) -> Dict[str, Any]:
        """
        Allocate seats for passengers.
        
        Args:
            train_id: Train ROWID
            travel_class: Class code
            journey_date: Journey date
            passengers: List of passenger dicts with Name, Age, Gender, Berth_Preference
            quota: Booking quota
        
        Returns:
            Dict with allocated passengers and overall status
        """
        try:
            # Validate input
            if not passengers:
                return {
                    'success': False,
                    'error': 'No passengers provided'
                }
            
            if len(passengers) > 6:
                return {
                    'success': False,
                    'error': 'Maximum 6 passengers per booking'
                }
            
            # Validate each passenger
            for i, p in enumerate(passengers):
                if not p.get('Name'):
                    return {
                        'success': False,
                        'error': f'Passenger {i+1}: Name is required'
                    }
                
                age = p.get('Age')
                if age is None:
                    return {
                        'success': False,
                        'error': f'Passenger {i+1}: Age is required'
                    }
            
            # Process allocation
            allocated_passengers, overall_status = process_booking_allocation(
                train_id=train_id,
                travel_class=travel_class,
                journey_date=journey_date,
                passengers=passengers
            )
            
            logger.info(
                f"Allocated {len(allocated_passengers)} passengers for train {train_id}: "
                f"status={overall_status}"
            )
            
            return {
                'success': True,
                'data': {
                    'passengers': allocated_passengers,
                    'status': overall_status,
                    'quota': quota
                }
            }
        
        except Exception as exc:
            logger.exception(f"Seat allocation failed: {exc}")
            return {
                'success': False,
                'error': str(exc)
            }
    
    def cancel_allocation(
        self,
        train_id: str,
        travel_class: str,
        journey_date: str,
        passengers: List[Dict]
    ) -> Dict[str, Any]:
        """
        Cancel seat allocation and free seats.
        
        Args:
            train_id: Train ROWID
            travel_class: Class code
            journey_date: Journey date
            passengers: List of passengers being cancelled
        
        Returns:
            Dict with cancellation results
        """
        try:
            result = process_booking_cancellation(
                train_id=train_id,
                travel_class=travel_class,
                journey_date=journey_date,
                passengers_to_cancel=passengers
            )
            
            logger.info(
                f"Cancelled allocation for train {train_id}: "
                f"freed={result.get('freed_seats')}, promoted={result.get('promoted_count')}"
            )
            
            return {
                'success': True,
                'data': result
            }
        
        except Exception as exc:
            logger.exception(f"Cancellation failed: {exc}")
            return {
                'success': False,
                'error': str(exc)
            }
    
    def get_refund_amount(
        self,
        total_fare: float,
        travel_class: str,
        quota: str,
        departure_datetime: str
    ) -> Dict[str, Any]:
        """
        Calculate refund amount for cancellation.
        
        Returns:
            Dict with refund amount, deduction, and rule applied
        """
        try:
            refund_info = calculate_refund(
                total_fare=total_fare,
                travel_class=travel_class,
                quota=quota,
                departure_datetime=departure_datetime
            )
            
            return {
                'success': True,
                'data': refund_info
            }
        
        except Exception as exc:
            logger.exception(f"Refund calculation failed: {exc}")
            return {
                'success': False,
                'error': str(exc)
            }
    
    def get_inventory_status(
        self,
        train_id: str,
        journey_date: str,
        travel_class: str
    ) -> Dict[str, Any]:
        """
        Get detailed inventory status (admin use).
        
        Returns full inventory record including seat allocation details.
        """
        try:
            inventory = get_train_inventory(train_id, journey_date, travel_class)
            
            if not inventory:
                return {
                    'success': False,
                    'error': 'Inventory not found'
                }
            
            return {
                'success': True,
                'data': {
                    'inventory_id': inventory.get('ROWID'),
                    'train_id': train_id,
                    'journey_date': journey_date,
                    'class': travel_class,
                    'total_capacity': inventory.get('Total_Capacity'),
                    'confirmed_count': inventory.get('Confirmed_Count'),
                    'rac_count': inventory.get('RAC_Count'),
                    'waitlist_count': inventory.get('Waitlist_Count'),
                    'chart_prepared': inventory.get('Chart_Prepared') == 'true'
                }
            }
        
        except Exception as exc:
            logger.exception(f"Error fetching inventory: {exc}")
            return {
                'success': False,
                'error': str(exc)
            }
    
    def trigger_promotion(
        self,
        train_id: str,
        travel_class: str,
        journey_date: str,
        num_seats: int = 1
    ) -> Dict[str, Any]:
        """
        Manually trigger waitlist promotion (admin use).
        
        Used when seats are freed administratively (e.g., chart preparation).
        """
        try:
            promoted = promote_waitlist(
                train_id=train_id,
                travel_class=travel_class,
                journey_date=journey_date,
                num_seats=num_seats
            )
            
            return {
                'success': True,
                'data': {
                    'promoted_count': promoted
                }
            }
        
        except Exception as exc:
            logger.exception(f"Promotion failed: {exc}")
            return {
                'success': False,
                'error': str(exc)
            }


# Singleton instance
seat_service = SeatService()
