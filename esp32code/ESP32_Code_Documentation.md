# ESP32 Smart Door Controller - Code Documentation

## Overview

The ESP32 Smart Door Controller (`esp32_updated_handler.cpp`) implements a sophisticated **authorization-based physical access control system**. Unlike traditional door controllers that operate independently, this ESP32 device integrates seamlessly with the backend access control system, ensuring that physical button presses respect the centralized security policies.

## Key Features

- 🔒 **Security-First Design**: Physical buttons cannot override locked doors
- 🌐 **Real-time Communication**: Persistent WebSocket connection to backend
- 🚨 **Smart Authorization**: Every button press requires backend approval
- 🔄 **State Synchronization**: Bidirectional state updates with backend
- 💡 **Visual Feedback**: Red/Green LEDs indicate door status
- 🛡️ **Complete Audit Trail**: All interactions logged by backend

---

## Hardware Configuration

### GPIO Pin Assignment
```cpp
const int LED_RED = 16;    // Red LED - indicates door closed
const int LED_GREEN = 17;  // Green LED - indicates door open  
const int SWITCH_PIN = 14; // Physical button with pull-down resistor
```

### Hardware Requirements
- **ESP32 Development Board** (any variant)
- **Red LED** + 220Ω resistor → GPIO 16
- **Green LED** + 220Ω resistor → GPIO 17
- **Push Button** + 10kΩ pull-down resistor → GPIO 14
- **WiFi Network** connection
- **5V Power Supply** (USB or external)

### Circuit Diagram
```
ESP32                    Components
GPIO 16 ──[220Ω]──┤>|── GND     (Red LED)
GPIO 17 ──[220Ω]──┤>|── GND     (Green LED)
GPIO 14 ──┐              
          │                     
          └──[Button]──┐         
                       │         
          ┌─[10kΩ]─────┘         
          │                     
         GND                    
```

---

## Code Architecture

### Main Components

#### 1. **Network Configuration**
```cpp
const char* ssid = "XXXX";           // WiFi network name
const char* password = "XXXXX";      // WiFi password
const char* websocket_server = "192.168.1.XX";  // Backend server IP
const int websocket_port = 5000;     // Backend server port
const char* websocket_path = "/ws/DOOR-001";    // Device-specific endpoint
```

#### 2. **State Management**
```cpp
bool doorOpen = false;               // Current door state (open/closed)
bool lastSwitchState = false;        // Previous button state
bool currentSwitchState = false;     // Current button state  
unsigned long lastDebounceTime = 0;  // Debouncing timestamp
const unsigned long debounceDelay = 50; // 50ms debounce period
```

#### 3. **WebSocket Client**
```cpp
WebSocketsClient webSocket;          // WebSocket connection handler
```

---

## Core Functions Analysis

### 1. Setup Function (`setup()`)

**Purpose**: Initialize hardware, connect to WiFi, and establish WebSocket connection

```cpp
void setup() {
  Serial.begin(115200);           // Initialize serial communication
  
  // Configure GPIO pins
  pinMode(LED_RED, OUTPUT);       // Set red LED as output
  pinMode(LED_GREEN, OUTPUT);     // Set green LED as output  
  pinMode(SWITCH_PIN, INPUT_PULLDOWN); // Set button as input with pull-down
  
  setDoorState(false);            // Initialize door as closed (red LED on)
  
  // WiFi connection with status monitoring
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");            // Visual connection progress
  }
  
  // WebSocket initialization with auto-reconnection
  webSocket.begin(websocket_server, websocket_port, websocket_path);
  webSocket.onEvent(webSocketEvent);    // Set event handler
  webSocket.setReconnectInterval(5000); // Auto-reconnect every 5 seconds
}
```

**Key Features:**
- **INPUT_PULLDOWN**: Ensures stable button readings (LOW when not pressed)
- **Auto-reconnection**: Maintains persistent connection to backend
- **Device-specific endpoint**: `/ws/DOOR-001` identifies this specific door

### 2. Main Loop (`loop()`)

