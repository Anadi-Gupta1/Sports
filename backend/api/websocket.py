"""
WebSocket handler for real-time communication

This module handles WebSocket connections for real-time action detection,
feedback delivery, and status updates.
"""

from fastapi import WebSocket, WebSocketDisconnect, Depends
from typing import Dict, List, Set
import logging
import asyncio
import json
from datetime import datetime

from core.tracker import ActionTracker
from analytics.session_tracker import SessionTracker
from api.models import WebSocketMessage, ActionResult, FeedbackMessage

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.session_connections: Dict[str, Set[str]] = {}  # session_id -> connection_ids
        self.connection_sessions: Dict[str, str] = {}  # connection_id -> session_id
        
    async def connect(self, websocket: WebSocket, connection_id: str, session_id: str = None):
        """Accept a new WebSocket connection"""
        await websocket.accept()
        self.active_connections[connection_id] = websocket
        
        if session_id:
            self.connection_sessions[connection_id] = session_id
            if session_id not in self.session_connections:
                self.session_connections[session_id] = set()
            self.session_connections[session_id].add(connection_id)
            
        logger.info(f"WebSocket connection {connection_id} established for session {session_id}")
        
    def disconnect(self, connection_id: str):
        """Remove a WebSocket connection"""
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]
            
        # Remove from session mapping
        if connection_id in self.connection_sessions:
            session_id = self.connection_sessions[connection_id]
            del self.connection_sessions[connection_id]
            
            if session_id in self.session_connections:
                self.session_connections[session_id].discard(connection_id)
                if not self.session_connections[session_id]:
                    del self.session_connections[session_id]
                    
        logger.info(f"WebSocket connection {connection_id} disconnected")
        
    async def send_personal_message(self, message: str, connection_id: str):
        """Send a message to a specific connection"""
        if connection_id in self.active_connections:
            websocket = self.active_connections[connection_id]
            try:
                await websocket.send_text(message)
            except Exception as e:
                logger.error(f"Error sending message to {connection_id}: {e}")
                self.disconnect(connection_id)
                
    async def send_to_session(self, message: str, session_id: str):
        """Send a message to all connections in a session"""
        if session_id in self.session_connections:
            disconnected = []
            for connection_id in self.session_connections[session_id].copy():
                try:
                    if connection_id in self.active_connections:
                        await self.active_connections[connection_id].send_text(message)
                except Exception as e:
                    logger.error(f"Error sending to connection {connection_id}: {e}")
                    disconnected.append(connection_id)
                    
            # Clean up disconnected connections
            for connection_id in disconnected:
                self.disconnect(connection_id)
                
    async def broadcast(self, message: str):
        """Broadcast a message to all connections"""
        disconnected = []
        for connection_id, websocket in self.active_connections.items():
            try:
                await websocket.send_text(message)
            except Exception as e:
                logger.error(f"Error broadcasting to {connection_id}: {e}")
                disconnected.append(connection_id)
                
        # Clean up disconnected connections
        for connection_id in disconnected:
            self.disconnect(connection_id)
            
    def get_session_connections(self, session_id: str) -> int:
        """Get number of connections for a session"""
        return len(self.session_connections.get(session_id, set()))


# Global connection manager
manager = ConnectionManager()


