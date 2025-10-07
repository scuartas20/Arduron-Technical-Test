# Refactoring: Migración de print() a logging

## Problema Identificado

El código utilizaba `print()` para mensajes de debug y estado en lugar del sistema de logging configurado, lo cual es una mala práctica en aplicaciones de producción.

## Cambios Realizados

### ✅ WebSocketManager (`websocket_manager.py`):

#### Antes:
```python
print(f"Device {device_id} reconnected, replacing old connection")
print(f"Device {device_id} connected via WebSocket")
print(f"Device {device_id} disconnected")
print(f"Cannot send command '{command}' to device {device_id}: Device not connected")
print(f"Command '{command}' sent successfully to device {device_id}")
print(f"Failed to send command '{command}' to device {device_id}: {e}")
```

#### Después:
```python
logger.info(f"Device {device_id} reconnected, replacing old connection")
logger.info(f"Device {device_id} connected via WebSocket")
logger.info(f"Device {device_id} disconnected")
logger.warning(f"Cannot send command '{command}' to device {device_id}: Device not connected")
logger.info(f"Command '{command}' sent successfully to device {device_id}")
logger.error(f"Failed to send command '{command}' to device {device_id}: {e}")
```

### ✅ Main (`main.py`):

#### Antes:
```python
print(f"WebSocket error: {e}")
```

#### Después:
```python
logger.error(f"WebSocket error: {e}")
```

## Beneficios del Refactoring

### 🎯 **Niveles de Log Apropiados:**
- **`logger.info()`**: Para eventos normales (conexiones, comandos exitosos)
- **`logger.warning()`**: Para situaciones que requieren atención (dispositivo no conectado)
- **`logger.error()`**: Para errores reales (fallos de comunicación, excepciones)

### 📊 **Ventajas sobre print():**

1. **Control de Niveles**: Se puede configurar qué niveles mostrar
2. **Formateo Consistente**: Timestamps, niveles, módulos automáticos
3. **Múltiples Destinos**: Consola, archivos, servicios externos
4. **Filtrado**: Posibilidad de filtrar por módulo o nivel
5. **Producción Ready**: Configuración centralizada

### 🔧 **Configuración del Logger:**

```python
import logging

# Configuración básica
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)
```

### 📝 **Ejemplo de Output:**

#### Con print():
```
Device DOOR-001 connected via WebSocket
Command 'open' sent successfully to device DOOR-001
```

#### Con logger:
```
2025-10-07 15:30:45,123 - websocket.websocket_manager - INFO - Device DOOR-001 connected via WebSocket
2025-10-07 15:30:47,456 - websocket.websocket_manager - INFO - Command 'open' sent successfully to device DOOR-001
```

## Consistencia con el Resto del Código

Ahora `WebSocketManager` es consistente con otros módulos que ya usan logging:
- ✅ `AccessControlService` usa `logger`
- ✅ `WebSocketManager` usa `logger`
- ✅ `main.py` usa `logger`

## Beneficios en Producción

1. **Debugging**: Más información contextual
2. **Monitoring**: Integración con sistemas de monitoreo
3. **Troubleshooting**: Logs persistentes y buscables
4. **Performance**: No bloquea la consola en producción
5. **Configuración**: Control granular por ambiente (dev/prod)

## Archivos Modificados

- ✅ `backend/src/websocket/websocket_manager.py`
- ✅ `backend/src/main.py`

## Verificación

- ✅ No hay errores de sintaxis
- ✅ Todos los `print()` reemplazados por `logger`
- ✅ Niveles de log apropiados asignados
- ✅ Import de logging agregado