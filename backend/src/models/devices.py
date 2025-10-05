"""
Door models for the Access Control System.
"""
from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel


class PhysicalStatus(str, Enum):
    OPEN = "open"
    CLOSED = "closed"


class LockState(str, Enum):
    LOCKED = "locked"
    UNLOCKED = "unlocked"


class Door(BaseModel):
    door_id: str
    location: str
    physical_status: PhysicalStatus = PhysicalStatus.CLOSED
    lock_state: LockState = LockState.LOCKED

    def to_dict(self) -> Dict:
        return {
            "door_id": self.door_id,
            "location": self.location,
            "physical_status": self.physical_status,
            "lock_state": self.lock_state
        }


class DoorRegistry:
    """In-memory registry of all doors in the system."""
    
    def __init__(self):
        self.doors: Dict[str, Door] = {}
    
    def register_door(self, door: Door) -> None:
        self.doors[door.door_id] = door
    
    def get_door(self, door_id: str) -> Optional[Door]:
        return self.doors.get(door_id)
    
    def get_all_doors(self) -> List[Door]:
        return list(self.doors.values())
    
    def update_door(self, door_id: str, **kwargs) -> Optional[Door]:
        if door_id in self.doors:
            for key, value in kwargs.items():
                setattr(self.doors[door_id], key, value)
            return self.doors[door_id]
        return None