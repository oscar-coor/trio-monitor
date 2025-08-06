/**
 * Main App component for Trio Monitor
 * Real-time dashboard for call center monitoring
 */

import React, { useState, useEffect } from 'react';
import { Container, Row, Col, Alert } from 'react-bootstrap';
import Dashboard from './components/Dashboard';
import Header from './components/Header';
import AlertContainer from './components/AlertContainer';
import ApiService from './services/api';
import './App.css';

function App() {
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);
  const [connectionStatus, setConnectionStatus] = useState('connecting');

  // Poll data every 10 seconds
  useEffect(() => {
    const fetchData = async () => {
      try {
        setError(null);
        const data = await ApiService.getDashboardData();
        setDashboardData(data);
        setLastUpdated(new Date());
        setConnectionStatus('connected');
        setLoading(false);
      } catch (err) {
        console.error('Failed to fetch dashboard data:', err);
        setError('Kunde inte hämta data från servern');
        setConnectionStatus('disconnected');
        
        // Don't set loading to false on first error, keep trying
        if (!dashboardData) {
          setLoading(false);
        }
      }
    };

    // Initial fetch
    fetchData();

    // Set up polling interval
    const interval = setInterval(fetchData, 10000); // 10 seconds

    // Cleanup
    return () => clearInterval(interval);
  }, [dashboardData]);

  // Health check on mount
  useEffect(() => {
    const checkHealth = async () => {
      try {
        await ApiService.healthCheck();
        setConnectionStatus('connected');
      } catch (err) {
        setConnectionStatus('disconnected');
      }
    };

    checkHealth();
  }, []);

  if (loading && !dashboardData) {
    return (
      <div className="dashboard-container">
        <Header 
          connectionStatus={connectionStatus}
          lastUpdated={lastUpdated}
        />
        <Container fluid className="main-content">
          <div className="loading-spinner">
            <div className="spinner-border spinner-border-custom text-primary" role="status">
              <span className="visually-hidden">Laddar...</span>
            </div>
          </div>
          <div className="text-center mt-3">
            <h5>Ansluter till Trio Enterprise API...</h5>
            <p className="text-muted">Vänligen vänta medan systemet startar upp.</p>
          </div>
        </Container>
      </div>
    );
  }

  return (
    <div className="dashboard-container">
      <Header 
        connectionStatus={connectionStatus}
        lastUpdated={lastUpdated}
      />
      
      <Container fluid className="main-content">
        {error && (
          <Row className="mb-3">
            <Col>
              <Alert variant="warning" className="d-flex align-items-center">
                <i className="bi bi-exclamation-triangle-fill me-2"></i>
                <div>
                  <strong>Anslutningsproblem:</strong> {error}
                  <br />
                  <small>Systemet försöker återansluta automatiskt...</small>
                </div>
              </Alert>
            </Col>
          </Row>
        )}
        
        <Dashboard data={dashboardData} />
      </Container>
      
      <AlertContainer alerts={dashboardData?.alerts || []} />
    </div>
  );
}

export default App;
