"""
Fare Model

Entity schema for Fares table.
"""

from dataclasses import dataclass
from typing import List, Optional
from models.base_model import BaseModel


@dataclass
class Fare(BaseModel):
    """Fare entity model."""

    __tablename__ = 'Fares'

    # Reference fields
    Train_ID: Optional[str] = None
    Route_ID: Optional[str] = None
    Source_Station_ID: Optional[str] = None
    Destination_Station_ID: Optional[str] = None

    # Class type
    Class: Optional[str] = None  # SL, 3A, 2A, 1A, CC, EC, GN

    # Fare components
    Base_Fare: float = 0.0
    Reservation_Charge: float = 0.0
    Superfast_Charge: float = 0.0
    Fuel_Surcharge: float = 0.0
    Catering_Charge: float = 0.0
    GST: float = 0.0
    Total_Fare: float = 0.0

    # Distance-based
    Distance_KM: float = 0.0
    Rate_Per_KM: float = 0.0

    # Validity
    Effective_From: Optional[str] = None
    Effective_To: Optional[str] = None
    Is_Active: bool = True

    @classmethod
    def get_required_fields(cls) -> List[str]:
        return ['Train_ID', 'Class', 'Base_Fare']

    def calculate_total(self) -> float:
        """Calculate total fare from components."""
        total = (self.Base_Fare + self.Reservation_Charge +
                 self.Superfast_Charge + self.Fuel_Surcharge +
                 self.Catering_Charge + self.GST)
        return round(total, 2)