class WebSocketHandler:
    """Handles WebSocket communication and real-time updates"""
    
    def __init__(self, tracker: ActionTracker, session_tracker: SessionTracker):
        self.tracker = tracker
        self.session_tracker = session_tracker
        self.is_broadcasting = False
        
    async def handle_connection(self, websocket: WebSocket, session_id: str, connection_id: str):
        """Handle a new WebSocket connection"""
        try:
            await manager.connect(websocket, connection_id, session_id)
            
            # Send initial status
            await self.send_status_update(session_id)
            
            # Listen for messages
            while True:
                try:
                    data = await websocket.receive_text()
                    message = json.loads(data)
                    await self.handle_message(message, connection_id, session_id)
                except WebSocketDisconnect:
                    break
                except json.JSONDecodeError:
                    logger.error(f"Invalid JSON received from {connection_id}")
                except Exception as e:
                    logger.error(f"Error handling message from {connection_id}: {e}")
                    
        except Exception as e:
            logger.error(f"Error in WebSocket connection {connection_id}: {e}")
        finally:
            manager.disconnect(connection_id)
            
    async def handle_message(self, message: Dict, connection_id: str, session_id: str):
        """Handle incoming WebSocket messages"""
        try:
            message_type = message.get("type")
            data = message.get("data", {})
            
            if message_type == "start_tracking":
                await self.start_tracking(session_id)
                
            elif message_type == "stop_tracking":
                await self.stop_tracking(session_id)
                
            elif message_type == "request_status":
                await self.send_status_update(session_id)
                
            elif message_type == "update_config":
                await self.update_session_config(session_id, data)
                
            elif message_type == "manual_action":
                await self.record_manual_action(session_id, data)
                
            else:
                logger.warning(f"Unknown message type: {message_type}")
                
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            await self.send_error(connection_id, str(e))
            
    async def start_tracking(self, session_id: str):
        """Start real-time tracking for a session"""
        try:
            # Configure tracker for session
            session_info = self.session_tracker.get_session_info(session_id)
            if session_info:
                sport = session_info["sport"]
                config = session_info.get("config", {})
                
                await self.tracker.configure_sport(sport, config)
                self.tracker.current_session_id = session_id
                
                # Start tracking with callback
                await self.tracker.start_tracking(callback=self.on_action_detected)
                
                # Notify clients
                message = WebSocketMessage(
                    type="tracking_started",
                    data={"session_id": session_id},
                    session_id=session_id
                )
                await manager.send_to_session(message.json(), session_id)
                
        except Exception as e:
            logger.error(f"Error starting tracking: {e}")
            await self.send_error_to_session(session_id, f"Failed to start tracking: {e}")
            
    async def stop_tracking(self, session_id: str):
        """Stop real-time tracking"""
        try:
            await self.tracker.stop_tracking()
            
            message = WebSocketMessage(
                type="tracking_stopped",
                data={"session_id": session_id},
                session_id=session_id
            )
            await manager.send_to_session(message.json(), session_id)
            
        except Exception as e:
            logger.error(f"Error stopping tracking: {e}")
            await self.send_error_to_session(session_id, f"Failed to stop tracking: {e}")
            
    async def on_action_detected(self, action_result: Dict):
        """Callback for when an action is detected"""
        try:
            session_id = self.tracker.current_session_id
            if not session_id:
                return
                
            # Record action in database
            self.session_tracker.record_action(session_id, action_result)
            
            # Send action result to clients
            message = WebSocketMessage(
                type="action_detected",
                data=action_result,
                session_id=session_id
            )
            await manager.send_to_session(message.json(), session_id)
            
            # Send feedback if available
            feedback = action_result.get("feedback")
            if feedback:
                feedback_message = WebSocketMessage(
                    type="feedback",
                    data=feedback,
                    session_id=session_id
                )
                await manager.send_to_session(feedback_message.json(), session_id)
                
        except Exception as e:
            logger.error(f"Error handling action detection: {e}")
            
    async def send_status_update(self, session_id: str):
        """Send status update to session clients"""
        try:
            session_info = self.session_tracker.get_session_info(session_id)
            tracking_status = {
                "tracking": getattr(self.tracker, 'is_tracking', False),
                "camera_active": self.tracker.camera_manager.is_camera_available(),
                "pose_detection_active": self.tracker.pose_detector is not None,
                "session_active": session_info is not None
            }
            
            message = WebSocketMessage(
                type="status_update",
                data=tracking_status,
                session_id=session_id
            )
            await manager.send_to_session(message.json(), session_id)
            
        except Exception as e:
            logger.error(f"Error sending status update: {e}")
            
    async def update_session_config(self, session_id: str, config_data: Dict):
        """Update session configuration"""
        try:
            # Update session in database
            self.session_tracker.update_session_config(session_id, config_data)
            
            # Update tracker configuration if active
            if getattr(self.tracker, 'current_session_id', None) == session_id:
                sport = config_data.get("sport")
                if sport:
                    await self.tracker.configure_sport(sport, config_data)
                    
            # Notify clients
            message = WebSocketMessage(
                type="config_updated",
                data=config_data,
                session_id=session_id
            )
            await manager.send_to_session(message.json(), session_id)
            
        except Exception as e:
            logger.error(f"Error updating session config: {e}")
            await self.send_error_to_session(session_id, f"Failed to update config: {e}")
            
    async def record_manual_action(self, session_id: str, action_data: Dict):
        """Record a manually reported action"""
        try:
            # Add timestamp if not provided
            if "timestamp" not in action_data:
                action_data["timestamp"] = datetime.now()
                
            # Record in database
            self.session_tracker.record_action(session_id, action_data)
            
            # Notify clients
            message = WebSocketMessage(
                type="manual_action_recorded",
                data=action_data,
                session_id=session_id
            )
            await manager.send_to_session(message.json(), session_id)
            
        except Exception as e:
            logger.error(f"Error recording manual action: {e}")
            await self.send_error_to_session(session_id, f"Failed to record action: {e}")
            
    async def send_error(self, connection_id: str, error_message: str):
        """Send error message to specific connection"""
        try:
            message = WebSocketMessage(
                type="error",
                data={"message": error_message}
            )
            await manager.send_personal_message(message.json(), connection_id)
            
        except Exception as e:
            logger.error(f"Error sending error message: {e}")
            
    async def send_error_to_session(self, session_id: str, error_message: str):
        """Send error message to all connections in session"""
        try:
            message = WebSocketMessage(
                type="error",
                data={"message": error_message},
                session_id=session_id
            )
            await manager.send_to_session(message.json(), session_id)
            
        except Exception as e:
            logger.error(f"Error sending error to session: {e}")
            
    async def broadcast_system_status(self):
        """Broadcast system status to all connections"""
        try:
            status = {
                "camera_available": self.tracker.camera_manager.is_camera_available(),
                "pose_detector_ready": self.tracker.pose_detector is not None,
                "active_sessions": len(self.session_tracker.get_active_sessions()),
                "timestamp": datetime.now().isoformat()
            }
            
            message = WebSocketMessage(
                type="system_status",
                data=status
            )
            await manager.broadcast(message.json())
            
        except Exception as e:
            logger.error(f"Error broadcasting system status: {e}")
            
    def get_connection_stats(self) -> Dict:
        """Get WebSocket connection statistics"""
        return {
            "total_connections": len(manager.active_connections),
            "sessions_with_connections": len(manager.session_connections),
            "connections_by_session": {
                session_id: len(connections) 
                for session_id, connections in manager.session_connections.items()
            }
        }
    

# Add simple WebSocket endpoint for testing (without authentication)
async def websocket_test_endpoint(websocket: WebSocket):
    """Simple WebSocket endpoint for testing connections"""
    await websocket.accept()
    connection_id = f"test_{datetime.now().timestamp()}"
    
    try:
        logger.info(f"Test WebSocket connection established: {connection_id}")
        
        # Send welcome message
        await websocket.send_text(json.dumps({
            "type": "connection",
            "status": "connected",
            "connection_id": connection_id,
            "message": "WebSocket connection established successfully!"
        }))
        
        while True:
            try:
                # Wait for messages from client
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # Echo the message back
                response = {
                    "type": "echo",
                    "original_message": message,
                    "timestamp": datetime.now().isoformat(),
                    "connection_id": connection_id
                }
                
                await websocket.send_text(json.dumps(response))
                
            except WebSocketDisconnect:
                logger.info(f"Test WebSocket client disconnected: {connection_id}")
                break
            except Exception as e:
                logger.error(f"Error in test WebSocket: {e}")
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": str(e)
                }))
                
    except Exception as e:
        logger.error(f"Error in test WebSocket endpoint: {e}")
    finally:
        logger.info(f"Test WebSocket connection closed: {connection_id}")
