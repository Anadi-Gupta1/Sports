"""
Core Action Tracker - Real-time sports action detection and analysis

This module handles the main computer vision pipeline for detecting and tracking
sports-specific actions using OpenCV and MediaPipe.
"""

import asyncio
import cv2
import mediapipe as mp
import numpy as np
import time
import logging
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from enum import Enum

from backend.sports.sport_factory import SportFactory
from backend.core.camera_manager import CameraManager
from backend.core.pose_detector import PoseDetector
from backend.analytics.session_tracker import SessionTracker

logger = logging.getLogger(__name__)

class ActionState(Enum):
    """States for action detection"""
    IDLE = "idle"
    PREPARING = "preparing"
    EXECUTING = "executing"
    COMPLETED = "completed"
    ANALYZING = "analyzing"

@dataclass
class ActionResult:
    """Result of an action detection"""
    action_type: str
    success: bool
    confidence: float
    timestamp: float
    metrics: Dict[str, Any]
    feedback_message: str

class ActionTracker:
    """Main action tracking engine with computer vision pipeline"""
    
    def __init__(self):
        self.camera_manager = CameraManager()
        self.pose_detector = PoseDetector()
        self.session_tracker = SessionTracker()
        
        # State management
        self.is_tracking = False
        self.current_sport = None
        self.sport_module = None
        self.action_state = ActionState.IDLE
        
        # Performance tracking
        self.fps_counter = 0
        self.last_fps_time = time.time()
        self.current_fps = 0
        
        # Action detection
        self.action_buffer = []
        self.last_action_time = 0
        self.action_cooldown = 2.0  # Seconds between actions
        
        # Configuration
        self.config = {
            "detection_sensitivity": 0.7,
            "min_confidence": 0.5,
            "frame_buffer_size": 30,
            "pose_tracking": True,
            "object_tracking": True
        }
        
        logger.info("ActionTracker initialized")
    
    async def initialize(self):
        """Initialize the tracking system"""
        try:
            # Initialize camera
            await self.camera_manager.initialize()
            
            # Initialize pose detector
            self.pose_detector.initialize()
            
            logger.info("ActionTracker initialization complete")
            
        except Exception as e:
            logger.error(f"Failed to initialize ActionTracker: {e}")
            raise
    
    async def cleanup(self):
        """Cleanup resources"""
        try:
            await self.stop_tracking()
            self.camera_manager.cleanup()
            self.pose_detector.cleanup()
            
            logger.info("ActionTracker cleanup complete")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    def configure_sport(self, sport_config: Dict[str, Any]):
        """Configure the tracker for a specific sport"""
        try:
            sport_name = sport_config.get("sport", "basketball")
            
            # Get sport-specific module
            self.sport_module = SportFactory.create_sport(sport_name, sport_config)
            self.current_sport = sport_name
            
            # Update configuration
            self.config.update(sport_config.get("tracker_config", {}))
            
            # Configure pose detector for sport
            pose_config = sport_config.get("pose_config", {})
            self.pose_detector.configure(pose_config)
            
            logger.info(f"Configured tracker for sport: {sport_name}")
            
        except Exception as e:
            logger.error(f"Failed to configure sport: {e}")
            raise
    
    async def start_tracking(self, sport_config: Dict[str, Any] = None):
        """Start the action tracking process"""
        try:
            if sport_config:
                self.configure_sport(sport_config)
            
            if not self.sport_module:
                raise ValueError("No sport configured. Call configure_sport() first.")
            
            # Start camera capture
            await self.camera_manager.start_capture()
            
            # Reset state
            self.action_state = ActionState.IDLE
            self.is_tracking = True
            self.session_tracker.start_session(self.current_sport)
            
            # Start tracking loop
            asyncio.create_task(self._tracking_loop())
            
            logger.info("Action tracking started")
            
        except Exception as e:
            logger.error(f"Failed to start tracking: {e}")
            raise
    
    async def stop_tracking(self):
        """Stop the action tracking process"""
        try:
            self.is_tracking = False
            await self.camera_manager.stop_capture()
            
            # Finalize session
            self.session_tracker.end_session()
            
            logger.info("Action tracking stopped")
            
        except Exception as e:
            logger.error(f"Error stopping tracking: {e}")
    
    async def _tracking_loop(self):
        """Main tracking loop - processes video frames"""
        try:
            while self.is_tracking:
                # Get latest frame
                frame = await self.camera_manager.get_frame()
                
                if frame is None:
                    await asyncio.sleep(0.01)
                    continue
                
                # Process frame
                await self._process_frame(frame)
                
                # Update FPS counter
                self._update_fps()
                
                # Small delay to prevent overwhelming CPU
                await asyncio.sleep(0.001)
                
        except Exception as e:
            logger.error(f"Error in tracking loop: {e}")
            self.is_tracking = False
    
    async def _process_frame(self, frame: np.ndarray):
        """Process a single frame for action detection"""
        try:
            # Detect pose landmarks
            pose_results = self.pose_detector.detect_pose(frame)
            
            # Sport-specific action detection
            if self.sport_module and pose_results:
                action_data = await self._detect_action(frame, pose_results)
                
                if action_data:
                    await self._handle_action_detected(action_data)
            
            # Add frame to buffer for analysis
            self._add_to_buffer(frame, pose_results)
            
        except Exception as e:
            logger.error(f"Error processing frame: {e}")
    
    async def _detect_action(self, frame: np.ndarray, pose_results) -> Optional[Dict[str, Any]]:
        """Detect sport-specific actions using the configured sport module"""
        try:
            # Check if enough time has passed since last action
            current_time = time.time()
            if current_time - self.last_action_time < self.action_cooldown:
                return None
            
            # Use sport module to detect action
            action_data = self.sport_module.detect_action(
                frame=frame,
                pose_landmarks=pose_results.pose_landmarks,
                pose_world_landmarks=pose_results.pose_world_landmarks,
                action_buffer=self.action_buffer[-self.config["frame_buffer_size"]:]
            )
            
            if action_data and action_data.get("confidence", 0) >= self.config["min_confidence"]:
                return action_data
            
            return None
            
        except Exception as e:
            logger.error(f"Error detecting action: {e}")
            return None
    
    async def _handle_action_detected(self, action_data: Dict[str, Any]):
        """Handle when an action is detected"""
        try:
            self.last_action_time = time.time()
            
            # Analyze action success/failure
            analysis_result = self.sport_module.analyze_action(action_data)
            
            # Create action result
            action_result = ActionResult(
                action_type=action_data["action_type"],
                success=analysis_result["success"],
                confidence=action_data["confidence"],
                timestamp=time.time(),
                metrics=analysis_result.get("metrics", {}),
                feedback_message=analysis_result.get("feedback_message", "")
            )
            
            # Record in session
            self.session_tracker.record_action(action_result)
            
            # Trigger feedback (handled by feedback manager)
            await self._send_feedback(action_result)
            
            logger.info(f"Action detected: {action_result.action_type} "
                       f"({'Success' if action_result.success else 'Failed'})")
            
        except Exception as e:
            logger.error(f"Error handling detected action: {e}")
    
    async def _send_feedback(self, action_result: ActionResult):
        """Send feedback for detected action (placeholder for feedback manager)"""
        # This will be handled by the feedback manager
        # For now, just log the feedback
        logger.info(f"Feedback: {action_result.feedback_message}")
    
    def _add_to_buffer(self, frame: np.ndarray, pose_results):
        """Add frame data to buffer for analysis"""
        frame_data = {
            "timestamp": time.time(),
            "frame": frame.copy(),
            "pose_results": pose_results
        }
        
        self.action_buffer.append(frame_data)
        
        # Keep buffer size manageable
        max_buffer_size = self.config["frame_buffer_size"] * 2
        if len(self.action_buffer) > max_buffer_size:
            self.action_buffer = self.action_buffer[-max_buffer_size:]
    
    def _update_fps(self):
        """Update FPS counter"""
        self.fps_counter += 1
        current_time = time.time()
        
        if current_time - self.last_fps_time >= 1.0:
            self.current_fps = self.fps_counter
            self.fps_counter = 0
            self.last_fps_time = current_time
    
    async def get_current_state(self) -> Dict[str, Any]:
        """Get current tracking state and statistics"""
        try:
            session_stats = self.session_tracker.get_current_stats()
            
            return {
                "is_tracking": self.is_tracking,
                "sport": self.current_sport,
                "action_state": self.action_state.value,
                "fps": self.current_fps,
                "session_stats": session_stats,
                "last_action_time": self.last_action_time,
                "buffer_size": len(self.action_buffer)
            }
            
        except Exception as e:
            logger.error(f"Error getting current state: {e}")
            return {}
    
    def get_session_summary(self) -> Dict[str, Any]:
        """Get summary of current session"""
        return self.session_tracker.get_session_summary()
