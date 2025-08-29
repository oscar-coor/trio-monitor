/**
 * Main App component for Trio Monitor
 * Real-time dashboard for call center monitoring
 */

import React, { useState, useEffect, useRef } from 'react';
import { Container, Row, Col, Alert } from 'react-bootstrap';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Dashboard from './components/Dashboard';
import Header from './components/Header';
import AlertContainer from './components/AlertContainer';
import ErrorBoundary from './components/ErrorBoundary';
import { AppProvider, useAppContext } from './context/AppContext';
import ApiService from './services/api';
import ServiceConfiguration from './components/admin/ServiceConfiguration';
import TaskManagement from './components/tasks/TaskManagement';
import './App.css';

// Main App component using Context
function AppContent() {
  const { state, actions } = useAppContext();
  const hasDataRef = useRef(false);

  // Poll data using user preferences
  useEffect(() => {
    const POLL_MS = state.userPreferences.pollingInterval;
    
    const fetchData = async () => {
      try {
        actions.setError(null);
        const data = await ApiService.getDashboardData();
        actions.setDashboardData(data);
        actions.setConnectionStatus('connected');
        hasDataRef.current = true;
      } catch (err) {
        console.error('Failed to fetch dashboard data:', err);
        actions.setError('Kunde inte hämta data från servern');
        actions.setConnectionStatus('disconnected');
        
        // Don't set loading to false on first error, keep trying
        if (!hasDataRef.current) {
          actions.setLoading(false);
        }
      }
    };

    // Only poll if auto refresh is enabled
    if (state.userPreferences.autoRefresh) {
      // Initial fetch
      fetchData();

      // Set up polling interval
      const interval = setInterval(fetchData, POLL_MS);

      // Cleanup
      return () => clearInterval(interval);
    }
  }, [state.userPreferences.pollingInterval, state.userPreferences.autoRefresh, actions]);

  // Health check on mount
  useEffect(() => {
    const checkHealth = async () => {
      try {
        await ApiService.healthCheck();
        actions.setConnectionStatus('connected');
      } catch (err) {
        actions.setConnectionStatus('disconnected');
      }
    };

    checkHealth();
  }, [actions]);

  const DashboardView = () => (
    <ErrorBoundary>
      <div className="dashboard-container">
        <Header />
        <Container fluid className="main-content">
          {state.loading && !state.dashboardData ? (
            <>
              <div className="loading-spinner">
                <div className="spinner-border spinner-border-custom text-primary" role="status">
                  <span className="visually-hidden">Laddar...</span>
                </div>
              </div>
              <div className="text-center mt-3">
                <h5>Ansluter till Trio Enterprise API...</h5>
                <p className="text-muted">Vänligen vänta medan systemet startar upp.</p>
              </div>
            </>
          ) : (
            <>
              {state.error && (
                <Row className="mb-3">
                  <Col>
                    <Alert variant="warning" className="d-flex align-items-center">
                      <i className="bi bi-exclamation-triangle-fill me-2"></i>
                      <div>
                        <strong>Anslutningsproblem:</strong> {state.error}
                        <br />
                        <small>Systemet försöker återansluta automatiskt...</small>
                      </div>
                    </Alert>
                  </Col>
                </Row>
              )}
              <ErrorBoundary>
                <Dashboard />
              </ErrorBoundary>
            </>
          )}
        </Container>
        <ErrorBoundary>
          <AlertContainer />
        </ErrorBoundary>
      </div>
    </ErrorBoundary>
  );

  const AdminView = () => (
    <ErrorBoundary>
      <div className="dashboard-container">
        <Header />
        <Container fluid className="main-content">
          <ErrorBoundary>
            <ServiceConfiguration />
          </ErrorBoundary>
        </Container>
      </div>
    </ErrorBoundary>
  );

  const TasksView = () => (
    <ErrorBoundary>
      <div className="dashboard-container">
        <Header />
        <Container fluid className="main-content">
          <ErrorBoundary>
            <TaskManagement />
          </ErrorBoundary>
        </Container>
      </div>
    </ErrorBoundary>
  );

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<DashboardView />} />
        <Route path="/admin" element={<AdminView />} />
        <Route path="/tasks" element={<TasksView />} />
      </Routes>
    </BrowserRouter>
  );
}

// Root App component with Provider
function App() {
  return (
    <AppProvider>
      <AppContent />
    </AppProvider>
  );
}

export default App;
