/**
 * DeviceCard - Simple component to display device status
 */
import React from 'react';

const DeviceCard = ({ device, onCommand }) => {
  const getStatusColor = (status) => {
    switch (status) {
      case 'open': return '#4CAF50';
      case 'closed': return '#757575';
      case 'locked': return '#F44336';
      case 'unlocked': return '#FF9800';
      default: return '#757575';
    }
  };

  const handleCommand = (command) => {
    onCommand(device.door_id, command);
  };

  return (
    <div className="device-card">
      <div className="device-header">
        <h3>{device.door_id}</h3>
        <span className="device-location">{device.location}</span>
      </div>
      
      <div className="device-status">
        <div className="status-item">
          <span className="status-label">Physical Status:</span>
          <span 
            className="status-value"
            style={{ color: getStatusColor(device.physical_status) }}
          >
            {device.physical_status?.toUpperCase()}
          </span>
        </div>
        
        <div className="status-item">
          <span className="status-label">Lock State:</span>
          <span 
            className="status-value"
            style={{ color: getStatusColor(device.lock_state) }}
          >
            {device.lock_state?.toUpperCase()}
          </span>
        </div>
      </div>
      
      <div className="device-controls">
        <div className="control-group">
          <span className="control-label">Physical Control:</span>
          <button
            className="control-btn open-btn"
            onClick={() => handleCommand('open')}
            disabled={device.physical_status === 'open'}
          >
            Open
          </button>
          <button
            className="control-btn close-btn"
            onClick={() => handleCommand('close')}
            disabled={device.physical_status === 'closed'}
          >
            Close
          </button>
        </div>
        
        <div className="control-group">
          <span className="control-label">Lock Control:</span>
          <button
            className="control-btn unlock-btn"
            onClick={() => handleCommand('unlock')}
            disabled={device.lock_state === 'unlocked'}
          >
            Unlock
          </button>
          <button
            className="control-btn lock-btn"
            onClick={() => handleCommand('lock')}
            disabled={device.lock_state === 'locked'}
          >
            Lock
          </button>
        </div>
      </div>
    </div>
  );
};

export default DeviceCard;