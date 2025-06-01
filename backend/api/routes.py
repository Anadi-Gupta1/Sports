"""
FastAPI routes for the Multi-Sport Action Tracker API

This module con@router.get("/sports", response_model=List[Dict[str, Any]])ains all the REST API endpoints for the tracking system.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from fastapi.responses import StreamingResponse
from typing import Dict, List, Optional, Any
import logging
import asyncio
import json
import cv2
from datetime import datetime

from core.tracker import ActionTracker
from analytics.session_tracker import SessionTracker
from sports.sport_factory import SportFactory
from api.models import (
    SessionCreate, SessionResponse, ActionResult, 
    SportConfig, SystemStatus, CameraConfig
)
from api.session_routes import router as session_router

logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

# Include session routes
router.include_router(session_router, prefix="/sessions", tags=["sessions"])

# Global tracker instance (will be initialized)
global_tracker: Optional[ActionTracker] = None
session_tracker = SessionTracker()


async def get_tracker() -> ActionTracker:
    """Dependency to get the global tracker instance"""
    global global_tracker
    if global_tracker is None:
        global_tracker = ActionTracker()
    return global_tracker


@router.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint"""
    return {
        "message": "Multi-Sport Action Tracker API",
        "version": "1.0.0",
        "status": "running"
    }