**Purpose**: Continuously handle WebSocket communication and monitor button input

```cpp
void loop() {
  webSocket.loop();        // Process WebSocket events and maintain connection
  handleSwitchInput();     // Check for button presses with debouncing
  delay(10);              // Small delay to prevent CPU overload
}
```

**Design Pattern**: Non-blocking loop that handles multiple tasks efficiently

### 3. Door State Management (`setDoorState()`)

**Purpose**: Control LED indicators and maintain visual door status

```cpp
void setDoorState(bool open) {
  doorOpen = open;
  
  if (doorOpen) {
    digitalWrite(LED_GREEN, HIGH);  // Turn on green LED
    digitalWrite(LED_RED, LOW);     // Turn off red LED
    Serial.println("🟢 Door OPEN");
  } else {
    digitalWrite(LED_RED, HIGH);    // Turn on red LED
    digitalWrite(LED_GREEN, LOW);   // Turn off green LED
    Serial.println("🔴 Door CLOSED");
  }
}
```

**Key Behavior:**
- **Mutually Exclusive LEDs**: Only one LED is on at a time
- **Clear Visual Feedback**: Red = Closed, Green = Open
- **Serial Logging**: Debug information with emoji indicators

### 4. Smart Button Handler (`handleSwitchInput()`)

**Purpose**: Detect button presses with debouncing and send authorization requests

```cpp
void handleSwitchInput() {
  int reading = digitalRead(SWITCH_PIN);
  
  // Debouncing algorithm
  if (reading != lastSwitchState) {
    lastDebounceTime = millis();    // Reset debounce timer
  }
  
  if ((millis() - lastDebounceTime) > debounceDelay) {
    if (reading != currentSwitchState) {
      currentSwitchState = reading;
      
      // Button pressed (LOW to HIGH transition)
      if (currentSwitchState == HIGH) {
        Serial.println("🔘 Switch pressed - Requesting door state change");
        
        // CRITICAL: Don't change state directly - request authorization
        String command = doorOpen ? "close" : "open";
        sendCommandRequest(command);  // Send request to backend
      }
    }
  }
  
  lastSwitchState = reading;
}
```

**Security Features:**
- **No Direct State Change**: Button press only sends request, doesn't change LEDs
- **Debouncing**: Prevents multiple triggers from mechanical button bounce
- **Toggle Logic**: Open door → request close, Closed door → request open
- **Authorization Required**: Backend must approve before any state change

### 5. Backend Communication Functions

#### Status Update (`sendStatusUpdate()`)
**Purpose**: Inform backend of current physical door state

```cpp
void sendStatusUpdate() {
  if (webSocket.isConnected()) {
    DynamicJsonDocument doc(1024);
    doc["type"] = "status_update";
    doc["data"]["physical_status"] = doorOpen ? "open" : "closed";
    doc["timestamp"] = getTimestamp();
    
    String message;
    serializeJson(doc, message);
    webSocket.sendTXT(message);
  }
}
```

**JSON Message Format:**
```json
{
  "type": "status_update",
  "data": {
    "physical_status": "open"
  },
  "timestamp": "123456789"
}
```

#### Command Request (`sendCommandRequest()`)
**Purpose**: Request authorization for physical button action

```cpp
void sendCommandRequest(String command) {
  if (webSocket.isConnected()) {
    DynamicJsonDocument doc(1024);
    doc["type"] = "button_command_request";
    doc["command"] = command;
    doc["timestamp"] = getTimestamp();
    
    String message;
    serializeJson(doc, message);
    webSocket.sendTXT(message);
  }
}
```

**JSON Message Format:**
```json
{
  "type": "button_command_request",
  "command": "open",
  "timestamp": "123456789"
}
```

#### Command Response (`sendCommandResponse()`)
**Purpose**: Acknowledge backend commands with execution status

```cpp
void sendCommandResponse(String command, bool success, String message) {
  if (webSocket.isConnected()) {
    DynamicJsonDocument doc(1024);
    doc["type"] = "command_response";
    doc["command"] = command;
    doc["success"] = success;
    doc["message"] = message;
    doc["timestamp"] = getTimestamp();
    
    String response;
    serializeJson(doc, response);
    webSocket.sendTXT(response);
  }
}
```

