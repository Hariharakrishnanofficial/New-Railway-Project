"""
Station Model

Entity schema for Stations table.
"""

from dataclasses import dataclass
from typing import List, Optional
from models.base_model import BaseModel


@dataclass
class Station(BaseModel):
    """Station entity model."""

    __tablename__ = 'Stations'

    # Core fields
    Station_Code: Optional[str] = None  # e.g., "NDLS", "MAS", "HWH"
    Station_Name: Optional[str] = None
    Station_Type: Optional[str] = None  # Junction, Terminal, Halt

    # Location fields
    City: Optional[str] = None
    State: Optional[str] = None
    Zone: Optional[str] = None  # NR, SR, ER, WR, CR, etc.
    Division: Optional[str] = None
    Latitude: Optional[float] = None
    Longitude: Optional[float] = None
    Address: Optional[str] = None
    Pincode: Optional[str] = None

    # Facilities
    Platforms: int = 1
    Has_WiFi: bool = False
    Has_Parking: bool = False
    Has_Waiting_Room: bool = True
    Has_Restaurant: bool = False

    # Status
    Is_Active: bool = True

    @classmethod
    def get_required_fields(cls) -> List[str]:
        return ['Station_Code', 'Station_Name', 'City', 'State']
