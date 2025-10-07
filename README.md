# Access Control Manager & Real-time Dashboard

## Project Overview

This project is a robust web application that simulates a real-time Access Control System (ACS) manager. It demonstrates the implementation of a WebSocket server to manage the state and status of virtual IoT devices (simulated smart doors), an HTTP server to register access logs, and a dynamic frontend for commanding and monitoring these devices.

The Access Control Logic is implemented on the backend, where the server serves as the single source of truth for device status.

## 🆕 NEW: ESP32 Physical Button Integration

### Enhanced Physical Device Control

The system now includes sophisticated integration with ESP32 devices, featuring **smart button control** that respects the access control system:

#### How Physical Button Works:
1. **Button Press Detection**: When the physical button on the ESP32 is pressed, it doesn't immediately change the door state
2. **Request Authorization**: Instead, it sends a `button_command_request` to the backend via WebSocket
3. **Access Control Validation**: The backend checks if the door is locked before authorizing the action
4. **Authorized Response**: If unlocked, the backend sends a `command` message to execute the action
5. **Denied Response**: If locked, the backend sends a `command_denied` message with the reason
6. **Smart Feedback**: The ESP32 only changes LED states when the command is authorized

#### Security Benefits:
- 🔒 **Respects Lock State**: Physical button cannot override locked doors
- 📊 **Complete Audit Trail**: All button presses are logged regardless of outcome
- 🔄 **Consistent Logic**: Same authorization flow as remote commands
- ⚡ **Real-time Updates**: All clients receive notifications instantly
- 🚫 **No Hanging States**: ESP32 receives immediate feedback on denied requests

## Core Features

### Frontend (The Dashboard)

1. **Device Status View**: A simple interface displaying current information for at least two simulated "Smart Door" devices, showing:
   - Device ID (e.g., DOOR-001) and Location
   - Current Physical Status (Open / Closed)
   - Current Lock State (Locked / Unlocked)

2. **Command Interface**: Basic controls for each device to:
   - Open Door / Close Door
   - Lock Device / Unlock Device

3. **Real-time Event Log**: A scrolling display of incoming access log events (door openings, closings, failed access attempts)

4. **WebSocket Client**: Establishes a persistent connection to the WebSocket server for bi-directional communication

### ESP32 Integration

The project includes complete ESP32 code (`esp32_updated_handler.cpp`) that demonstrates:

1. **WebSocket Communication**: Persistent connection to the backend
2. **Physical Controls**: Button input with debouncing
3. **LED Feedback**: Red/Green LEDs indicating door state
4. **Smart Button Logic**: Authorization-based physical control
5. **Status Synchronization**: Real-time state updates

#### Physical Device Features:
- **GPIO 14**: Physical button input (with pull-down resistor)
- **GPIO 16**: Red LED (door closed)
- **GPIO 17**: Green LED (door open)
- **WiFi Connectivity**: Connects to local network
- **WebSocket Client**: Maintains persistent connection to backend

### Backend (The Servers)

1. **Access Control State Manager**: Maintains the current, authoritative state of simulated devices (Physical Status and Lock State) in memory

2. **WebSocket Server (Bi-directional)**:
   - Status Broadcast: Pushes real-time status updates to all connected clients
   - Command Listener: Receives control commands from the frontend and executes access control logic
   - **Device Communication**: Dedicated endpoints for ESP32 devices (`/ws/{device_id}`)
   - **Button Request Handling**: Processes physical button authorization requests

3. **HTTP Server (Audit & Management Endpoints)**:
   - `GET /api/devices/status`: Endpoint to fetch the initial list and current state of all registered devices
   - `GET /api/access_logs`: Endpoint to retrieve the stored access history/log
   - `POST /api/access_log`: Simulates a device sending an access attempt to open or close a door

## Technology Stack

| Area | Technology Used |
|------|-----------------|
| Frontend | React with Vite, JavaScript, CSS |
| Backend | Python with FastAPI, WebSockets |
| Hardware | ESP32 with Arduino IDE |
| Communication | WebSocket (real-time), REST API |
| Data Source | In-memory state management |

## 🚀 Getting Started

### Backend Setup
```bash
cd backend
pip install -r requirements.txt
python src/main.py
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

### ESP32 Setup
1. Install Arduino IDE with ESP32 support
2. Install required libraries: `WebSocketsClient`, `ArduinoJson`
3. Update WiFi credentials in `esp32_updated_handler.cpp`
4. Update backend IP address
5. Upload to ESP32

### Testing Physical Button
```bash
# Test button functionality
python test_esp32_button.py
```

## WebSocket Message Protocol

### ESP32 → Backend Messages:
```json
// Physical button request
{
  "type": "button_command_request",
  "command": "open|close",
  "timestamp": "ISO8601"
}

// Status update
{
  "type": "status_update", 
  "data": {
    "physical_status": "open|closed"
  },
  "timestamp": "ISO8601"
}
```

### Backend → ESP32 Messages:
```json
// Authorized command
{
  "type": "command",
  "command": "open|close",
  "timestamp": "ISO8601"
}

// Denied command
{
  "type": "command_denied",
  "command": "open|close",
  "reason": "Door is locked",
  "timestamp": "ISO8601"
}
```

## User Stories

- As a Security Operator, I want to see the real-time status of all monitored doors on a single screen
- As an Administrator, I want to be able to immediately send commands to remotely lock or unlock any door
- **🆕 As a User, I want physical buttons to respect the lock state and not override security settings**
- **🆕 As a Security Auditor, I want all physical button presses logged regardless of authorization result**
- As an Audit System, I want to see a log of all simulated access attempts as they occur
- As a Developer, I want the server to manage device states and ensure only valid state transitions occur

## Security Features

- 🔐 **Lock State Enforcement**: Physical buttons cannot override locked doors
- 📝 **Complete Audit Trail**: All interactions logged with timestamps
- 🔍 **Real-time Monitoring**: Instant notifications of all events
- 🚫 **Authorization Validation**: Every action requires backend approval
- 👤 **User Attribution**: Clear tracking of command sources (remote vs physical)

## Deployment

The application can be deployed to cloud providers such as Vercel, Netlify, Google Cloud Platform (GCP), or Amazon Web Services (AWS).

## Testing

Use the included test script to verify ESP32 button functionality:
- `test_esp32_button.py`: Simulates ESP32 button presses
- `test_button_functionality.md`: Comprehensive testing guide
