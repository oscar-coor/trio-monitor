/**
 * Queue Table component
 * Displays detailed queue metrics in a responsive table
 */

import React from 'react';
import { Table, Badge } from 'react-bootstrap';

const QueueTable = ({ queues }) => {
  const getStatusBadge = (status, waitTime) => {
    switch (status) {
      case 'critical':
        return <Badge bg="danger" className="px-2 py-1">Kritisk</Badge>;
      case 'warning':
        return <Badge bg="warning" text="dark" className="px-2 py-1">Varning</Badge>;
      case 'good':
      default:
        return <Badge bg="success" className="px-2 py-1">Bra</Badge>;
    }
  };

  const formatWaitTime = (seconds) => {
    if (seconds < 60) {
      return `${seconds}s`;
    }
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}m ${remainingSeconds}s`;
  };

  if (!queues || queues.length === 0) {
    return (
      <div className="text-center py-4">
        <i className="fas fa-inbox fa-3x text-muted mb-3"></i>
        <p className="text-muted">Inga köer att visa</p>
      </div>
    );
  }

  return (
    <div className="table-responsive">
      <Table className="table-custom mb-0">
        <thead>
          <tr>
            <th>Kö</th>
            <th>Status</th>
            <th>Väntetid</th>
            <th>Ködjup</th>
            <th>Väntande</th>
            <th>Snitt</th>
            <th>Längsta</th>
          </tr>
        </thead>
        <tbody>
          {queues.map((queue) => (
            <tr key={queue.queue_id}>
              <td>
                <div className="fw-bold">{queue.queue_name}</div>
                <small className="text-muted">ID: {queue.queue_id}</small>
              </td>
              <td>
                {getStatusBadge(queue.status, queue.current_wait_time)}
              </td>
              <td>
                <div className={`fw-bold ${
                  queue.current_wait_time >= 20 ? 'text-danger' : 
                  queue.current_wait_time >= 15 ? 'text-warning' : 
                  'text-success'
                }`}>
                  {formatWaitTime(queue.current_wait_time || 0)}
                </div>
              </td>
              <td>
                <span className="badge bg-light text-dark">
                  {queue.queue_depth || 0}
                </span>
              </td>
              <td>
                <span className="fw-bold">
                  {queue.calls_waiting || 0}
                </span>
              </td>
              <td>
                <span className="text-muted">
                  {formatWaitTime(Math.round(queue.average_wait_time || 0))}
                </span>
              </td>
              <td>
                <span className={`fw-bold ${
                  (queue.longest_wait_time || 0) >= 20 ? 'text-danger' : 
                  (queue.longest_wait_time || 0) >= 15 ? 'text-warning' : 
                  'text-success'
                }`}>
                  {formatWaitTime(queue.longest_wait_time || 0)}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </Table>
    </div>
  );
};

export default QueueTable;
