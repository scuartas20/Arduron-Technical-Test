"""
Access control service - Business logic for processing access attempts.
"""
from datetime import datetime
from typing import Tuple, Optional
import logging
import json

from models.devices import Door, PhysicalStatus, LockState, DeviceType
from models.access_log import AccessEvent, AccessStatus, AccessCommand
from services.app_state import app_state
from config.settings import settings

logger = logging.getLogger(__name__)


class AccessControlService:
    """Service for processing access control logic."""
    
    @staticmethod
    async def process_access_attempt(device_id: str, user_id: str, command: AccessCommand) -> Tuple[AccessStatus, str, Optional[Door]]:
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
            status, message, updated_door = await AccessControlService._process_open_command(door, is_admin)
        elif command == AccessCommand.CLOSE:
            status, message, updated_door = await AccessControlService._process_close_command(door, is_admin)
        elif command == AccessCommand.LOCK:
            status, message, updated_door = await AccessControlService._process_lock_command(door, is_admin)
        elif command == AccessCommand.UNLOCK:
            status, message, updated_door = await AccessControlService._process_unlock_command(door, is_admin)
        else:
            return AccessStatus.DENIED, f"Unknown command: {command}", None
        
        return status, message, updated_door
    
    @staticmethod
    async def _process_open_command(door: Door, is_admin: bool) -> Tuple[AccessStatus, str, Optional[Door]]:
        """Process an OPEN command."""
        # Check if door is locked
        if door.lock_state == LockState.LOCKED and not is_admin:
            return AccessStatus.DENIED, "Door is locked and user is not admin", None
        
        # Check if door is already open
        if door.physical_status == PhysicalStatus.OPEN:
            return AccessStatus.GRANTED, "Door was already open", door
        
        # Comportamiento diferente según tipo de dispositivo
        if door.device_type == DeviceType.PHYSICAL:
            # Para dispositivos físicos: solo enviar comando, NO actualizar estado aún
            from websocket.websocket_manager import websocket_manager
            command_sent = await websocket_manager.send_command_to_device(door.door_id, "open")
            
            if command_sent:
                logger.info(f"Open command sent to physical device {door.door_id}")
                # El estado se actualizará cuando el ESP32 responda
                return AccessStatus.GRANTED, "Open command sent to device", None
            else:
                logger.warning(f"Failed to send open command to device {door.door_id} - device not connected")
                return AccessStatus.DENIED, "Device not connected", None
        else:
            # Para dispositivos virtuales: actualizar estado inmediatamente
            updated_door = app_state.update_door_state(
                door.door_id, 
                physical_status=PhysicalStatus.OPEN
            )
            return AccessStatus.GRANTED, "Door opened successfully", updated_door
    
    @staticmethod
    async def _process_close_command(door: Door, is_admin: bool) -> Tuple[AccessStatus, str, Optional[Door]]:
        """Process a CLOSE command."""
        # Check if door is already closed
        if door.physical_status == PhysicalStatus.CLOSED:
            return AccessStatus.GRANTED, "Door was already closed", door
        
        # Comportamiento diferente según tipo de dispositivo
        if door.device_type == DeviceType.PHYSICAL:
            # Para dispositivos físicos: solo enviar comando, NO actualizar estado aún
            from websocket.websocket_manager import websocket_manager
            command_sent = await websocket_manager.send_command_to_device(door.door_id, "close")
            
            if command_sent:
                logger.info(f"Close command sent to physical device {door.door_id}")
                # El estado se actualizará cuando el ESP32 responda
                return AccessStatus.GRANTED, "Close command sent to device", None
            else:
                logger.warning(f"Failed to send close command to device {door.door_id} - device not connected")
                return AccessStatus.DENIED, "Device not connected", None
        else:
            # Para dispositivos virtuales: actualizar estado inmediatamente
            updated_door = app_state.update_door_state(
                door.door_id,
                physical_status=PhysicalStatus.CLOSED
            )
            return AccessStatus.GRANTED, "Door closed successfully", updated_door
    
    @staticmethod
    async def _process_lock_command(door: Door, is_admin: bool) -> Tuple[AccessStatus, str, Optional[Door]]:
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
    async def _process_unlock_command(door: Door, is_admin: bool) -> Tuple[AccessStatus, str, Optional[Door]]:
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
    async def handle_device_status_update(device_id: str, status_data: dict):
        """Procesar actualización de estado desde un dispositivo físico."""
        try:
            # Obtener la puerta
            door = app_state.get_door(device_id)
            if not door:
                logger.warning(f"Status update received for unknown device: {device_id}")
                return
            
            # Verificar que sea un dispositivo físico
            if door.device_type != DeviceType.PHYSICAL:
                logger.warning(f"Status update received for non-physical device: {device_id}")
                return
            
            # Extraer el nuevo estado físico
            new_physical_status = status_data.get("physical_status")
            if new_physical_status and new_physical_status in ["open", "closed"]:
                # Convertir a enum
                physical_status = PhysicalStatus.OPEN if new_physical_status == "open" else PhysicalStatus.CLOSED
                
                # Actualizar el estado en el sistema
                updated_door = app_state.update_door_state(
                    device_id,
                    physical_status=physical_status
                )
                
                if updated_door:
                    logger.info(f"Status updated for {device_id}: {new_physical_status}")
                    
                    # Crear evento de log para el cambio manual
                    access_event = AccessControlService.create_access_event(
                        device_id=device_id,
                        user_id="device",  # Indica que fue el dispositivo físico
                        command=AccessCommand.OPEN if physical_status == PhysicalStatus.OPEN else AccessCommand.CLOSE,
                        status=AccessStatus.GRANTED,
                        message=f"Door {new_physical_status} physically"
                    )
                    
                    # Agregar al log
                    app_state.add_access_log(access_event)
                    
                    # Notificar a todos los clientes conectados
                    from websocket.websocket_manager import websocket_manager
                    await websocket_manager.broadcast_device_state_change(
                        device_id, updated_door.to_dict()
                    )
                    await websocket_manager.broadcast_access_event(access_event.to_dict())
                    
        except Exception as e:
            logger.error(f"Error procesando actualización de estado para {device_id}: {str(e)}")
    
    @staticmethod
    async def handle_button_command_request(device_id: str, command: str, device_websocket):
        """Manejar solicitud de comando desde botón físico del ESP32."""
        try:
            # Obtener la puerta
            door = app_state.get_door(device_id)
            if not door:
                logger.warning(f"Button command request from unknown device: {device_id}")
                await AccessControlService._send_command_denied(
                    device_websocket, command, "Device not found"
                )
                return
            
            # Verificar que sea un dispositivo físico
            if door.device_type != DeviceType.PHYSICAL:
                logger.warning(f"Button command request from non-physical device: {device_id}")
                await AccessControlService._send_command_denied(
                    device_websocket, command, "Device is not physical"
                )
                return
            
            # Convertir comando a enum
            try:
                access_command = AccessCommand(command.lower())
            except ValueError:
                logger.error(f"Invalid command from button: {command}")
                await AccessControlService._send_command_denied(
                    device_websocket, command, "Invalid command"
                )
                return
            
            # Verificar si la puerta está bloqueada
            if door.lock_state == LockState.LOCKED:
                logger.info(f"Button command '{command}' denied for {device_id}: Door is locked")
                await AccessControlService._send_command_denied(
                    device_websocket, command, "Door is locked"
                )
                
                # Crear evento de log para el intento denegado
                access_event = AccessControlService.create_access_event(
                    device_id=device_id,
                    user_id="physical_button",
                    command=access_command,
                    status=AccessStatus.DENIED,
                    message="Button command denied - Door is locked"
                )
                
                app_state.add_access_log(access_event)
                
                # Notificar a clientes conectados sobre el intento denegado
                from websocket.websocket_manager import websocket_manager
                await websocket_manager.broadcast_access_event(access_event.to_dict())
                return
            
            # Si la puerta no está bloqueada, procesar el comando normalmente
            status, message, updated_door = await AccessControlService.process_access_attempt(
                device_id=device_id,
                user_id="physical_button",
                command=access_command
            )
            
            # Crear evento de log
            access_event = AccessControlService.create_access_event(
                device_id=device_id,
                user_id="physical_button",
                command=access_command,
                status=status,
                message=message
            )
            
            app_state.add_access_log(access_event)
            
            # Notificar a todos los clientes conectados
            from websocket.websocket_manager import websocket_manager
            await websocket_manager.broadcast_access_event(access_event.to_dict())
            
            if updated_door:
                await websocket_manager.broadcast_device_state_change(
                    device_id, updated_door.to_dict()
                )
            
            logger.info(f"Button command '{command}' processed for {device_id}: {status.value} - {message}")
            
        except Exception as e:
            logger.error(f"Error processing button command request from {device_id}: {str(e)}")
            await AccessControlService._send_command_denied(
                device_websocket, command, f"Internal error: {str(e)}"
            )
    
    @staticmethod
    async def _send_command_denied(websocket, command: str, reason: str):
        """Enviar mensaje de comando denegado al dispositivo."""
        try:
            denial_message = {
                "type": "command_denied",
                "command": command,
                "reason": reason,
                "timestamp": datetime.now().isoformat()
            }
            
            await websocket.send_text(json.dumps(denial_message))
            logger.info(f"Command denial sent: {command} - {reason}")
            
        except Exception as e:
            logger.error(f"Error sending command denial: {str(e)}")
    
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