---

## WebSocket Communication Protocol

### 1. Connection Establishment

```cpp
void webSocketEvent(WStype_t type, uint8_t * payload, size_t length) {
  switch(type) {
    case WStype_CONNECTED:
      Serial.printf("🔌 WebSocket Connected to: %s\n", payload);
      sendStatusUpdate();  // Send initial door state
      break;
  }
}
```

**Connection Flow:**
1. ESP32 connects to `/ws/DOOR-001` endpoint
2. Backend validates device ID and accepts connection
3. ESP32 immediately sends current door status
4. Ready to receive commands and send updates

### 2. Message Handling (`handleWebSocketMessage()`)

**Purpose**: Process incoming messages from backend

```cpp
void handleWebSocketMessage(String message) {
  DynamicJsonDocument doc(1024);
  DeserializationError error = deserializeJson(doc, message);
  
  if (error) {
    Serial.println("❌ JSON parsing error: " + String(error.c_str()));
    return;
  }
  
  String type = doc["type"];
  
  if (type == "command") {
    // Handle authorized commands from backend
  } else if (type == "command_denied") {
    // Handle denied authorization requests  
  } else if (type == "handshake") {
    // Handle connection handshake
  }
}
```

### 3. Command Processing

#### Authorized Command Handling
```cpp
if (type == "command") {
  String command = doc["command"];
  
  if (command == "open") {
    if (!doorOpen) {
      setDoorState(true);                    // Change LED state
      sendCommandResponse("open", true, "Door opened successfully");
      sendStatusUpdate();                    // Notify backend of new state
    } else {
      sendCommandResponse("open", true, "Door was already open");
    }
  }
}
```

#### Command Denial Handling
```cpp
else if (type == "command_denied") {
  String command = doc["command"];
  String reason = doc["reason"];
  Serial.println("❌ Command DENIED: " + command + " - Reason: " + reason);
  // Don't change state, just log the denial
}
```

---

## Security Implementation

### 1. Authorization-Based Control Flow

```
Physical Button Press → Authorization Request → Backend Validation → Response → LED Update
       │                        │                      │               │           │
       │                        │                      │               │           └─► Only if authorized
       │                        │                      │               └─► command/command_denied
       │                        │                      └─► Lock state + rate limiting check
       │                        └─► button_command_request sent via WebSocket
       └─► ESP32 does NOT change LEDs immediately
```

### 2. Security Benefits

**Lock State Enforcement:**
- Physical button cannot override locked doors
- Backend checks `door.lock_state` before authorization
- If locked, `command_denied` message sent to ESP32

**Rate Limiting Protection:**
- Backend applies same rate limits to physical button as remote commands
- Prevents button spam attacks
- Failed attempts trigger temporary lockout

**Complete Audit Trail:**
- Every button press logged in backend (successful or denied)
- Real-time notifications to all connected dashboard clients
- Centralized security monitoring

### 3. Fail-Safe Behavior

**Connection Loss:**
```cpp
case WStype_DISCONNECTED:
  Serial.println("🔌 WebSocket Disconnected");
  // ESP32 maintains last known state
  // Auto-reconnection attempts every 5 seconds
  break;
```

**Invalid Commands:**
```cpp
else {
  sendCommandResponse(command, false, "Unknown command");
}
```

**JSON Parsing Errors:**
```cpp
if (error) {
  Serial.println("❌ JSON parsing error: " + String(error.c_str()));
  return;  // Ignore malformed messages
}
```

---

## Message Types and Protocols

### 1. Outgoing Messages (ESP32 → Backend)

#### Status Update
```json
{
  "type": "status_update",
  "data": {
    "physical_status": "open|closed"
  },
  "timestamp": "123456789"
}
```
**Trigger**: Connection established, manual door operation

#### Button Command Request
```json
{
  "type": "button_command_request", 
  "command": "open|close",
  "timestamp": "123456789"
}
```
**Trigger**: Physical button pressed

