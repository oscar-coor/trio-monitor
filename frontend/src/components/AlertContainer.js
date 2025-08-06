/**
 * Alert Container component
 * Displays real-time alerts and notifications
 */

import React, { useState, useEffect } from 'react';
import { Alert, Button } from 'react-bootstrap';

const AlertContainer = ({ alerts }) => {
  const [visibleAlerts, setVisibleAlerts] = useState([]);

  useEffect(() => {
    if (alerts && alerts.length > 0) {
      // Convert string alerts to objects if needed
      const alertObjects = alerts.map((alert, index) => {
        if (typeof alert === 'string') {
          return {
            id: `alert_${index}_${Date.now()}`,
            message: alert,
            type: alert.toLowerCase().includes('kritisk') ? 'critical' : 
                  alert.toLowerCase().includes('varning') ? 'warning' : 'info',
            timestamp: new Date()
          };
        }
        return alert;
      });

      setVisibleAlerts(alertObjects);
    } else {
      setVisibleAlerts([]);
    }
  }, [alerts]);

  const dismissAlert = (alertId) => {
    setVisibleAlerts(prev => prev.filter(alert => alert.id !== alertId));
  };

  const getAlertVariant = (type) => {
    switch (type) {
      case 'critical':
        return 'danger';
      case 'warning':
        return 'warning';
      case 'info':
      default:
        return 'info';
    }
  };

  const getAlertIcon = (type) => {
    switch (type) {
      case 'critical':
        return 'fas fa-exclamation-circle';
      case 'warning':
        return 'fas fa-exclamation-triangle';
      case 'info':
      default:
        return 'fas fa-info-circle';
    }
  };

  if (!visibleAlerts || visibleAlerts.length === 0) {
    return null;
  }

  return (
    <div className="alert-container">
      {visibleAlerts.map((alert) => (
        <Alert
          key={alert.id}
          variant={getAlertVariant(alert.type)}
          className={`alert-item alert-${alert.type}`}
          dismissible
          onClose={() => dismissAlert(alert.id)}
        >
          <div className="d-flex align-items-start">
            <i className={`${getAlertIcon(alert.type)} me-2 mt-1`}></i>
            <div className="flex-grow-1">
              <div className="fw-bold">
                {alert.type === 'critical' ? 'KRITISK VARNING' : 
                 alert.type === 'warning' ? 'VARNING' : 'INFORMATION'}
              </div>
              <div>{alert.message}</div>
              {alert.timestamp && (
                <small className="text-muted">
                  {alert.timestamp.toLocaleTimeString('sv-SE')}
                </small>
              )}
            </div>
          </div>
        </Alert>
      ))}
    </div>
  );
};

export default AlertContainer;
