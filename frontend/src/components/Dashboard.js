/**
 * Main Dashboard component for Trio Monitor
 * Displays real-time metrics, queue status, and agent information
 */

import React from 'react';
import { Row, Col } from 'react-bootstrap';
import QueueStatusCards from './QueueStatusCards';
import ServiceLevelCard from './ServiceLevelCard';
import AgentTable from './AgentTable';
import QueueTable from './QueueTable';
import MetricsChart from './MetricsChart';

const Dashboard = ({ data }) => {
  if (!data) {
    return (
      <div className="text-center py-5">
        <div className="spinner-border spinner-border-custom text-primary" role="status">
          <span className="visually-hidden">Laddar dashboard...</span>
        </div>
        <div className="mt-3">
          <h5>Laddar dashboard data...</h5>
        </div>
      </div>
    );
  }

  const { agents = [], queues = [], service_level = {} } = data;

  // Calculate summary statistics
  const totalAgents = agents.length;
  const availableAgents = agents.filter(agent => agent.status === 'available').length;
  const busyAgents = agents.filter(agent => agent.status === 'busy').length;
  const totalCallsWaiting = queues.reduce((sum, queue) => sum + (queue.calls_waiting || 0), 0);
  const maxWaitTime = Math.max(...queues.map(queue => queue.current_wait_time || 0), 0);
  
  // Queue status counts
  const criticalQueues = queues.filter(queue => queue.status === 'critical').length;
  const warningQueues = queues.filter(queue => queue.status === 'warning').length;
  const goodQueues = queues.filter(queue => queue.status === 'good').length;

  return (
    <div className="dashboard-content">
      {/* Top Level Metrics */}
      <Row className="dashboard-row">
        <Col lg={3} md={6} className="mb-3">
          <div className="status-card">
            <div className="status-card-header">
              <h6 className="status-card-title">Totala Agenter</h6>
              <i className="fas fa-users text-primary"></i>
            </div>
            <div className="d-flex align-items-baseline">
              <h2 className="status-card-value text-primary">{totalAgents}</h2>
            </div>
            <div className="status-card-change text-success">
              <small>
                <i className="fas fa-check-circle me-1"></i>
                {availableAgents} tillgängliga • {busyAgents} upptagna
              </small>
            </div>
          </div>
        </Col>

        <Col lg={3} md={6} className="mb-3">
          <div className="status-card">
            <div className="status-card-header">
              <h6 className="status-card-title">Väntande Samtal</h6>
              <i className="fas fa-phone text-warning"></i>
            </div>
            <div className="d-flex align-items-baseline">
              <h2 className="status-card-value text-warning">{totalCallsWaiting}</h2>
            </div>
            <div className="status-card-change">
              <small className="text-muted">
                <i className="fas fa-clock me-1"></i>
                Max väntetid: {maxWaitTime}s
              </small>
            </div>
          </div>
        </Col>

        <Col lg={3} md={6} className="mb-3">
          <div className={`status-card ${maxWaitTime >= 20 ? 'queue-critical' : maxWaitTime >= 15 ? 'queue-warning' : 'queue-good'}`}>
            <div className="status-card-header">
              <h6 className="status-card-title">Längsta Väntetid</h6>
              <i className="fas fa-stopwatch"></i>
            </div>
            <div className="d-flex align-items-baseline">
              <h2 className="status-card-value">{maxWaitTime}</h2>
              <span className="status-card-unit">sek</span>
            </div>
            <div className="status-card-change">
              <small>
                {maxWaitTime >= 20 ? (
                  <span className="text-danger">
                    <i className="fas fa-exclamation-triangle me-1"></i>
                    Över gränsen!
                  </span>
                ) : maxWaitTime >= 15 ? (
                  <span className="text-warning">
                    <i className="fas fa-exclamation-circle me-1"></i>
                    Närmar sig gränsen
                  </span>
                ) : (
                  <span className="text-success">
                    <i className="fas fa-check-circle me-1"></i>
                    Under gränsen
                  </span>
                )}
              </small>
            </div>
          </div>
        </Col>

        <Col lg={3} md={6} className="mb-3">
          <ServiceLevelCard serviceLevel={service_level} />
        </Col>
      </Row>

      {/* Queue Status Overview */}
      <Row className="dashboard-row">
        <Col>
          <QueueStatusCards 
            queues={queues}
            criticalCount={criticalQueues}
            warningCount={warningQueues}
            goodCount={goodQueues}
          />
        </Col>
      </Row>

      {/* Main Content Grid */}
      <Row className="dashboard-row">
        <Col lg={8} className="mb-4">
          <div className="status-card">
            <div className="status-card-header">
              <h5 className="status-card-title mb-0">Köstatus i Realtid</h5>
            </div>
            <QueueTable queues={queues} />
          </div>
        </Col>

        <Col lg={4} className="mb-4">
          <div className="status-card">
            <div className="status-card-header">
              <h5 className="status-card-title mb-0">Agentstatus</h5>
            </div>
            <AgentTable agents={agents} />
          </div>
        </Col>
      </Row>

      {/* Charts Row */}
      <Row className="dashboard-row">
        <Col>
          <div className="status-card">
            <div className="status-card-header">
              <h5 className="status-card-title mb-0">Väntetider Senaste Timmen</h5>
            </div>
            <MetricsChart queues={queues} />
          </div>
        </Col>
      </Row>
    </div>
  );
};

export default Dashboard;
