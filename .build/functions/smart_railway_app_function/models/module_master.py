"""
Module Master Model

Entity schema for Module_Master table.
"""

from dataclasses import dataclass
from typing import List, Optional
from models.base_model import BaseModel


@dataclass
class ModuleMaster(BaseModel):
    """Module Master entity model."""

    __tablename__ = 'Module_Master'

    # Core fields
    Module_Code: Optional[str] = None  # e.g., "USR", "TRN", "BKG"
    Module_Name: Optional[str] = None
    Description: Optional[str] = None

    # Hierarchy
    Parent_Module_ID: Optional[str] = None
    Display_Order: int = 0

    # Access control
    Is_Active: bool = True
    Requires_Auth: bool = True
    Min_Role_Level: int = 0  # 0=all, 1=user, 2=operator, 3=admin

    # UI settings
    Icon: Optional[str] = None
    Route_Path: Optional[str] = None
    Show_In_Menu: bool = True

    @classmethod
    def get_required_fields(cls) -> List[str]:
        return ['Module_Code', 'Module_Name']
