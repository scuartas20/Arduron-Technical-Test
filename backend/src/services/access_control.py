"""
Access control service - Business logic for processing access attempts.
"""
from datetime import datetime
from typing import Tuple, Optional

from models.devices import Door, PhysicalStatus, LockState
from models.access_log import AccessEvent, AccessStatus, AccessCommand
from services.app_state import app_state
from config.settings import settings


class AccessControlService:
    """Service for processing access control logic."""
    
    @staticmethod
    def process_access_attempt(device_id: str, user_id: str, command: AccessCommand) -> Tuple[AccessStatus, str, Optional[Door]]:
        """
        Process an access attempt and return the result.
        
        Args:
            device_id: ID of the device/door
            user_id: ID of the user making the attempt
            command: The command being attempted
            
        Returns:
            Tuple of (access_status, message, updated_door)
        """
        # Get the door
        door = app_state.get_door(device_id)
        if not door:
            return AccessStatus.DENIED, f"Device {device_id} not found", None
        
        # Check if user is admin (simplified authentication)
        is_admin = user_id.lower() == settings.admin_user_id.lower()
        
        # Process different commands
        if command == AccessCommand.OPEN:
            return AccessControlService._process_open_command(door, is_admin)
        elif command == AccessCommand.CLOSE:
            return AccessControlService._process_close_command(door, is_admin)
        elif command == AccessCommand.LOCK:
            return AccessControlService._process_lock_command(door, is_admin)
        elif command == AccessCommand.UNLOCK:
            return AccessControlService._process_unlock_command(door, is_admin)
        else:
            return AccessStatus.DENIED, f"Unknown command: {command}", None
    
    @staticmethod
    def _process_open_command(door: Door, is_admin: bool) -> Tuple[AccessStatus, str, Optional[Door]]:
        """Process an OPEN command."""
        # Check if door is locked
        if door.lock_state == LockState.LOCKED and not is_admin:
            return AccessStatus.DENIED, "Door is locked and user is not admin", None
        
        # Check if door is already open
        if door.physical_status == PhysicalStatus.OPEN:
            return AccessStatus.GRANTED, "Door was already open", door
        
        # Open the door
        updated_door = app_state.update_door_state(
            door.door_id, 
            physical_status=PhysicalStatus.OPEN
        )
        
        return AccessStatus.GRANTED, "Door opened successfully", updated_door
    
    @staticmethod
    def _process_close_command(door: Door, is_admin: bool) -> Tuple[AccessStatus, str, Optional[Door]]:
        """Process a CLOSE command."""
        # Check if door is already closed
        if door.physical_status == PhysicalStatus.CLOSED:
            return AccessStatus.GRANTED, "Door was already closed", door
        
        # Close the door
        updated_door = app_state.update_door_state(
            door.door_id,
            physical_status=PhysicalStatus.CLOSED
        )
        
        return AccessStatus.GRANTED, "Door closed successfully", updated_door
    
    @staticmethod
    def _process_lock_command(door: Door, is_admin: bool) -> Tuple[AccessStatus, str, Optional[Door]]:
        """Process a LOCK command."""
        # Only admins can lock doors
        if not is_admin:
            return AccessStatus.DENIED, "Only admin users can lock doors", None
        
        # Check if door is already locked
        if door.lock_state == LockState.LOCKED:
            return AccessStatus.GRANTED, "Door was already locked", door
        
        # Lock the door
        updated_door = app_state.update_door_state(
            door.door_id,
            lock_state=LockState.LOCKED
        )
        
        return AccessStatus.GRANTED, "Door locked successfully", updated_door
    
    @staticmethod
    def _process_unlock_command(door: Door, is_admin: bool) -> Tuple[AccessStatus, str, Optional[Door]]:
        """Process an UNLOCK command."""
        # Only admins can unlock doors
        if not is_admin:
            return AccessStatus.DENIED, "Only admin users can unlock doors", None
        
        # Check if door is already unlocked
        if door.lock_state == LockState.UNLOCKED:
            return AccessStatus.GRANTED, "Door was already unlocked", door
        
        # Unlock the door
        updated_door = app_state.update_door_state(
            door.door_id,
            lock_state=LockState.UNLOCKED
        )
        
        return AccessStatus.GRANTED, "Door unlocked successfully", updated_door
    
    @staticmethod
    def create_access_event(device_id: str, user_id: str, command: AccessCommand, 
                          status: AccessStatus, message: str) -> AccessEvent:
        """Create an access event."""
        return AccessEvent(
            timestamp=datetime.now(),
            device_id=device_id,
            user_id=user_id,
            command=command,
            status=status,
            message=message
        )