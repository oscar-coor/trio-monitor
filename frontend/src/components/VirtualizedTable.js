/**
 * Virtualized table component for handling large datasets efficiently
 * Uses react-window for performance optimization
 */

import React, { useMemo } from 'react';
import { FixedSizeList as List } from 'react-window';
import { Table } from 'react-bootstrap';

const VirtualizedTable = ({ 
  data, 
  columns, 
  rowHeight = 50, 
  height = 400,
  className = "",
  onRowClick = null
}) => {
  const memoizedData = useMemo(() => data, [data]);

  const Row = ({ index, style }) => {
    const item = memoizedData[index];
    
    return (
      <div 
        style={style} 
        className={`d-flex align-items-center border-bottom ${onRowClick ? 'cursor-pointer' : ''}`}
        onClick={() => onRowClick && onRowClick(item)}
      >
        {columns.map((column, colIndex) => (
          <div 
            key={colIndex}
            className={`flex-fill px-2 ${column.className || ''}`}
            style={{ 
              minWidth: column.width || 'auto',
              maxWidth: column.width || 'none'
            }}
          >
            {column.render ? column.render(item) : item[column.key]}
          </div>
        ))}
      </div>
    );
  };

  const Header = () => (
    <div className="d-flex bg-light border-bottom fw-bold py-2">
      {columns.map((column, index) => (
        <div 
          key={index}
          className={`flex-fill px-2 ${column.headerClassName || ''}`}
          style={{ 
            minWidth: column.width || 'auto',
            maxWidth: column.width || 'none'
          }}
        >
          {column.title}
        </div>
      ))}
    </div>
  );

  if (!memoizedData || memoizedData.length === 0) {
    return (
      <div className={`border rounded ${className}`}>
        <Header />
        <div className="text-center py-4 text-muted">
          Inga data att visa
        </div>
      </div>
    );
  }

  return (
    <div className={`border rounded ${className}`}>
      <Header />
      <List
        height={height}
        itemCount={memoizedData.length}
        itemSize={rowHeight}
        overscanCount={5}
      >
        {Row}
      </List>
    </div>
  );
};

// Specialized component for agent table
export const VirtualizedAgentTable = ({ agents }) => {
  const columns = [
    {
      key: 'name',
      title: 'Agent',
      width: '200px',
      render: (agent) => (
        <div>
          <strong>{agent.name}</strong>
          <br />
          <small className="text-muted">ID: {agent.agent_id}</small>
        </div>
      )
    },
    {
      key: 'status',
      title: 'Status',
      width: '120px',
      render: (agent) => {
        const statusColors = {
          available: 'success',
          busy: 'warning',
          unavailable: 'danger',
          break: 'info'
        };
        return (
          <span className={`badge bg-${statusColors[agent.status] || 'secondary'}`}>
            {agent.status}
          </span>
        );
      }
    },
    {
      key: 'calls_handled_today',
      title: 'Samtal idag',
      width: '100px'
    },
    {
      key: 'average_call_time',
      title: 'Snitt samtaltid',
      width: '120px',
      render: (agent) => agent.average_call_time ? `${Math.round(agent.average_call_time)}s` : '-'
    },
    {
      key: 'current_call_duration',
      title: 'Pågående samtal',
      render: (agent) => agent.current_call_duration ? `${Math.round(agent.current_call_duration)}s` : '-'
    }
  ];

  return <VirtualizedTable data={agents} columns={columns} />;
};

// Specialized component for queue table
export const VirtualizedQueueTable = ({ queues }) => {
  const columns = [
    {
      key: 'queue_name',
      title: 'Kö',
      width: '200px'
    },
    {
      key: 'status',
      title: 'Status',
      width: '100px',
      render: (queue) => {
        const statusColors = {
          good: 'success',
          warning: 'warning',
          critical: 'danger'
        };
        return (
          <span className={`badge bg-${statusColors[queue.status] || 'secondary'}`}>
            {queue.status}
          </span>
        );
      }
    },
    {
      key: 'calls_waiting',
      title: 'Väntande',
      width: '100px'
    },
    {
      key: 'current_wait_time',
      title: 'Väntetid',
      width: '100px',
      render: (queue) => `${queue.current_wait_time}s`
    },
    {
      key: 'longest_wait_time',
      title: 'Längsta väntetid',
      width: '120px',
      render: (queue) => `${queue.longest_wait_time}s`
    },
    {
      key: 'average_wait_time',
      title: 'Snitt väntetid',
      render: (queue) => `${Math.round(queue.average_wait_time)}s`
    }
  ];

  return <VirtualizedTable data={queues} columns={columns} />;
};

export default VirtualizedTable;
