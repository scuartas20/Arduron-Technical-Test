"""
WebSocket server for real-time communication.
"""
import json
import asyncio
import logging
from typing import Dict, Any
from fastapi import WebSocket
from datetime import datetime

from services.app_state import app_state
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
        # Track last ping time for each device
        self.device_last_ping: Dict[str, datetime] = {}
        # Heartbeat task (will be started when first device connects)
        self._heartbeat_task = None
        self._heartbeat_started = False
    
    def _start_heartbeat(self):
        """Start the heartbeat task to monitor device connections."""
        if not self._heartbeat_started and (self._heartbeat_task is None or self._heartbeat_task.done()):
            try:
                self._heartbeat_task = asyncio.create_task(self._heartbeat_monitor())
                self._heartbeat_started = True
                logger.info("Heartbeat monitor started")
            except RuntimeError:
                # No event loop running yet, will be started when first device connects
                logger.debug("Event loop not running, heartbeat will start when needed")
    
    async def _heartbeat_monitor(self):
        """Monitor device connections and send periodic pings."""
        while True:
            try:
                await asyncio.sleep(10)  # Check every 10 seconds
                await self._check_device_connections()
            except Exception as e:
                logger.error(f"Error in heartbeat monitor: {e}")
                await asyncio.sleep(10)
    
    async def _check_device_connections(self):
        """Check if devices are still connected by sending pings."""
        current_time = datetime.now()
        disconnected_devices = []
        
        for device_id, websocket in self.device_connections.items():
            try:
                # Send ping to device
                ping_message = {
                    "type": "ping",
                    "timestamp": current_time.isoformat()
                }
                await websocket.send_text(json.dumps(ping_message))
                logger.debug(f"Ping sent to device {device_id}")
                
                # Check if device responded to previous pings
                last_ping = self.device_last_ping.get(device_id)
                if last_ping and (current_time - last_ping).total_seconds() > 30:
                    # Device hasn't responded in 30 seconds, consider it disconnected
                    logger.warning(f"Device {device_id} hasn't responded to ping in 30 seconds")
                    disconnected_devices.append(device_id)
                
            except Exception as e:
                logger.warning(f"Failed to ping device {device_id}: {e}")
                disconnected_devices.append(device_id)
        
        # Disconnect unresponsive devices
        for device_id in disconnected_devices:
            websocket = self.device_connections.get(device_id)
            if websocket:
                await self._force_disconnect_device(device_id, "Ping timeout")
    
    async def _force_disconnect_device(self, device_id: str, reason: str):
        """Force disconnect a device and update its status."""
        logger.info(f"Force disconnecting device {device_id}: {reason}")
        
        # Remove from connections
        websocket = self.device_connections.pop(device_id, None)
        self.device_last_ping.pop(device_id, None)
        
        # Update device status to offline
        from models.devices import ConnectionStatus
        app_state.update_door_state(device_id, connection_status=ConnectionStatus.OFFLINE)
        
        # Broadcast status change
        door = app_state.get_door(device_id)
        if door:
            await self.broadcast_device_state_change(device_id, door.to_dict())
    
    def _update_device_ping(self, device_id: str):
        """Update the last ping time for a device."""
        self.device_last_ping[device_id] = datetime.now()
    
    def get_connected_devices(self) -> Dict[str, Any]:
        """Get information about currently connected devices."""
        connected_devices = {}
        current_time = datetime.now()
        
        for device_id, websocket in self.device_connections.items():
            last_ping = self.device_last_ping.get(device_id)
            connected_devices[device_id] = {
                "connected": True,
                "last_ping": last_ping.isoformat() if last_ping else None,
                "seconds_since_ping": (current_time - last_ping).total_seconds() if last_ping else None
            }
        
        return connected_devices
    
    def is_device_connected(self, device_id: str) -> bool:
        """Check if a specific device is currently connected."""
        return device_id in self.device_connections
    
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
        
        # Start heartbeat monitor if not already started
        if not self._heartbeat_started:
            self._start_heartbeat()
        
        # If device was already connected, replace the old connection
        if device_id in self.device_connections:
            logger.info(f"Device {device_id} reconnected, replacing old connection")
        
        # Store the new connection
        self.device_connections[device_id] = websocket
        self.device_last_ping[device_id] = datetime.now()
        
        # Update device status to online
        from models.devices import ConnectionStatus
        app_state.update_door_state(device_id, connection_status=ConnectionStatus.ONLINE)
        
        logger.info(f"Device {device_id} connected via WebSocket")
        
        # Broadcast status change
        door = app_state.get_door(device_id)
        if door:
            await self.broadcast_device_state_change(device_id, door.to_dict())
    
    def disconnect_device(self, websocket: WebSocket, device_id: str):
        """Remove a device WebSocket connection."""
        if device_id in self.device_connections and self.device_connections[device_id] == websocket:
            del self.device_connections[device_id]
            self.device_last_ping.pop(device_id, None)
            
            # Update device status to offline
            from models.devices import ConnectionStatus
            app_state.update_door_state(device_id, connection_status=ConnectionStatus.OFFLINE)
            
            logger.info(f"Device {device_id} disconnected")
            
            # Broadcast status change asynchronously
            asyncio.create_task(self._broadcast_disconnect(device_id))
    
    async def _broadcast_disconnect(self, device_id: str):
        """Broadcast device disconnection asynchronously."""
        door = app_state.get_door(device_id)
        if door:
            await self.broadcast_device_state_change(device_id, door.to_dict())
    
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