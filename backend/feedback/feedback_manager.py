"""
Feedback Manager - Handles real-time feedback delivery

Manages visual, audio, and haptic feedback for detected actions.
"""

import asyncio
import logging
import pygame
import json
import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class FeedbackType(Enum):
    """Types of feedback"""
    VISUAL = "visual"
    AUDIO = "audio"
    HAPTIC = "haptic"
    TEXT = "text"

@dataclass
class FeedbackConfig:
    """Configuration for feedback settings"""
    visual_enabled: bool = True
    audio_enabled: bool = True
    haptic_enabled: bool = False
    text_enabled: bool = True
    
    # Audio settings
    volume: float = 0.7
    success_sound: str = "success.wav"
    failure_sound: str = "failure.wav"
    
    # Visual settings
    display_duration: float = 3.0
    overlay_opacity: float = 0.8
    
    # Haptic settings
    vibration_duration: int = 200  # milliseconds
    success_pattern: List[int] = None
    failure_pattern: List[int] = None

class FeedbackManager:
    """Manages all types of feedback for sports actions"""
    
    def __init__(self):
        self.config = FeedbackConfig()
        self.is_active = False
        
        # Audio system
        self.audio_initialized = False
        self.sound_cache = {}
        
        # Feedback queue
        self.feedback_queue = asyncio.Queue()
        self.active_feedback = []
        
        # Statistics
        self.total_feedback_sent = 0
        self.feedback_history = []
        
        logger.info("FeedbackManager initialized")
    
    def start(self):
        """Start the feedback manager"""
        try:
            self._initialize_audio()
            self.is_active = True
            
            # Start feedback processing loop
            asyncio.create_task(self._process_feedback_loop())
            
            logger.info("FeedbackManager started")
            
        except Exception as e:
            logger.error(f"Failed to start FeedbackManager: {e}")
    
    def stop(self):
        """Stop the feedback manager"""
        try:
            self.is_active = False
            
            if self.audio_initialized:
                pygame.mixer.quit()
                pygame.quit()
            
            logger.info("FeedbackManager stopped")
            
        except Exception as e:
            logger.error(f"Error stopping FeedbackManager: {e}")
    
    def _initialize_audio(self):
        """Initialize pygame audio system"""
        try:
            pygame.mixer.pre_init(frequency=22050, size=-16, channels=2, buffer=512)
            pygame.mixer.init()
            pygame.init()
            
            # Load default sounds
            self._load_default_sounds()
            
            self.audio_initialized = True
            logger.info("Audio system initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize audio: {e}")
            self.config.audio_enabled = False
    
    def _load_default_sounds(self):
        """Load default feedback sounds"""
        try:
            # Create simple sounds programmatically if files don't exist
            self._create_default_sounds()
            
        except Exception as e:
            logger.error(f"Error loading sounds: {e}")
    
    def _create_default_sounds(self):
        """Create simple feedback sounds"""
        try:
            import numpy as np
            
            # Create success sound (higher pitch beep)
            duration = 0.3
            sample_rate = 22050
            frequency = 800
            
            frames = int(duration * sample_rate)
            arr = np.zeros(frames)
            
            for i in range(frames):
                arr[i] = np.sin(2 * np.pi * frequency * i / sample_rate)
              # Convert to pygame sound
            arr = (arr * 32767).astype(np.int16)
            # Create stereo array properly
            stereo_arr = np.zeros((frames, 2), dtype=np.int16)
            stereo_arr[:, 0] = arr  # Left channel
            stereo_arr[:, 1] = arr  # Right channel
            
            success_sound = pygame.sndarray.make_sound(stereo_arr)
            self.sound_cache["success"] = success_sound
            
            # Create failure sound (lower pitch buzz)
            frequency = 200
            for i in range(frames):
                arr[i] = np.sin(2 * np.pi * frequency * i / sample_rate)
            
            arr = (arr * 32767).astype(np.int16)
            # Create stereo array for failure sound
            stereo_arr = np.zeros((frames, 2), dtype=np.int16)
            stereo_arr[:, 0] = arr  # Left channel
            stereo_arr[:, 1] = arr  # Right channel            
            failure_sound = pygame.sndarray.make_sound(stereo_arr)
            self.sound_cache["failure"] = failure_sound
            
            logger.info("Default sounds created")
            
        except Exception as e:
            logger.error(f"Error creating default sounds: {e}")
    
    async def send_feedback(self, action_result: Dict[str, Any], feedback_types: List[FeedbackType] = None):
        """Send feedback for an action result"""
        try:
            if not self.is_active:
                return
            
            if feedback_types is None:
                feedback_types = [FeedbackType.VISUAL, FeedbackType.AUDIO, FeedbackType.TEXT]
            
            feedback_data = {
                "timestamp": time.time(),
                "action_result": action_result,
                "feedback_types": feedback_types,
                "success": action_result.get("success", False),
                "message": action_result.get("feedback_message", ""),
                "sport": action_result.get("sport", "unknown"),
                "action_type": action_result.get("action_type", "unknown")
            }
            
            # Add to queue for processing
            await self.feedback_queue.put(feedback_data)
            
            self.total_feedback_sent += 1
            
        except Exception as e:
            logger.error(f"Error sending feedback: {e}")
    
    async def _process_feedback_loop(self):
        """Main feedback processing loop"""
        try:
            while self.is_active:
                try:
                    # Get feedback from queue with timeout
                    feedback_data = await asyncio.wait_for(
                        self.feedback_queue.get(), 
                        timeout=1.0
                    )
                    
                    # Process the feedback
                    await self._process_feedback(feedback_data)
                    
                except asyncio.TimeoutError:
                    # Continue loop if no feedback in queue
                    continue
                    
                except Exception as e:
                    logger.error(f"Error processing feedback: {e}")
                    
        except Exception as e:
            logger.error(f"Error in feedback processing loop: {e}")
    
    async def _process_feedback(self, feedback_data: Dict[str, Any]):
        """Process individual feedback item"""
        try:
            feedback_types = feedback_data["feedback_types"]
            success = feedback_data["success"]
            message = feedback_data["message"]
            
            # Process each feedback type
            for feedback_type in feedback_types:
                if feedback_type == FeedbackType.AUDIO and self.config.audio_enabled:
                    await self._send_audio_feedback(success, feedback_data)
                
                elif feedback_type == FeedbackType.VISUAL and self.config.visual_enabled:
                    await self._send_visual_feedback(success, message, feedback_data)
                
                elif feedback_type == FeedbackType.HAPTIC and self.config.haptic_enabled:
                    await self._send_haptic_feedback(success, feedback_data)
                
                elif feedback_type == FeedbackType.TEXT and self.config.text_enabled:
                    await self._send_text_feedback(message, feedback_data)
            
            # Add to history
            self.feedback_history.append(feedback_data)
            
            # Keep history manageable
            if len(self.feedback_history) > 100:
                self.feedback_history = self.feedback_history[-100:]
            
            logger.info(f"Feedback processed: {feedback_data['action_type']} - "
                       f"{'Success' if success else 'Failed'}")
            
        except Exception as e:
            logger.error(f"Error processing individual feedback: {e}")
    
    async def _send_audio_feedback(self, success: bool, feedback_data: Dict[str, Any]):
        """Send audio feedback"""
        try:
            if not self.audio_initialized:
                return
            
            sound_key = "success" if success else "failure"
            
            if sound_key in self.sound_cache:
                sound = self.sound_cache[sound_key]
                sound.set_volume(self.config.volume)
                sound.play()
                
                logger.debug(f"Audio feedback played: {sound_key}")
            
        except Exception as e:
            logger.error(f"Error sending audio feedback: {e}")
    
    async def _send_visual_feedback(self, success: bool, message: str, feedback_data: Dict[str, Any]):
        """Send visual feedback (overlay, colors, etc.)"""
        try:
            # Visual feedback would be handled by the frontend
            # For now, just log the feedback
            
            visual_feedback = {
                "type": "visual",
                "success": success,
                "message": message,
                "color": "green" if success else "red",
                "duration": self.config.display_duration,
                "opacity": self.config.overlay_opacity,
                "timestamp": time.time()
            }
            
            # This would be sent to frontend via WebSocket
            logger.debug(f"Visual feedback: {visual_feedback}")
            
        except Exception as e:
            logger.error(f"Error sending visual feedback: {e}")
    
    async def _send_haptic_feedback(self, success: bool, feedback_data: Dict[str, Any]):
        """Send haptic feedback (vibration patterns)"""
        try:
            # Haptic feedback would require mobile app or smartwatch integration
            # For now, just log the feedback
            
            pattern = self.config.success_pattern if success else self.config.failure_pattern
            
            haptic_feedback = {
                "type": "haptic",
                "success": success,
                "pattern": pattern or [self.config.vibration_duration],
                "timestamp": time.time()
            }
            
            # This would be sent to mobile app via WebSocket
            logger.debug(f"Haptic feedback: {haptic_feedback}")
            
        except Exception as e:
            logger.error(f"Error sending haptic feedback: {e}")
    
    async def _send_text_feedback(self, message: str, feedback_data: Dict[str, Any]):
        """Send text feedback"""
        try:
            text_feedback = {
                "type": "text",
                "message": message,
                "timestamp": time.time(),
                "action_type": feedback_data.get("action_type", ""),
                "sport": feedback_data.get("sport", "")
            }
            
            # This would be sent to frontend via WebSocket
            logger.info(f"Text feedback: {message}")
            
        except Exception as e:
            logger.error(f"Error sending text feedback: {e}")
    
    def configure(self, new_config: Dict[str, Any]):
        """Update feedback configuration"""
        try:
            # Update configuration
            for key, value in new_config.items():
                if hasattr(self.config, key):
                    setattr(self.config, key, value)
              # Reinitialize audio if settings changed
            if "volume" in new_config and self.audio_initialized:
                # Set volume for all cached sounds
                for sound in self.sound_cache.values():
                    sound.set_volume(self.config.volume)
            
            logger.info(f"Feedback configuration updated: {new_config}")
            
        except Exception as e:
            logger.error(f"Error updating feedback configuration: {e}")
    
    def get_feedback_stats(self) -> Dict[str, Any]:
        """Get feedback system statistics"""
        return {
            "total_feedback_sent": self.total_feedback_sent,
            "audio_initialized": self.audio_initialized,
            "is_active": self.is_active,
            "config": {
                "visual_enabled": self.config.visual_enabled,
                "audio_enabled": self.config.audio_enabled,
                "haptic_enabled": self.config.haptic_enabled,
                "text_enabled": self.config.text_enabled,
                "volume": self.config.volume
            },
            "recent_feedback": self.feedback_history[-5:] if self.feedback_history else []
        }
    
    async def send_motivational_message(self, performance_data: Dict[str, Any]):
        """Send motivational message based on performance"""
        try:
            success_rate = performance_data.get("success_rate", 0)
            total_actions = performance_data.get("total_actions", 0)
            
            if total_actions == 0:
                return
            
            # Generate motivational message
            if success_rate >= 80:
                messages = [
                    "Excellent performance! You're on fire!",
                    "Outstanding accuracy! Keep it up!",
                    "You're in the zone! Great shooting!"
                ]
            elif success_rate >= 60:
                messages = [
                    "Good work! You're improving!",
                    "Nice consistency! Keep practicing!",
                    "You're getting better! Stay focused!"
                ]
            else:
                messages = [
                    "Keep practicing! You've got this!",
                    "Don't give up! Every miss is a lesson!",
                    "Focus on form! Improvement is coming!"
                ]
            
            import random
            message = random.choice(messages)
            
            # Send as text feedback
            await self.send_feedback({
                "success": True,
                "feedback_message": message,
                "action_type": "motivational",
                "sport": "general"
            }, [FeedbackType.TEXT, FeedbackType.AUDIO])
            
        except Exception as e:
            logger.error(f"Error sending motivational message: {e}")
    
    def load_custom_sounds(self, sound_files: Dict[str, str]):
        """Load custom sound files"""
        try:
            for sound_name, file_path in sound_files.items():
                try:
                    sound = pygame.mixer.Sound(file_path)
                    self.sound_cache[sound_name] = sound
                    logger.info(f"Loaded custom sound: {sound_name}")
                except Exception as e:
                    logger.error(f"Failed to load sound {sound_name}: {e}")
                    
        except Exception as e:
            logger.error(f"Error loading custom sounds: {e}")
    
    async def test_feedback_system(self):
        """Test all feedback types"""
        try:
            # Test success feedback
            await self.send_feedback({
                "success": True,
                "feedback_message": "Test successful action",
                "action_type": "test",
                "sport": "test"
            })
            
            await asyncio.sleep(1)
            
            # Test failure feedback
            await self.send_feedback({
                "success": False,
                "feedback_message": "Test failed action",
                "action_type": "test",
                "sport": "test"
            })
            
            logger.info("Feedback system test completed")
            
        except Exception as e:
            logger.error(f"Error testing feedback system: {e}")
