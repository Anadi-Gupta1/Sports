"""
Session routes for the API
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any
import logging

from analytics.session_tracker import SessionTracker

# Create router
router = APIRouter()

# Instance of session tracker
session_tracker = SessionTracker()
logger = logging.getLogger(__name__)

@router.get("/sessions")
async def get_sessions():
    """Get all sessions"""
    try:
        # Get historical sessions
        sessions = session_tracker.get_historical_sessions()
        
        # Add active status
        active_sessions = session_tracker.get_active_sessions()
        for session in sessions:
            session["active"] = session["session_id"] in active_sessions
        
        return sessions
        
    except Exception as e:
        logger.error(f"Error getting sessions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sessions/{session_id}")
async def get_session(session_id: str):
    """Get a specific session"""
    try:
        # Check if it's the current session
        if session_tracker.current_session and session_tracker.current_session["session_id"] == session_id:
            # Get current session summary
            return session_tracker.get_session_summary()
        
        # Otherwise, get from database
        conn = session_tracker._get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM sessions WHERE session_id = ?', (session_id,))
        session_row = cursor.fetchone()
        
        if not session_row:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Convert to dictionary
        session_columns = [
            'session_id', 'sport', 'start_time', 'end_time', 'duration',
            'total_actions', 'successful_actions', 'success_rate',
            'average_confidence', 'performance_trend', 'notes', 'created_at'
        ]
        session = dict(zip(session_columns, session_row))
        
        # Get session actions
        cursor.execute('SELECT * FROM actions WHERE session_id = ?', (session_id,))
        actions_rows = cursor.fetchall()
        
        action_columns = [
            'id', 'session_id', 'timestamp', 'sport', 'action_type',
            'success', 'confidence', 'metrics', 'feedback_message'
        ]
        
        actions = []
        for row in actions_rows:
            action = dict(zip(action_columns, row))
            actions.append(action)
        
        session["actions"] = actions
        session["active"] = session_id in session_tracker.get_active_sessions()
        
        conn.close()
        return session
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
