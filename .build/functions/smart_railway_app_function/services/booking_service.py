"""
Booking service - Full booking workflow orchestration.

Coordinates:
  - Fare calculation
  - Seat allocation
  - Booking creation
  - Cancellation with refund
"""

import json
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List

from repositories.cloudscale_repository import cloudscale_repo
from repositories.cache_manager import cache
from services.fare_service import fare_service
from services.seat_service import seat_service
from config import (
    TABLES,
    MAX_PASSENGERS_PER_BOOKING,
    BOOKING_ADVANCE_DAYS,
    MONTHLY_BOOKING_LIMIT_UNVERIFIED,
    MONTHLY_BOOKING_LIMIT_VERIFIED,
)
from utils.date_helpers import to_zoho_date_only, parse_date, get_zoho_date_criteria
from utils.helpers import generate_pnr

logger = logging.getLogger(__name__)


class BookingService:
    """
    Orchestrates the complete booking workflow.
    
    Flow:
        1. Validate request (passengers, dates, limits)
        2. Calculate fare (with concessions)
        3. Allocate seats (CNF/RAC/WL)
        4. Create booking record
        5. Create passenger records
        6. Return confirmation
    """
    
    def __init__(self):
        self.repo = cloudscale_repo
        self.fare_service = fare_service
        self.seat_service = seat_service
    
    def create_booking(
        self,
        user_id: str,
        train_id: str,
        from_station_id: str,
        to_station_id: str,
        journey_date: str,
        travel_class: str,
        quota: str,
        passengers: List[Dict],
        contact_email: str = None,
        contact_phone: str = None,
        user_verified: bool = False
    ) -> Dict[str, Any]:
        """
        Create a new booking with all passengers.
        
        Args:
            user_id: User ROWID
            train_id: Train ROWID
            from_station_id: Source station ROWID
            to_station_id: Destination station ROWID
            journey_date: Journey date (YYYY-MM-DD or DD-MMM-YYYY)
            travel_class: Class code (SL, 3A, etc.)
            quota: Quota code (GN, TQ, LD, etc.)
            passengers: List of passenger dicts
            contact_email: Contact email (optional, uses user's)
            contact_phone: Contact phone (optional, uses user's)
            user_verified: Whether user is KYC verified
        
        Returns:
            Dict with success, booking_id, PNR, etc.
        """
        try:
            # ── Step 1: Validate request ─────────────────────────────────────
            validation = self._validate_booking_request(
                user_id=user_id,
                passengers=passengers,
                journey_date=journey_date,
                user_verified=user_verified
            )
            
            if not validation['valid']:
                return {
                    'success': False,
                    'error': validation['error']
                }
            
            # ── Step 2: Get train details ────────────────────────────────────
            train = self.repo.get_train_cached(train_id)
            if not train:
                return {
                    'success': False,
                    'error': f'Train not found: {train_id}'
                }
            
            train_type = train.get('Train_Type', 'Express')
            
            # ── Step 3: Calculate fare ───────────────────────────────────────
            adults, children, seniors = self._categorize_passengers(passengers)
            
            fare_result = self.fare_service.get_fare(
                train_id=train_id,
                from_station_id=from_station_id,
                to_station_id=to_station_id,
                travel_class=travel_class,
                quota=quota,
                train_type=train_type,
                adults=adults,
                children=children,
                seniors=seniors
            )
            
            if not fare_result.get('success'):
                return {
                    'success': False,
                    'error': f"Fare calculation failed: {fare_result.get('error')}"
                }
            
            total_fare = fare_result['data']['total']
            fare_breakdown = fare_result['data']
            
            # ── Step 4: Allocate seats ───────────────────────────────────────
            allocation_result = self.seat_service.allocate_seats(
                train_id=train_id,
                travel_class=travel_class,
                journey_date=journey_date,
                passengers=passengers,
                quota=quota
            )
            
            if not allocation_result.get('success'):
                return {
                    'success': False,
                    'error': f"Seat allocation failed: {allocation_result.get('error')}"
                }
            
            allocated_passengers = allocation_result['data']['passengers']
            booking_status = allocation_result['data']['status']
            
            # ── Step 5: Generate PNR ─────────────────────────────────────────
            pnr = generate_pnr()
            
            # ── Step 6: Create booking record ────────────────────────────────
            journey_date_zoho = to_zoho_date_only(journey_date) or journey_date
            booking_time = datetime.now().strftime('%d-%b-%Y %H:%M:%S')
            
            booking_data = {
                'PNR': pnr,
                'User_ID': user_id,
                'Train_ID': train_id,
                'Train_Number': train.get('Train_Number'),
                'Train_Name': train.get('Train_Name'),
                'From_Station': from_station_id,
                'From_Station_Code': self._get_station_code(from_station_id),
                'To_Station': to_station_id,
                'To_Station_Code': self._get_station_code(to_station_id),
                'Journey_Date': journey_date_zoho,
                'Class': travel_class,
                'Quota': quota,
                'Total_Passengers': len(passengers),
                'Total_Fare': total_fare,
                'Fare_Breakdown': json.dumps(fare_breakdown),
                'Booking_Status': booking_status,
                'Booking_Time': booking_time,
                'Contact_Email': contact_email,
                'Contact_Phone': contact_phone,
            }
            
            # ── Step 7: Create passenger records ─────────────────────────────
            passenger_records = []
            for i, p in enumerate(allocated_passengers):
                passenger_records.append({
                    'Name': p.get('Name'),
                    'Age': p.get('Age'),
                    'Gender': p.get('Gender', 'M'),
                    'ID_Type': p.get('ID_Type'),
                    'ID_Number': p.get('ID_Number'),
                    'Berth_Preference': p.get('Berth_Preference'),
                    'Current_Status': p.get('Current_Status'),
                    'Coach': p.get('Coach', ''),
                    'Seat_Number': p.get('Seat_Number', ''),
                    'Berth': p.get('Berth', ''),
                    'Meal_Preference': p.get('Meal_Preference'),
                    'Passenger_Type': self._get_passenger_type(p.get('Age')),
                })
            
            result = self.repo.create_booking_with_passengers(booking_data, passenger_records)
            
            if not result.get('success'):
                # Rollback seat allocation
                self.seat_service.cancel_allocation(
                    train_id, travel_class, journey_date, allocated_passengers
                )
                return {
                    'success': False,
                    'error': f"Failed to save booking: {result.get('error')}"
                }
            
            logger.info(f"Booking created: PNR={pnr}, Status={booking_status}")
            
            return {
                'success': True,
                'data': {
                    'booking_id': result['data']['booking_id'],
                    'pnr': pnr,
                    'status': booking_status,
                    'passengers': allocated_passengers,
                    'total_fare': total_fare,
                    'fare_breakdown': fare_breakdown,
                    'journey_date': journey_date_zoho,
                    'train': {
                        'number': train.get('Train_Number'),
                        'name': train.get('Train_Name'),
                        'departure': train.get('Departure_Time'),
                        'arrival': train.get('Arrival_Time')
                    }
                }
            }
        
        except Exception as exc:
            logger.exception(f"Booking creation failed: {exc}")
            return {
                'success': False,
                'error': str(exc)
            }
    
    def cancel_booking(
        self,
        booking_id: str = None,
        pnr: str = None,
        user_id: str = None,
        cancel_passengers: List[str] = None
    ) -> Dict[str, Any]:
        """
        Cancel a booking or specific passengers.
        
        Args:
            booking_id: Booking ROWID
            pnr: PNR (alternative to booking_id)
            user_id: User ROWID (for authorization)
            cancel_passengers: List of passenger IDs to cancel (None = all)
        
        Returns:
            Dict with refund amount and updated status
        """
        try:
            # Get booking
            if pnr:
                booking = self.repo.get_booking_by_pnr(pnr)
            elif booking_id:
                result = self.repo.get_record(TABLES['bookings'], booking_id)
                booking = result.get('data', {}).get('data') if result.get('success') else None
            else:
                return {'success': False, 'error': 'Booking ID or PNR required'}
            
            if not booking:
                return {'success': False, 'error': 'Booking not found'}
            
            booking_id = booking.get('ROWID')
            
            # Check authorization
            if user_id and str(booking.get('User_ID')) != str(user_id):
                return {'success': False, 'error': 'Not authorized to cancel this booking'}
            
            # Check if already cancelled
            if booking.get('Booking_Status') == 'cancelled':
                return {'success': False, 'error': 'Booking already cancelled'}
            
            # Get passengers
            passengers = self.repo.get_passengers_by_booking(booking_id)
            if not passengers:
                return {'success': False, 'error': 'No passengers found'}
            
            # Filter passengers to cancel
            if cancel_passengers:
                passengers_to_cancel = [
                    p for p in passengers 
                    if p.get('ROWID') in cancel_passengers
                ]
            else:
                passengers_to_cancel = passengers
            
            if not passengers_to_cancel:
                return {'success': False, 'error': 'No matching passengers to cancel'}
            
            # Calculate refund
            total_fare = float(booking.get('Total_Fare') or 0)
            per_passenger_fare = total_fare / len(passengers)
            cancelling_fare = per_passenger_fare * len(passengers_to_cancel)
            
            # Get departure datetime
            journey_date = booking.get('Journey_Date')
            train = self.repo.get_train_cached(booking.get('Train_ID'))
            departure_time = train.get('Departure_Time', '00:00') if train else '00:00'
            departure_datetime = f"{journey_date} {departure_time}"
            
            refund_result = self.seat_service.get_refund_amount(
                total_fare=cancelling_fare,
                travel_class=booking.get('Class', 'SL'),
                quota=booking.get('Quota', 'GN'),
                departure_datetime=departure_datetime
            )
            
            refund_info = refund_result.get('data', {})
            
            # Free seats
            self.seat_service.cancel_allocation(
                train_id=booking.get('Train_ID'),
                travel_class=booking.get('Class'),
                journey_date=journey_date,
                passengers=passengers_to_cancel
            )
            
            # Update passenger statuses
            for p in passengers_to_cancel:
                self.repo.update_record(
                    TABLES['passengers'],
                    p['ROWID'],
                    {
                        'Previous_Status': p.get('Current_Status'),
                        'Current_Status': 'CAN'
                    }
                )
            
            # Update booking status
            cancelled_count = len(passengers_to_cancel)
            remaining = len(passengers) - cancelled_count
            
            if remaining == 0:
                new_status = 'cancelled'
            else:
                new_status = booking.get('Booking_Status')  # Keep current if partial
            
            self.repo.update_record(
                TABLES['bookings'],
                booking_id,
                {
                    'Booking_Status': new_status,
                    'Refund_Amount': refund_info.get('refund', 0),
                    'Cancellation_Time': datetime.now().strftime('%d-%b-%Y %H:%M:%S')
                }
            )
            
            logger.info(f"Cancelled {cancelled_count} passengers from PNR {booking.get('PNR')}, refund={refund_info.get('refund')}")
            
            return {
                'success': True,
                'data': {
                    'pnr': booking.get('PNR'),
                    'cancelled_passengers': cancelled_count,
                    'remaining_passengers': remaining,
                    'refund_amount': refund_info.get('refund', 0),
                    'deduction': refund_info.get('deduction', 0),
                    'rule': refund_info.get('rule'),
                    'new_status': new_status
                }
            }
        
        except Exception as exc:
            logger.exception(f"Cancellation failed: {exc}")
            return {
                'success': False,
                'error': str(exc)
            }
    
    def get_booking_details(
        self,
        booking_id: str = None,
        pnr: str = None
    ) -> Dict[str, Any]:
        """
        Get complete booking details with passengers.
        
        Args:
            booking_id: Booking ROWID
            pnr: PNR (alternative)
        
        Returns:
            Dict with booking and passenger details
        """
        try:
            # Get booking
            if pnr:
                booking = self.repo.get_booking_by_pnr(pnr)
            elif booking_id:
                result = self.repo.get_record(TABLES['bookings'], booking_id)
                booking = result.get('data', {}).get('data') if result.get('success') else None
            else:
                return {'success': False, 'error': 'Booking ID or PNR required'}
            
            if not booking:
                return {'success': False, 'error': 'Booking not found'}
            
            # Get passengers
            passengers = self.repo.get_passengers_by_booking(booking.get('ROWID'))
            
            # Parse fare breakdown
            fare_breakdown = {}
            try:
                fare_breakdown = json.loads(booking.get('Fare_Breakdown') or '{}')
            except Exception:
                pass
            
            # Get train details
            train = self.repo.get_train_cached(booking.get('Train_ID'))
            
            return {
                'success': True,
                'data': {
                    'booking': {
                        'id': booking.get('ROWID'),
                        'pnr': booking.get('PNR'),
                        'status': booking.get('Booking_Status'),
                        'journey_date': booking.get('Journey_Date'),
                        'class': booking.get('Class'),
                        'quota': booking.get('Quota'),
                        'total_fare': booking.get('Total_Fare'),
                        'fare_breakdown': fare_breakdown,
                        'booking_time': booking.get('Booking_Time'),
                        'refund_amount': booking.get('Refund_Amount'),
                        'cancellation_time': booking.get('Cancellation_Time'),
                    },
                    'train': {
                        'id': booking.get('Train_ID'),
                        'number': booking.get('Train_Number') or (train.get('Train_Number') if train else ''),
                        'name': booking.get('Train_Name') or (train.get('Train_Name') if train else ''),
                        'from_station': booking.get('From_Station_Code'),
                        'to_station': booking.get('To_Station_Code'),
                        'departure': train.get('Departure_Time') if train else '',
                        'arrival': train.get('Arrival_Time') if train else '',
                    },
                    'passengers': [
                        {
                            'id': p.get('ROWID'),
                            'name': p.get('Name'),
                            'age': p.get('Age'),
                            'gender': p.get('Gender'),
                            'status': p.get('Current_Status'),
                            'coach': p.get('Coach'),
                            'seat': p.get('Seat_Number'),
                            'berth': p.get('Berth'),
                        }
                        for p in passengers
                    ]
                }
            }
        
        except Exception as exc:
            logger.exception(f"Get booking details failed: {exc}")
            return {
                'success': False,
                'error': str(exc)
            }
    
    def get_user_bookings(
        self,
        user_id: str,
        status: str = None,
        limit: int = 50
    ) -> Dict[str, Any]:
        """
        Get all bookings for a user.
        
        Args:
            user_id: User ROWID
            status: Filter by status (optional)
            limit: Max results
        
        Returns:
            Dict with list of bookings
        """
        try:
            bookings = self.repo.get_user_bookings(user_id, status, limit)
            
            # Enrich with train info
            enriched = []
            for b in bookings:
                train = self.repo.get_train_cached(b.get('Train_ID'))
                enriched.append({
                    'id': b.get('ROWID'),
                    'pnr': b.get('PNR'),
                    'status': b.get('Booking_Status'),
                    'journey_date': b.get('Journey_Date'),
                    'class': b.get('Class'),
                    'total_fare': b.get('Total_Fare'),
                    'passengers': b.get('Total_Passengers'),
                    'train_number': b.get('Train_Number') or (train.get('Train_Number') if train else ''),
                    'train_name': b.get('Train_Name') or (train.get('Train_Name') if train else ''),
                    'from': b.get('From_Station_Code'),
                    'to': b.get('To_Station_Code'),
                    'booking_time': b.get('Booking_Time'),
                })
            
            return {
                'success': True,
                'data': {
                    'bookings': enriched,
                    'count': len(enriched)
                }
            }
        
        except Exception as exc:
            logger.exception(f"Get user bookings failed: {exc}")
            return {
                'success': False,
                'error': str(exc)
            }
    
    def _validate_booking_request(
        self,
        user_id: str,
        passengers: List[Dict],
        journey_date: str,
        user_verified: bool
    ) -> Dict[str, Any]:
        """Validate booking request."""
        # Check passenger count
        if not passengers:
            return {'valid': False, 'error': 'At least one passenger required'}
        
        if len(passengers) > MAX_PASSENGERS_PER_BOOKING:
            return {'valid': False, 'error': f'Maximum {MAX_PASSENGERS_PER_BOOKING} passengers allowed'}
        
        # Check journey date
        journey_dt = parse_date(journey_date)
        if not journey_dt:
            return {'valid': False, 'error': 'Invalid journey date format'}
        
        today = datetime.now().date()
        
        if journey_dt.date() < today:
            return {'valid': False, 'error': 'Journey date cannot be in the past'}
        
        days_ahead = (journey_dt.date() - today).days
        if days_ahead > BOOKING_ADVANCE_DAYS:
            return {'valid': False, 'error': f'Cannot book more than {BOOKING_ADVANCE_DAYS} days in advance'}
        
        # Check monthly booking limit
        start_of_month = today.replace(day=1).strftime('%d-%b-%Y')
        monthly_count = self.repo.count_monthly_bookings(user_id, start_of_month)
        
        limit = MONTHLY_BOOKING_LIMIT_VERIFIED if user_verified else MONTHLY_BOOKING_LIMIT_UNVERIFIED
        if monthly_count >= limit:
            return {'valid': False, 'error': f'Monthly booking limit ({limit}) reached'}
        
        return {'valid': True}
    
    def _categorize_passengers(self, passengers: List[Dict]) -> tuple:
        """Categorize passengers by type (adults, children, seniors)."""
        adults = 0
        children = 0
        seniors = 0
        
        for p in passengers:
            age = int(p.get('Age') or 30)
            if age < 5:
                # Infants - no ticket needed (handled separately)
                pass
            elif age < 12:
                children += 1
            elif age >= 60:
                seniors += 1
            else:
                adults += 1
        
        return adults, children, seniors
    
    def _get_passenger_type(self, age: int) -> str:
        """Get passenger type based on age."""
        age = int(age or 30)
        if age < 5:
            return 'Infant'
        elif age < 12:
            return 'Child'
        elif age >= 60:
            return 'Senior'
        else:
            return 'Adult'
    
    def _get_station_code(self, station_id: str) -> str:
        """Get station code from ID."""
        cache_key = f"station_code:{station_id}"
        cached = cache.get(cache_key)
        if cached:
            return cached
        
        result = self.repo.get_record(TABLES['stations'], station_id)
        if result.get('success'):
            station = result.get('data', {}).get('data')
            if station:
                code = station.get('Station_Code', '')
                cache.set(cache_key, code, ttl=86400)
                return code
        
        return ''


# Singleton instance
booking_service = BookingService()
