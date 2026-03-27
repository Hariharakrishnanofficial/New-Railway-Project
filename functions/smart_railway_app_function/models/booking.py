"""
Booking Model

Entity schema for Bookings table.
"""

from dataclasses import dataclass
from typing import List, Optional
from models.base_model import BaseModel


@dataclass
class Booking(BaseModel):
    """Booking entity model."""

    __tablename__ = 'Bookings'

    # Reference fields (Foreign Keys)
    User_ID: Optional[str] = None
    Train_ID: Optional[str] = None
    Route_ID: Optional[str] = None
    Source_Station_ID: Optional[str] = None
    Destination_Station_ID: Optional[str] = None

    # Booking identifiers
    PNR: Optional[str] = None
    Booking_Reference: Optional[str] = None

    # Journey details
    Journey_Date: Optional[str] = None
    Boarding_Time: Optional[str] = None
    Class: Optional[str] = None  # SL, 3A, 2A, 1A, CC, EC
    Quota: Optional[str] = None  # GN, TQ, LD, PT, HP

    # Passenger info
    Passengers: int = 1
    Passenger_Details: Optional[str] = None  # JSON string

    # Payment
    Base_Fare: float = 0.0
    Tax: float = 0.0
    Convenience_Fee: float = 0.0
    Total_Fare: float = 0.0
    Payment_Status: str = 'Pending'  # Pending, Completed, Failed, Refunded
    Payment_Method: Optional[str] = None
    Transaction_ID: Optional[str] = None

    # Booking status
    Status: str = 'Pending'  # Pending, Confirmed, Waitlisted, RAC, Cancelled
    Waitlist_Number: Optional[int] = None
    RAC_Number: Optional[int] = None

    # Timestamps
    Booking_Date: Optional[str] = None
    Cancellation_Date: Optional[str] = None
    Refund_Amount: float = 0.0

    @classmethod
    def get_required_fields(cls) -> List[str]:
        return ['User_ID', 'Train_ID', 'Journey_Date', 'Class', 'Passengers']

    def is_confirmed(self) -> bool:
        """Check if booking is confirmed."""
        return self.Status == 'Confirmed'

    def can_cancel(self) -> bool:
        """Check if booking can be cancelled."""
        return self.Status in ['Pending', 'Confirmed', 'Waitlisted', 'RAC']

    def calculate_refund(self, cancellation_charge_percent: float = 10.0) -> float:
        """Calculate refund amount."""
        if not self.can_cancel():
            return 0.0
        charge = self.Total_Fare * (cancellation_charge_percent / 100)
        return round(self.Total_Fare - charge, 2)
