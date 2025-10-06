/**
 * EventLog - Simple component to display real-time access events
 */
import React from 'react';

const EventLog = ({ events, maxEvents = 20 }) => {
  const formatTimestamp = (timestamp) => {
    return new Date(timestamp).toLocaleString();
  };

  const getEventColor = (status) => {
    return status === 'granted' ? '#4CAF50' : '#F44336';
  };

  const getEventIcon = (command) => {
    switch (command?.toLowerCase()) {
      case 'open': return '🔓';
      case 'close': return '🔒';
      case 'lock': return '🔐';
      case 'unlock': return '🗝️';
      default: return '📋';
    }
  };

  // Show only the most recent events
  const displayEvents = events.slice(0, maxEvents);

  return (
    <div className="event-log">
      <h3>Real-time Event Log</h3>
      
      {displayEvents.length === 0 ? (
        <div className="no-events">
          <p>No events yet. Device interactions will appear here...</p>
        </div>
      ) : (
        <div className="events-container">
          {displayEvents.map((event, index) => (
            <div key={`${event.timestamp}-${index}`} className="event-item">
              <div className="event-header">
                <span className="event-icon">{getEventIcon(event.command)}</span>
                <span className="event-device">{event.device_id}</span>
                <span 
                  className="event-status"
                  style={{ color: getEventColor(event.status) }}
                >
                  {event.status?.toUpperCase()}
                </span>
              </div>
              
              <div className="event-details">
                <span className="event-command">
                  Command: {event.command}
                </span>
                <span className="event-user">
                  User: {event.user_id}
                </span>
              </div>
              
              <div className="event-timestamp">
                {formatTimestamp(event.timestamp)}
              </div>
              
              {event.message && (
                <div className="event-message">
                  {event.message}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default EventLog;