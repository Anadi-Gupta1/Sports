"""
Basketball Tracker - Sport-specific module for basketball action detection

Detects and analyzes basketball actions including shots, dribbling, and free throws.
"""

import cv2
import numpy as np
import time
import logging
from typing import Dict, Any, Optional, List, Tuple
import math

from backend.sports.base_sport import BaseSportTracker

logger = logging.getLogger(__name__)

class BasketballTracker(BaseSportTracker):
    """Basketball-specific action tracking"""
    
    ACTION_TYPES = ["shot", "free_throw", "three_pointer", "dribble", "pass"]
    SUCCESS_CRITERIA = ["ball_in_hoop", "successful_pass", "controlled_dribble"]
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        
        # Basketball-specific configuration
        self.shot_detection_config = config.get("shot_detection", {
            "min_arm_extension": 0.7,
            "release_angle_range": (30, 80),  # degrees
            "follow_through_time": 0.5,  # seconds
            "detection_zone": None  # Will be configured based on court
        })
        
        # Tracking state
        self.current_action_state = "idle"
        self.shot_preparation_frames = []
        self.last_wrist_positions = []
        self.shot_start_time = None
        self.ball_tracking_enabled = config.get("ball_tracking", True)
        
        # Court configuration
        self.court_config = config.get("court_config", {
            "hoop_position": {"x": 0.5, "y": 0.3},  # Normalized coordinates
            "free_throw_line": {"y": 0.6},
            "three_point_line": {"distance": 0.4}
        })
        
        logger.info("Basketball tracker initialized")
    
    def detect_action(self, frame: np.ndarray, pose_landmarks, pose_world_landmarks, action_buffer: List) -> Optional[Dict[str, Any]]:
        """Detect basketball actions (shots, dribbles, passes)"""
        try:
            if not pose_landmarks:
                return None
            
            # Get key landmarks
            landmarks = pose_landmarks.landmark
            
            # Get arm positions
            left_shoulder = landmarks[11]
            left_elbow = landmarks[13]
            left_wrist = landmarks[15]
            right_shoulder = landmarks[12]
            right_elbow = landmarks[14]
            right_wrist = landmarks[16]
            
            # Determine dominant hand (for shooting)
            dominant_hand = self._determine_dominant_hand(landmarks)
            
            # Detect different actions
            shot_action = self._detect_shot(frame, landmarks, dominant_hand, action_buffer)
            if shot_action:
                return shot_action
            
            dribble_action = self._detect_dribble(frame, landmarks, action_buffer)
            if dribble_action:
                return dribble_action
            
            pass_action = self._detect_pass(frame, landmarks, action_buffer)
            if pass_action:
                return pass_action
            
            return None
            
        except Exception as e:
            logger.error(f"Error detecting basketball action: {e}")
            return None
    
    def _detect_shot(self, frame: np.ndarray, landmarks, dominant_hand: str, action_buffer: List) -> Optional[Dict[str, Any]]:
        """Detect basketball shooting motion"""
        try:
            # Get shooting hand landmarks
            if dominant_hand == "right":
                shoulder = landmarks[12]
                elbow = landmarks[14]
                wrist = landmarks[16]
            else:
                shoulder = landmarks[11]
                elbow = landmarks[13]
                wrist = landmarks[15]
            
            # Calculate arm extension
            arm_extension = self._calculate_arm_extension(shoulder, elbow, wrist)
            
            # Calculate release angle
            release_angle = self._calculate_release_angle(shoulder, elbow, wrist)
            
            # Track wrist position over time
            wrist_position = (wrist.x, wrist.y, wrist.z)
            self.last_wrist_positions.append(wrist_position)
            
            # Keep only recent positions
            if len(self.last_wrist_positions) > 10:
                self.last_wrist_positions.pop(0)
            
            # Detect shooting motion phases
            current_time = time.time()
            
            # Phase 1: Preparation (arm coming up)
            if (self.current_action_state == "idle" and 
                arm_extension > 0.3 and 
                release_angle > 20 and 
                self._is_wrist_moving_up()):
                
                self.current_action_state = "preparing"
                self.shot_start_time = current_time
                self.shot_preparation_frames = []
                
            # Phase 2: Release (arm fully extended, wrist snap)
            elif (self.current_action_state == "preparing" and
                  arm_extension > self.shot_detection_config["min_arm_extension"] and
                  self.shot_detection_config["release_angle_range"][0] <= release_angle <= self.shot_detection_config["release_angle_range"][1] and
                  self._detect_wrist_snap()):
                
                # Shot detected!
                shot_type = self._determine_shot_type(landmarks)
                
                action_data = {
                    "action_type": shot_type,
                    "confidence": 0.8,
                    "timestamp": current_time,
                    "dominant_hand": dominant_hand,
                    "release_metrics": {
                        "arm_extension": arm_extension,
                        "release_angle": release_angle,
                        "wrist_position": wrist_position,
                        "preparation_time": current_time - self.shot_start_time if self.shot_start_time else 0
                    },
                    "frame_data": {
                        "preparation_frames": len(self.shot_preparation_frames),
                        "frame_shape": frame.shape
                    }
                }
                
                # Reset state
                self.current_action_state = "completed"
                self.shot_start_time = None
                
                return action_data
            
            # Timeout if preparation takes too long
            elif (self.current_action_state == "preparing" and 
                  current_time - self.shot_start_time > 3.0):
                self.current_action_state = "idle"
                self.shot_start_time = None
            
            # Store preparation frames
            if self.current_action_state == "preparing":
                self.shot_preparation_frames.append({
                    "timestamp": current_time,
                    "arm_extension": arm_extension,
                    "release_angle": release_angle,
                    "wrist_position": wrist_position
                })
            
            return None
            
        except Exception as e:
            logger.error(f"Error detecting shot: {e}")
            return None
    
    def _detect_dribble(self, frame: np.ndarray, landmarks, action_buffer: List) -> Optional[Dict[str, Any]]:
        """Detect basketball dribbling motion"""
        try:
            # Get hand positions
            left_wrist = landmarks[15]
            right_wrist = landmarks[16]
            
            # Check for rhythmic up-down motion of hands
            if len(action_buffer) < 5:
                return None
            
            # Analyze wrist movement patterns
            wrist_heights = []
            for frame_data in action_buffer[-5:]:
                if frame_data.get("pose_results") and frame_data["pose_results"].pose_landmarks:
                    landmarks_hist = frame_data["pose_results"].pose_landmarks.landmark
                    wrist_heights.append({
                        "left": landmarks_hist[15].y,
                        "right": landmarks_hist[16].y,
                        "timestamp": frame_data["timestamp"]
                    })
            
            if len(wrist_heights) < 5:
                return None
            
            # Check for dribbling pattern (rhythmic motion)
            if self._is_dribbling_pattern(wrist_heights):
                return {
                    "action_type": "dribble",
                    "confidence": 0.7,
                    "timestamp": time.time(),
                    "dribble_metrics": {
                        "frequency": self._calculate_dribble_frequency(wrist_heights),
                        "hand_used": self._determine_dribbling_hand(wrist_heights),
                        "consistency": self._calculate_dribble_consistency(wrist_heights)
                    }
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error detecting dribble: {e}")
            return None
    
    def _detect_pass(self, frame: np.ndarray, landmarks, action_buffer: List) -> Optional[Dict[str, Any]]:
        """Detect basketball passing motion"""
        try:
            # Get arm positions
            left_wrist = landmarks[15]
            right_wrist = landmarks[16]
            left_shoulder = landmarks[11]
            right_shoulder = landmarks[12]
            
            # Check for quick arm extension (passing motion)
            if len(action_buffer) < 3:
                return None
            
            # Calculate arm movement velocity
            arm_velocity = self._calculate_arm_velocity(action_buffer)
            
            # Check for pass characteristics
            if (arm_velocity > 0.5 and  # Quick movement
                self._both_hands_involved(landmarks) and  # Two-handed pass
                self._forward_motion_detected(action_buffer)):  # Forward direction
                
                return {
                    "action_type": "pass",
                    "confidence": 0.6,
                    "timestamp": time.time(),
                    "pass_metrics": {
                        "velocity": arm_velocity,
                        "pass_type": self._determine_pass_type(landmarks),
                        "direction": self._calculate_pass_direction(action_buffer)
                    }
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error detecting pass: {e}")
            return None
    
    def analyze_action(self, action_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze basketball action for success/failure and provide feedback"""
        try:
            action_type = action_data["action_type"]
            
            if action_type in ["shot", "free_throw", "three_pointer"]:
                return self._analyze_shot(action_data)
            elif action_type == "dribble":
                return self._analyze_dribble(action_data)
            elif action_type == "pass":
                return self._analyze_pass(action_data)
            else:
                return {
                    "success": False,
                    "confidence": 0.0,
                    "feedback_message": "Unknown action type",
                    "metrics": {}
                }
                
        except Exception as e:
            logger.error(f"Error analyzing action: {e}")
            return {
                "success": False,
                "confidence": 0.0,
                "feedback_message": "Analysis error",
                "metrics": {}
            }
    
    def _analyze_shot(self, action_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze shooting technique and success"""
        metrics = action_data.get("release_metrics", {})
        
        # Evaluate technique
        technique_score = 0
        feedback_points = []
        
        # Release angle analysis
        release_angle = metrics.get("release_angle", 0)
        optimal_range = self.shot_detection_config["release_angle_range"]
        
        if optimal_range[0] <= release_angle <= optimal_range[1]:
            technique_score += 30
        else:
            if release_angle < optimal_range[0]:
                feedback_points.append("Release angle too low - aim higher")
            else:
                feedback_points.append("Release angle too high - follow through down")
        
        # Arm extension analysis
        arm_extension = metrics.get("arm_extension", 0)
        if arm_extension >= self.shot_detection_config["min_arm_extension"]:
            technique_score += 25
        else:
            feedback_points.append("Extend your shooting arm fully")
        
        # Preparation time analysis
        prep_time = metrics.get("preparation_time", 0)
        if 0.5 <= prep_time <= 2.0:  # Optimal preparation time
            technique_score += 20
        else:
            if prep_time < 0.5:
                feedback_points.append("Too quick - take more time to set up")
            else:
                feedback_points.append("Too slow - practice quicker release")
        
        # Consistency bonus (if multiple shots in history)
        if len(self.action_history) > 3:
            recent_angles = [action.get("metrics", {}).get("release_angle", 0) 
                           for action in self.action_history[-3:]]
            angle_variance = np.var(recent_angles) if recent_angles else 0
            
            if angle_variance < 100:  # Low variance = consistent
                technique_score += 25
                feedback_points.append("Great consistency!")
        
        # Determine success (in real scenario, would use ball tracking)
        # For now, use technique score as proxy
        success = technique_score >= 70
        
        if not feedback_points:
            feedback_points.append("Excellent form!" if success else "Keep practicing!")
        
        return {
            "success": success,
            "confidence": min(technique_score / 100, 1.0),
            "technique_score": technique_score,
            "feedback_message": " | ".join(feedback_points),
            "metrics": {
                "release_angle": release_angle,
                "arm_extension": arm_extension,
                "preparation_time": prep_time,
                "technique_score": technique_score
            },
            "recommendations": self._get_shot_recommendations(metrics, technique_score)
        }
    
    def _analyze_dribble(self, action_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze dribbling technique"""
        metrics = action_data.get("dribble_metrics", {})
        
        frequency = metrics.get("frequency", 0)
        consistency = metrics.get("consistency", 0)
        
        # Evaluate dribbling
        success = frequency > 1.0 and consistency > 0.7  # Good frequency and consistency
        
        feedback = []
        if frequency < 1.0:
            feedback.append("Dribble faster for better control")
        if consistency < 0.7:
            feedback.append("Focus on consistent rhythm")
        
        if success:
            feedback.append("Good dribbling control!")
        
        return {
            "success": success,
            "confidence": 0.8,
            "feedback_message": " | ".join(feedback) if feedback else "Good dribbling",
            "metrics": metrics
        }
    
    def _analyze_pass(self, action_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze passing technique"""
        metrics = action_data.get("pass_metrics", {})
        
        velocity = metrics.get("velocity", 0)
        pass_type = metrics.get("pass_type", "unknown")
        
        # Evaluate pass
        success = velocity > 0.3  # Sufficient velocity
        
        feedback = []
        if velocity < 0.3:
            feedback.append("Put more power into your pass")
        else:
            feedback.append("Good pass velocity!")
        
        return {
            "success": success,
            "confidence": 0.7,
            "feedback_message": " | ".join(feedback),
            "metrics": metrics
        }
    
    def get_feedback_message(self, analysis_result: Dict[str, Any]) -> str:
        """Generate feedback message for basketball actions"""
        return analysis_result.get("feedback_message", "Keep practicing!")
    
    @classmethod
    def get_sport_info(cls) -> Dict[str, Any]:
        """Get basketball sport information"""
        return {
            "name": "Basketball",
            "action_types": cls.ACTION_TYPES,
            "success_criteria": cls.SUCCESS_CRITERIA,
            "configuration_options": {
                "shot_detection": {
                    "min_arm_extension": {"type": "float", "range": [0.5, 1.0], "default": 0.7},
                    "release_angle_range": {"type": "tuple", "default": [30, 80]},
                    "follow_through_time": {"type": "float", "range": [0.1, 1.0], "default": 0.5}
                },
                "court_config": {
                    "hoop_position": {"type": "coordinates", "default": {"x": 0.5, "y": 0.3}},
                    "free_throw_line": {"type": "coordinates", "default": {"y": 0.6}},
                    "three_point_line": {"type": "distance", "default": 0.4}
                }
            },
            "recommended_camera_setup": {
                "position": "Side view of shooting area",
                "height": "Chest level or higher",
                "distance": "10-15 feet from player"
            }
        }
    
    # Helper methods
    def _determine_dominant_hand(self, landmarks) -> str:
        """Determine dominant shooting hand based on arm position"""
        left_wrist = landmarks[15]
        right_wrist = landmarks[16]
        
        # Simple heuristic: higher wrist is likely the shooting hand
        return "right" if right_wrist.y < left_wrist.y else "left"
    
    def _calculate_arm_extension(self, shoulder, elbow, wrist) -> float:
        """Calculate how extended the arm is (0-1)"""
        try:
            # Calculate distances
            shoulder_to_elbow = math.sqrt(
                (shoulder.x - elbow.x)**2 + (shoulder.y - elbow.y)**2 + (shoulder.z - elbow.z)**2
            )
            elbow_to_wrist = math.sqrt(
                (elbow.x - wrist.x)**2 + (elbow.y - wrist.y)**2 + (elbow.z - wrist.z)**2
            )
            shoulder_to_wrist = math.sqrt(
                (shoulder.x - wrist.x)**2 + (shoulder.y - wrist.y)**2 + (shoulder.z - wrist.z)**2
            )
            
            # Calculate extension ratio
            max_extension = shoulder_to_elbow + elbow_to_wrist
            current_extension = shoulder_to_wrist
            
            return min(current_extension / max_extension, 1.0) if max_extension > 0 else 0
            
        except:
            return 0.0
    
    def _calculate_release_angle(self, shoulder, elbow, wrist) -> float:
        """Calculate release angle in degrees"""
        try:
            # Vector from elbow to wrist
            arm_vector = np.array([wrist.x - elbow.x, wrist.y - elbow.y])
            
            # Calculate angle with horizontal
            angle = math.degrees(math.atan2(-arm_vector[1], arm_vector[0]))  # Negative y for upward
            
            return max(0, angle) if angle > 0 else 0
            
        except:
            return 0.0
    
    def _is_wrist_moving_up(self) -> bool:
        """Check if wrist is moving upward"""
        if len(self.last_wrist_positions) < 3:
            return False
        
        recent_y = [pos[1] for pos in self.last_wrist_positions[-3:]]
        return recent_y[0] > recent_y[-1]  # y decreases as we move up in image coordinates
    
    def _detect_wrist_snap(self) -> bool:
        """Detect wrist snap motion (quick downward movement)"""
        if len(self.last_wrist_positions) < 3:
            return False
        
        # Check for quick wrist movement
        recent_positions = self.last_wrist_positions[-3:]
        
        # Calculate movement magnitude
        movement = math.sqrt(
            (recent_positions[-1][0] - recent_positions[0][0])**2 +
            (recent_positions[-1][1] - recent_positions[0][1])**2
        )
        
        return movement > 0.05  # Threshold for wrist snap
    
    def _determine_shot_type(self, landmarks) -> str:
        """Determine type of shot based on player position"""
        # For now, default to "shot"
        # In real implementation, would use court position
        return "shot"
    
    def _is_dribbling_pattern(self, wrist_heights: List[Dict]) -> bool:
        """Check if wrist movement shows dribbling pattern"""
        # Simple pattern detection - would be more sophisticated in real implementation
        if len(wrist_heights) < 5:
            return False
        
        # Check for rhythmic up-down motion
        heights = [h["left"] for h in wrist_heights] + [h["right"] for h in wrist_heights]
        
        # Calculate variance in heights (rhythmic motion should have variance)
        variance = np.var(heights)
        
        return variance > 0.001  # Threshold for rhythmic motion
    
    def _calculate_dribble_frequency(self, wrist_heights: List[Dict]) -> float:
        """Calculate dribbling frequency"""
        # Simplified calculation
        return len(wrist_heights) / 2.0  # Approximate frequency
    
    def _determine_dribbling_hand(self, wrist_heights: List[Dict]) -> str:
        """Determine which hand is dribbling"""
        left_variance = np.var([h["left"] for h in wrist_heights])
        right_variance = np.var([h["right"] for h in wrist_heights])
        
        return "left" if left_variance > right_variance else "right"
    
    def _calculate_dribble_consistency(self, wrist_heights: List[Dict]) -> float:
        """Calculate dribbling consistency (0-1)"""
        # Simplified consistency calculation
        return 0.8  # Placeholder
    
    def _calculate_arm_velocity(self, action_buffer: List) -> float:
        """Calculate arm movement velocity"""
        # Simplified velocity calculation
        return 0.7  # Placeholder
    
    def _both_hands_involved(self, landmarks) -> bool:
        """Check if both hands are involved in motion"""
        # Simplified check
        return True  # Placeholder
    
    def _forward_motion_detected(self, action_buffer: List) -> bool:
        """Check for forward motion indicating a pass"""
        # Simplified check
        return True  # Placeholder
    
    def _determine_pass_type(self, landmarks) -> str:
        """Determine type of pass"""
        return "chest_pass"  # Placeholder
    
    def _calculate_pass_direction(self, action_buffer: List) -> str:
        """Calculate pass direction"""
        return "forward"  # Placeholder
    
    def _get_shot_recommendations(self, metrics: Dict[str, Any], technique_score: int) -> List[str]:
        """Get specific recommendations for improving shot"""
        recommendations = []
        
        if technique_score < 70:
            recommendations.append("Practice shooting form daily")
            recommendations.append("Focus on consistent release point")
        
        release_angle = metrics.get("release_angle", 0)
        if release_angle < 30:
            recommendations.append("Increase arc on your shot")
        elif release_angle > 80:
            recommendations.append("Lower your release angle")
        
        if metrics.get("preparation_time", 0) > 2.0:
            recommendations.append("Practice quicker shot release")
        
        return recommendations
