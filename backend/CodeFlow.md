# 🏗️ Backend Code Flow - Access Control Manager

## 📋 Table of Contents
- [Architecture Overview](#architecture-overview)
- [Directory Structure](#directory-structure)
- [Core Components](#core-components)
- [Data Flow](#data-flow)
- [API Endpoints](#api-endpoints)
- [WebSocket Communication](#websocket-communication)
- [Function Interactions](#function-interactions)

---

## 🎯 Architecture Overview

The backend follows a **layered architecture** pattern with clear separation of concerns:

```
┌─────────────────┐
│   Presentation  │ ← FastAPI Routes & WebSocket Endpoints
├─────────────────┤
│   Controllers   │ ← Business Logic Orchestration
├─────────────────┤
│    Services     │ ← Core Business Logic & State Management
├─────────────────┤
│     Models      │ ← Data Models & Entities
├─────────────────┤
│  Configuration  │ ← Settings & Environment Variables
└─────────────────┘
```

---

## 📁 Directory Structure

```
backend/
├── src/
│   ├── main.py                 # 🚀 Application Entry Point
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py         # ⚙️ Configuration Management
│   ├── controllers/
│   │   ├── __init__.py
│   │   └── api_controllers.py  # 🎮 Request/Response Handlers
│   ├── models/
│   │   ├── __init__.py
│   │   ├── access_log.py       # 📝 Access Event Models
│   │   └── devices.py          # 🚪 Door/Device Models
│   ├── routes/
│   │   ├── __init__.py
│   │   └── api_routes.py       # 🛣️ HTTP Route Definitions
│   ├── services/
│   │   ├── __init__.py
│   │   ├── access_control.py   # 🔐 Business Logic Engine
│   │   └── app_state.py        # 🗄️ State Management Singleton
│   └── websocket/
│       ├── __init__.py
│       └── websocket_manager.py # 🔌 Real-time Communication
├── requirements.txt
└── .env                        # 🔑 Environment Variables
```

---

## 🧩 Core Components

### 1. **Application Entry Point** (`main.py`)

**Purpose**: Initializes and configures the FastAPI application

**Key Functions**:
- `app = FastAPI()` - Creates the FastAPI instance
- `app.add_middleware()` - Configures CORS for frontend communication
- `app.include_router()` - Registers API routes
- `@app.websocket()` - WebSocket endpoint handler
- `websocket_endpoint()` - Main WebSocket connection handler

**Dependencies**: 
- `config.settings` → Application configuration
- `routes.api_routes` → HTTP API routes
- `websocket.websocket_manager` → WebSocket handling

---

### 2. **Configuration Management** (`config/settings.py`)

**Purpose**: Centralized configuration using environment variables

**Key Features**:
- Environment variable loading with defaults
- Type conversion and validation
- Development/production settings separation

**Key Variables**:
```python
host: str = "0.0.0.0"
port: int = 5000
api_prefix: str = "/api"
ws_endpoint: str = "/ws"
admin_user_id: str = "admin"
allowed_origins_list: List[str]
```

---

### 3. **Data Models** (`models/`)

#### 3.1 **Access Log Models** (`access_log.py`)

**Core Classes**:
- `AccessStatus(Enum)` - GRANTED | DENIED
- `AccessCommand(Enum)` - OPEN | CLOSE | LOCK | UNLOCK  
- `AccessAttemptIn(BaseModel)` - Request payload
- `AccessEvent(BaseModel)` - Log entry with timestamp
- `AccessLogRegistry` - In-memory log storage

**Key Methods**:
```python
AccessEvent.to_dict() → Dict               # Serialization
AccessLogRegistry.add_log(event)           # Store event
AccessLogRegistry.get_logs(limit) → List   # Retrieve logs
```

#### 3.2 **Device Models** (`devices.py`)

**Core Classes**:
- `PhysicalStatus(Enum)` - OPEN | CLOSED
- `LockState(Enum)` - LOCKED | UNLOCKED
- `Door(BaseModel)` - Device representation
- `DoorRegistry` - In-memory device storage

**Key Methods**:
```python
Door.to_dict() → Dict                      # Serialization
DoorRegistry.register_door(door)           # Add device
DoorRegistry.update_door(id, **kwargs)     # Update state
```

---

### 4. **Business Logic Layer** (`services/`)

#### 4.1 **Access Control Service** (`access_control.py`)

**Purpose**: Core business logic for access control decisions

**Main Function**:
```python
@staticmethod
def process_access_attempt(device_id: str, user_id: str, command: AccessCommand) 
    → Tuple[AccessStatus, str, Optional[Door]]
```

**Business Rules Implementation**:
- `_process_open_command()` - Handle door opening logic
- `_process_close_command()` - Handle door closing logic  
- `_process_lock_command()` - Handle locking (admin only)
- `_process_unlock_command()` - Handle unlocking (admin only)

**Admin Authentication**:
```python
is_admin = user_id.lower() == settings.admin_user_id.lower()
```

**Helper Functions**:
```python
create_access_event() → AccessEvent        # Create log entry
```

#### 4.2 **Application State Manager** (`app_state.py`)

**Purpose**: Singleton state management for the entire application

**Singleton Pattern**:
```python
class AppStateManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
```

**State Components**:
- `door_registry: DoorRegistry` - All device states
- `access_log_registry: AccessLogRegistry` - All access events

**Key Methods**:
```python
# Device Management
get_all_doors() → List[Door]
get_door(door_id) → Optional[Door]
update_door_state(door_id, **kwargs) → Optional[Door]

# Log Management  
add_access_log(event: AccessEvent)
get_access_logs(limit) → List[AccessEvent]
get_device_access_logs(device_id, limit) → List[AccessEvent]
```

**Sample Data Initialization**:
- DOOR-001: Main Entrance (CLOSED, LOCKED)
- DOOR-002: Conference Room A (CLOSED, UNLOCKED)

---

### 5. **Controller Layer** (`controllers/api_controllers.py`)

**Purpose**: Orchestrates business logic and handles HTTP request/response lifecycle

#### 5.1 **DeviceController**

```python
@staticmethod
def get_device_status() → Dict[str, Any]
```
- Retrieves all device states
- Formats response with timestamp and count

#### 5.2 **AccessLogController**

```python
@staticmethod
def get_access_logs(limit: int = 100) → Dict[str, Any]
```
- Retrieves access history
- Formats paginated response

```python
@staticmethod  
async def handle_access_request(request: AccessAttemptIn) → Dict[str, Any]
```
- **Main orchestration function for access requests**
- Processes business logic via `AccessControlService`
- Creates and stores access events
- **Broadcasts WebSocket updates** (🔥 Critical for real-time updates)
- Formats HTTP response

**WebSocket Integration**:
```python
# Send real-time updates to all connected clients
await websocket_manager.broadcast_access_event(access_event.to_dict())

if updated_door:
    await websocket_manager.broadcast_device_state_change(
        request.device_id, updated_door.to_dict()
    )
```

---

### 6. **HTTP Routes** (`routes/api_routes.py`)

**Purpose**: Defines HTTP API endpoints and request validation

**Route Definitions**:
```python
api_router = APIRouter(prefix="/api", tags=["api"])

@api_router.get("/devices/status")          # Get all device states
@api_router.get("/access_logs")             # Get access history  
@api_router.post("/access_log")             # Simulate access attempt
```

**Request Handling Pattern**:
```python
async def endpoint_function(request_data):
    try:
        return await Controller.method(request_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

---

### 7. **WebSocket Manager** (`websocket/websocket_manager.py`)

**Purpose**: Real-time bidirectional communication with frontend clients

#### 7.1 **WebSocketManager Class**

**Connection Management**:
```python
async def connect(websocket: WebSocket)     # Accept new connection
def disconnect(websocket: WebSocket)        # Remove connection
active_connections: List[WebSocket]         # Active client list
```

**Broadcasting Functions**:
```python
async def broadcast(message: Dict[str, Any])
    # Send to all connected clients

async def broadcast_device_state_change(device_id: str, new_state: Dict)
    # Notify device state updates

async def broadcast_access_event(access_event: Dict)
    # Notify new access events
```

**Initial Data Sync**:
```python
async def send_initial_data(websocket: WebSocket)
    # Send current system state to new clients
```

#### 7.2 **Message Handling**

```python
async def handle_websocket_message(websocket: WebSocket, message: str)
```
- Parses incoming JSON messages
- Routes by message type (command, ping)
- Handles errors gracefully

```python
async def handle_command_message(websocket: WebSocket, data: Dict)
```
- Processes device commands from frontend
- **Reuses existing controller logic** to avoid duplication
- Sends command responses back to requesting client

**Message Types**:
- `command` - Device control requests
- `ping/pong` - Connection health checks
- `initial_data` - System state on connection
- `device_state_change` - Device updates
- `access_event` - New access logs
- `command_response` - Command results
- `error` - Error notifications

---

## 🔄 Data Flow

### 1. **HTTP API Request Flow**

```
Frontend HTTP Request
       ↓
FastAPI Route (api_routes.py)
       ↓
Controller Method (api_controllers.py)
       ↓
Business Logic (access_control.py)
       ↓
State Update (app_state.py)
       ↓
WebSocket Broadcast (websocket_manager.py)
       ↓
All Connected Clients
```

### 2. **WebSocket Command Flow**

```
Frontend WebSocket Command
       ↓
WebSocket Handler (websocket_manager.py)
       ↓
Controller Method (api_controllers.py)  # Reuses same logic
       ↓
Business Logic (access_control.py)
       ↓
State Update (app_state.py)
       ↓
WebSocket Broadcast (websocket_manager.py)
       ↓
All Connected Clients (including sender)
```

### 3. **State Management Flow**

```
Access Request
       ↓
AccessControlService.process_access_attempt()
  ├─ Validate device exists
  ├─ Check user permissions (admin/user)
  ├─ Apply business rules
  └─ Update device state if needed
       ↓
app_state.update_door_state() / add_access_log()
       ↓
WebSocket Broadcast to all clients
```

---

## 🛣️ API Endpoints

### **GET** `/api/devices/status`
- **Purpose**: Retrieve current state of all devices
- **Controller**: `DeviceController.get_device_status()`
- **Response**: Device list with states and metadata

### **GET** `/api/access_logs?limit=100`
- **Purpose**: Retrieve access history with pagination
- **Controller**: `AccessLogController.get_access_logs(limit)`
- **Response**: Chronological list of access events

### **POST** `/api/access_log`
- **Purpose**: Simulate access attempt (testing endpoint)
- **Payload**: `AccessAttemptIn` (device_id, user_card_id, command)
- **Controller**: `AccessLogController.handle_access_request()`
- **Side Effects**: 
  - Updates device state
  - Creates access log
  - Broadcasts WebSocket updates
- **Response**: Access result with updated state

---

## 🔌 WebSocket Communication

### **Connection Endpoint**: `/ws`

### **Message Types**:

#### **Incoming** (Frontend → Backend):
```json
{
  "type": "command",
  "device_id": "DOOR-001", 
  "command": "open",
  "user_id": "admin"
}

{
  "type": "ping"
}
```

#### **Outgoing** (Backend → Frontend):
```json
{
  "type": "initial_data",
  "data": {
    "devices": [...],
    "timestamp": "2025-10-06T15:30:00"
  }
}

{
  "type": "access_event",
  "data": {
    "timestamp": "2025-10-06T15:30:00",
    "device_id": "DOOR-001",
    "user_id": "admin", 
    "command": "open",
    "status": "granted",
    "message": "Door opened successfully"
  }
}

{
  "type": "device_state_change",
  "data": {
    "device_id": "DOOR-001",
    "new_state": {
      "door_id": "DOOR-001",
      "location": "Main Entrance",
      "physical_status": "open",
      "lock_state": "locked"
    },
    "timestamp": "2025-10-06T15:30:00"
  }
}
```

---

## 🔗 Function Interactions

### **Critical Interaction Pattern**:

```python
# 1. Entry Point (HTTP or WebSocket)
main.py → api_routes.py OR websocket_manager.py

# 2. Request Orchestration  
api_controllers.py:
  └─ handle_access_request(request)
      ├─ AccessControlService.process_access_attempt()
      ├─ AccessControlService.create_access_event()
      ├─ app_state.add_access_log()
      ├─ websocket_manager.broadcast_access_event()
      └─ websocket_manager.broadcast_device_state_change()

# 3. Business Logic
access_control.py:
  └─ process_access_attempt()
      ├─ app_state.get_door() 
      ├─ Check admin permissions
      ├─ Apply business rules (_process_*_command)
      └─ app_state.update_door_state()

# 4. State Management
app_state.py (Singleton):
  ├─ door_registry (Device states)
  └─ access_log_registry (Event history)
```

### **Key Dependencies**:

```
main.py
├─ config.settings
├─ routes.api_routes  
└─ websocket.websocket_manager

api_routes.py
└─ controllers.api_controllers

api_controllers.py  
├─ services.access_control
├─ services.app_state
└─ websocket.websocket_manager

access_control.py
├─ services.app_state
├─ models.devices
├─ models.access_log
└─ config.settings

websocket_manager.py
├─ services.app_state
├─ models.access_log
└─ controllers.api_controllers (for command handling)
```

---

## 🎯 Design Principles

### **1. Single Responsibility**
- Each module has a clear, focused purpose
- Controllers orchestrate, Services contain business logic
- Models define data structures only

### **2. Dependency Injection**
- Configuration injected via environment variables
- State management via singleton pattern
- Clear dependency hierarchy

### **3. Event-Driven Architecture**
- WebSocket broadcasts for real-time updates
- State changes trigger notifications
- Loose coupling between components

### **4. Error Handling**
- Graceful WebSocket connection management
- HTTP exception handling with proper status codes
- Comprehensive logging throughout

### **5. Scalability Considerations**
- In-memory storage (suitable for demo/small scale)
- Stateless business logic (easy to scale horizontally)
- WebSocket manager handles multiple connections efficiently

---

## 🔧 Configuration & Environment

### **Environment Variables** (`.env`):
```bash
# Server Configuration
HOST=0.0.0.0
PORT=5000
DEBUG=True

# CORS Configuration  
FRONTEND_URL=http://localhost:3000
ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# WebSocket Configuration
WS_ENDPOINT=/ws

# API Configuration
API_PREFIX=/api

# Security Configuration
ADMIN_USER_ID=admin
```

### **Dependencies** (`requirements.txt`):
- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `pydantic` - Data validation
- `python-dotenv` - Environment variable loading

---

This documentation provides a comprehensive overview of the backend architecture, making it easy for developers to understand the codebase structure and how different components interact to provide a robust access control system with real-time capabilities.