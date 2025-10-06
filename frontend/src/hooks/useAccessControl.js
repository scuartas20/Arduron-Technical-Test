/**
 * Custom hook to manage access control application state
 */
import { useState, useEffect, useCallback } from 'react';
import { webSocketService } from '../services/websocket';
import { apiService } from '../services/api';

export const useAccessControl = () => {
  const [devices, setDevices] = useState([]);
  const [accessLogs, setAccessLogs] = useState([]);
  const [connectionStatus, setConnectionStatus] = useState('disconnected');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [logsInitialized, setLogsInitialized] = useState(false); // Track if logs have been initialized

  // Load initial data from API
  const loadInitialData = useCallback(async () => {
    try {
      console.log('Loading initial data from API...');
      setError(null);

      // Load devices status
      const devicesData = await apiService.getDevicesStatus();
      console.log('Devices data:', devicesData);
      setDevices(devicesData.devices || []);

      // Load access logs only once on initial load
      if (!logsInitialized) {
        const logsData = await apiService.getAccessLogs(50);
        console.log('Initial logs data:', logsData);
        setAccessLogs(logsData.logs || []);
        setLogsInitialized(true);
      }

    } catch (err) {
      console.error('Failed to load initial data:', err);
      setError('Failed to load device data: ' + err.message);
    } finally {
      setLoading(false);
    }
  }, [logsInitialized]);

  // Initialize on mount
  useEffect(() => {
    console.log('useAccessControl: Component mounted, loading data...');
    loadInitialData();
  }, [loadInitialData]);

  // Handle WebSocket connection
  useEffect(() => {
    const handleConnection = (data) => {
      console.log('Connection status changed:', data.status);
      setConnectionStatus(data.status);
      
      if (data.status === 'connected') {
        setError(null);
      }
    };

    const handleInitialData = (data) => {
      console.log('Received initial data:', data);
      if (data && data.devices) {
        setDevices(data.devices);
      }
    };

    const handleDeviceStateChange = (data) => {
      console.log('Device state changed:', data);
      if (data && data.device_id && data.new_state) {
        setDevices(prevDevices => 
          prevDevices.map(device => 
            device.door_id === data.device_id ? data.new_state : device
          )
        );
      }
    };

    const handleAccessEvent = (data) => {
      console.log('New access event via WebSocket:', data);
      if (data) {
        // Add new event to the beginning of the logs
        // Only keep the 50 most recent logs to prevent memory issues
        setAccessLogs(prevLogs => [data, ...prevLogs.slice(0, 49)]);
      }
    };

    const handleCommandResponse = (data) => {
      console.log('Command response:', data);
    };

    const handleError = (error) => {
      console.error('WebSocket error:', error);
      setError('WebSocket connection error');
    };

    // Register WebSocket event listeners
    webSocketService.on('connection', handleConnection);
    webSocketService.on('initial_data', handleInitialData);
    webSocketService.on('device_state_change', handleDeviceStateChange);
    webSocketService.on('access_event', handleAccessEvent);
    webSocketService.on('command_response', handleCommandResponse);
    webSocketService.on('error', handleError);

    // Connect to WebSocket
    webSocketService.connect();

    // Cleanup function
    return () => {
      webSocketService.off('connection', handleConnection);
      webSocketService.off('initial_data', handleInitialData);
      webSocketService.off('device_state_change', handleDeviceStateChange);
      webSocketService.off('access_event', handleAccessEvent);
      webSocketService.off('command_response', handleCommandResponse);
      webSocketService.off('error', handleError);
      webSocketService.disconnect();
    };
  }, []);

  // Send device command
  const sendCommand = useCallback((deviceId, command) => {
    if (connectionStatus !== 'connected') {
      setError('Cannot send command: WebSocket not connected');
      return;
    }
    
    try {
      webSocketService.sendCommand(deviceId, command);
    } catch (err) {
      console.error('Failed to send command:', err);
      setError('Failed to send command: ' + err.message);
    }
  }, [connectionStatus]);

  // Simulate access attempt (for testing)
  const simulateAccess = useCallback(async (deviceId, userId, command) => {
    try {
      await apiService.simulateAccessAttempt(deviceId, userId, command);
    } catch (err) {
      console.error('Failed to simulate access:', err);
      setError('Failed to simulate access attempt: ' + err.message);
    }
  }, []);

  // Reconnect WebSocket
  const reconnect = useCallback(() => {
    setLoading(true);
    setError(null);
    webSocketService.connect();
    loadInitialData();
  }, [loadInitialData]);

  // Refresh data
  const refresh = useCallback(async () => {
    try {
      // Only refresh devices, not logs (logs come from WebSocket)
      const devicesData = await apiService.getDevicesStatus();
      setDevices(devicesData.devices || []);
    } catch (err) {
      console.error('Failed to refresh data:', err);
      setError('Failed to refresh device data: ' + err.message);
    }
  }, []);

  return {
    devices,
    accessLogs,
    connectionStatus,
    loading,
    error,
    sendCommand,
    simulateAccess,
    reconnect,
    refresh,
    clearError: () => setError(null)
  };
};