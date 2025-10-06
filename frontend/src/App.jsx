/**
 * Main App Component - Access Control Dashboard
 */
import React, { useState } from 'react';
import DeviceCard from './components/DeviceCard';
import EventLog from './components/EventLog';
import ConnectionStatus from './components/ConnectionStatus';
import { useAccessControl } from './hooks/useAccessControl';
import './index.css';

function App() {
  const {
    devices,
    accessLogs,
    connectionStatus,
    loading,
    error,
    sendCommand,
    simulateAccess,
    reconnect,
    refresh,
    clearError
  } = useAccessControl();

  // Test form state
  const [testForm, setTestForm] = useState({
    deviceId: 'DOOR-001',
    userId: 'user123',
    command: 'open'
  });

  const handleTestSubmit = (e) => {
    e.preventDefault();
    simulateAccess(testForm.deviceId, testForm.userId, testForm.command);
  };

  const handleDeviceCommand = (deviceId, command) => {
    sendCommand(deviceId, command);
  };

  if (loading) {
    return (
      <div className="app">
        <div className="loading">
          <h2>Loading Access Control Dashboard...</h2>
          {connectionStatus === 'connecting' && <p>⏳ Establishing WebSocket connection...</p>}
          {connectionStatus === 'connected' && <p>✅ Connected! Waiting for device data...</p>}
          {connectionStatus === 'disconnected' && <p>🔌 Connecting to server...</p>}
          {connectionStatus === 'failed' && <p>❌ Connection failed. Please check if backend is running.</p>}
        </div>
      </div>
    );
  }

  return (
    <div className="app">
      {/* Header */}
      <header className="app-header">
        <h1 className="app-title">Access Control Manager</h1>
        <p className="app-subtitle">Real-time Dashboard for Smart Door Control</p>
      </header>

      {/* Connection Status */}
      <ConnectionStatus 
        status={connectionStatus} 
        onReconnect={reconnect}
      />

      {/* Error Display */}
      {error && (
        <div className="error">
          ⚠️ {error}
          <button onClick={clearError}>✕</button>
        </div>
      )}

      {/* Main Content */}
      <div className="main-content">
        {/* Device Status Section */}
        <section className="devices-section">
          <h2>Device Status ({devices.length} devices)</h2>
          
          {devices.length === 0 ? (
            <div className="no-devices">
              <p>No devices found. Please check the server connection.</p>
              <button onClick={refresh}>Refresh</button>
            </div>
          ) : (
            <div className="devices-grid">
              {devices.map(device => (
                <DeviceCard
                  key={device.door_id}
                  device={device}
                  onCommand={handleDeviceCommand}
                />
              ))}
            </div>
          )}
        </section>

        {/* Event Log Section */}
        <EventLog events={accessLogs} />
      </div>

      {/* Test Controls */}
      <section className="test-controls">
        <h3>🧪 Simulate Access Attempt</h3>
        <form className="test-form" onSubmit={handleTestSubmit}>
          <div className="form-group">
            <label>Device ID:</label>
            <select
              value={testForm.deviceId}
              onChange={(e) => setTestForm({...testForm, deviceId: e.target.value})}
            >
              {devices.map(device => (
                <option key={device.door_id} value={device.door_id}>
                  {device.door_id}
                </option>
              ))}
            </select>
          </div>
          
          <div className="form-group">
            <label>User ID:</label>
            <input
              type="text"
              value={testForm.userId}
              onChange={(e) => setTestForm({...testForm, userId: e.target.value})}
              placeholder="Enter user ID"
            />
          </div>
          
          <div className="form-group">
            <label>Command:</label>
            <select
              value={testForm.command}
              onChange={(e) => setTestForm({...testForm, command: e.target.value})}
            >
              <option value="open">Open</option>
              <option value="close">Close</option>
              <option value="lock">Lock</option>
              <option value="unlock">Unlock</option>
            </select>
          </div>
          
          <button 
            type="submit" 
            className="test-btn"
            disabled={connectionStatus !== 'connected'}
          >
            {connectionStatus === 'connected' ? 'Simulate Access' : 'Connecting...'}
          </button>
        </form>
        
        <p style={{ marginTop: '10px', fontSize: '0.9em', color: '#666' }}>
          💡 Try different user IDs like "admin", "user123", or "guest" to see different access results.
        </p>
      </section>
    </div>
  );
}

export default App;