/**
 * Agent Table component
 * Displays agent status and performance metrics
 */

import React from 'react';
import { Table, Badge } from 'react-bootstrap';

const AgentTable = ({ agents }) => {
  const getStatusBadge = (status) => {
    const statusConfig = {
      available: { bg: 'success', text: 'Tillgänglig', class: 'agent-available' },
      busy: { bg: 'warning', text: 'Upptagen', class: 'agent-busy' },
      unavailable: { bg: 'danger', text: 'Otillgänglig', class: 'agent-unavailable' },
      break: { bg: 'info', text: 'Paus', class: 'agent-break' },
      training: { bg: 'secondary', text: 'Utbildning', class: 'agent-training' }
    };

    const config = statusConfig[status] || statusConfig.unavailable;
    return (
      <Badge bg={config.bg} className={`agent-status ${config.class}`}>
        {config.text}
      </Badge>
    );
  };

  const formatDuration = (seconds) => {
    if (!seconds) return '-';
    
    if (seconds < 60) {
      return `${seconds}s`;
    }
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}m ${remainingSeconds}s`;
  };

  const formatAverage = (seconds) => {
    if (!seconds) return '-';
    return `${Math.round(seconds)}s`;
  };

  if (!agents || agents.length === 0) {
    return (
      <div className="text-center py-4">
        <i className="fas fa-user-slash fa-3x text-muted mb-3"></i>
        <p className="text-muted">Inga agenter att visa</p>
      </div>
    );
  }

  return (
    <div className="table-responsive">
      <Table className="table-custom mb-0" size="sm">
        <thead>
          <tr>
            <th>Agent</th>
            <th>Status</th>
            <th>Samtal</th>
            <th>Snitt</th>
          </tr>
        </thead>
        <tbody>
          {agents.map((agent) => (
            <tr key={agent.agent_id}>
              <td>
                <div className="fw-bold">{agent.name}</div>
                <small className="text-muted">ID: {agent.agent_id}</small>
              </td>
              <td>
                {getStatusBadge(agent.status)}
                {agent.current_call_duration && (
                  <div className="mt-1">
                    <small className="text-muted">
                      Samtal: {formatDuration(agent.current_call_duration)}
                    </small>
                  </div>
                )}
              </td>
              <td>
                <span className="fw-bold text-primary">
                  {agent.calls_handled_today || 0}
                </span>
                <div>
                  <small className="text-muted">idag</small>
                </div>
              </td>
              <td>
                <span className="text-muted">
                  {formatAverage(agent.average_call_time)}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </Table>
      
      <div className="mt-3 p-2 bg-light rounded">
        <small className="text-muted">
          <strong>Sammanfattning:</strong> {agents.length} agenter • {' '}
          {agents.filter(a => a.status === 'available').length} tillgängliga • {' '}
          {agents.filter(a => a.status === 'busy').length} upptagna
        </small>
      </div>
    </div>
  );
};

export default AgentTable;
