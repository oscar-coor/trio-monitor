/**
 * Error Boundary component for catching and handling React errors gracefully
 */

import React from 'react';
import { Alert, Button, Container, Row, Col } from 'react-bootstrap';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { 
      hasError: false, 
      error: null, 
      errorInfo: null,
      errorId: null
    };
  }

  static getDerivedStateFromError(error) {
    // Update state so the next render will show the fallback UI
    return { 
      hasError: true, 
      errorId: Date.now().toString(36) + Math.random().toString(36).substr(2)
    };
  }

  componentDidCatch(error, errorInfo) {
    // Log error details
    console.error('Error caught by boundary:', error, errorInfo);
    
    this.setState({
      error: error,
      errorInfo: errorInfo
    });

    // Report error to monitoring service (if available)
    this.reportError(error, errorInfo);
  }

  reportError = (error, errorInfo) => {
    // In production, send to error reporting service
    const errorReport = {
      message: error.message,
      stack: error.stack,
      componentStack: errorInfo.componentStack,
      timestamp: new Date().toISOString(),
      userAgent: navigator.userAgent,
      url: window.location.href,
      errorId: this.state.errorId
    };

    // For now, just log to console
    console.error('Error Report:', errorReport);
    
    // TODO: Send to actual error reporting service
    // fetch('/api/errors', { method: 'POST', body: JSON.stringify(errorReport) });
  };

  handleReload = () => {
    window.location.reload();
  };

  handleReset = () => {
    this.setState({ 
      hasError: false, 
      error: null, 
      errorInfo: null,
      errorId: null 
    });
  };

  render() {
    if (this.state.hasError) {
      const { fallback: CustomFallback } = this.props;
      
      // Use custom fallback if provided
      if (CustomFallback) {
        return (
          <CustomFallback 
            error={this.state.error}
            errorInfo={this.state.errorInfo}
            onReset={this.handleReset}
            onReload={this.handleReload}
          />
        );
      }

      // Default error UI
      return (
        <Container className="mt-4">
          <Row className="justify-content-center">
            <Col md={8} lg={6}>
              <Alert variant="danger" className="text-center">
                <Alert.Heading>
                  <i className="bi bi-exclamation-triangle-fill me-2"></i>
                  Något gick fel
                </Alert.Heading>
                
                <p className="mb-3">
                  Ett oväntat fel inträffade i applikationen. Detta har loggats automatiskt.
                </p>
                
                <div className="d-grid gap-2 d-md-flex justify-content-md-center">
                  <Button 
                    variant="outline-danger" 
                    onClick={this.handleReset}
                    className="me-md-2"
                  >
                    <i className="bi bi-arrow-clockwise me-1"></i>
                    Försök igen
                  </Button>
                  
                  <Button 
                    variant="danger" 
                    onClick={this.handleReload}
                  >
                    <i className="bi bi-bootstrap-reboot me-1"></i>
                    Ladda om sidan
                  </Button>
                </div>

                {process.env.NODE_ENV === 'development' && this.state.error && (
                  <details className="mt-3 text-start">
                    <summary className="mb-2">
                      <small className="text-muted">Teknisk information (endast utveckling)</small>
                    </summary>
                    <pre className="bg-light p-2 rounded small">
                      <strong>Fel:</strong> {this.state.error.message}
                      {'\n\n'}
                      <strong>Stack:</strong> {this.state.error.stack}
                      {this.state.errorInfo && (
                        <>
                          {'\n\n'}
                          <strong>Komponent Stack:</strong> {this.state.errorInfo.componentStack}
                        </>
                      )}
                    </pre>
                  </details>
                )}

                <hr />
                <small className="text-muted">
                  Fel-ID: {this.state.errorId}
                </small>
              </Alert>
            </Col>
          </Row>
        </Container>
      );
    }

    return this.props.children;
  }
}

// Higher-order component for easier usage
export const withErrorBoundary = (Component, fallback) => {
  return function WrappedComponent(props) {
    return (
      <ErrorBoundary fallback={fallback}>
        <Component {...props} />
      </ErrorBoundary>
    );
  };
};

// Hook for error reporting in functional components
export const useErrorHandler = () => {
  return (error, errorInfo = {}) => {
    console.error('Manual error report:', error, errorInfo);
    
    // Report error manually
    const errorReport = {
      message: error.message || String(error),
      stack: error.stack || 'No stack trace available',
      timestamp: new Date().toISOString(),
      userAgent: navigator.userAgent,
      url: window.location.href,
      ...errorInfo
    };

    // TODO: Send to error reporting service
    console.error('Error Report:', errorReport);
  };
};

export default ErrorBoundary;
