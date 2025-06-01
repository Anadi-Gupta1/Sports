"""
Configuration settings for the Multi-Sport Action Tracker

Centralized configuration management using Pydantic for validation.
"""

import os
from pydantic import BaseSettings, Field
from typing import Dict, List, Optional, Any
from pathlib import Path

class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # Application
    app_name: str = "Multi-Sport Action Tracker"
    app_version: str = "1.0.0"
    debug_mode: bool = Field(False, env="DEBUG")
    
    # Server
    host: str = Field("0.0.0.0", env="HOST")
    port: int = Field(8000, env="PORT")
    reload: bool = Field(True, env="RELOAD")
    
    # Database
    database_url: str = Field("sqlite:///./data/sports_tracker.db", env="DATABASE_URL")
    
    # Camera Settings
    default_camera_index: int = Field(0, env="CAMERA_INDEX")
    default_camera_width: int = Field(1280, env="CAMERA_WIDTH")
    default_camera_height: int = Field(720, env="CAMERA_HEIGHT")
    default_camera_fps: int = Field(30, env="CAMERA_FPS")
    
    # Computer Vision
    pose_model_complexity: int = Field(1, env="POSE_MODEL_COMPLEXITY")  # 0, 1, 2
    min_detection_confidence: float = Field(0.5, env="MIN_DETECTION_CONFIDENCE")
    min_tracking_confidence: float = Field(0.5, env="MIN_TRACKING_CONFIDENCE")
    
    # Processing
    max_frame_buffer_size: int = Field(30, env="MAX_FRAME_BUFFER_SIZE")
    processing_interval_ms: int = Field(33, env="PROCESSING_INTERVAL_MS")  # ~30 FPS
    
    # Feedback
    audio_enabled: bool = Field(True, env="AUDIO_ENABLED")
    visual_feedback_enabled: bool = Field(True, env="VISUAL_FEEDBACK_ENABLED")
    default_volume: float = Field(0.7, env="DEFAULT_VOLUME")
    
    # File Paths
    models_dir: str = Field("./models", env="MODELS_DIR")
    data_dir: str = Field("./data", env="DATA_DIR")
    logs_dir: str = Field("./logs", env="LOGS_DIR")
    temp_dir: str = Field("./temp", env="TEMP_DIR")
    
    # Export Settings
    max_export_sessions: int = Field(100, env="MAX_EXPORT_SESSIONS")
    export_formats: List[str] = Field(["json", "csv"], env="EXPORT_FORMATS")
    
    # Security
    allowed_origins: List[str] = Field([
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ], env="ALLOWED_ORIGINS")
    
    # Sport-Specific Defaults
    sport_configs: Dict[str, Dict[str, Any]] = Field(default_factory=lambda: {
        "basketball": {
            "shot_detection_threshold": 0.8,
            "hoop_detection_enabled": True,
            "arc_analysis_enabled": True,
            "feedback_messages": {
                "success": ["Great shot!", "Perfect form!", "On target!"],
                "miss": ["Keep practicing!", "Adjust your aim", "Try again!"]
            }
        },
        "tennis": {
            "serve_detection_threshold": 0.7,
            "court_detection_enabled": True,
            "speed_analysis_enabled": True,
            "feedback_messages": {
                "success": ["Ace!", "Perfect serve!", "Great power!"],
                "fault": ["Fault! Try again", "Watch your foot position", "Adjust your angle"]
            }
        },
        "soccer": {
            "kick_detection_threshold": 0.6,
            "goal_detection_enabled": True,
            "power_analysis_enabled": True,
            "feedback_messages": {
                "success": ["Goal!", "Perfect kick!", "Great accuracy!"],
                "miss": ["Close one!", "Keep trying!", "Focus on accuracy"]
            }
        },
        "golf": {
            "swing_detection_threshold": 0.8,
            "club_tracking_enabled": True,
            "swing_analysis_enabled": True,
            "feedback_messages": {
                "success": ["Perfect swing!", "Great form!", "Excellent!"],
                "improvement": ["Watch your posture", "Smooth your swing", "Keep practicing"]
            }
        }
    })
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

# Create global settings instance
settings = Settings()

def get_settings() -> Settings:
    """Get application settings"""
    return settings

def ensure_directories():
    """Ensure all required directories exist"""
    directories = [
        settings.data_dir,
        settings.logs_dir,
        settings.temp_dir,
        settings.models_dir
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)

# Initialize directories on import
ensure_directories()
