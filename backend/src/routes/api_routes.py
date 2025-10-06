"""
API routes for the Access Control Manager.
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any

from controllers.api_controllers import DeviceController, AccessLogController
from models.access_log import AccessAttemptIn

# Create router
api_router = APIRouter(tags=["api"])


@api_router.get("/devices/status")
async def get_devices_status() -> Dict[str, Any]:
    """
    Get the current status of all registered devices.
    
    Returns:
        Dict containing list of devices with their current state
    """
    try:
        return DeviceController.get_device_status()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@api_router.get("/access_logs")
async def get_access_logs(
    limit: int = Query(default=100, ge=1, le=1000, description="Maximum number of logs to return")
) -> Dict[str, Any]:
    """
    Get access logs from the system.
    
    Args:
        limit: Maximum number of logs to return (default: 100, max: 1000)
        
    Returns:
        Dict containing list of access logs
    """
    try:
        return AccessLogController.get_access_logs(limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@api_router.post("/access_log")
async def create_access_log(request: AccessAttemptIn) -> Dict[str, Any]:
    """
    Simulate a device sending an access attempt.
    
    This endpoint simulates a device (like an ESP32) sending an access attempt
    to open or close a door. The server will:
    1. Log the attempt (in memory)
    2. Apply access control logic
    3. Update device state if access is granted
    4. Broadcast changes via WebSocket (when implemented)
    
    Args:
        request: Access attempt details including device_id, user_card_id, and command
        
    Returns:
        Dict containing the result of the access attempt
    """
    try:
        return await AccessLogController.process_access_attempt(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@api_router.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy", "service": "Access Control Manager API"}