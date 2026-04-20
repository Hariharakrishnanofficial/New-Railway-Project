"""
Train Model

Entity schema for Trains table.
"""

from dataclasses import dataclass
from typing import List, Optional
from models.base_model import BaseModel


@dataclass
class Train(BaseModel):
    """Train entity model."""

    __tablename__ = 'Trains'

    # Core fields
    Train_Number: Optional[str] = None
    Train_Name: Optional[str] = None
    Train_Type: Optional[str] = None  # Express, Superfast, Rajdhani, Shatabdi, Local

    # Capacity fields
    Total_Seats: int = 0
    AC_First_Class: int = 0
    AC_2_Tier: int = 0
    AC_3_Tier: int = 0
    Sleeper: int = 0
    General: int = 0

    # Schedule fields
    Source_Station_ID: Optional[str] = None
    Destination_Station_ID: Optional[str] = None
    Departure_Time: Optional[str] = None
    Arrival_Time: Optional[str] = None
    Duration_Minutes: int = 0
    Running_Days: Optional[str] = None  # "Mon,Tue,Wed,Thu,Fri,Sat,Sun"

    # Status
    Is_Active: bool = True

    @classmethod
    def get_required_fields(cls) -> List[str]:
        return ['Train_Number', 'Train_Name', 'Train_Type']

    def get_total_capacity(self) -> int:
        """Calculate total seat capacity."""
        return (self.AC_First_Class + self.AC_2_Tier +
                self.AC_3_Tier + self.Sleeper + self.General)
