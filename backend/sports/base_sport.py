"""
Base Sport Tracker - Abstract base class for all sport-specific trackers

Defines the interface and common functionality for sport tracking modules.
"""

from abc import ABC, abstractmethod
import numpy as np
import time
import logging
from typing import Dict, Any, Optional, List, Tuple

logger = logging.getLogger(__name__)

class BaseSportTracker(ABC):
    """Abstract base class for sport-specific trackers"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.sport_name = self.__class__.__name__.replace("Tracker", "").lower()
        
        # Common tracking state
        self.is_active = False
        self.last_action_time = 0
        self.action_history = []
        
        # Performance metrics
        self.total_actions = 0
        self.successful_actions = 0
        
        logger.info(f"Initialized {self.sport_name} tracker")
    
    @abstractmethod
    def detect_action(self, frame: np.ndarray, pose_landmarks, pose_world_landmarks, action_buffer: List) -> Optional[Dict[str, Any]]:
        """
        Detect sport-specific actions in the current frame
        
        Args:
            frame: Current video frame
            pose_landmarks: MediaPipe pose landmarks
            pose_world_landmarks: MediaPipe world coordinates
            action_buffer: Recent frames for temporal analysis
            
        Returns:
            Action data if detected, None otherwise
        """
        pass
    
    @abstractmethod
    def analyze_action(self, action_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze detected action for success/failure and metrics
        
        Args:
            action_data: Raw action detection data
            
        Returns:
            Analysis result with success status, metrics, and feedback
        """
        pass
    
    @abstractmethod
    def get_feedback_message(self, analysis_result: Dict[str, Any]) -> str:
        """
        Generate feedback message based on analysis result
        
        Args:
            analysis_result: Result from analyze_action
            
        Returns:
            Human-readable feedback message
        """
        pass
    
    @classmethod
    @abstractmethod
    def get_sport_info(cls) -> Dict[str, Any]:
        """
        Get sport-specific information and configuration options
        
        Returns:
            Sport information dictionary
        """
        pass
    
    def configure(self, new_config: Dict[str, Any]):
        """Update tracker configuration"""
        self.config.update(new_config)
        logger.info(f"Updated {self.sport_name} configuration")
    
    def reset_session(self):
        """Reset session statistics"""
        self.total_actions = 0
        self.successful_actions = 0
        self.action_history = []
        logger.info(f"Reset {self.sport_name} session")
    
    def get_session_stats(self) -> Dict[str, Any]:
        """Get current session statistics"""
        success_rate = (self.successful_actions / self.total_actions * 100) if self.total_actions > 0 else 0
        
        return {
            "sport": self.sport_name,
            "total_actions": self.total_actions,
            "successful_actions": self.successful_actions,
            "success_rate": success_rate,
            "recent_actions": self.action_history[-10:]  # Last 10 actions
        }
    
    def record_action(self, action_result: Dict[str, Any]):
        """Record an action result"""
        self.total_actions += 1
        
        if action_result.get("success", False):
            self.successful_actions += 1
        
        # Add to history
        self.action_history.append({
            "timestamp": time.time(),
            "success": action_result.get("success", False),
            "action_type": action_result.get("action_type", "unknown"),
            "metrics": action_result.get("metrics", {})
        })
        
        # Keep history manageable
        if len(self.action_history) > 100:
            self.action_history = self.action_history[-100:]
    
    def get_action_types(self) -> List[str]:
        """Get list of action types this sport can detect"""
        return getattr(self, 'ACTION_TYPES', ['default_action'])
    
    def get_success_criteria(self) -> List[str]:
        """Get list of success criteria for this sport"""
        return getattr(self, 'SUCCESS_CRITERIA', ['default_success'])
    
    def calculate_performance_trend(self, window_size: int = 10) -> float:
        """Calculate performance trend over recent actions"""
        if len(self.action_history) < window_size:
            return 0.0
        
        recent_actions = self.action_history[-window_size:]
        recent_success_rate = sum(1 for action in recent_actions if action["success"]) / len(recent_actions)
        
        if len(self.action_history) >= window_size * 2:
            previous_actions = self.action_history[-(window_size * 2):-window_size]
            previous_success_rate = sum(1 for action in previous_actions if action["success"]) / len(previous_actions)
            
            return recent_success_rate - previous_success_rate
        
        return 0.0
    
    def get_recommended_adjustments(self, analysis_result: Dict[str, Any]) -> List[str]:
        """Get recommended technique adjustments based on analysis"""
        # Default implementation - override in sport-specific classes
        adjustments = []
        
        if not analysis_result.get("success", False):
            adjustments.append("Focus on form and technique")
            adjustments.append("Practice the movement slowly")
        
        return adjustments
    
    def is_ready_for_action(self, current_time: float, cooldown: float = 2.0) -> bool:
        """Check if enough time has passed since last action"""
        return current_time - self.last_action_time >= cooldown
    
    def update_last_action_time(self, current_time: float):
        """Update the timestamp of the last detected action"""
        self.last_action_time = current_time
