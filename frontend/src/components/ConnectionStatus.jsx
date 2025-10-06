/**
 * ConnectionStatus - Simple component to show WebSocket connection status
 */
import React from 'react';

const ConnectionStatus = ({ status, onReconnect }) => {
  const getStatusColor = () => {
    switch (status) {
      case 'connected': return '#4CAF50';
      case 'connecting': return '#FF9800';
      case 'disconnected': return '#F44336';
      case 'failed': return '#D32F2F';
      default: return '#757575';
    }
  };

  const getStatusIcon = () => {
    switch (status) {
      case 'connected': return '✅';
      case 'connecting': return '🔄';
      case 'disconnected': return '❌';
      case 'failed': return '🚫';
      default: return '❓';
    }
  };

  const getStatusText = () => {
    switch (status) {
      case 'connected': return 'Connected';
      case 'connecting': return 'Connecting...';
      case 'disconnected': return 'Disconnected';
      case 'failed': return 'Connection Failed';
      default: return 'Unknown';
    }
  };

  return (
    <div className="connection-status">
      <span className="status-icon">{getStatusIcon()}</span>
      <span 
        className="status-text"
        style={{ color: getStatusColor() }}
      >
        {getStatusText()}
      </span>
      
      {(status === 'disconnected' || status === 'failed') && (
        <button 
          className="reconnect-btn"
          onClick={onReconnect}
        >
          Reconnect
        </button>
      )}
    </div>
  );
};

export default ConnectionStatus;