/**
 * WebSocket service for real-time communication with the backend
 */
import { io } from 'socket.io-client';

class WebSocketService {
  constructor() {
    this.socket = null;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.reconnectInterval = 3000;
    this.eventListeners = new Map();
    this.isConnecting = false; // Prevent multiple simultaneous connections
  }

  connect() {
    // Prevent multiple connections
    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
      console.log('🔍 CONNECT: Already connected, skipping');
      return;
    }
    
    if (this.isConnecting) {
      console.log('🔍 CONNECT: Already connecting, skipping');
      return;
    }
    
    this.isConnecting = true;
    
    try {
      // Use native WebSocket since our backend uses native WebSocket, not Socket.IO
      this.socket = new WebSocket('ws://localhost:5000/ws');
      
      this.socket.onopen = () => {
        console.log('🔍 CONNECT: Connected to WebSocket server');
        this.reconnectAttempts = 0;
        this.isConnecting = false;
        this.emit('connection', { status: 'connected' });
        
        // Request initial status after a small delay
        setTimeout(() => {
          this.send({
            type: 'ping'
          });
        }, 100);
      };

      this.socket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          console.log('🔍 RECEIVED: WebSocket message:', data);
          
          // Emit specific events based on message type
          if (data.type) {
            this.emit(data.type, data.data);
          }
          
          // 🔥 REMOVED: Don't emit generic 'message' event to avoid duplication
          // this.emit('message', data);
          
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };

      this.socket.onclose = () => {
        console.log('🔍 CLOSE: WebSocket connection closed');
        this.isConnecting = false;
        this.emit('connection', { status: 'disconnected' });
        this.handleReconnect();
      };

      this.socket.onerror = (error) => {
        console.error('🔍 ERROR: WebSocket error:', error);
        this.isConnecting = false;
        this.emit('error', error);
      };

    } catch (error) {
      console.error('🔍 ERROR: Failed to connect to WebSocket:', error);
      this.isConnecting = false;
      this.emit('error', error);
    }
  }

  disconnect() {
    if (this.socket) {
      console.log('🔍 DISCONNECT: Closing WebSocket connection');
      this.socket.close();
      this.socket = null;
    }
    this.isConnecting = false;
  }

  send(message) {
    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
      this.socket.send(JSON.stringify(message));
      console.log('Sent message:', message);
    } else {
      console.warn('WebSocket is not connected');
    }
  }

  // Send device command
  sendCommand(deviceId, command, userId = 'admin') {
    this.send({
      type: 'command',
      device_id: deviceId,
      command: command,
      user_id: userId
    });
  }

  // Send ping
  sendPing() {
    this.send({
      type: 'ping'
    });
  }

  handleReconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      console.log(`Attempting to reconnect... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
      
      setTimeout(() => {
        this.connect();
      }, this.reconnectInterval);
    } else {
      console.error('Max reconnection attempts reached');
      this.emit('connection', { status: 'failed' });
    }
  }

  // Event listener management
  on(event, callback) {
    if (!this.eventListeners.has(event)) {
      this.eventListeners.set(event, []);
    }
    this.eventListeners.get(event).push(callback);
    console.log(`🔍 ON: Added listener for '${event}'. Total listeners: ${this.eventListeners.get(event).length}`);
  }

  off(event, callback) {
    if (this.eventListeners.has(event)) {
      const listeners = this.eventListeners.get(event);
      const index = listeners.indexOf(callback);
      if (index > -1) {
        listeners.splice(index, 1);
        console.log(`🔍 OFF: Removed listener for '${event}'. Remaining listeners: ${listeners.length}`);
      } else {
        console.log(`🔍 OFF: Listener not found for '${event}'`);
      }
    } else {
      console.log(`🔍 OFF: No listeners registered for '${event}'`);
    }
  }

  emit(event, data) {
    if (this.eventListeners.has(event)) {
      const listeners = this.eventListeners.get(event);
      console.log(`🔍 EMIT: Event '${event}' to ${listeners.length} listeners:`, data);
      listeners.forEach((callback, index) => {
        try {
          console.log(`🔍 EMIT: Calling listener ${index + 1} for '${event}'`);
          callback(data);
        } catch (error) {
          console.error(`Error in event listener for ${event}:`, error);
        }
      });
    } else {
      console.log(`🔍 EMIT: No listeners for event '${event}'`);
    }
  }

  getConnectionStatus() {
    if (!this.socket) return 'disconnected';
    
    switch (this.socket.readyState) {
      case WebSocket.CONNECTING: return 'connecting';
      case WebSocket.OPEN: return 'connected';
      case WebSocket.CLOSING: return 'closing';
      case WebSocket.CLOSED: return 'disconnected';
      default: return 'unknown';
    }
  }
}

// Export singleton instance
export const webSocketService = new WebSocketService();