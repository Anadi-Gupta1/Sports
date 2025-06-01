"""
Soccer-specific action tracking module.
Detects kicks, headers, dribbles, and passes.
"""

import cv2
import numpy as np
from typing import Dict, List, Optional, Tuple
from .base_sport import BaseSport
from ..core.pose_detector import PoseDetector


class SoccerTracker(BaseSport):
    """Soccer action tracker for kicks, headers, and ball control."""
    
    def __init__(self, config: Dict):
        super().__init__("soccer", config)
        self.sport_specific_config = {
            "kick_velocity_threshold": 3.0,  # Minimum foot velocity for kick
            "header_height_threshold": 0.8,  # Head height for header detection
            "dribble_touch_interval": 0.5,  # Seconds between dribble touches
            "pass_accuracy_zone": 0.2,  # Target zone accuracy
            "kick_power_zones": {
                "light": (0, 30),
                "medium": (30, 70),
                "powerful": (70, 100)
            },
            "technique_thresholds": {
                "excellent": 85,
                "good": 70,
                "needs_work": 50
            }
        }
        self.sport_specific_config.update(config.get("soccer", {}))
        
        # Tracking variables
        self.kick_started = False
        self.header_started = False
        self.dribble_active = False
        self.foot_position = None
        self.foot_velocity = 0
        self.head_position = None
        self.kick_trajectory = []
        self.dribble_touches = []
        self.last_touch_time = 0
        
    def detect_action(self, frame: np.ndarray, pose_landmarks) -> Optional[Dict]:
        """Detect soccer actions (kick, header, dribble, pass)."""
        if pose_landmarks is None:
            return None
            
        # Get key body points
        landmarks = pose_landmarks.landmark
        
        # Foot positions (prioritize right foot)
        right_ankle = self._get_landmark_coords(landmarks[28], frame.shape)
        left_ankle = self._get_landmark_coords(landmarks[27], frame.shape)
        right_knee = self._get_landmark_coords(landmarks[26], frame.shape)
        left_knee = self._get_landmark_coords(landmarks[25], frame.shape)
        
        # Head position for headers
        nose = self._get_landmark_coords(landmarks[0], frame.shape)
        
        if not all([right_ankle, left_ankle, right_knee, left_knee, nose]):
            return None
            
        # Update foot position and velocity (use right foot primarily)
        active_foot = right_ankle
        active_knee = right_knee
        
        if self.foot_position is not None:
            velocity = np.linalg.norm(np.array(active_foot) - np.array(self.foot_position))
            self.foot_velocity = velocity
        self.foot_position = active_foot
        self.head_position = nose
        
        # Detect different soccer actions
        kick_action = self._detect_kick(active_foot, active_knee, frame.shape)
        header_action = self._detect_header(nose, frame.shape)
        dribble_action = self._detect_dribble(active_foot)
        
        if kick_action:
            return kick_action
        elif header_action:
            return header_action
        elif dribble_action:
            return dribble_action
            
        return None
        
    def _detect_kick(self, ankle, knee, frame_shape) -> Optional[Dict]:
        """Detect soccer kick motion."""
        # Calculate leg extension and foot velocity
        leg_angle = self._calculate_angle([ankle[0], ankle[1] + 50], knee, ankle)
        
        # Kick detection based on foot velocity and leg movement
        if self.foot_velocity > self.sport_specific_config["kick_velocity_threshold"]:
            if not self.kick_started:
                self.kick_started = True
                self.kick_trajectory = [ankle]
                return None
            else:
                self.kick_trajectory.append(ankle)
                
        elif self.kick_started and self.foot_velocity < 1.0:
            # Kick completed
            self.kick_started = False
            kick_analysis = self._analyze_kick()
            
            # Determine kick type
            kick_type = self._classify_kick_type()
            
            return {
                "action": kick_type,
                "timestamp": self._get_timestamp(),
                "success": kick_analysis["success"],
                "analysis": kick_analysis,
                "confidence": 0.82
            }
            
        return None
        
    def _detect_header(self, nose, frame_shape) -> Optional[Dict]:
        """Detect soccer header motion."""
        head_height = 1 - (nose[1] / frame_shape[0])  # Normalized height
        
        # Header detection based on head position and movement
        if head_height > self.sport_specific_config["header_height_threshold"]:
            if not self.header_started:
                self.header_started = True
                return None
                
        elif self.header_started and head_height < 0.6:
            # Header completed
            self.header_started = False
            header_analysis = self._analyze_header()
            
            return {
                "action": "header",
                "timestamp": self._get_timestamp(),
                "success": header_analysis["success"],
                "analysis": header_analysis,
                "confidence": 0.75
            }
            
        return None
        
    def _detect_dribble(self, ankle) -> Optional[Dict]:
        """Detect soccer dribbling touches."""
        current_time = self._get_timestamp()
        
        # Check for quick foot movements (dribbling)
        if (self.foot_velocity > 2.0 and 
            current_time - self.last_touch_time > self.sport_specific_config["dribble_touch_interval"]):
            
            self.dribble_touches.append({
                "position": ankle,
                "timestamp": current_time,
                "velocity": self.foot_velocity
            })
            self.last_touch_time = current_time
            
            # If we have multiple touches in sequence, it's dribbling
            if len(self.dribble_touches) >= 3:
                dribble_analysis = self._analyze_dribble()
                
                # Reset for next sequence
                self.dribble_touches = []
                
                return {
                    "action": "dribble",
                    "timestamp": current_time,
                    "success": dribble_analysis["success"],
                    "analysis": dribble_analysis,
                    "confidence": 0.70
                }
                
        return None
        
    def _analyze_kick(self) -> Dict:
        """Analyze kick technique and power."""
        if len(self.kick_trajectory) < 3:
            return {"success": False, "reason": "Incomplete kick motion"}
            
        # Calculate kick power based on trajectory and velocity
        trajectory_length = len(self.kick_trajectory)
        max_velocity = max([self.foot_velocity] + [3.0])  # Ensure minimum
        
        # Power estimation
        power_score = min(100, (max_velocity * 10) + (trajectory_length * 2))
        
        # Determine power zone
        power_zone = "light"
        for zone, (min_power, max_power) in self.sport_specific_config["kick_power_zones"].items():
            if min_power <= power_score <= max_power:
                power_zone = zone
                break
                
        # Technique analysis
        technique_score = 80  # Base score
        feedback = []
        
        # Check follow-through
        if trajectory_length < 5:
            technique_score -= 15
            feedback.append("Follow through with your kick")
            
        # Check trajectory smoothness
        smoothness = self._calculate_trajectory_smoothness(self.kick_trajectory)
        if smoothness < 0.6:
            technique_score -= 10
            feedback.append("Keep your kicking motion smooth")
            
        return {
            "success": True,
            "power_score": power_score,
            "power_zone": power_zone,
            "technique_score": technique_score,
            "smoothness": smoothness,
            "feedback": feedback,
            "trajectory_points": len(self.kick_trajectory)
        }
        
    def _analyze_header(self) -> Dict:
        """Analyze header technique."""
        # Basic header analysis
        technique_score = 75  # Base score for header
        feedback = []
        
        # Headers require timing and positioning
        feedback.append("Keep your eyes on the ball")
        feedback.append("Use your forehead for power")
        
        return {
            "success": True,
            "technique_score": technique_score,
            "timing": "good",
            "feedback": feedback
        }
        
    def _analyze_dribble(self) -> Dict:
        """Analyze dribbling technique and control."""
        if len(self.dribble_touches) < 3:
            return {"success": False, "reason": "Not enough touches for dribble"}
            
        # Calculate dribble consistency
        touch_intervals = []
        for i in range(1, len(self.dribble_touches)):
            interval = (self.dribble_touches[i]["timestamp"] - 
                       self.dribble_touches[i-1]["timestamp"])
            touch_intervals.append(interval)
            
        # Consistency score based on interval variance
        if touch_intervals:
            avg_interval = np.mean(touch_intervals)
            interval_variance = np.var(touch_intervals)
            consistency = max(0, 1 - (interval_variance / (avg_interval + 0.1)))
        else:
            consistency = 0.5
            
        # Control analysis
        velocities = [touch["velocity"] for touch in self.dribble_touches]
        avg_velocity = np.mean(velocities)
        
        technique_score = 70 + (consistency * 20)  # Up to 90
        feedback = []
        
        if consistency < 0.6:
            feedback.append("Keep a consistent rhythm while dribbling")
        if avg_velocity > 5.0:
            feedback.append("Control your touches - lighter contact")
        elif avg_velocity < 2.0:
            feedback.append("Be more assertive with your touches")
            
        return {
            "success": True,
            "technique_score": technique_score,
            "consistency": consistency,
            "touch_count": len(self.dribble_touches),
            "avg_velocity": avg_velocity,
            "feedback": feedback
        }
        
    def _classify_kick_type(self) -> str:
        """Classify the type of kick based on characteristics."""
        if len(self.kick_trajectory) < 3:
            return "kick"
            
        trajectory_length = len(self.kick_trajectory)
        
        # Simple classification based on trajectory characteristics
        if trajectory_length > 8:
            return "shot"  # Longer motion suggests shooting
        elif self.foot_velocity > 4.0:
            return "pass"  # High velocity suggests passing
        else:
            return "kick"  # General kick
            
    def _calculate_trajectory_smoothness(self, trajectory: List[Tuple]) -> float:
        """Calculate smoothness of movement trajectory."""
        if len(trajectory) < 3:
            return 0.0
            
        # Calculate variance in direction changes
        direction_changes = []
        for i in range(1, len(trajectory) - 1):
            p1, p2, p3 = trajectory[i-1], trajectory[i], trajectory[i+1]
            
            v1 = np.array(p2) - np.array(p1)
            v2 = np.array(p3) - np.array(p2)
            
            if np.linalg.norm(v1) > 0 and np.linalg.norm(v2) > 0:
                dot_product = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))
                angle = np.arccos(np.clip(dot_product, -1, 1))
                direction_changes.append(angle)
                
        if not direction_changes:
            return 0.0
            
        # Lower variance means smoother motion
        variance = np.var(direction_changes)
        smoothness = max(0, 1 - variance)
        
        return smoothness
        
    def get_sport_info(self) -> Dict:
        """Get soccer-specific information."""
        return {
            "name": "Soccer",
            "actions": ["kick", "shot", "pass", "header", "dribble"],
            "metrics": [
                "kick_power", "accuracy", "ball_control", 
                "first_touch", "passing_precision"
            ],
            "equipment": ["soccer_ball"],
            "feedback_types": ["technique", "power", "accuracy", "control"]
        }
        
    def get_feedback_template(self, action_result: Dict) -> Dict:
        """Get soccer-specific feedback template."""
        action = action_result.get("action", "unknown")
        analysis = action_result.get("analysis", {})
        
        if action in ["kick", "shot", "pass"]:
            return self._get_kick_feedback(action, analysis)
        elif action == "header":
            return self._get_header_feedback(analysis)
        elif action == "dribble":
            return self._get_dribble_feedback(analysis)
        else:
            return {"message": "Keep practicing your soccer skills!", "type": "encouragement"}
            
    def _get_kick_feedback(self, action: str, analysis: Dict) -> Dict:
        """Generate kick-specific feedback."""
        if not analysis.get("success", False):
            return {
                "message": f"Complete your {action} motion for better analysis",
                "type": "instruction",
                "audio": "kick_incomplete.wav"
            }
            
        power_zone = analysis.get("power_zone", "light")
        technique_score = analysis.get("technique_score", 0)
        
        if power_zone == "powerful" and technique_score > 80:
            return {
                "message": f"Excellent {action}! Great power and technique!",
                "type": "success",
                "audio": "excellent_kick.wav",
                "visual_effect": "power_kick"
            }
        elif technique_score > 70:
            return {
                "message": f"Good {action}! Power: {power_zone}",
                "type": "success",
                "audio": "good_kick.wav"
            }
        else:
            feedback_text = "Focus on: " + ", ".join(analysis.get("feedback", []))
            return {
                "message": feedback_text,
                "type": "improvement",
                "audio": "kick_tips.wav"
            }
            
    def _get_header_feedback(self, analysis: Dict) -> Dict:
        """Generate header-specific feedback."""
        if not analysis.get("success", False):
            return {
                "message": "Complete your header motion",
                "type": "instruction",
                "audio": "header_incomplete.wav"
            }
            
        technique_score = analysis.get("technique_score", 0)
        
        if technique_score > 80:
            return {
                "message": "Great header! Perfect timing and positioning!",
                "type": "success",
                "audio": "great_header.wav"
            }
        else:
            feedback_text = ", ".join(analysis.get("feedback", []))
            return {
                "message": f"Header tip: {feedback_text}",
                "type": "improvement",
                "audio": "header_tips.wav"
            }
            
    def _get_dribble_feedback(self, analysis: Dict) -> Dict:
        """Generate dribble-specific feedback."""
        if not analysis.get("success", False):
            return {
                "message": "Keep dribbling for better analysis",
                "type": "instruction",
                "audio": "dribble_more.wav"
            }
            
        technique_score = analysis.get("technique_score", 0)
        consistency = analysis.get("consistency", 0)
        
        if technique_score > 85 and consistency > 0.8:
            return {
                "message": "Excellent ball control! Perfect dribbling!",
                "type": "success",
                "audio": "excellent_dribble.wav",
                "visual_effect": "perfect_control"
            }
        elif technique_score > 70:
            return {
                "message": f"Good dribbling! {analysis.get('touch_count', 0)} touches",
                "type": "success",
                "audio": "good_dribble.wav"
            }
        else:
            feedback_text = ", ".join(analysis.get("feedback", []))
            return {
                "message": f"Dribbling: {feedback_text}",
                "type": "improvement",
                "audio": "dribble_tips.wav"
            }
