/**
 * Alert Container component
 * Displays real-time alerts and notifications
 */

import React, { useState, useEffect, useRef } from 'react';
import { Alert } from 'react-bootstrap';

const AlertContainer = ({ alerts }) => {
  const [visibleAlerts, setVisibleAlerts] = useState([]);
  // Suppress re-showing dismissed/duplicate alerts for a short period
  const suppressedRef = useRef(new Map()); // key -> expiry timestamp (ms)
  const SUPPRESS_TTL_MS = 15000; // 15s suppression window

  const deriveStableKey = (message, type) => {
    if (!message) return `${type}:unknown`;
    const msg = String(message);
    // Daily limit breach
    if (msg.startsWith('KRITISK: Daglig kötidsgräns överskriden')) {
      return 'critical:daily_limit';
    }
    // Service level below target
    if (msg.startsWith('Servicenivå under mål')) {
      return 'service_level:below_target';
    }
    // Queue critical: "KRITISK: <queue> har väntetid över ..."
    const critMatch = msg.match(/^KRITISK:\s+(.+?)\s+har väntetid/);
    if (critMatch && critMatch[1]) {
      const queueName = critMatch[1].trim();
      return `critical:queue:${queueName}`;
    }
    // Queue warning: "VARNING: <queue> närmar sig gränsen"
    const warnMatch = msg.match(/^VARNING:\s+(.+?)\s+närmar sig gränsen/);
    if (warnMatch && warnMatch[1]) {
      const queueName = warnMatch[1].trim();
      return `warning:queue:${queueName}`;
    }
    // Fallback to message-based key
    return `${type}:${msg}`;
  };

  const normalizeAlert = (alert, index) => {
    if (typeof alert === 'string') {
      const lower = alert.toLowerCase();
      const type = lower.includes('kritisk') ? 'critical' : lower.includes('varning') ? 'warning' : 'info';
      const key = deriveStableKey(alert, type);
      return {
        id: key, // stable id
        key,
        message: alert,
        type,
        timestamp: new Date()
      };
    }
    // Ensure stable key for object alerts
    const type = alert.type || 'info';
    const message = alert.message || '';
    const key = alert.id || deriveStableKey(message, type);
    return {
      id: key,
      key,
      message,
      type,
      timestamp: alert.timestamp ? new Date(alert.timestamp) : new Date()
    };
  };

  useEffect(() => {
    if (!alerts) return;

    const now = Date.now();
    // Cleanup expired suppressions
    for (const [k, exp] of suppressedRef.current.entries()) {
      if (exp <= now) suppressedRef.current.delete(k);
    }

    const incoming = alerts.map(normalizeAlert);

    setVisibleAlerts(prev => {
      const existingById = new Map(prev.map(a => [a.id, a]));
      const next = [...prev];

      for (const a of incoming) {
        // Skip if suppressed
        const suppressedUntil = suppressedRef.current.get(a.id);
        if (suppressedUntil && suppressedUntil > now) continue;
        // Add only if not already visible
        if (!existingById.has(a.id)) {
          next.push(a);
          existingById.set(a.id, a);
        }
      }
      return next;
    });
  }, [alerts]);

  const dismissAlert = (alertId) => {
    // Suppress this alert for a period so it doesn't immediately reappear
    suppressedRef.current.set(alertId, Date.now() + SUPPRESS_TTL_MS);
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
