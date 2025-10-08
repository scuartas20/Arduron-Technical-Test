# Access Control Manager - Code Flow Documentation

## Table of Contents
1. [Project Architecture Overview](#project-architecture-overview)
2. [Application Startup Flow](#application-startup-flow)
3. [Data Models and State Management](#data-models-and-state-management)
4. [WebSocket Communication Flows](#websocket-communication-flows)
5. [HTTP API Request Flows](#http-api-request-flows)
6. [Physical Device Integration Flow](#physical-device-integration-flow)
7. [Rate Limiting and Security Flow](#rate-limiting-and-security-flow)
8. [File Dependencies and Interactions](#file-dependencies-and-interactions)
9. [Critical Code Paths](#critical-code-paths)

---

## Project Architecture Overview

The Access Control Manager is a full-stack real-time application that manages smart door devices through a centralized backend system. The architecture follows a **layered design pattern** with clear separation of concerns:

### Core Components:
- **FastAPI Application** (`main.py`) - Entry point and server configuration
- **State Manager** (`app_state.py`) - Single source of truth for all system data
- **WebSocket Manager** (`websocket_manager.py`) - Real-time bidirectional communication
- **Access Control Service** (`access_control.py`) - Business logic and authorization
- **Rate Limiter** (`rate_limiter.py`) - Security and abuse prevention
- **Controllers** (`api_controllers.py`) - Request handling and response formatting
- **Models** (`devices.py`, `access_log.py`) - Data structures and validation

---

## Application Startup Flow

### 1. Server Initialization (`main.py`)
```python
# 1. Configuration Loading
settings = Settings()  # Loads from environment variables or defaults

# 2. FastAPI App Creation
app = FastAPI(title=settings.api_title, ...)

# 3. CORS Middleware Setup
app.add_middleware(CORSMiddleware, allow_origins=settings.allowed_origins_list, ...)

# 4. API Routes Registration
app.include_router(api_router, prefix="/api")

# 5. WebSocket Endpoints Registration
@app.websocket("/ws")           # Frontend dashboard connections
@app.websocket("/ws/{device_id}") # ESP32/Physical device connections
```

### 2. State Initialization (`app_state.py`)
```python
# Singleton pattern ensures single source of truth
class AppStateManager:
    def __init__(self):
        self.door_registry = DoorRegistry()      # Manages all doors
        self.access_log_registry = AccessLogRegistry()  # Stores all events
        self._initialize_sample_data()           # Creates DOOR-001 and DOOR-002
```

### 3. Sample Data Creation
- **DOOR-001**: Main Entrance (Physical device with ESP32, Locked)
- **DOOR-002**: Conference Room A (Virtual device, Unlocked)

---

## Data Models and State Management

### Device Models (`models/devices.py`)

#### Door Entity Structure:
```python
class Door(BaseModel):
    door_id: str                    # Unique identifier (e.g., "DOOR-001")
    location: str                   # Human-readable location
    physical_status: PhysicalStatus # OPEN or CLOSED
    lock_state: LockState          # LOCKED or UNLOCKED
    device_type: DeviceType        # PHYSICAL (ESP32) or VIRTUAL
```

#### Key Distinctions:
- **Physical Devices**: Have real ESP32 hardware, state changes require device confirmation
- **Virtual Devices**: Software-only, state changes are immediate

### Access Log Models (`models/access_log.py`)

#### Access Event Structure:
```python
class AccessEvent(BaseModel):
    timestamp: datetime
    device_id: str
    user_id: str               # "admin", "physical_button", or card ID
    command: AccessCommand     # OPEN, CLOSE, LOCK, UNLOCK
    status: AccessStatus       # GRANTED or DENIED
    message: str              # Detailed reason/result
```

### State Management Pattern (`services/app_state.py`)

The `AppStateManager` uses the **Singleton pattern** to ensure a single source of truth:

```python
# All components access the same instance
app_state = AppStateManager()

# State operations are centralized
door = app_state.get_door("DOOR-001")
app_state.update_door_state(door_id, physical_status=PhysicalStatus.OPEN)
app_state.add_access_log(access_event)
```

---

## WebSocket Communication Flows

### Frontend Dashboard Connection Flow

#### 1. Client Connection (`/ws` endpoint)
```
1. Client connects to ws://localhost:5000/ws
2. websocket_manager.connect(websocket) called
3. Connection added to active_connections list
4. send_initial_data() sends current state of all doors
5. Client receives: {"type": "initial_data", "data": {"devices": [...]}}
```

#### 2. Frontend Command Processing
```
Frontend sends:
{
  "type": "command",
  "device_id": "DOOR-001",
  "command": "open",
  "user_id": "admin"
}

Backend Flow:
1. handle_websocket_message() parses JSON
2. handle_command_message() validates command
3. AccessLogController.handle_access_request() processes
4. AccessControlService.process_access_attempt() applies logic
5. Rate limiting check performed
6. Command result broadcasted to all clients
7. Device state change broadcasted if successful
```

### ESP32 Device Connection Flow

#### 1. Device Connection (`/ws/{device_id}` endpoint)
```
1. ESP32 connects to ws://localhost:5000/ws/DOOR-001
2. websocket_manager.connect_device(websocket, "DOOR-001")
3. Device stored in device_connections["DOOR-001"]
4. Ready to receive commands and send status updates
```

#### 2. Physical Button Request Flow
```
ESP32 sends:
{
  "type": "button_command_request",
  "command": "open",
  "timestamp": "2025-10-08T10:30:00Z"
}

Backend Processing:
1. Device message received at /ws/{device_id}
2. JSON parsed and type identified as "button_command_request"
3. AccessControlService.handle_button_command_request() called
4. Door lock state checked (CRITICAL SECURITY CHECK)
5. If locked: command_denied message sent to ESP32
6. If unlocked: Regular access attempt processing
7. Access event logged regardless of outcome
8. All clients notified via WebSocket broadcast
```

#### 3. Device Status Update Flow
```
ESP32 sends:
{
  "type": "status_update",
  "data": {"physical_status": "open"},
  "timestamp": "2025-10-08T10:30:05Z"
}

Backend Processing:
1. handle_device_status_update() called
2. Physical device verification performed
3. app_state.update_door_state() updates system state
4. broadcast_device_state_change() notifies all clients
5. ESP32 receives acknowledgment
```

---

## HTTP API Request Flows

### Device Status Request (`GET /api/devices/status`)
```
Request: GET /api/devices/status

Flow:
1. api_routes.get_devices_status() receives request
2. DeviceController.get_device_status() called
3. app_state.get_all_doors() retrieves all doors
4. Response formatted with timestamp and count
5. JSON returned to client

Response:
{
  "devices": [
    {
      "door_id": "DOOR-001",
      "location": "Main Entrance",
      "physical_status": "closed",
      "lock_state": "locked",
      "device_type": "physical"
    }
  ],
  "timestamp": "2025-10-08T10:30:00Z",
  "total_count": 2
}
```

### Access Log Request (`POST /api/access_log`)
```
Request Body:
{
  "device_id": "DOOR-001",
  "user_card_id": "USER123",
  "command": "open"
}

Flow:
1. api_routes.create_access_log() receives request
2. AccessLogController.handle_access_request() processes
3. AccessControlService.process_access_attempt() applies business logic
4. Rate limiting checked first
5. Door state validated
6. Access event created and logged
7. WebSocket broadcasts sent to all clients
8. Response with result returned

Critical: This endpoint triggers WebSocket broadcasts!
```

---

## Physical Device Integration Flow

### ESP32 Command Authorization Flow

The system implements **smart button control** where physical buttons cannot override security settings:

#### 1. Button Press Detection
```cpp
// ESP32 Code (simplified)
if (digitalRead(BUTTON_PIN) == HIGH && !lastButtonState) {
  // Don't change LED immediately - ask permission first
  sendButtonRequest("open");  // or "close"
}
```

#### 2. Backend Authorization Process
```python
# In AccessControlService.handle_button_command_request()

# STEP 1: Verify device exists and is physical
door = app_state.get_door(device_id)
if door.device_type != DeviceType.PHYSICAL:
    return DENIED

# STEP 2: Check rate limiting (prevent button spam)
is_allowed, message = rate_limiter.check_rate_limit(device_id, "physical_button", command)
if not is_allowed:
    return DENIED

# STEP 3: CRITICAL SECURITY CHECK - Respect lock state
if door.lock_state == LockState.LOCKED:
    send_command_denied(websocket, command, "Door is locked")
    log_denied_attempt()
    return

# STEP 4: If unlocked, process normally
process_access_attempt(device_id, "physical_button", command)
```

#### 3. ESP32 Response Handling
```
Backend sends one of:

AUTHORIZED:
{
  "type": "command",
  "command": "open",
  "timestamp": "..."
}

DENIED:
{
  "type": "command_denied",
  "command": "open",
  "reason": "Door is locked",
  "timestamp": "..."
}
```

### Virtual vs Physical Device Behavior

#### Virtual Devices (DOOR-002):
```python
# Immediate state change
updated_door = app_state.update_door_state(
    door.door_id, 
    physical_status=PhysicalStatus.OPEN
)
return AccessStatus.GRANTED, "Door opened successfully", updated_door
```

#### Physical Devices (DOOR-001):
```python
# Send command to ESP32, wait for confirmation
command_sent = await websocket_manager.send_command_to_device(door.door_id, "open")
if command_sent:
    # State will be updated when ESP32 confirms via status_update
    return AccessStatus.GRANTED, "Open command sent to device", None
else:
    return AccessStatus.DENIED, "Device not connected", None
```

---

## Rate Limiting and Security Flow

### Rate Limiting Strategy (`services/rate_limiter.py`)

The system implements **multi-layered rate limiting**:

#### 1. General Rate Limiting
- **20 attempts per minute** per user/device combination
- Prevents command spam from any source

#### 2. Failed Attempt Protection
- **5 failed attempts** triggers lockout
- **1 minute lockout** after reaching threshold
- Prevents brute force attacks

#### 3. Rate Limit Check Process
```python
def check_rate_limit(device_id, user_id, command):
    # Check for lockout due to failed attempts
    recent_failed = get_recent_failed_attempts(device_id, user_id)
    if len(recent_failed) >= max_failed_attempts:
        return False, "Locked out due to failed attempts"
    
    # Check general rate limiting
    recent_attempts = get_recent_attempts(device_id, user_id)
    if len(recent_attempts) >= max_attempts_per_minute:
        return False, "Rate limit exceeded"
    
    return True, "Allowed"
```

### Security Integration Points

#### 1. Every Access Attempt
```python
# Rate limiting is checked BEFORE any other processing
is_allowed, message = rate_limiter.check_rate_limit(device_id, user_id, command)
if not is_allowed:
    rate_limiter.record_attempt(device_id, user_id, command, False)
    return AccessStatus.DENIED, f"Rate Limited: {message}", None
```

#### 2. Physical Button Protection
```python
# Physical buttons respect the same rate limits
# This prevents button spam attacks
is_allowed, message = rate_limiter.check_rate_limit(device_id, "physical_button", command)
```

#### 3. Lock State Enforcement
```python
# Physical buttons cannot override locked doors
if door.lock_state == LockState.LOCKED:
    # Log the attempt but deny the command
    log_denied_access_event(device_id, "physical_button", command, "Door is locked")
    return DENIED
```

---

## File Dependencies and Interactions

### Dependency Graph
```
main.py
├── config/settings.py (configuration)
├── routes/api_routes.py (HTTP endpoints)
│   └── controllers/api_controllers.py (request handling)
│       ├── services/app_state.py (state management)
│       ├── services/access_control.py (business logic)
│       └── services/rate_limiter.py (security)
├── websocket/websocket_manager.py (real-time communication)
│   ├── services/app_state.py
│   ├── services/access_control.py
│   └── models/access_log.py (data structures)
└── models/
    ├── devices.py (door models)
    └── access_log.py (event models)
```

### Key Interactions

#### 1. WebSocket ↔ Access Control
```python
# WebSocket receives command, delegates to access control
await AccessControlService.process_access_attempt(device_id, user_id, command)

# Access control sends commands to devices via WebSocket
await websocket_manager.send_command_to_device(device_id, command)
```

#### 2. Controllers ↔ State Management
```python
# Controllers read state through app_state
doors = app_state.get_all_doors()

# Controllers modify state through app_state
app_state.add_access_log(access_event)
updated_door = app_state.update_door_state(door_id, **kwargs)
```

#### 3. Access Control ↔ Rate Limiting
```python
# Access control checks rate limits before processing
is_allowed, message = rate_limiter.check_rate_limit(device_id, user_id, command)

# Access control records attempts for rate limiting
rate_limiter.record_attempt(device_id, user_id, command, success)
```

---

## Critical Code Paths

### 1. Dashboard Command Execution
```
User clicks "Open Door" in frontend
    ↓
WebSocket message sent to backend
    ↓
websocket_manager.handle_websocket_message()
    ↓
handle_command_message() validates input
    ↓
AccessLogController.handle_access_request()
    ↓
AccessControlService.process_access_attempt()
    ↓
Rate limiting check performed
    ↓
Business logic applied (lock state, admin privileges)
    ↓
For Physical Device: Command sent to ESP32
For Virtual Device: State updated immediately
    ↓
Access event logged in app_state
    ↓
WebSocket broadcasts sent:
  - access_event to all clients
  - device_state_change if state changed
    ↓
Frontend receives updates and refreshes UI
```

### 2. ESP32 Button Press Flow
```
Physical button pressed on ESP32
    ↓
ESP32 sends button_command_request via WebSocket
    ↓
device_websocket_endpoint receives message
    ↓
AccessControlService.handle_button_command_request()
    ↓
Device validation (must be physical device)
    ↓
Rate limiting check (prevent button spam)
    ↓
CRITICAL: Lock state check
  - If locked: Send command_denied to ESP32
  - If unlocked: Continue processing
    ↓
Normal access attempt processing
    ↓
Access event logged (regardless of outcome)
    ↓
WebSocket broadcasts to all clients
    ↓
ESP32 receives authorized command or denial
    ↓
ESP32 updates LED states only if authorized
```

### 3. State Synchronization Flow
```
ESP32 physically changes state (manual operation)
    ↓
ESP32 sends status_update message
    ↓
AccessControlService.handle_device_status_update()
    ↓
Verify device is physical type
    ↓
app_state.update_door_state() updates system state
    ↓
websocket_manager.broadcast_device_state_change()
    ↓
All connected clients receive state update
    ↓
Frontend UI updates to show current state
```

### 4. HTTP API Access Log Creation
```
External system sends POST /api/access_log
    ↓
api_routes.create_access_log() receives request
    ↓
AccessLogController.handle_access_request()
    ↓
Same processing as WebSocket commands
    ↓
AccessControlService.process_access_attempt()
    ↓
Rate limiting, business logic applied
    ↓
WebSocket broadcasts sent (real-time updates!)
    ↓
HTTP response returned to caller
```

---

## Key Design Principles

### 1. Single Source of Truth
- All state managed by `AppStateManager` singleton
- No duplicate state storage across components
- Consistent data across all interfaces

### 2. Security-First Design
- Rate limiting on all access attempts
- Physical buttons respect lock state
- Complete audit trail of all attempts
- Clear separation of admin vs user privileges

### 3. Real-Time Communication
- WebSocket broadcasts for all state changes
- Immediate UI updates across all clients
- Device commands sent in real-time

### 4. Separation of Concerns
- Models: Data structure and validation
- Services: Business logic and state management
- Controllers: Request handling and formatting
- Routes: HTTP endpoint definitions
- WebSocket Manager: Real-time communication

### 5. Extensibility
- Easy to add new device types
- Configurable rate limiting parameters
- Pluggable authentication system
- Support for both physical and virtual devices

This architecture ensures a robust, secure, and scalable access control system that can handle both physical ESP32 devices and virtual door simulations while maintaining complete audit trails and real-time communication capabilities.