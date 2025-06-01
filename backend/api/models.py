"""
Pydantic models for API request/response validation

This module contains all the data models used by the FastAPI endpoints.
"""

from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum


class SportType(str, Enum):
    """Available sport types"""
    basketball = "basketball"
    tennis = "tennis"
    soccer = "soccer"
    football = "soccer"  # Alias for soccer
    golf = "golf"


class FeedbackType(str, Enum):
    """Types of feedback"""
    audio = "audio"
    visual = "visual"
    haptic = "haptic"
    text = "text"


class ActionType(str, Enum):
    """Types of actions that can be tracked"""
    # Basketball
    shot = "shot"
    free_throw = "free_throw"
    dribble = "dribble"
    
    # Tennis
    serve = "serve"
    forehand = "forehand"
    backhand = "backhand"
    volley = "volley"
    
    # Soccer
    kick = "kick"
    pass_action = "pass"
    header = "header"
    
    # Golf
    drive = "drive"
    iron_shot = "iron_shot"
    chip = "chip"
    putt = "putt"


class SessionStatus(str, Enum):
    """Session status types"""
    active = "active"
    paused = "paused"
    completed = "completed"
    cancelled = "cancelled"


class SportConfig(BaseModel):
    """Sport-specific configuration"""
    sport_name: str
    difficulty_level: Optional[str] = "medium"
    feedback_enabled: bool = True
    feedback_types: List[FeedbackType] = [FeedbackType.audio, FeedbackType.visual]
    custom_settings: Optional[Dict[str, Any]] = {}
    
    class Config:
        schema_extra = {
            "example": {
                "sport_name": "basketball",
                "difficulty_level": "medium",
                "feedback_enabled": True,
                "feedback_types": ["audio", "visual"],
                "custom_settings": {
                    "shot_distance_threshold": 2.0,
                    "success_angle_tolerance": 15
                }
            }
        }


class CameraConfig(BaseModel):
    """Camera configuration settings"""
    camera_index: int = 0
    resolution_width: int = 1280
    resolution_height: int = 720
    fps: int = 30
    auto_exposure: bool = True
    brightness: Optional[float] = None
    contrast: Optional[float] = None
    
    class Config:
        schema_extra = {
            "example": {
                "camera_index": 0,
                "resolution_width": 1280,
                "resolution_height": 720,
                "fps": 30,
                "auto_exposure": True
            }
        }


class SessionCreate(BaseModel):
    """Request model for creating a new session"""
    sport: SportType
    user_id: str
    config: Optional[SportConfig] = None
    duration_minutes: Optional[int] = None
    goals: Optional[List[str]] = []
    
    class Config:
        schema_extra = {
            "example": {
                "sport": "basketball",
                "user_id": "user123",
                "config": {
                    "sport_name": "basketball",
                    "difficulty_level": "medium",
                    "feedback_enabled": True,
                    "feedback_types": ["audio", "visual"]
                },
                "duration_minutes": 30,
                "goals": ["Improve shooting accuracy", "Better form"]
            }
        }


class SessionResponse(BaseModel):
    """Response model for session information"""
    session_id: str
    sport: str
    user_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    status: SessionStatus
    config: Optional[Dict[str, Any]] = None
    duration_minutes: Optional[int] = None
    goals: Optional[List[str]] = []
    
    class Config:
        schema_extra = {
            "example": {
                "session_id": "sess_12345",
                "sport": "basketball",
                "user_id": "user123",
                "start_time": "2024-01-15T10:30:00",
                "status": "active",
                "config": {"difficulty_level": "medium"},
                "duration_minutes": 30
            }
        }


class ActionResult(BaseModel):
    """Model for action detection results"""
    action: str
    timestamp: datetime
    success: bool
    confidence: float = Field(..., ge=0.0, le=1.0)
    analysis: Dict[str, Any]
    feedback: Optional[Dict[str, Any]] = None
    session_id: Optional[str] = None
    
    class Config:
        schema_extra = {
            "example": {
                "action": "shot",
                "timestamp": "2024-01-15T10:35:22",
                "success": True,
                "confidence": 0.85,
                "analysis": {
                    "release_angle": 45.2,
                    "arc_height": 3.2,
                    "technique_score": 82
                },
                "feedback": {
                    "message": "Great shot! Perfect arc!",
                    "type": "success"
                }
            }
        }


