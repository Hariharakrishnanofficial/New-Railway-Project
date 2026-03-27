"""
Route Model

Entity schema for Routes table.
"""

from dataclasses import dataclass
from typing import List, Optional
from models.base_model import BaseModel


@dataclass
class Route(BaseModel):
    """Route entity model."""

    __tablename__ = 'Routes'

    # Reference fields
    Train_ID: Optional[str] = None
    Station_ID: Optional[str] = None

    # Route details
    Route_Name: Optional[str] = None
    Sequence_Number: int = 0  # Order of station in route
    Distance_From_Origin: float = 0.0  # km

    # Timing
    Arrival_Time: Optional[str] = None
    Departure_Time: Optional[str] = None
    Halt_Duration: int = 0  # minutes
    Day_Number: int = 1  # Day 1, 2, etc. for multi-day journeys

    # Platform
    Platform_Number: Optional[str] = None

    # Status
    Is_Active: bool = True

    @classmethod
    def get_required_fields(cls) -> List[str]:
        return ['Train_ID', 'Station_ID', 'Sequence_Number']
