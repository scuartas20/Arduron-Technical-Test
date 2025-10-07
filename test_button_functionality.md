# Prueba de Funcionalidad del Botón del ESP32

## Cambios Implementados

### 1. Modificaciones en el ESP32 (`esp32_updated_handler.cpp`)

- **Función `handleSwitchInput()`**: Cambiada para enviar solicitudes de comando en lugar de cambiar el estado directamente.
- **Nueva función `sendCommandRequest()`**: Envía solicitudes de comando al backend vía WebSocket.
- **Función `handleWebSocketMessage()`**: Actualizada para manejar mensajes de comando denegado (`command_denied`).

### 2. Modificaciones en el Backend

#### Archivo: `main.py`
- **Endpoint WebSocket de dispositivos**: Agregado manejo para `button_command_request`.

#### Archivo: `services/access_control.py`
- **Nueva función `handle_button_command_request()`**: Procesa solicitudes de botón del ESP32.
- **Nueva función `_send_command_denied()`**: Envía mensajes de denegación al ESP32.
- **Lógica de validación**: Verifica si la puerta está bloqueada antes de procesar comandos de botón.

## Flujo de Funcionamiento

1. **Botón presionado en ESP32**:
   - ESP32 detecta presión del botón
   - Envía `button_command_request` al backend vía WebSocket
   - **NO cambia el estado localmente**

2. **Backend procesa la solicitud**:
   - Verifica que el dispositivo existe
   - Verifica que es un dispositivo físico
   - **Verifica si la puerta está bloqueada (`LOCKED`)**
   - Si está bloqueada: envía `command_denied` al ESP32
   - Si no está bloqueada: procesa el comando normalmente

3. **ESP32 recibe respuesta**:
   - Si recibe `command`: ejecuta el comando y cambia estado
   - Si recibe `command_denied`: registra la denegación y NO cambia estado

## Tipos de Mensajes WebSocket

### Del ESP32 al Backend:
```json
{
  "type": "button_command_request",
  "command": "open" | "close",
  "timestamp": "timestamp"
}
```

### Del Backend al ESP32:
```json
// Comando autorizado
{
  "type": "command",
  "command": "open" | "close",
  "timestamp": "timestamp"
}

// Comando denegado
{
  "type": "command_denied",
  "command": "open" | "close",
  "reason": "Door is locked",
  "timestamp": "timestamp"
}
```

## Escenarios de Prueba

### Escenario 1: Puerta desbloqueada
1. Configurar DOOR-001 con `lock_state: "unlocked"`
2. Presionar botón en ESP32
3. **Resultado esperado**: Backend procesa comando y envía `command` al ESP32

### Escenario 2: Puerta bloqueada
1. Configurar DOOR-001 con `lock_state: "locked"`
2. Presionar botón en ESP32
3. **Resultado esperado**: Backend envía `command_denied` al ESP32

### Escenario 3: Logging de eventos
- Ambos escenarios deben generar eventos en el log de acceso
- Los eventos deben mostrar `user_id: "physical_button"`
- Estado debe ser `GRANTED` o `DENIED` según corresponda

## Verificación

Para verificar que funciona correctamente:

1. **Logs del ESP32**: Mostrarán si recibe comandos o denegaciones
2. **Logs del Backend**: Mostrarán el procesamiento de solicitudes
3. **Frontend**: Mostrará eventos en tiempo real via WebSocket
4. **Estado de LEDs**: Solo cambian cuando el comando es autorizado

## Beneficios de esta Implementación

1. **Seguridad**: El botón físico respeta el estado de bloqueo
2. **Consistencia**: Mismo flujo de autorización que comandos remotos
3. **Auditoría**: Todos los intentos se registran en logs
4. **Feedback**: El ESP32 sabe si el comando fue denegado
5. **Tiempo real**: Los clientes reciben notificaciones inmediatas