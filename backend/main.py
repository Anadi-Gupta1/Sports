"""
Multi-Sport Action Tracker - Main Application Entry Point

A comprehensive real-time sports action tracking system with computer vision,
instant feedback, and performance analytics.
"""

import asyncio
import logging
import uvicorn
import cv2
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import json
from pathlib import Path
from typing import Dict, Any
import uuid
from datetime import datetime

from core.tracker import ActionTracker
from analytics.session_tracker import SessionTracker
from api.routes import router
from api.websocket import WebSocketHandler, manager
from api.models import WebSocketMessage

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Multi-Sport Action Tracker",
    description="Real-time sports action detection and feedback system",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router, prefix="/api", tags=["api"])

# Serve static files (frontend build)
frontend_path = Path(__file__).parent.parent / "frontend" / "build"
if frontend_path.exists():
    app.mount("/", StaticFiles(directory=str(frontend_path), html=True), name="static")

# Global instances
action_tracker = ActionTracker()
session_tracker = SessionTracker()
websocket_handler = WebSocketHandler(action_tracker, session_tracker)

@app.on_event("startup")
async def startup_event():
    """Initialize application components on startup"""
    logger.info("Starting Multi-Sport Action Tracker...")
    
    try:
        # Initialize action tracker
        await action_tracker.initialize()
        logger.info("Action tracker initialized successfully")
          # Initialize session tracker database
        session_tracker._init_database()
        logger.info("Session tracker database initialized")
        
        logger.info("Application startup complete!")
        
    except Exception as e:
        logger.error(f"Error during startup: {e}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on application shutdown"""
    logger.info("Shutting down Multi-Sport Action Tracker...")
    
    try:
        # Stop any active tracking
        if hasattr(action_tracker, 'is_tracking') and action_tracker.is_tracking:
            await action_tracker.stop_tracking()
            
        # Cleanup tracker resources
        if hasattr(action_tracker, 'cleanup'):
            await action_tracker.cleanup()
            
        # Close database connections
        session_tracker.close()
        
        logger.info("Application shutdown complete!")
        
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")


@app.get("/")
async def root():
    """Root endpoint - API information"""
    return {
        "message": "Multi-Sport Action Tracker API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/api/docs",
        "websocket": "/ws/{session_id}",
        "available_sports": ["basketball", "tennis", "soccer", "golf"]
    }

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time communication"""
    connection_id = str(uuid.uuid4())
    
    try:
        await websocket_handler.handle_connection(websocket, session_id, connection_id)
    except WebSocketDisconnect:
        logger.info(f"WebSocket {connection_id} disconnected from session {session_id}")
    except Exception as e:
        logger.error(f"WebSocket error for {connection_id}: {e}")
    finally:
        manager.disconnect(connection_id)


@app.get("/ws/stats")
async def get_websocket_stats():
    """Get WebSocket connection statistics"""
    try:
        stats = websocket_handler.get_connection_stats()
        return stats
    except Exception as e:
        logger.error(f"Error getting WebSocket stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/system/broadcast")
async def broadcast_message(message: Dict[str, Any]):
    """Broadcast a message to all connected clients (admin only)"""
    try:
        ws_message = WebSocketMessage(
            type="system_broadcast",
            data=message
        )
        await manager.broadcast(ws_message.json())
        return {"message": "Broadcast sent successfully"}
    except Exception as e:
        logger.error(f"Error broadcasting message: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Background task for system status updates
async def broadcast_system_status():
    """Periodically broadcast system status"""
    while True:
        try:
            await websocket_handler.broadcast_system_status()
            await asyncio.sleep(30)  # Broadcast every 30 seconds
        except Exception as e:
            logger.error(f"Error in system status broadcast: {e}")
            await asyncio.sleep(60)  # Wait longer on error


# Start background tasks
@app.on_event("startup")
async def start_background_tasks():
    """Start background tasks"""
    asyncio.create_task(broadcast_system_status())

@app.websocket("/ws")
async def simple_websocket_endpoint(websocket: WebSocket):
    """Simple WebSocket endpoint for testing"""
    await websocket.accept()
    connection_id = str(uuid.uuid4())
    
    try:
        logger.info(f"Simple WebSocket connection {connection_id} established")
        
        # Send welcome message
        await websocket.send_text(json.dumps({
            "type": "connected",
            "connection_id": connection_id,
            "message": "Connected to Multi-Sport Action Tracker"
        }))
        
        # Listen for messages
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # Echo the message back with timestamp
                response = {
                    "type": "echo",
                    "original_message": message,
                    "timestamp": datetime.now().isoformat(),
                    "connection_id": connection_id
                }
                
                await websocket.send_text(json.dumps(response))
                
            except WebSocketDisconnect:
                break
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "Invalid JSON format"
                }))
            except Exception as e:
                logger.error(f"Error in simple WebSocket {connection_id}: {e}")
                break
                
    except Exception as e:
        logger.error(f"Simple WebSocket error for {connection_id}: {e}")
    finally:
        logger.info(f"Simple WebSocket connection {connection_id} closed")


if __name__ == "__main__":
    # Run the application
    logger.info("Starting Multi-Sport Action Tracker server...")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
        access_log=True
    )
