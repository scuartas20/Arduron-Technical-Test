"""
Controllers for handling API requests.
"""
from typing import List, Dict, Any
from datetime import datetime
from fastapi import HTTPException

from services.app_state import app_state
from services.access_control import AccessControlService
from models.access_log import AccessAttemptIn


class DeviceController:
    """Controller for device-related operations."""
    
    @staticmethod
    def get_device_status() -> Dict[str, Any]:
        """Get the status of all devices."""
        doors = app_state.get_all_doors()
        return {
            "devices": [door.to_dict() for door in doors],
            "timestamp": datetime.now().isoformat(),
            "total_count": len(doors)
        }


class AccessLogController:
    """Controller for access log operations."""
    
    @staticmethod
    def get_access_logs(limit: int = 100) -> Dict[str, Any]:
        """Get access logs."""
        logs = app_state.get_access_logs(limit)
        return {
            "logs": [log.to_dict() for log in logs],
            "timestamp": datetime.now().isoformat(),
            "total_count": len(logs)
        }
    
    @staticmethod
    async def process_access_attempt(request: AccessAttemptIn) -> Dict[str, Any]:
        """Process an access attempt from a simulated device."""
        # Process the access attempt
        status, message, updated_door = AccessControlService.process_access_attempt(
            device_id=request.device_id,
            user_id=request.user_card_id,
            command=request.command
        )
        
        # Create and log the access event
        access_event = AccessControlService.create_access_event(
            device_id=request.device_id,
            user_id=request.user_card_id,
            command=request.command,
            status=status,
            message=message
        )
        
        app_state.add_access_log(access_event)
        
        # Prepare response
        response = {
            "access_granted": status.value == "granted",
            "message": message,
            "timestamp": access_event.timestamp.isoformat(),
            "device_id": request.device_id,
            "user_id": request.user_card_id,
            "command": request.command.value,
            "status": status.value
        }
        
        # If the door state was updated, include the new state
        if updated_door:
            response["updated_device_state"] = updated_door.to_dict()
        
        return response