@router.get("/health", response_model=SystemStatus)
async def health_check(tracker: ActionTracker = Depends(get_tracker)):
    """Health check endpoint"""
    try:
        camera_status = tracker.camera_manager.is_camera_available()
        pose_detector_status = tracker.pose_detector is not None
        
        return SystemStatus(
            status="healthy" if camera_status and pose_detector_status else "degraded",
            camera_available=camera_status,
            pose_detector_ready=pose_detector_status,
            active_sessions=len(session_tracker.get_active_sessions()),
            timestamp=datetime.now()
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return SystemStatus(
            status="unhealthy",
            camera_available=False,
            pose_detector_ready=False,
            active_sessions=0,
            timestamp=datetime.now(),
            error=str(e)
        )


@router.get("/sports", response_model=List[Dict[str, Any]])
async def get_available_sports():
    """Get list of available sports"""
    try:
        sports_info = []
        available_sports = ["basketball", "tennis", "soccer", "golf"]
        
        for sport in available_sports:
            sport_info = SportFactory.get_sport_info(sport)
            if sport_info:
                sports_info.append(sport_info)
        
        return sports_info
    except Exception as e:
        logger.error(f"Error getting sports info: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sports/{sport_name}", response_model=Dict[str, Any])
async def get_sport_info(sport_name: str):
    """Get information about a specific sport"""
    try:
        sport_info = SportFactory.get_sport_info(sport_name)
        if sport_info is None:
            raise HTTPException(status_code=404, detail=f"Sport '{sport_name}' not found")
        return sport_info
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting sport info for {sport_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sessions", response_model=SessionResponse)
async def create_session(
    session_data: SessionCreate,
    tracker: ActionTracker = Depends(get_tracker)
):
    """Create a new tracking session"""
    try:
        # Configure the tracker for the selected sport
        await tracker.configure_sport(session_data.sport, session_data.config)
        
        # Create session in database
        session_id = session_tracker.create_session(
            sport=session_data.sport,
            user_id=session_data.user_id,
            config=session_data.config
        )
        
        session_info = session_tracker.get_session_info(session_id)
        
        return SessionResponse(
            session_id=session_id,
            sport=session_info["sport"],
            user_id=session_info["user_id"],
            start_time=session_info["start_time"],
            status="active",
            config=session_info["config"]
        )
        
    except Exception as e:
        logger.error(f"Error creating session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_session(session_id: str):
    """Get session information"""
    try:
        session_info = session_tracker.get_session_info(session_id)
        if session_info is None:
            raise HTTPException(status_code=404, detail="Session not found")
            
        return SessionResponse(**session_info)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sessions/{session_id}/actions", response_model=ActionResult)
async def record_action(
    session_id: str,
    action_data: Dict,
    tracker: ActionTracker = Depends(get_tracker)
):
    """Manually record an action for a session"""
    try:
        # Verify session exists
        session_info = session_tracker.get_session_info(session_id)
        if session_info is None:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Record the action
        session_tracker.record_action(session_id, action_data)
        
        return ActionResult(**action_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error recording action for session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}/actions", response_model=List[ActionResult])
async def get_session_actions(session_id: str, limit: int = 50):
    """Get actions for a session"""
    try:
        actions = session_tracker.get_session_actions(session_id, limit=limit)
        return [ActionResult(**action) for action in actions]
        
    except Exception as e:
        logger.error(f"Error getting actions for session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}/analytics", response_model=Dict[str, Any])
async def get_session_analytics(session_id: str):
    """Get analytics for a session"""
    try:
        analytics = session_tracker.get_session_analytics(session_id)
        if analytics is None:
            raise HTTPException(status_code=404, detail="Session not found")
            
        return analytics
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting analytics for session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sessions/{session_id}/stop")
async def stop_session(
    session_id: str,
    tracker: ActionTracker = Depends(get_tracker)
):
    """Stop a tracking session"""
    try:
        session_tracker.end_session(session_id)
        
        # Stop tracking if this was the active session
        if hasattr(tracker, 'current_session_id') and tracker.current_session_id == session_id:
            await tracker.stop_tracking()
            
        return {"message": "Session stopped successfully"}
        
    except Exception as e:
        logger.error(f"Error stopping session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tracking/start/{session_id}")
async def start_tracking(
    session_id: str,
    background_tasks: BackgroundTasks,
    tracker: ActionTracker = Depends(get_tracker)
):
    """Start real-time tracking for a session"""
    try:
        # Verify session exists
        session_info = session_tracker.get_session_info(session_id)
        if session_info is None:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Start tracking in background
        tracker.current_session_id = session_id
        background_tasks.add_task(tracker.start_tracking)
        
        return {"message": "Tracking started", "session_id": session_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting tracking for session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tracking/stop")
async def stop_tracking(tracker: ActionTracker = Depends(get_tracker)):
    """Stop real-time tracking"""
    try:
        await tracker.stop_tracking()
        return {"message": "Tracking stopped"}
        
    except Exception as e:
        logger.error(f"Error stopping tracking: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tracking/status")
async def get_tracking_status(tracker: ActionTracker = Depends(get_tracker)):
    """Get current tracking status"""
    try:
        is_tracking = tracker.is_tracking if hasattr(tracker, 'is_tracking') else False
        current_session = getattr(tracker, 'current_session_id', None)
        
        return {
            "tracking": is_tracking,
            "session_id": current_session,
            "camera_active": tracker.camera_manager.is_camera_available(),
            "timestamp": datetime.now()
        }
        
    except Exception as e:
        logger.error(f"Error getting tracking status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/camera/config", response_model=CameraConfig)
async def get_camera_config(tracker: ActionTracker = Depends(get_tracker)):
    """Get camera configuration"""
    try:
        config = tracker.camera_manager.get_camera_config()
        return CameraConfig(**config)
        
    except Exception as e:
        logger.error(f"Error getting camera config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/camera/config")
async def update_camera_config(
    config: CameraConfig,
    tracker: ActionTracker = Depends(get_tracker)
):
    """Update camera configuration"""
    try:
        success = tracker.camera_manager.update_camera_config(config.dict())
        
        if success:
            return {"message": "Camera configuration updated successfully"}
        else:
            raise HTTPException(status_code=400, detail="Failed to update camera configuration")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating camera config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/feedback/test/{feedback_type}")
async def test_feedback(
    feedback_type: str,
    tracker: ActionTracker = Depends(get_tracker)
):
    """Test feedback system"""
    try:
        test_feedback = {
            "message": f"Testing {feedback_type} feedback",
            "type": "test",
            "audio": f"test_{feedback_type}.wav"
        }
        
        # Send test feedback
        await tracker.feedback_manager.send_feedback(test_feedback)
        
        return {"message": f"Test {feedback_type} feedback sent"}
        
    except Exception as e:
        logger.error(f"Error testing feedback: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/user/{user_id}/sessions", response_model=List[SessionResponse])
async def get_user_sessions(user_id: str, limit: int = 20):
    """Get sessions for a specific user"""
    try:
        sessions = session_tracker.get_user_sessions(user_id, limit=limit)
        return [SessionResponse(**session) for session in sessions]
        
    except Exception as e:
        logger.error(f"Error getting sessions for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/user/{user_id}/analytics", response_model=Dict[str, Any])
async def get_user_analytics(user_id: str):
    """Get overall analytics for a user"""
    try:
        analytics = session_tracker.get_user_analytics(user_id)
        return analytics
        
    except Exception as e:
        logger.error(f"Error getting analytics for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Video streaming endpoint (for debugging/monitoring)
@router.get("/camera/stream")
async def video_stream(tracker: ActionTracker = Depends(get_tracker)):
    """Stream video feed from camera"""
    try:
        if not tracker.camera_manager.is_camera_available():
            raise HTTPException(status_code=503, detail="Camera not available")
        
        def generate_frames():
            """Generate video frames"""
            try:
                while True:
                    frame = tracker.camera_manager.get_frame()
                    if frame is not None:
                        # Convert frame to JPEG
                        _, buffer = cv2.imencode('.jpg', frame)
                        frame_data = buffer.tobytes()
                        
                        yield (b'--frame\r\n'
                               b'Content-Type: image/jpeg\r\n\r\n' + frame_data + b'\r\n')
                    else:
                        break
            except Exception as e:
                logger.error(f"Error in video stream: {e}")
        
        return StreamingResponse(
            generate_frames(),
            media_type="multipart/x-mixed-replace; boundary=frame"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting video stream: {e}")
        raise HTTPException(status_code=500, detail=str(e))
