# Access Control Dashboard - Frontend

This is the frontend React application for the Access Control Manager system. It provides a simple, real-time dashboard for monitoring and controlling smart door devices.

## Features

- **Device Status View**: Display current status of all smart doors (physical status and lock state)
- **Command Interface**: Simple buttons to open/close doors and lock/unlock devices
- **Real-time Event Log**: Live feed of access attempts and device state changes
- **WebSocket Connection**: Real-time bi-directional communication with backend
- **Responsive Design**: Works on desktop and mobile devices

## Requirements

- Node.js (version 16 or higher)
- npm (comes with Node.js)
- Backend server running on `http://localhost:5000`

## Installation

1. **Navigate to the frontend directory**:
   ```bash
   cd frontend
   ```

2. **Install dependencies**:
   ```bash
   npm install
   ```

3. **Start the development server**:
   ```bash
   npm run dev
   ```

4. **Open your browser and go to**:
   ```
   http://localhost:3000
   ```

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build

## Usage

### Monitoring Devices
- The main dashboard shows all registered smart doors
- Each device card displays:
  - Device ID and location
  - Current physical status (Open/Closed)
  - Current lock state (Locked/Unlocked)

### Controlling Devices
- Use the control buttons on each device card:
  - **Open/Close**: Control physical door position
  - **Lock/Unlock**: Control door lock mechanism
- Commands are sent via WebSocket to the backend
- Device status updates in real-time

### Event Log
- View real-time access events on the right side
- See access attempts, granted/denied status
- Monitor all device interactions

### Testing Access Attempts
- Use the "Simulate Access Attempt" section at the bottom
- Test different user IDs to see access control logic:
  - `admin` - Has full access to all commands
  - Other users - Limited access based on door state

## Configuration

The frontend connects to:
- **Backend API**: `http://localhost:5000/api`
- **WebSocket**: `ws://localhost:5000/ws`

To change these URLs, edit the configuration in:
- `src/services/api.js` (for HTTP requests)
- `src/services/websocket.js` (for WebSocket connection)

## Troubleshooting

### Connection Issues
- Ensure the backend server is running on port 5000
- Check that CORS is properly configured on the backend
- Look for connection status in the top of the dashboard

### WebSocket Not Working
- Verify WebSocket endpoint is accessible
- Check browser console for error messages
- Try refreshing the page to reconnect

### No Devices Showing
- Make sure backend is running and accessible
- Check that devices are properly registered in the backend
- Use browser dev tools to inspect API responses

## Architecture

The frontend is built with:
- **React 18** - Main framework
- **Vite** - Build tool and dev server
- **Native WebSocket** - Real-time communication
- **Axios** - HTTP requests
- **CSS3** - Styling (no external UI libraries for simplicity)

## File Structure

```
frontend/
├── src/
│   ├── components/          # React components
│   │   ├── DeviceCard.jsx   # Individual device display
│   │   ├── EventLog.jsx     # Access events log
│   │   └── ConnectionStatus.jsx # WebSocket status
│   ├── hooks/               # Custom React hooks
│   │   └── useAccessControl.js # Main app state management
│   ├── services/            # External service clients
│   │   ├── api.js          # HTTP API client
│   │   └── websocket.js    # WebSocket client
│   ├── App.jsx             # Main application component
│   ├── main.jsx            # Application entry point
│   └── index.css           # Global styles
├── public/                 # Static assets
├── index.html              # HTML template
├── package.json            # Dependencies and scripts
└── vite.config.js         # Build configuration
```