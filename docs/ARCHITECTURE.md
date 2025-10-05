# Access Control Manager & Real-time Dashboard - Architecture

This document describes the architecture and folder structure of the Access Control Manager & Real-time Dashboard project.

## System Architecture

The project follows a client-server architecture with three main components:

1. **Frontend**: A web application that displays device status and provides control interfaces
2. **Backend**: Servers that handle device state management, API requests, and WebSocket communication
3. **Simulation**: Code that simulates IoT devices (smart doors)

```
                          ┌─────────────────┐
                          │                 │
                          │    Frontend     │◄───┐
                          │    (Browser)    │    │
                          │                 │    │
                          └────────┬────────┘    │
                                   │             │
                                   │             │
                      ┌────────────▼─────────────┴───┐
            HTTP      │                              │   WebSocket
        ┌────────────►│         Backend Server       │◄────────────┐
        │             │                              │             │
        │             └──────────────┬───────────────┘             │
        │                            │                             │
        │                            │                             │
┌───────┴────────┐          ┌────────▼─────────┐          ┌───────┴────────┐
│                │          │                  │          │                │
│  HTTP Client   │          │   WebSocket      │          │   Simulated    │
│  (API Calls)   │          │   Client/Server  │          │   IoT Devices  │
│                │          │                  │          │                │
└────────────────┘          └──────────────────┘          └────────────────┘
```

## Folder Structure

```
Arduron-Technical-Test/
├── README.md                # Project overview and description
├── ARCHITECTURE.md          # This file
├── frontend/                # Frontend application
│   ├── public/              # Static assets, index.html
│   └── src/                 # Source code
│       ├── assets/          # Images, fonts, and other static assets
│       ├── components/      # Reusable UI components
│       ├── hooks/           # Custom React hooks
│       ├── services/        # API services, WebSocket client
│       └── utils/           # Helper functions and utilities
│
├── backend/                 # Backend server
│   ├── config/              # Configuration files and environment variables
│   ├── src/                 # Source code
│   │   ├── controllers/     # Request handlers
│   │   ├── models/          # Data models for devices and access logs
│   │   ├── routes/          # API route definitions
│   │   ├── services/        # Business logic layer
│   │   ├── middleware/      # Express middleware
│   │   ├── utils/           # Helper functions
│   │   └── websocket/       # WebSocket server implementation
│   └── tests/               # Unit and integration tests
│
├── simulation/              # Device simulation code
│   ├── device1/             # Code for simulating the first smart door device
│   └── device2/             # Code for simulating the second smart door device
│
└── docs/                    # Project documentation
```

## Component Details

### Frontend Components

The frontend is structured to support a component-based architecture:

- **Device Status View**: Components to display the current status of doors
- **Command Interface**: UI components for sending control commands
- **Event Log**: Components for displaying the real-time event log
- **WebSocket Client**: Service that handles bi-directional communication with the server

### Backend Components

The backend follows a layered architecture:

1. **API Layer (Routes & Controllers)**: Handle incoming HTTP requests
   - Device Status API
   - Access Logs API
   
2. **WebSocket Layer**: Manages real-time bi-directional communication
   - Status Broadcasting
   - Command Listening
   
3. **Service Layer**: Contains business logic
   - Access Control State Management
   - Access Control Rules
   
4. **Data Layer (Models)**: In-memory data structures
   - Device State Models
   - Access Log Models

### Simulation Components

The simulation code mimics physical IoT devices:

- **Device Logic**: Code that simulates the behavior of a physical smart door
- **Communication**: Logic for receiving commands and sending status updates

## Data Flow

1. **User Interaction Flow**:
   - User interacts with the frontend UI
   - Frontend sends command via WebSocket to the backend
   - Backend processes command and updates device state
   - Backend broadcasts state change to all connected clients
   - Frontend updates UI to reflect the new state

2. **Device Simulation Flow**:
   - Simulated device sends access attempt to backend via HTTP
   - Backend validates access, updates state, and logs the attempt
   - Backend broadcasts state change to all connected clients
   - Frontend updates UI to reflect the new state and logs

## Security Considerations

- WebSocket connections should be secured with authentication
- API endpoints should implement proper validation and authorization
- Access control rules should be enforced server-side

## Scalability Considerations

- WebSocket server can be scaled horizontally with a message broker
- Stateless API servers can be load-balanced
- In-memory data can be migrated to a database for persistence