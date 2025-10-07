# FastAPI application entry point
import uvicorn
import json
import logging
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Path
from fastapi.middleware.cors import CORSMiddleware

from config.settings import settings
from routes.api_routes import api_router
from websocket.websocket_manager import websocket_manager, handle_websocket_message

logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.api_title,
    description=settings.api_description,
    version=settings.api_version
)

# Configure CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix=settings.api_prefix)

@app.get("/")
async def root():
    return {
        "message": settings.api_title,
        "version": settings.api_version,
        "environment": settings.environment,
        "endpoints": {
            "api": settings.api_prefix,
            "websocket": settings.ws_endpoint,
            "device_websocket": "/ws/{device_id}",
            "health": f"{settings.api_prefix}/health",
            "docs": "/docs"
        }
    }

@app.websocket(settings.ws_endpoint)
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time communication."""
    await websocket_manager.connect(websocket)
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            # Handle the message
            await handle_websocket_message(websocket, data)
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        websocket_manager.disconnect(websocket)

@app.websocket("/ws/{device_id}")
async def device_websocket_endpoint(
    websocket: WebSocket, 
    device_id: str = Path(..., description="The unique ID of the device")
):
    """WebSocket endpoint for device communication (ESP32)."""
    # Connect the device with its ID
    await websocket_manager.connect_device(websocket, device_id)
    
    try:
        while True:
            # Receive message from device
            data = await websocket.receive_text()
            
            # Parse JSON message from device
            try:
                message = json.loads(data)
                message_type = message.get("type")
                
                if message_type == "status_update":
                    # Handle device status updates (manual changes)
                    from services.access_control import AccessControlService
                    await AccessControlService.handle_device_status_update(
                        device_id, message.get("data", {})
                    )
                    
                    # Send acknowledgment to device
                    await websocket.send_text(json.dumps({
                        "type": "ack",
                        "message": "Status update received"
                    }))
                    
                elif message_type == "command_response":
                    # Handle response to commands sent from server
                    logger.info(f"Device {device_id} responded: {message}")
                    
                else:
                    logger.warning(f"Unknown message type from device {device_id}: {message_type}")
                    
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON received from device {device_id}: {data}")
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "Invalid JSON format"
                }))
                
    except WebSocketDisconnect:
        websocket_manager.disconnect_device(websocket, device_id)
    except Exception as e:
        logger.error(f"Device WebSocket error ({device_id}): {e}")
        websocket_manager.disconnect_device(websocket, device_id)

if __name__ == "__main__":
    uvicorn.run(
        "main:app", 
        host=settings.host, 
        port=settings.port, 
        reload=settings.reload
    )