"""Tests for Trio Monitor API endpoints."""

import pytest
from fastapi.testclient import TestClient
from app import app

client = TestClient(app)


def test_root_endpoint():
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Trio Monitor API"
    assert data["version"] == "1.0.0"


def test_health_check():
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] == "healthy"


def test_dashboard_endpoint():
    """Test dashboard data endpoint."""
    # Note: This might return 503 if no data is available yet
    response = client.get("/api/dashboard")
    assert response.status_code in [200, 503]


def test_agents_endpoint():
    """Test agents endpoint."""
    response = client.get("/api/agents")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_queues_endpoint():
    """Test queues endpoint."""
    response = client.get("/api/queues")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_stats_endpoint():
    """Test stats endpoint."""
    response = client.get("/api/stats")
    assert response.status_code == 200
    data = response.json()
    assert "agents" in data
    assert "queues" in data
    assert "service_level" in data
    assert "system" in data
