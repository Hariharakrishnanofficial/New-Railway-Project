"""
Booking Controller

Business logic for booking operations.
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime
from controllers.base_controller import BaseController
from controllers.train_controller import TrainController
from models.booking import Booking
from utils.helpers import generate_pnr, generate_booking_reference
from config import TABLES


class BookingController(BaseController):
    """Controller for booking-related operations."""

    def __init__(self):
        super().__init__(TABLES.get('bookings', 'Bookings'), Booking)
        self.train_controller = TrainController()

    def create_booking(self, user_id: str, train_id: str, journey_date: str,
                      class_type: str, passengers: int,
                      passenger_details: List[Dict] = None) -> Tuple[Optional[Dict], Optional[str]]:
        """
        Create a new booking.

        Args:
            user_id: User's ROWID
            train_id: Train's ROWID
            journey_date: Journey date (YYYY-MM-DD)
            class_type: Class (SL, 3A, 2A, 1A)
            passengers: Number of passengers
            passenger_details: List of passenger info

        Returns:
            Tuple of (booking data, error message)
        """
        # Check availability
        availability = self.train_controller.get_seat_availability(
            train_id, journey_date, class_type)

        if availability['available'] < passengers:
            if availability['rac_available'] >= passengers:
                status = 'RAC'
            else:
                status = 'Waitlisted'
        else:
            status = 'Confirmed'

        # Calculate fare (simplified)
        base_fare = self._calculate_fare(train_id, class_type, passengers)

        booking_data = {
            'User_ID': user_id,
            'Train_ID': train_id,
            'PNR': generate_pnr(),
            'Booking_Reference': generate_booking_reference(),
            'Journey_Date': journey_date,
            'Class': class_type,
            'Passengers': passengers,
            'Passenger_Details': str(passenger_details) if passenger_details else None,
            'Status': status,
            'Base_Fare': base_fare,
            'Tax': round(base_fare * 0.05, 2),  # 5% tax
            'Convenience_Fee': 20.0,
            'Total_Fare': round(base_fare * 1.05 + 20, 2),
            'Payment_Status': 'Pending',
            'Booking_Date': datetime.now().isoformat(),
        }

        if status == 'RAC':
            booking_data['RAC_Number'] = availability['rac'] + 1
        elif status == 'Waitlisted':
            booking_data['Waitlist_Number'] = self._get_next_waitlist(
                train_id, journey_date, class_type)

        return self.create(booking_data)

    def cancel_booking(self, booking_id: str, user_id: str) -> Tuple[Optional[Dict], Optional[str]]:
        """
        Cancel a booking and calculate refund.

        Returns:
            Tuple of (updated booking, error message)
        """
        booking = self.get_by_id(booking_id)
        if not booking:
            return None, "Booking not found"

        if booking.get('User_ID') != user_id:
            return None, "Unauthorized to cancel this booking"

        if booking.get('Status') == 'Cancelled':
            return None, "Booking is already cancelled"

        # Calculate refund
        total_fare = booking.get('Total_Fare', 0)
        cancellation_charge = self._calculate_cancellation_charge(booking)
        refund_amount = max(0, total_fare - cancellation_charge)

        update_data = {
            'Status': 'Cancelled',
            'Cancellation_Date': datetime.now().isoformat(),
            'Refund_Amount': refund_amount,
            'Payment_Status': 'Refund_Initiated' if refund_amount > 0 else 'Cancelled',
        }

        return self.update(booking_id, update_data)

    def get_booking_by_pnr(self, pnr: str) -> Optional[Dict]:
        """Get booking by PNR number."""
        return self.repo.find_one({'PNR': pnr})

    def get_user_bookings(self, user_id: str, status: str = None) -> List[Dict]:
        """Get all bookings for a user."""
        filters = {'User_ID': user_id}
        if status:
            filters['Status'] = status
        return self.repo.find_many(filters)

    def get_upcoming_bookings(self, user_id: str) -> List[Dict]:
        """Get upcoming bookings for a user."""
        today = datetime.now().strftime('%Y-%m-%d')
        bookings = self.get_user_bookings(user_id)
        return [b for b in bookings
                if b.get('Journey_Date', '') >= today
                and b.get('Status') != 'Cancelled']

    def _calculate_fare(self, train_id: str, class_type: str,
                       passengers: int) -> float:
        """Calculate base fare for booking."""
        # Base fare per class (simplified)
        class_rates = {
            '1A': 2500,
            '2A': 1500,
            '3A': 1000,
            'SL': 500,
            'CC': 800,
            'EC': 2000,
            'GN': 200,
        }
        base = class_rates.get(class_type, 500)
        return base * passengers

    def _calculate_cancellation_charge(self, booking: Dict) -> float:
        """Calculate cancellation charge based on time before journey."""
        journey_date = booking.get('Journey_Date', '')
        try:
            journey = datetime.strptime(journey_date, '%Y-%m-%d')
            days_before = (journey - datetime.now()).days

            total = booking.get('Total_Fare', 0)

            if days_before > 7:
                return total * 0.10  # 10% charge
            elif days_before > 2:
                return total * 0.25  # 25% charge
            elif days_before > 0:
                return total * 0.50  # 50% charge
            else:
                return total  # No refund
        except:
            return booking.get('Total_Fare', 0) * 0.25

    def _get_next_waitlist(self, train_id: str, date: str, class_type: str) -> int:
        """Get next waitlist number."""
        bookings = self.repo.find_many({
            'Train_ID': train_id,
            'Journey_Date': date,
            'Class': class_type,
            'Status': 'Waitlisted'
        })
        if not bookings:
            return 1
        max_wl = max(b.get('Waitlist_Number', 0) for b in bookings)
        return max_wl + 1