#### Command Response
```json
{
  "type": "command_response",
  "command": "open|close",
  "success": true|false,
  "message": "Execution result",
  "timestamp": "123456789"
}
```
**Trigger**: After executing backend command

### 2. Incoming Messages (Backend → ESP32)

#### Authorized Command
```json
{
  "type": "command",
  "command": "open|close", 
  "timestamp": "2025-10-08T10:30:00Z"
}
```
**Action**: Execute command, update LEDs, send response

#### Command Denied
```json
{
  "type": "command_denied",
  "command": "open|close",
  "reason": "Door is locked",
  "timestamp": "2025-10-08T10:30:00Z"
}
```
**Action**: Log denial, do NOT change LEDs

#### Handshake
```json
{
  "type": "handshake"
}
```
**Action**: Send current status update

#### Acknowledgment
```json
{
  "type": "ack",
  "message": "Status update received"
}
```
**Action**: Log confirmation

---

## Configuration and Deployment

### 1. Network Configuration

**Required Changes for Deployment:**
```cpp
// Update these values for your network
const char* ssid = "YOUR_WIFI_NETWORK";
const char* password = "YOUR_WIFI_PASSWORD";
const char* websocket_server = "YOUR_BACKEND_IP";  // e.g., "192.168.1.100"
```

### 2. Device Identification

**Device ID Configuration:**
```cpp
const char* websocket_path = "/ws/DOOR-001";  // Must match backend device registry
```

**Backend Registration:**
```python
# In app_state.py - device must be registered as PHYSICAL type
door1 = Door(
    door_id="DOOR-001",
    location="Main Entrance", 
    device_type=DeviceType.PHYSICAL  # Critical for ESP32 integration
)
```

### 3. Arduino IDE Setup

**Required Libraries:**
```
- WiFi (ESP32 built-in)
- WebSocketsClient by Markus Sattler
- ArduinoJson by Benoit Blanchon
```

**Board Configuration:**
- **Board**: ESP32 Dev Module
- **Upload Speed**: 921600
- **CPU Frequency**: 240MHz
- **Flash Size**: 4MB
- **Partition Scheme**: Default 4MB with spiffs

### 4. Serial Monitor Output

**Normal Operation:**
```
WiFi connected! IP: 192.168.1.150
ESP32 DOOR-001 started
🔌 WebSocket Connected to: ws://192.168.1.100:5000/ws/DOOR-001
📤 Status sent to backend: {"type":"status_update"...}
🔴 Door CLOSED
🔘 Switch pressed - Requesting door state change
📤 Button command request sent to backend
🎯 Command received: open
🟢 Door OPEN
📤 Response sent: {"type":"command_response"...}
```

**Error Scenarios:**
```
⚠️ WebSocket not connected - Could not send command request
❌ Command DENIED: open - Reason: Door is locked
❌ JSON parsing error: Invalid input
```

---

## Integration with Backend System

### 1. Backend Device Registration

The ESP32 must be registered in the backend as a physical device:

```python
# In services/app_state.py
door1 = Door(
    door_id="DOOR-001",           # Must match ESP32 websocket_path
    location="Main Entrance",
    physical_status=PhysicalStatus.CLOSED,
    lock_state=LockState.LOCKED,  # Initial lock state
    device_type=DeviceType.PHYSICAL  # Enables ESP32 integration
)
```

### 2. WebSocket Endpoint Handling

Backend processes ESP32 connections at device-specific endpoints:

```python
# In main.py
@app.websocket("/ws/{device_id}")
async def device_websocket_endpoint(websocket: WebSocket, device_id: str):
    await websocket_manager.connect_device(websocket, device_id)
    # Handle ESP32 messages: status_update, button_command_request, command_response
```

### 3. Command Authorization Flow

When ESP32 sends `button_command_request`:

```python
# In services/access_control.py
async def handle_button_command_request(device_id: str, command: str, device_websocket):
    # 1. Verify device exists and is physical
    # 2. Check rate limiting
    # 3. CRITICAL: Check if door is locked
    # 4. If locked: send command_denied
    # 5. If unlocked: process normally and send command
```

