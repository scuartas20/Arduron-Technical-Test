"""
WebSocket server for real-time communication.
"""
import json
import asyncio
from typing import Dict, Any
from fastapi import WebSocket, WebSocketDisconnect
from datetime import datetime

from services.app_state import app_state
from services.access_control import AccessControlService
from models.access_log import AccessCommand


class WebSocketManager:
    """Manages WebSocket connections and message broadcasting."""
    
    def __init__(self):
        self.active_connections: list[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        """Accept a new WebSocket connection."""
        await websocket.accept()
        self.active_connections.append(websocket)
        
        # Send initial data to the new connection
        await self.send_initial_data(websocket)
    
    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        """Send a message to a specific WebSocket connection."""
        try:
            await websocket.send_text(message)
        except Exception:
            # Connection might be closed
            self.disconnect(websocket)
    
    async def broadcast(self, message: Dict[str, Any]):
        """Broadcast a message to all connected clients."""
        if not self.active_connections:
            return
        
        message_str = json.dumps(message)
        disconnected = []
        
        for connection in self.active_connections:
            try:
                await connection.send_text(message_str)
            except Exception:
                # Connection is closed, mark for removal
                disconnected.append(connection)
        
        # Remove disconnected connections
        for connection in disconnected:
            self.disconnect(connection)
    
    async def send_initial_data(self, websocket: WebSocket):
        """Send initial data to a newly connected client."""
        # Send current device states
        doors = app_state.get_all_doors()
        initial_data = {
            "type": "initial_data",
            "data": {
                "devices": [door.to_dict() for door in doors],
                "timestamp": datetime.now().isoformat()
            }
        }
        await self.send_personal_message(json.dumps(initial_data), websocket)
    
    async def broadcast_device_state_change(self, device_id: str, new_state: Dict[str, Any]):
        """Broadcast a device state change to all clients."""
        message = {
            "type": "device_state_change",
            "data": {
                "device_id": device_id,
                "new_state": new_state,
                "timestamp": datetime.now().isoformat()
            }
        }
        await self.broadcast(message)
    
    async def broadcast_access_event(self, access_event: Dict[str, Any]):
        """Broadcast a new access event to all clients."""
        message = {
            "type": "access_event",
            "data": access_event
        }
        await self.broadcast(message)


# Global WebSocket manager instance
websocket_manager = WebSocketManager()


async def handle_websocket_message(websocket: WebSocket, message: str):
    """Handle incoming WebSocket messages (commands from frontend)."""
    try:
        data = json.loads(message)
        message_type = data.get("type")
        
        if message_type == "command":
            await handle_command_message(websocket, data)
        elif message_type == "ping":
            await websocket.send_text(json.dumps({"type": "pong", "timestamp": datetime.now().isoformat()}))
        else:
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": f"Unknown message type: {message_type}"
            }))
            
    except json.JSONDecodeError:
        await websocket.send_text(json.dumps({
            "type": "error",
            "message": "Invalid JSON format"
        }))
    except Exception as e:
        await websocket.send_text(json.dumps({
            "type": "error",
            "message": f"Error processing message: {str(e)}"
        }))


async def handle_command_message(websocket: WebSocket, data: Dict[str, Any]):
    """Handle command messages from the frontend."""
    try:
        device_id = data.get("device_id")
        command = data.get("command")
        user_id = data.get("user_id", "admin")  # Default to admin for frontend commands
        
        if not device_id or not command:
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": "Missing device_id or command"
            }))
            return
        
        # Convert command string to AccessCommand enum
        try:
            access_command = AccessCommand(command.lower())
        except ValueError:
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": f"Invalid command: {command}"
            }))
            return
        
        # Create AccessAttemptIn object to use the existing controller logic
        from models.access_log import AccessAttemptIn
        from controllers.api_controllers import AccessLogController
        
        request = AccessAttemptIn(
            device_id=device_id,
            user_card_id=user_id,
            command=access_command
        )
        
        # Use the existing controller method (which already handles WebSocket broadcasts)
        result = await AccessLogController.handle_access_request(request)
        
        # Send response back to the requesting client
        response = {
            "type": "command_response",
            "data": {
                "device_id": device_id,
                "command": command,
                "status": result["status"],
                "message": result["message"],
                "timestamp": result["timestamp"],
                "access_granted": result["access_granted"]
            }
        }
        
        await websocket.send_text(json.dumps(response))
        
    except Exception as e:
        await websocket.send_text(json.dumps({
            "type": "error",
            "message": f"Error processing command: {str(e)}"
        }))