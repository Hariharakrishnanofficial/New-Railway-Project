"""
Announcement Model

Entity schema for Announcements table.
"""

from dataclasses import dataclass
from typing import List, Optional
from models.base_model import BaseModel


@dataclass
class Announcement(BaseModel):
    """Announcement entity model."""

    __tablename__ = 'Announcements'

    # Content
    Title: Optional[str] = None
    Message: Optional[str] = None
    Type: str = 'info'  # info, warning, alert, maintenance

    # Targeting
    Target_Audience: str = 'all'  # all, passengers, operators, admins
    Station_ID: Optional[str] = None  # If station-specific
    Train_ID: Optional[str] = None  # If train-specific
    Route_ID: Optional[str] = None  # If route-specific

    # Display settings
    Priority: int = 5  # 1-10, higher = more important
    Display_From: Optional[str] = None
    Display_Until: Optional[str] = None
    Show_On_Homepage: bool = False
    Show_On_Booking: bool = False

    # Status
    Is_Active: bool = True
    Created_By: Optional[str] = None

    @classmethod
    def get_required_fields(cls) -> List[str]:
        return ['Title', 'Message', 'Type']
