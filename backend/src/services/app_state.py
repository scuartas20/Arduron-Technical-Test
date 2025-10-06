"""
Application state manager - Single source of truth for all system state.
"""
from typing import Dict, List, Optional
from datetime import datetime

from models.devices import Door, DoorRegistry, PhysicalStatus, LockState
from models.access_log import AccessEvent, AccessLogRegistry, AccessStatus, AccessCommand


class AppStateManager:
    """Singleton service that manages all application state."""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AppStateManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self.door_registry = DoorRegistry()
        self.access_log_registry = AccessLogRegistry()
        self._initialized = True
        
        # Initialize with sample doors
        self._initialize_sample_data()
    
    def _initialize_sample_data(self):
        """Initialize the system with sample doors."""
        door1 = Door(
            door_id="DOOR-001",
            location="Main Entrance",
            physical_status=PhysicalStatus.CLOSED,
            lock_state=LockState.LOCKED
        )
        
        door2 = Door(
            door_id="DOOR-002", 
            location="Conference Room A",
            physical_status=PhysicalStatus.CLOSED,
            lock_state=LockState.UNLOCKED
        )
        
        self.door_registry.register_door(door1)
        self.door_registry.register_door(door2)
    
    # Door management methods
    def get_all_doors(self) -> List[Door]:
        """Get all registered doors."""
        return self.door_registry.get_all_doors()
    
    def get_door(self, door_id: str) -> Optional[Door]:
        """Get a specific door by ID."""
        return self.door_registry.get_door(door_id)
    
    def update_door_state(self, door_id: str, **kwargs) -> Optional[Door]:
        """Update door state and return the updated door."""
        return self.door_registry.update_door(door_id, **kwargs)
    
    # Access log methods
    def add_access_log(self, event: AccessEvent) -> None:
        """Add a new access event to the log."""
        self.access_log_registry.add_log(event)
    
    def get_access_logs(self, limit: int = 100) -> List[AccessEvent]:
        """Get recent access logs."""
        return self.access_log_registry.get_logs(limit)
    
    def get_device_access_logs(self, device_id: str, limit: int = 50) -> List[AccessEvent]:
        """Get access logs for a specific device."""
        return self.access_log_registry.get_logs_by_device(device_id, limit)
    
    # Utility methods
    def reset_state(self):
        """Reset all state (useful for testing)."""
        self.door_registry = DoorRegistry()
        self.access_log_registry = AccessLogRegistry()
        self._initialize_sample_data()


# Global singleton instance
app_state = AppStateManager()