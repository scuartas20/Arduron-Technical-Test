# Access Control Manager

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Node.js](https://img.shields.io/badge/node.js-16+-green.svg)](https://nodejs.org/)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![React](https://img.shields.io/badge/react-18.2+-blue.svg)](https://reactjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)

A real-time access control system that manages smart door devices through a centralized dashboard with ESP32 hardware integration and WebSocket communication.

## 🚀 Features

### Core Functionality
- **Real-time Dashboard** - Live monitoring and control of smart door devices
- **Physical Device Integration** - ESP32-based smart door controllers
- **WebSocket Communication** - Bi-directional real-time messaging
- **Access Control Logic** - Server-side authorization and state management
- **Singleton State Management** - Single source of truth for all device states and events
- **Audit Trail** - Complete logging of all access attempts and device changes

### Security & Monitoring
- **Rate Limiting** - Protection against spam and brute force attacks
- **Connection Health Monitoring** - 10-second ping/pong heartbeat system
- **Lock State Enforcement** - Physical buttons respect security settings
- **Real-time Status Updates** - Instant connection and state synchronization

### Device Types
- **Physical Devices** (ESP32) - Hardware-controlled doors with buttons and LEDs
- **Virtual Devices** - Software-simulated doors for testing and development

## 🌟 Bonus Features

Beyond the core requirements, this project includes several advanced features:

### 1. **Real-time Connection Health Monitoring**
- **10-second ping/pong heartbeat** system between server and ESP32 devices
- **Automatic disconnection detection** within 30 seconds of device failure
- **Visual heartbeat indicators** on ESP32 LEDs showing active communication
- **Connection status API endpoints** for monitoring device connectivity

### 2. **Advanced Rate Limiting & Security**
- **Multi-layered rate limiting** (10 attempts/minute, 3 failed attempts lockout)
- **Brute force protection** with automatic 1-minute lockouts
- **Rate limiting statistics** and monitoring endpoints
- **Admin-only rate limiter management** with user authentication

### 3. **Smart Physical Button Integration**
- **Authorization-based button control** - buttons respect lock state
- **Command denial system** - locked doors cannot be overridden by physical buttons  
- **Complete audit trail** - all button presses logged regardless of authorization
- **Real-time feedback** - ESP32 receives immediate authorization responses

### 4. **Comprehensive State Management**
- **Physical vs Virtual device handling** with different behavior patterns


## 🏗️ Architecture

```
┌─────────────────┐    WebSocket     ┌─────────────────┐    WebSocket     ┌─────────────────┐
│   React Frontend│◄────────────────►│  FastAPI Backend│◄────────────────►│ ESP32 Devices   │
│   Dashboard     │   (Bidirectional)│                 │   (Bidirectional)│ (Physical)      │
└─────────────────┘                  └─────────────────┘                  └─────────────────┘
                                               ▲
                                               │ HTTP/REST API
                                               │ (GET/POST/DELETE)
                                               ▼
                                     ┌─────────────────┐
                                     │  External Tools │
                                     │ & API Clients   │
                                     └─────────────────┘
```

### Backend Components
- **FastAPI Application** - Entry point and server configuration
- **State Manager** - Single source of truth for all system data
- **WebSocket Manager** - Real-time communication with heartbeat monitoring
- **Access Control Service** - Business logic and authorization
- **Rate Limiter** - Security and abuse prevention

### Frontend Components
- **Device Status View** - Real-time door monitoring interface
- **Command Interface** - Controls for door operations (open/close/lock/unlock)
- **Event Log** - Live stream of access attempts and device changes
- **Connection Status** - WebSocket connectivity indicator
- **Access Attempt Simulator** - Test interface at the bottom of the dashboard for simulating access card attempts

### 💡 Frontend Testing Feature
The dashboard includes a **built-in access attempt simulator** at the bottom of the page where you can:
- Select a device (DOOR-001 or DOOR-002)
- Enter a user card ID (try "admin", "user123", or any custom ID)
- Choose a command (open/close)
- Send simulated access attempts to test the system

This feature is perfect for testing rate limiting, access control logic, and real-time updates without needing physical devices or external API calls.

## 📋 Prerequisites

- **Python 3.11+**
- **Node.js 16+**
- **ESP32 Development Board** (optional, for physical devices)
- **Arduino IDE** (for ESP32 programming)

## 🚀 Quick Start

### 1. Clone Repository
```bash
git clone <repository-url>
cd Arduron-Technical-Test
```

### 2. Backend Setup
```bash
cd backend

# Setup environment configuration (optional)
cp .env.example .env
# Edit .env to customize door configurations

# Create venv in backend and activate it for better practices
pip install -r requirements.txt
python src/main.py
```
Server starts at: `http://localhost:5000`

### 3. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
Dashboard available at: `http://localhost:3000`

### 4. ESP32 Setup (Optional)

**By default, all devices are virtual for easy simulation. To enable ESP32 physical devices:**

1. **Update Backend Configuration**:
   ```bash
   # Copy .env.example to .env
   cp backend/.env.example backend/.env
   
   # Edit .env file and change:
   DOOR1_TYPE=physical  # Change from "virtual" to "physical"
   ```

2. **ESP32 Hardware Setup**:
   - Install Arduino IDE with ESP32 support
   - Install libraries: `WebSocketsClient`, `ArduinoJson`
   - Update WiFi credentials in `esp32code/esp32_updated_handler.cpp`
   - Update backend IP address
   - Upload to ESP32

3. **Hardware Connections**:
   - GPIO 14: Physical button (with pull-down resistor)
   - GPIO 16: Red LED (door closed indicator)
   - GPIO 17: Green LED (door open indicator)

## 🔌 API Endpoints

### Device Management
- `GET /api/devices/status` - Get all device states
- `GET /api/devices/connections` - Get WebSocket connection status
- `GET /api/devices/{device_id}/connection` - Get specific device connection

### Access Control
- `GET /api/access_logs?limit=100` - Retrieve access history
- `POST /api/access_log` - Simulate access attempt

### Security
- `GET /api/security/rate_limiter/stats` - Rate limiting statistics
- `DELETE /api/security/rate_limiter/clear` - Clear rate limit data (admin)

### Health Check
- `GET /api/health` - Server health status

## 🔄 WebSocket Protocol

### ESP32 → Backend
```json
// Physical button request
{
  \"type\": \"button_command_request\",
  \"command\": \"open|close\",
  \"timestamp\": \"2025-10-08T10:30:00Z\"
}

// Status update
{
  \"type\": \"status_update\", 
  \"data\": {\"physical_status\": \"open|closed\"},
  \"timestamp\": \"2025-10-08T10:30:00Z\"
}

// Heartbeat response
{
  \"type\": \"pong\",
  \"timestamp\": \"2025-10-08T10:30:00Z\"
}
```

### Backend → ESP32
```json
// Authorized command
{
  \"type\": \"command\",
  \"command\": \"open|close\",
  \"timestamp\": \"2025-10-08T10:30:00Z\"
}

// Denied command
{
  \"type\": \"command_denied\",
  \"command\": \"open\",
  \"reason\": \"Door is locked\",
  \"timestamp\": \"2025-10-08T10:30:00Z\"
}

// Heartbeat check
{
  \"type\": \"ping\",
  \"timestamp\": \"2025-10-08T10:30:00Z\"
}
```

## 🔧 Configuration

### Backend Configuration

#### Environment Variables (`.env` file)
```bash
# Door Configuration - Edit to match your setup
DOOR1_ID=DOOR-001
DOOR1_LOCATION=Main Entrance
DOOR1_TYPE=virtual  # Change to "physical" for ESP32
DOOR1_INITIAL_PHYSICAL_STATUS=closed
DOOR1_INITIAL_LOCK_STATE=locked

DOOR2_ID=DOOR-002
DOOR2_LOCATION=Conference Room A
DOOR2_TYPE=virtual
DOOR2_INITIAL_PHYSICAL_STATUS=closed
DOOR2_INITIAL_LOCK_STATE=unlocked

# Security Settings
RATE_LIMIT_MAX_ATTEMPTS_PER_MINUTE=10
RATE_LIMIT_MAX_FAILED_ATTEMPTS=10
ADMIN_USER_ID=admin

# WebSocket Settings
WS_PING_INTERVAL=10  # seconds
WS_PING_TIMEOUT=30   # seconds
```

#### For ESP32 Integration
1. **Copy `.env.example` to `.env`**
2. **Change device type**: Set `DOOR1_TYPE=physical` (or `DOOR2_TYPE=physical`)
3. **Update ESP32 code**: Use the same door ID in your ESP32 WebSocket path

### ESP32 Configuration
```cpp
// WiFi credentials
const char* ssid = \"YOUR_WIFI_SSID\";
const char* password = \"YOUR_WIFI_PASSWORD\";

// Backend server
const char* websocket_server = \"192.168.1.XXX\";
const int websocket_port = 5000;
const char* websocket_path = \"/ws/DOOR-001\";

// GPIO pins
const int LED_RED = 16;    // Door closed indicator
const int LED_GREEN = 17;  // Door open indicator  
const int SWITCH_PIN = 14; // Physical button input
```

### API Testing

#### Device Management

**Get All Device Status**
```powershell
# PowerShell
Invoke-RestMethod -Uri "http://localhost:5000/api/devices/status" | ConvertTo-Json -Depth 3
```
```bash
# cURL
curl -X GET "http://localhost:5000/api/devices/status"
```

**Get Device Connections**
```powershell
# PowerShell
Invoke-RestMethod -Uri "http://localhost:5000/api/devices/connections" | ConvertTo-Json -Depth 3
```
```bash
# cURL
curl -X GET "http://localhost:5000/api/devices/connections"
```

**Get Specific Device Connection**
```powershell
# PowerShell
Invoke-RestMethod -Uri "http://localhost:5000/api/devices/DOOR-001/connection" | ConvertTo-Json -Depth 3
```
```bash
# cURL
curl -X GET "http://localhost:5000/api/devices/DOOR-001/connection"
```

#### Access Control

**Get Access Logs**
```powershell
# PowerShell
Invoke-RestMethod -Uri "http://localhost:5000/api/access_logs?limit=50" | ConvertTo-Json -Depth 3
```
```bash
# cURL
curl -X GET "http://localhost:5000/api/access_logs?limit=50"
```

**Simulate Access Attempt**
```powershell
# PowerShell
$body = @{
    device_id = "DOOR-001"
    user_card_id = "USER123"
    command = "open"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:5000/api/access_log" -Method POST -Body $body -ContentType "application/json" | ConvertTo-Json -Depth 3
```
```bash
# cURL
curl -X POST "http://localhost:5000/api/access_log" \
  -H "Content-Type: application/json" \
  -d '{"device_id":"DOOR-001","user_card_id":"USER123","command":"open"}'
```

**💡 Alternative: Use Frontend Simulator**
Instead of using API calls, you can use the **built-in access attempt simulator** at the bottom of the dashboard (`http://localhost:3000`). This provides:
- Easy form-based interface
- No need for JSON formatting
- Real-time visual feedback
- Perfect for quick testing and demos

#### Security & Rate Limiting

**Get Rate Limiter Statistics**
```powershell
# PowerShell
Invoke-RestMethod -Uri "http://localhost:5000/api/security/rate_limiter/stats" | ConvertTo-Json -Depth 3
```
```bash
# cURL
curl -X GET "http://localhost:5000/api/security/rate_limiter/stats"
```

**Get User Rate Limit Status**
```powershell
# PowerShell
Invoke-RestMethod -Uri "http://localhost:5000/api/security/rate_limiter/user_status?device_id=DOOR-001&user_id=USER123" | ConvertTo-Json -Depth 3
```
```bash
# cURL
curl -X GET "http://localhost:5000/api/security/rate_limiter/user_status?device_id=DOOR-001&user_id=USER123"
```

**Clear Rate Limiter (Admin Only)**
```powershell
# PowerShell
Invoke-RestMethod -Uri "http://localhost:5000/api/security/rate_limiter/clear?user_id=admin" -Method DELETE | ConvertTo-Json -Depth 3
```
```bash
# cURL
curl -X DELETE "http://localhost:5000/api/security/rate_limiter/clear?user_id=admin"
```

#### Health Check

**Server Health**
```powershell
# PowerShell
Invoke-RestMethod -Uri "http://localhost:5000/api/health" | ConvertTo-Json -Depth 3
```
```bash
# cURL
curl -X GET "http://localhost:5000/api/health"
```

**Root Endpoint (API Info)**
```powershell
# PowerShell
Invoke-RestMethod -Uri "http://localhost:5000/" | ConvertTo-Json -Depth 3
```
```bash
# cURL
curl -X GET "http://localhost:5000/"
```

## 📁 Project Structure

```
├── backend/                    # FastAPI backend
│   ├── src/
│   │   ├── main.py            # Application entry point
│   │   ├── config/            # Configuration management
│   │   ├── models/            # Data models
│   │   ├── services/          # Business logic
│   │   ├── controllers/       # Request handlers
│   │   ├── routes/            # API endpoints
│   │   └── websocket/         # WebSocket management
│   └── requirements.txt       # Python dependencies
├── frontend/                  # React frontend
│   ├── src/
│   │   ├── components/        # React components
│   │   ├── hooks/             # Custom hooks
│   │   ├── services/          # API clients
│   │   └── App.jsx           # Main component
│   └── package.json          # Node.js dependencies
├── esp32code/                # ESP32 Arduino code
│   └── esp32_updated_handler.cpp
├── docs/                     # Documentation
└── README.md                 # Project overview
```

## 🔒 Security Features

### Access Control
- **Lock State Enforcement** - Physical buttons cannot override locked doors
- **Authorization Validation** - All commands require backend approval
- **Complete Audit Trail** - All interactions logged with timestamps

### Rate Limiting
- **10 attempts per minute** per user/device combination
- **10 failed attempts** trigger 1-minute lockout
- **Real-time monitoring** and statistics

### Connection Security
- **Heartbeat Monitoring** - 10-second ping/pong system
- **Connection Status Tracking** - Real-time device connectivity
- **Automatic Cleanup** - Disconnected devices removed within 30 seconds

## 🌟 User Stories

- **Security Operator**: Monitor real-time status of all doors on a single dashboard
- **Administrator**: Remotely control door locks and access permissions
- **Physical User**: Use hardware buttons that respect security settings
- **Audit System**: Track all access attempts with complete history
- **Developer**: Extend system with new device types and features
- **Tester/Demo User**: Simulate access card attempts using the built-in dashboard simulator

## 🚀 Deployment

### Local Development (Recommended for Getting Started)
```bash
# Backend - Option 1: Local Python
cd backend
pip install -r requirements.txt
python src/main.py

# Frontend  
cd frontend
npm install
npm run dev
```

### Next steps (In development): Docker Deployment

#### Backend with Docker
The backend includes a simple, optimized Dockerfile for easy containerization:

```bash
# Build the backend image
cd backend
docker build -t access-control-backend .

# Run the backend container
docker run -p 5000:5000 access-control-backend

# Optional: Run with environment file
docker run -p 5000:5000 --env-file .env access-control-backend
```

### Production Options

## 🚀 Deployment Plan

The application will be deployed using a modern, scalable architecture with the following components:

- **AWS EC2** – to host the backend service on a reliable and always-available virtual server.
- **Docker** – to containerize the application, ensuring consistent environments and easy deployment.
- **Nginx** – as a reverse proxy to route incoming traffic and support secure WebSocket connections.
- **HTTPS (SSL/TLS)** – to provide encrypted and secure communication between clients and the server.
- **Vercel / Netlify** – for hosting the frontend, allowing fast global delivery and simple integration with the backend API.

This setup ensures scalability, security, and a clear separation between frontend and backend components, making future updates and maintenance more efficient.

## 📚 Documentation

- [`docs/CodeFlow.md`](docs/CodeFlow.md) - Code flow and data flow documentation

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For support and questions:
- Check the [documentation](docs/)
- Review [existing issues](https://github.com/your-repo/issues)
- Create a [new issue](https://github.com/your-repo/issues/new)

## 🏆 Acknowledgments

- FastAPI for the excellent async web framework
- React for the frontend framework
- ESP32 community for hardware integration resources