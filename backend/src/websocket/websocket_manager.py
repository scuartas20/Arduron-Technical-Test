"""
WebSocket server for real-time communication.
"""
import json
import asyncio
import logging
from typing import Dict, Any
from fastapi import WebSocket, WebSocketDisconnect
from datetime import datetime

from services.app_state import app_state
from services.access_control import AccessControlService
from models.access_log import AccessCommand

logger = logging.getLogger(__name__)


class WebSocketManager:
    """
    Manages WebSocket connections and message broadcasting.
    
    This class encapsulates all WebSocket-related functionality including:
    - Connection management for both frontend clients and physical devices
    - Message handling and routing
    - Broadcasting updates to connected clients
    - Command processing and validation
    """
    
    def __init__(self):
        self.active_connections: list[WebSocket] = []
        # Device connections (ESP32, etc.)
        self.device_connections: Dict[str, WebSocket] = {}
    
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
    
    async def connect_device(self, websocket: WebSocket, device_id: str):
        """Accept a connection from a device like ESP32."""
        await websocket.accept()
        
        # If device was already connected, replace the old connection
        if device_id in self.device_connections:
            logger.info(f"Device {device_id} reconnected, replacing old connection")
        
        # Store the new connection
        self.device_connections[device_id] = websocket
        logger.info(f"Device {device_id} connected via WebSocket")
    
    def disconnect_device(self, websocket: WebSocket, device_id: str):
        """Remove a device WebSocket connection."""
        if device_id in self.device_connections and self.device_connections[device_id] == websocket:
            del self.device_connections[device_id]
            logger.info(f"Device {device_id} disconnected")
    
    async def send_command_to_device(self, device_id: str, command: str) -> bool:
        """Send a command to a specific device (ESP32)."""
        if device_id not in self.device_connections:
            logger.warning(f"Cannot send command '{command}' to device {device_id}: Device not connected")
            return False
        
        device_ws = self.device_connections[device_id]
        command_message = {
            "type": "command",
            "command": command.lower(),
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            await device_ws.send_text(json.dumps(command_message))
            logger.info(f"Command '{command}' sent successfully to device {device_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to send command '{command}' to device {device_id}: {e}")
            # Remove disconnected device
            self.disconnect_device(device_ws, device_id)
            return False
    
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
    
    async def handle_websocket_message(self, websocket: WebSocket, message: str):
        """Handle incoming WebSocket messages (commands from frontend)."""
        try:
            data = json.loads(message)
            message_type = data.get("type")
            
            if message_type == "command":
                await self.handle_command_message(websocket, data)
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

    async def handle_command_message(self, websocket: WebSocket, data: Dict[str, Any]):
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


# Global WebSocket manager instance
websocket_manager = WebSocketManager()