/**
 * Queue Status Cards component
 * Displays overview of queue status with color-coded indicators
 */

import React from 'react';
import { Row, Col, Card } from 'react-bootstrap';

const QueueStatusCards = ({ queues, criticalCount, warningCount, goodCount }) => {
  const totalQueues = queues.length;

  return (
    <Row>
      <Col md={4} className="mb-3">
        <Card className="status-card queue-good h-100">
          <Card.Body className="text-center">
            <div className="d-flex justify-content-between align-items-center mb-2">
              <h6 className="status-card-title">Bra Köer</h6>
              <i className="fas fa-check-circle fa-2x text-success"></i>
            </div>
            <h2 className="status-card-value text-success">{goodCount}</h2>
            <small className="text-muted">
              <15 sekunder väntetid
            </small>
            <div className="progress-custom mt-2">
              <div 
                className="progress-bar progress-bar-good" 
                style={{ width: `${totalQueues > 0 ? (goodCount / totalQueues) * 100 : 0}%` }}
              ></div>
            </div>
          </Card.Body>
        </Card>
      </Col>

      <Col md={4} className="mb-3">
        <Card className="status-card queue-warning h-100">
          <Card.Body className="text-center">
            <div className="d-flex justify-content-between align-items-center mb-2">
              <h6 className="status-card-title">Varning</h6>
              <i className="fas fa-exclamation-triangle fa-2x text-warning"></i>
            </div>
            <h2 className="status-card-value text-warning">{warningCount}</h2>
            <small className="text-muted">
              15-20 sekunder väntetid
            </small>
            <div className="progress-custom mt-2">
              <div 
                className="progress-bar progress-bar-warning" 
                style={{ width: `${totalQueues > 0 ? (warningCount / totalQueues) * 100 : 0}%` }}
              ></div>
            </div>
          </Card.Body>
        </Card>
      </Col>

      <Col md={4} className="mb-3">
        <Card className="status-card queue-critical h-100">
          <Card.Body className="text-center">
            <div className="d-flex justify-content-between align-items-center mb-2">
              <h6 className="status-card-title">Kritisk</h6>
              <i className="fas fa-exclamation-circle fa-2x text-danger"></i>
            </div>
            <h2 className="status-card-value text-danger">{criticalCount}</h2>
            <small className="text-muted">
              >20 sekunder väntetid
            </small>
            <div className="progress-custom mt-2">
              <div 
                className="progress-bar progress-bar-critical" 
                style={{ width: `${totalQueues > 0 ? (criticalCount / totalQueues) * 100 : 0}%` }}
              ></div>
            </div>
          </Card.Body>
        </Card>
      </Col>
    </Row>
  );
};

export default QueueStatusCards;