class FeedbackMessage(BaseModel):
    """Model for feedback messages"""
    message: str
    type: str  # success, improvement, instruction, encouragement
    audio: Optional[str] = None
    visual_effect: Optional[str] = None
    haptic_pattern: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)
    
    class Config:
        schema_extra = {
            "example": {
                "message": "Perfect shot! Excellent technique!",
                "type": "success",
                "audio": "perfect_shot.wav",
                "visual_effect": "perfect_shot_animation",
                "timestamp": "2024-01-15T10:35:22"
            }
        }


class SystemStatus(BaseModel):
    """System health and status information"""
    status: str  # healthy, degraded, unhealthy
    camera_available: bool
    pose_detector_ready: bool
    active_sessions: int
    timestamp: datetime
    error: Optional[str] = None
    
    class Config:
        schema_extra = {
            "example": {
                "status": "healthy",
                "camera_available": True,
                "pose_detector_ready": True,
                "active_sessions": 2,
                "timestamp": "2024-01-15T10:30:00"
            }
        }


class TrackingStatus(BaseModel):
    """Real-time tracking status"""
    tracking: bool
    session_id: Optional[str] = None
    camera_active: bool
    pose_detection_active: bool
    current_action: Optional[str] = None
    last_action_time: Optional[datetime] = None
    timestamp: datetime
    
    class Config:
        schema_extra = {
            "example": {
                "tracking": True,
                "session_id": "sess_12345",
                "camera_active": True,
                "pose_detection_active": True,
                "current_action": "shot",
                "timestamp": "2024-01-15T10:30:00"
            }
        }


class AnalyticsMetric(BaseModel):
    """Individual analytics metric"""
    name: str
    value: float
    unit: Optional[str] = None
    description: Optional[str] = None
    
    class Config:
        schema_extra = {
            "example": {
                "name": "shooting_accuracy",
                "value": 75.5,
                "unit": "percentage",
                "description": "Percentage of successful shots"
            }
        }


class SessionAnalytics(BaseModel):
    """Analytics for a specific session"""
    session_id: str
    total_actions: int
    successful_actions: int
    success_rate: float
    metrics: List[AnalyticsMetric]
    improvement_suggestions: List[str]
    session_duration: float  # in minutes
    
    class Config:
        schema_extra = {
            "example": {
                "session_id": "sess_12345",
                "total_actions": 25,
                "successful_actions": 18,
                "success_rate": 72.0,
                "metrics": [
                    {
                        "name": "average_technique_score",
                        "value": 78.5,
                        "unit": "score",
                        "description": "Average technique score"
                    }
                ],
                "improvement_suggestions": [
                    "Focus on follow-through",
                    "Improve shooting arc"
                ],
                "session_duration": 25.5
            }
        }


class UserAnalytics(BaseModel):
    """Overall analytics for a user"""
    user_id: str
    total_sessions: int
    total_actions: int
    overall_success_rate: float
    favorite_sport: Optional[str] = None
    improvement_trend: str  # improving, stable, declining
    metrics_by_sport: Dict[str, List[AnalyticsMetric]]
    recent_sessions: List[str]  # session IDs
    
    class Config:
        schema_extra = {
            "example": {
                "user_id": "user123",
                "total_sessions": 15,
                "total_actions": 450,
                "overall_success_rate": 68.5,
                "favorite_sport": "basketball",
                "improvement_trend": "improving",
                "metrics_by_sport": {
                    "basketball": [
                        {
                            "name": "shooting_accuracy",
                            "value": 70.5,
                            "unit": "percentage"
                        }
                    ]
                },
                "recent_sessions": ["sess_12345", "sess_12344"]
            }
        }


class WebSocketMessage(BaseModel):
    """WebSocket message format"""
    type: str  # action_detected, feedback, status_update, error
    data: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.now)
    session_id: Optional[str] = None
    
    class Config:
        schema_extra = {
            "example": {
                "type": "action_detected",
                "data": {
                    "action": "shot",
                    "success": True,
                    "confidence": 0.85
                },
                "timestamp": "2024-01-15T10:35:22",
                "session_id": "sess_12345"
            }
        }


class ErrorResponse(BaseModel):
    """Error response format"""
    error: str
    message: str
    timestamp: datetime = Field(default_factory=datetime.now)
    details: Optional[Dict[str, Any]] = None
    
    class Config:
        schema_extra = {
            "example": {
                "error": "ValidationError",
                "message": "Invalid sport type provided",
                "timestamp": "2024-01-15T10:30:00",
                "details": {"field": "sport", "value": "invalid_sport"}
            }
        }
