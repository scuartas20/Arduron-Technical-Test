"""
API routes for the Access Control Manager.
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any
from datetime import datetime

from controllers.api_controllers import DeviceController, AccessLogController, RateLimiterController
from models.access_log import AccessAttemptIn
from websocket.websocket_manager import websocket_manager

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
        return await AccessLogController.handle_access_request(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@api_router.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy", "service": "Access Control Manager API"}


@api_router.get("/security/rate_limiter/stats")
async def get_rate_limiter_stats() -> Dict[str, Any]:
    """
    Get rate limiter statistics and monitoring data.
    
    Returns:
        Dict containing rate limiter statistics including attempt counts,
        success/failure rates, and configuration details
    """
    try:
        return RateLimiterController.get_rate_limiter_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@api_router.get("/security/rate_limiter/user_status")
async def get_user_rate_limit_status(
    device_id: str = Query(..., description="Device ID to check"),
    user_id: str = Query(..., description="User ID to check")
) -> Dict[str, Any]:
    """
    Get rate limit status for a specific user/device combination.
    
    Args:
        device_id: ID of the device to check
        user_id: ID of the user to check
        
    Returns:
        Dict containing user-specific rate limit status including lockout info
    """
    try:
        return RateLimiterController.get_user_rate_limit_status(device_id, user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@api_router.delete("/security/rate_limiter/clear")
async def clear_rate_limiter(
    user_id: str = Query(..., description="User ID requesting the operation")
) -> Dict[str, Any]:
    """
    Clear all rate limiter data (admin function).
    
    This endpoint clears all stored rate limiting attempts.
    Only admin users are authorized to perform this operation.
    
    Args:
        user_id: ID of the user requesting the operation (must be 'admin')
        
    Returns:
        Dict containing confirmation and count of cleared data
    """
    try:
        # Simple admin check
        if user_id.lower() != "admin":
            raise HTTPException(
                status_code=403, 
                detail="Access denied. Only admin users can clear rate limiter data."
            )
        
        return RateLimiterController.clear_rate_limiter()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@api_router.get("/devices/connections")
async def get_device_connections() -> Dict[str, Any]:
    """
    Get current WebSocket connection status for all devices.
    
    Returns:
        Dict containing connection information for all devices including
        connection status, last ping time, and response times
    """
    try:
        return {
            "connected_devices": websocket_manager.get_connected_devices(),
            "total_connected": len(websocket_manager.device_connections),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@api_router.get("/devices/{device_id}/connection")
async def get_device_connection_status(device_id: str) -> Dict[str, Any]:
    """
    Get WebSocket connection status for a specific device.
    
    Args:
        device_id: ID of the device to check
        
    Returns:
        Dict containing connection status and timing information for the device
    """
    try:
        is_connected = websocket_manager.is_device_connected(device_id)
        connected_devices = websocket_manager.get_connected_devices()
        device_info = connected_devices.get(device_id, {"connected": False})
        
        return {
            "device_id": device_id,
            "connected": is_connected,
            "connection_info": device_info,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")