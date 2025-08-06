/**
 * Service Level Card component
 * Displays service level metrics with progress indicator
 */

import React from 'react';

const ServiceLevelCard = ({ serviceLevel }) => {
  const {
    service_level_percentage = 0,
    total_calls = 0,
    calls_answered_within_target = 0,
    total_queue_time = 0,
    queue_time_limit_breached = false
  } = serviceLevel;

  const target = 80; // 80% target
  const isAboveTarget = service_level_percentage >= target;
  const progressWidth = Math.min((service_level_percentage / target) * 100, 100);

  return (
    <div className={`status-card ${queue_time_limit_breached ? 'queue-critical' : isAboveTarget ? 'queue-good' : 'queue-warning'}`}>
      <div className="status-card-header">
        <h6 className="status-card-title">Servicenivå</h6>
        <i className="fas fa-chart-line"></i>
      </div>
      <div className="d-flex align-items-baseline">
        <h2 className="status-card-value">{service_level_percentage.toFixed(1)}</h2>
        <span className="status-card-unit">%</span>
      </div>
      
      <div className="progress-custom mt-2 mb-2">
        <div 
          className={`progress-bar ${isAboveTarget ? 'progress-bar-good' : 'progress-bar-warning'}`}
          style={{ width: `${progressWidth}%` }}
        ></div>
      </div>
      
      <div className="status-card-change">
        <small>
          {isAboveTarget ? (
            <span className="text-success">
              <i className="fas fa-arrow-up me-1"></i>
              Över mål ({target}%)
            </span>
          ) : (
            <span className="text-warning">
              <i className="fas fa-arrow-down me-1"></i>
              Under mål ({target}%)
            </span>
          )}
        </small>
      </div>
      
      <div className="mt-2">
        <small className="text-muted d-block">
          {calls_answered_within_target} av {total_calls} samtal
        </small>
        {queue_time_limit_breached && (
          <small className="text-danger d-block">
            <i className="fas fa-exclamation-triangle me-1"></i>
            Daglig gräns överskriden ({total_queue_time}s)
          </small>
        )}
      </div>
    </div>
  );
};

export default ServiceLevelCard;
