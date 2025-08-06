"""Main FastAPI application for Trio Monitor."""

import logging
from contextlib import asynccontextmanager
from typing import List, Dict, Any
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from config import settings
from models import DashboardData, AgentState, QueueMetrics, ServiceLevelMetrics, AlertData
from database import get_db, db_manager
from scheduler import trio_scheduler
from auth import auth_manager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting Trio Monitor backend...")
    
    # Test API connection
    connection_ok = await auth_manager.test_connection()
    if connection_ok:
        logger.info("Successfully connected to Trio Enterprise API")
    else:
        logger.warning("Could not connect to Trio Enterprise API - using mock data")
    
    # Start scheduler
    trio_scheduler.start()
    
    yield
    
    # Shutdown
    logger.info("Shutting down Trio Monitor backend...")
    trio_scheduler.stop()
    await auth_manager.close()


# Create FastAPI app
app = FastAPI(
    title="Trio Monitor API",
    description="Real-time monitoring system for Trio Enterprise API",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Trio Monitor API", "version": "1.0.0", "status": "operational"}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": trio_scheduler.get_latest_data().get("last_updated"),
        "scheduler_running": trio_scheduler.is_running
    }


@app.get("/api/dashboard", response_model=Dict[str, Any])
async def get_dashboard_data():
    """Get complete dashboard data."""
    try:
        data = trio_scheduler.get_latest_data()
        if not data:
            raise HTTPException(status_code=503, detail="No data available yet")
        
        return data
    except Exception as e:
        logger.error(f"Error getting dashboard data: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/api/agents", response_model=List[Dict[str, Any]])
async def get_agents():
    """Get current agent states."""
    try:
        data = trio_scheduler.get_latest_data()
        return data.get("agents", [])
    except Exception as e:
        logger.error(f"Error getting agents: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/api/queues", response_model=List[Dict[str, Any]])
async def get_queues():
    """Get current queue metrics."""
    try:
        data = trio_scheduler.get_latest_data()
        return data.get("queues", [])
    except Exception as e:
        logger.error(f"Error getting queues: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/api/service-level", response_model=Dict[str, Any])
async def get_service_level():
    """Get service level metrics."""
    try:
        data = trio_scheduler.get_latest_data()
        return data.get("service_level", {})
    except Exception as e:
        logger.error(f"Error getting service level: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/api/alerts", response_model=List[Dict[str, Any]])
async def get_alerts():
    """Get current alerts."""
    try:
        alerts = trio_scheduler.get_alerts()
        return [alert.dict() for alert in alerts]
    except Exception as e:
        logger.error(f"Error getting alerts: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/api/stats")
async def get_stats():
    """Get system statistics."""
    try:
        data = trio_scheduler.get_latest_data()
        agents = data.get("agents", [])
        queues = data.get("queues", [])
        service_level = data.get("service_level", {})
        
        # Calculate statistics
        total_agents = len(agents)
        available_agents = len([a for a in agents if a.get("status") == "available"])
        busy_agents = len([a for a in agents if a.get("status") == "busy"])
        
        total_calls_waiting = sum(q.get("calls_waiting", 0) for q in queues)
        max_wait_time = max((q.get("current_wait_time", 0) for q in queues), default=0)
        
        critical_queues = len([q for q in queues if q.get("status") == "critical"])
        warning_queues = len([q for q in queues if q.get("status") == "warning"])
        
        return {
            "agents": {
                "total": total_agents,
                "available": available_agents,
                "busy": busy_agents,
                "utilization": (busy_agents / total_agents * 100) if total_agents > 0 else 0
            },
            "queues": {
                "total": len(queues),
                "calls_waiting": total_calls_waiting,
                "max_wait_time": max_wait_time,
                "critical_count": critical_queues,
                "warning_count": warning_queues
            },
            "service_level": {
                "percentage": service_level.get("service_level_percentage", 0),
                "total_calls": service_level.get("total_calls", 0),
                "average_wait_time": service_level.get("average_wait_time", 0),
                "total_queue_time": service_level.get("total_queue_time", 0),
                "limit_breached": service_level.get("queue_time_limit_breached", False)
            },
            "system": {
                "status": data.get("system_status", "unknown"),
                "last_updated": data.get("last_updated"),
                "alerts_count": len(trio_scheduler.get_alerts())
            }
        }
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/api/historical/{queue_id}")
async def get_historical_data(queue_id: str, hours: int = 24, db: Session = Depends(get_db)):
    """Get historical data for a specific queue."""
    try:
        from datetime import datetime, timedelta
        from database import HistoricalDataDB
        
        start_time = datetime.now() - timedelta(hours=hours)
        
        historical_data = db.query(HistoricalDataDB).filter(
            HistoricalDataDB.queue_id == queue_id,
            HistoricalDataDB.timestamp >= start_time
        ).order_by(HistoricalDataDB.timestamp).all()
        
        return [
            {
                "timestamp": record.timestamp.isoformat(),
                "wait_time": record.wait_time,
                "queue_depth": record.queue_depth,
                "service_level": record.service_level
            }
            for record in historical_data
        ]
    except Exception as e:
        logger.error(f"Error getting historical data: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/api/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: str):
    """Acknowledge an alert."""
    try:
        # In a real implementation, this would update the alert in the database
        logger.info(f"Alert {alert_id} acknowledged")
        return {"message": "Alert acknowledged", "alert_id": alert_id}
    except Exception as e:
        logger.error(f"Error acknowledging alert: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level="info"
    )