### 4. Real-time Dashboard Updates

When ESP32 button is pressed:
1. ESP32 sends authorization request
2. Backend processes and logs event
3. All dashboard clients receive real-time notification
4. ESP32 receives authorization or denial
5. ESP32 updates LEDs only if authorized

---

## Troubleshooting Guide

### 1. Common Connection Issues

**WiFi Connection Failed:**
```cpp
// Add connection timeout and retry logic
int attempts = 0;
while (WiFi.status() != WL_CONNECTED && attempts < 20) {
  delay(500);
  Serial.print(".");
  attempts++;
}
if (WiFi.status() != WL_CONNECTED) {
  Serial.println("WiFi connection failed!");
  ESP.restart();  // Restart ESP32
}
```

**WebSocket Connection Issues:**
- Verify backend server IP and port
- Check firewall settings
- Ensure backend is running and accessible
- Verify device ID matches backend registration

### 2. Hardware Issues

**LEDs Not Working:**
- Check resistor values (220Ω recommended)
- Verify GPIO pin connections
- Test with simple digitalWrite test

**Button Not Responsive:**
- Verify pull-down resistor (10kΩ)
- Check debounce timing
- Test with digitalRead monitoring

### 3. Message Protocol Issues

**JSON Parsing Errors:**
- Verify ArduinoJson library version (v6.x recommended)
- Check message size limits (1024 bytes buffer)
- Monitor serial output for malformed messages

**Command Not Executed:**
- Check WebSocket connection status
- Verify message type and format
- Monitor backend logs for authorization results

### 4. Integration Issues

**Backend Not Recognizing Device:**
- Verify device_id matches backend registration
- Check device_type is set to PHYSICAL
- Monitor backend logs for connection attempts

**Commands Denied:**
- Check door lock state in backend
- Verify rate limiting configuration
- Monitor access logs for denial reasons

---

## Advanced Features and Extensions

### 1. Security Enhancements

**Encrypted Communication:**
```cpp
// Add TLS/SSL support for production
WiFiClientSecure client;
client.setCACert(root_ca);  // Set certificate authority
webSocket.beginSSL(websocket_server, websocket_port, websocket_path);
```

**Device Authentication:**
```cpp
// Add device-specific authentication token
DynamicJsonDocument doc(1024);
doc["type"] = "authenticate";
doc["device_id"] = "DOOR-001";
doc["auth_token"] = "device_specific_token";
```

### 2. Hardware Extensions

**Additional Sensors:**
```cpp
const int DOOR_SENSOR_PIN = 18;  // Magnetic door sensor
const int PIR_SENSOR_PIN = 19;   // Motion detection
const int RFID_SS_PIN = 5;       // RFID card reader
```

**Status Indicators:**
```cpp
const int BUZZER_PIN = 21;       // Audio feedback
const int SERVO_PIN = 22;        // Automatic door lock
const int LCD_SDA = 23;          // Status display
const int LCD_SCL = 24;
```

### 3. Monitoring and Diagnostics

**Heartbeat Monitoring:**
```cpp
unsigned long lastHeartbeat = 0;
const unsigned long heartbeatInterval = 30000;  // 30 seconds

void sendHeartbeat() {
  if (millis() - lastHeartbeat > heartbeatInterval) {
    // Send periodic status update
    sendStatusUpdate();
    lastHeartbeat = millis();
  }
}
```

**Diagnostic Information:**
```cpp
void sendDiagnostics() {
  DynamicJsonDocument doc(1024);
  doc["type"] = "diagnostics";
  doc["wifi_rssi"] = WiFi.RSSI();
  doc["free_heap"] = ESP.getFreeHeap();
  doc["uptime"] = millis();
  doc["firmware_version"] = "1.0.0";
}
```

This ESP32 implementation provides a robust, secure, and scalable foundation for physical access control devices that seamlessly integrate with centralized backend systems while maintaining complete security and audit compliance.