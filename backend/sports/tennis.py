"""
Tennis-specific action tracking module.
Detects serves, forehands, backhands, and volleys.
"""

import cv2
import numpy as np
from typing import Dict, List, Optional, Tuple
from .base_sport import BaseSport
from ..core.pose_detector import PoseDetector


class TennisTracker(BaseSport):
    """Tennis action tracker for serves, strokes, and volleys."""
    
    def __init__(self, config: Dict):
        super().__init__("tennis", config)
        self.sport_specific_config = {
            "serve_height_threshold": 0.7,  # Minimum reach height for serve
            "stroke_velocity_threshold": 2.0,  # Minimum racket velocity
            "follow_through_angle": 45,  # Degrees for proper follow-through
            "contact_zone_width": 0.3,  # Width of optimal contact zone
            "serve_power_zones": {
                "low": (0, 30),
                "medium": (30, 60),
                "high": (60, 100)
            }
        }
        self.sport_specific_config.update(config.get("tennis", {}))
        
        # Tracking variables
        self.serve_started = False
        self.stroke_started = False
        self.racket_position = None
        self.racket_velocity = 0
        self.serve_trajectory = []
        self.stroke_trajectory = []
        
    def detect_action(self, frame: np.ndarray, pose_landmarks) -> Optional[Dict]:
        """Detect tennis actions (serve, forehand, backhand, volley)."""
        if pose_landmarks is None:
            return None
            
        # Get key body points
        landmarks = pose_landmarks.landmark
        
        # Right hand position (assuming right-handed player)
        right_wrist = self._get_landmark_coords(landmarks[16], frame.shape)
        right_elbow = self._get_landmark_coords(landmarks[14], frame.shape)
        right_shoulder = self._get_landmark_coords(landmarks[12], frame.shape)
        left_shoulder = self._get_landmark_coords(landmarks[11], frame.shape)
        
        if not all([right_wrist, right_elbow, right_shoulder, left_shoulder]):
            return None
            
        # Update racket position and velocity
        if self.racket_position is not None:
            velocity = np.linalg.norm(np.array(right_wrist) - np.array(self.racket_position))
            self.racket_velocity = velocity
        self.racket_position = right_wrist
        
        # Detect different tennis actions
        serve_action = self._detect_serve(right_wrist, right_elbow, right_shoulder, frame.shape)
        stroke_action = self._detect_stroke(right_wrist, right_elbow, right_shoulder, left_shoulder)
        
        if serve_action:
            return serve_action
        elif stroke_action:
            return stroke_action
            
        return None
        
    def _detect_serve(self, wrist, elbow, shoulder, frame_shape) -> Optional[Dict]:
        """Detect tennis serve motion."""
        # Calculate arm extension and height
        arm_angle = self._calculate_angle(shoulder, elbow, wrist)
        wrist_height = 1 - (wrist[1] / frame_shape[0])  # Normalized height
        
        # Serve detection logic
        if wrist_height > self.sport_specific_config["serve_height_threshold"] and arm_angle > 140:
            if not self.serve_started:
                self.serve_started = True
                self.serve_trajectory = [wrist]
                return None
            else:
                self.serve_trajectory.append(wrist)
                
        elif self.serve_started and wrist_height < 0.5:
            # Serve completed
            self.serve_started = False
            serve_analysis = self._analyze_serve()
            return {
                "action": "serve",
                "timestamp": self._get_timestamp(),
                "success": serve_analysis["success"],
                "analysis": serve_analysis,
                "confidence": 0.85
            }
            
        return None
        
    def _detect_stroke(self, wrist, elbow, shoulder, left_shoulder) -> Optional[Dict]:
        """Detect forehand, backhand, or volley."""
        # Calculate stroke type based on arm position relative to body
        body_center_x = (shoulder[0] + left_shoulder[0]) / 2
        arm_extension = np.linalg.norm(np.array(wrist) - np.array(shoulder))
        
        # High velocity indicates active stroke
        if self.racket_velocity > self.sport_specific_config["stroke_velocity_threshold"]:
            if not self.stroke_started:
                self.stroke_started = True
                self.stroke_trajectory = [wrist]
                
                # Determine stroke type
                if wrist[0] > body_center_x:
                    stroke_type = "forehand"
                else:
                    stroke_type = "backhand"
                    
                # Check if it's a volley (close to net, less backswing)
                if arm_extension < 100:  # Short stroke
                    stroke_type = "volley"
                    
                return None
            else:
                self.stroke_trajectory.append(wrist)
                
        elif self.stroke_started and self.racket_velocity < 1.0:
            # Stroke completed
            self.stroke_started = False
            stroke_analysis = self._analyze_stroke()
            
            # Determine final stroke type
            stroke_type = self._classify_stroke_type()
            
            return {
                "action": stroke_type,
                "timestamp": self._get_timestamp(),
                "success": stroke_analysis["success"],
                "analysis": stroke_analysis,
                "confidence": 0.80
            }
            
        return None
        
    def _analyze_serve(self) -> Dict:
        """Analyze serve technique and power."""
        if len(self.serve_trajectory) < 3:
            return {"success": False, "reason": "Incomplete serve motion"}
            
        # Calculate serve power based on trajectory
        max_height = max([point[1] for point in self.serve_trajectory])
        trajectory_length = len(self.serve_trajectory)
        
        # Estimate power based on trajectory characteristics
        power_score = min(100, trajectory_length * 2)
        
        # Determine power zone
        power_zone = "low"
        for zone, (min_power, max_power) in self.sport_specific_config["serve_power_zones"].items():
            if min_power <= power_score <= max_power:
                power_zone = zone
                break
                
        # Check technique
        technique_score = 85  # Base score
        feedback = []
        
        if trajectory_length < 5:
            technique_score -= 20
            feedback.append("Extend your serving motion for more power")
            
        return {
            "success": True,
            "power_score": power_score,
            "power_zone": power_zone,
            "technique_score": technique_score,
            "feedback": feedback,
            "trajectory_points": len(self.serve_trajectory)
        }
        
    def _analyze_stroke(self) -> Dict:
        """Analyze stroke technique and timing."""
        if len(self.stroke_trajectory) < 3:
            return {"success": False, "reason": "Incomplete stroke"}
            
        # Calculate stroke smoothness
        smoothness = self._calculate_trajectory_smoothness(self.stroke_trajectory)
        
        # Analyze follow-through
        start_point = self.stroke_trajectory[0]
        end_point = self.stroke_trajectory[-1]
        follow_through_distance = np.linalg.norm(np.array(end_point) - np.array(start_point))
        
        technique_score = 75  # Base score
        feedback = []
        
        if smoothness < 0.7:
            technique_score -= 15
            feedback.append("Keep your stroke smooth and controlled")
            
        if follow_through_distance < 50:
            technique_score -= 10
            feedback.append("Extend your follow-through")
            
        return {
            "success": True,
            "technique_score": technique_score,
            "smoothness": smoothness,
            "follow_through": follow_through_distance,
            "feedback": feedback
        }
        
    def _classify_stroke_type(self) -> str:
        """Classify the stroke type based on trajectory."""
        if len(self.stroke_trajectory) < 3:
            return "unknown"
            
        # Simple classification based on trajectory characteristics
        trajectory_length = len(self.stroke_trajectory)
        
        if trajectory_length < 8:
            return "volley"
        elif self.stroke_trajectory[0][0] < self.stroke_trajectory[-1][0]:
            return "forehand"
        else:
            return "backhand"
            
    def _calculate_trajectory_smoothness(self, trajectory: List[Tuple]) -> float:
        """Calculate smoothness of racket trajectory."""
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
            
        # Higher variance means less smooth
        variance = np.var(direction_changes)
        smoothness = max(0, 1 - variance)
        
        return smoothness
        
    def get_sport_info(self) -> Dict:
        """Get tennis-specific information."""
        return {
            "name": "Tennis",
            "actions": ["serve", "forehand", "backhand", "volley"],
            "metrics": [
                "serve_power", "stroke_technique", "consistency", 
                "court_coverage", "shot_placement"
            ],
            "equipment": ["tennis_racket", "tennis_ball"],
            "feedback_types": ["technique", "power", "timing", "positioning"]
        }
        
    def get_feedback_template(self, action_result: Dict) -> Dict:
        """Get tennis-specific feedback template."""
        action = action_result.get("action", "unknown")
        analysis = action_result.get("analysis", {})
        
        if action == "serve":
            return self._get_serve_feedback(analysis)
        elif action in ["forehand", "backhand", "volley"]:
            return self._get_stroke_feedback(action, analysis)
        else:
            return {"message": "Keep practicing your tennis technique!", "type": "encouragement"}
            
    def _get_serve_feedback(self, analysis: Dict) -> Dict:
        """Generate serve-specific feedback."""
        if not analysis.get("success", False):
            return {
                "message": "Complete your serve motion for better analysis",
                "type": "instruction",
                "audio": "serve_incomplete.wav"
            }
            
        power_zone = analysis.get("power_zone", "low")
        technique_score = analysis.get("technique_score", 0)
        
        if power_zone == "high" and technique_score > 80:
            return {
                "message": "Excellent serve! Great power and technique!",
                "type": "success",
                "audio": "excellent_serve.wav",
                "visual_effect": "power_serve"
            }
        elif technique_score > 70:
            return {
                "message": f"Good serve technique! Power zone: {power_zone}",
                "type": "success",
                "audio": "good_serve.wav"
            }
        else:
            feedback_text = "Focus on: " + ", ".join(analysis.get("feedback", []))
            return {
                "message": feedback_text,
                "type": "improvement",
                "audio": "serve_tips.wav"
            }
            
    def _get_stroke_feedback(self, stroke_type: str, analysis: Dict) -> Dict:
        """Generate stroke-specific feedback."""
        if not analysis.get("success", False):
            return {
                "message": f"Complete your {stroke_type} motion",
                "type": "instruction",
                "audio": "stroke_incomplete.wav"
            }
            
        technique_score = analysis.get("technique_score", 0)
        smoothness = analysis.get("smoothness", 0)
        
        if technique_score > 85 and smoothness > 0.8:
            return {
                "message": f"Perfect {stroke_type}! Excellent technique!",
                "type": "success",
                "audio": "perfect_stroke.wav",
                "visual_effect": "perfect_shot"
            }
        elif technique_score > 70:
            return {
                "message": f"Good {stroke_type}! Keep it consistent!",
                "type": "success",
                "audio": "good_stroke.wav"
            }
        else:
            feedback_text = ", ".join(analysis.get("feedback", []))
            return {
                "message": f"{stroke_type.title()}: {feedback_text}",
                "type": "improvement",
                "audio": "stroke_tips.wav"
            }
