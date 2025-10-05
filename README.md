# Access Control Manager & Real-time Dashboard

## Project Overview

This project is a robust web application that simulates a real-time Access Control System (ACS) manager. It demonstrates the implementation of a WebSocket server to manage the state and status of virtual IoT devices (simulated smart doors), an HTTP server to register access logs, and a dynamic frontend for commanding and monitoring these devices.

The Access Control Logic is implemented on the backend, where the server serves as the single source of truth for device status.

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

### Simulation

The project demonstrates the complete logic required to integrate a physical device (ESP32, Arduino, or Raspberry Pi) for at least one door. It shows how a command sent from the dashboard via the WebSocket server is:
1. Received and processed by the server
2. Sent to the simulated device
3. Results in a state change on the simulated device

### Backend (The Servers)

1. **Access Control State Manager**: Maintains the current, authoritative state of simulated devices (Physical Status and Lock State) in memory

2. **WebSocket Server (Bi-directional)**:
   - Status Broadcast: Pushes real-time status updates to all connected clients
   - Command Listener: Receives control commands from the frontend and executes access control logic

3. **HTTP Server (Audit & Management Endpoints)**:
   - `GET /api/devices/status`: Endpoint to fetch the initial list and current state of all registered devices
   - `GET /api/access_logs`: Endpoint to retrieve the stored access history/log
   - `POST /api/access_log`: Simulates a device sending an access attempt to open or close a door

## Technology Stack

| Area | Requirement / Suggestion |
|------|--------------------------|
| Frontend | React, Angular, or Vue.js. Standard CSS approach, responsive design required |
| Backend | Node.js (with Express/ws) or Python (with FastAPI/Flask and websockets library) |
| Data Source | All data (Device States, User List, Access Logs) managed in-memory |

## User Stories

- As a Security Operator, I want to see the real-time status of all monitored doors on a single screen
- As an Administrator, I want to be able to immediately send commands to remotely lock or unlock any door
- As an Audit System, I want to see a log of all simulated access attempts as they occur
- As a Developer, I want the server to manage device states and ensure only valid state transitions occur

## Bonus Features

The project includes proposals and explanations for at least two enhancements focusing on scalability, security, or robustness (e.g., persistence, advanced access rules, simulated user authentication).

## Deployment

The application can be deployed to cloud providers such as Vercel, Netlify, Google Cloud Platform (GCP), or Amazon Web Services (AWS).
