/**
 * Header component for Trio Monitor dashboard
 * Displays title, connection status, and last update time
 */

import React from 'react';
import { Navbar, Container, Badge, Button } from 'react-bootstrap';
import { Link, useLocation } from 'react-router-dom';
import { format } from 'date-fns';
import { sv } from 'date-fns/locale';

const Header = ({ connectionStatus, lastUpdated }) => {
  const location = useLocation();
  const onAdmin = location.pathname.startsWith('/admin');
  const getConnectionBadge = () => {
    switch (connectionStatus) {
      case 'connected':
        return (
          <Badge bg="success" className="connection-indicator connection-connected">
            <span className="status-indicator status-online"></span>
            Ansluten
          </Badge>
        );
      case 'connecting':
        return (
          <Badge bg="warning" className="connection-indicator connection-connecting">
            <span className="status-indicator status-offline"></span>
            Ansluter...
          </Badge>
        );
      case 'disconnected':
      default:
        return (
          <Badge bg="danger" className="connection-indicator connection-disconnected">
            <span className="status-indicator status-offline"></span>
            Frånkopplad
          </Badge>
        );
    }
  };

  const formatLastUpdated = () => {
    if (!lastUpdated) return 'Aldrig';
    
    try {
      return format(lastUpdated, 'HH:mm:ss', { locale: sv });
    } catch (error) {
      return 'Okänd';
    }
  };

  return (
    <Navbar className="dashboard-header" variant="dark">
      <Container fluid>
        <Navbar.Brand>
          <div>
            <h1 className="header-title">
              Trio Monitor
              <small className="ms-3">{getConnectionBadge()}</small>
            </h1>
            <p className="header-subtitle">
              Realtidsövervakning av kötider • Senast uppdaterad: {formatLastUpdated()}
            </p>
          </div>
        </Navbar.Brand>
        
        <div className="d-flex align-items-center text-light gap-3">
          <div className="text-end me-2">
            <div className="fw-bold">20-Sekunders Gräns</div>
            <small className="opacity-75">Servicenivå: 80% mål</small>
          </div>
          <Link to={onAdmin ? '/' : '/admin'}>
            <Button variant={onAdmin ? 'outline-light' : 'light'} size="sm">
              {onAdmin ? 'Till Dashboard' : 'Administration'}
            </Button>
          </Link>
        </div>
      </Container>
    </Navbar>
  );
};

export default Header;
