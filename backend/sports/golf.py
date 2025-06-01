"""
Golf-specific action tracking module.
Detects swings, putts, and analyzes technique.
"""

import cv2
import numpy as np
from typing import Dict, List, Optional, Tuple
from sports.base_sport import BaseSport
from core.pose_detector import PoseDetector


class GolfTracker(BaseSport):
    """Golf swing tracker for drives, irons, and putts."""
    
    def __init__(self, config: Dict):
        super().__init__("golf", config)
        self.sport_specific_config = {
            "backswing_threshold": 45,  # Degrees for backswing detection
            "downswing_speed_threshold": 4.0,  # Minimum speed for downswing
            "follow_through_angle": 90,  # Degrees for proper follow-through
            "putt_speed_threshold": 1.5,  # Lower speed threshold for putts
            "swing_tempo_ideal": 3.0,  # Ideal tempo ratio (backswing:downswing)
            "swing_plane_tolerance": 15,  # Degrees tolerance for swing plane
            "club_types": {
                "driver": {"distance": "long", "loft": "low"},
                "iron": {"distance": "medium", "loft": "medium"},
                "wedge": {"distance": "short", "loft": "high"},
                "putter": {"distance": "very_short", "loft": "minimal"}
            }
        }
        self.sport_specific_config.update(config.get("golf", {}))
        
        # Tracking variables
        self.swing_phase = "address"  # address, backswing, downswing, follow_through
        self.swing_started = False
        self.club_position = None
        self.club_velocity = 0
        self.swing_trajectory = []
        self.backswing_peak = None
        self.swing_start_time = None
        self.phase_timestamps = {}
        
    def detect_action(self, frame: np.ndarray, pose_landmarks) -> Optional[Dict]:
        """Detect golf swings and putts."""
        if pose_landmarks is None:
            return None
            
        # Get key body points for golf swing
        landmarks = pose_landmarks.landmark
        
        # Hand positions (club grip)
        right_wrist = self._get_landmark_coords(landmarks[16], frame.shape)
        left_wrist = self._get_landmark_coords(landmarks[15], frame.shape)
        right_elbow = self._get_landmark_coords(landmarks[14], frame.shape)
        left_elbow = self._get_landmark_coords(landmarks[13], frame.shape)
        right_shoulder = self._get_landmark_coords(landmarks[12], frame.shape)
        left_shoulder = self._get_landmark_coords(landmarks[11], frame.shape)
        
        if not all([right_wrist, left_wrist, right_elbow, left_elbow, right_shoulder, left_shoulder]):
            return None
            
        # Calculate club position (average of wrists)
        club_pos = [(right_wrist[0] + left_wrist[0]) / 2, (right_wrist[1] + left_wrist[1]) / 2]
        
        # Update club velocity
        if self.club_position is not None:
            velocity = np.linalg.norm(np.array(club_pos) - np.array(self.club_position))
            self.club_velocity = velocity
        self.club_position = club_pos
        
        # Detect swing motion
        swing_action = self._detect_swing(club_pos, right_shoulder, left_shoulder, frame.shape)
        
        return swing_action
        
    def _detect_swing(self, club_pos, right_shoulder, left_shoulder, frame_shape) -> Optional[Dict]:
        """Detect golf swing phases and completion."""
        current_time = self._get_timestamp()
        
        # Calculate club angle relative to body
        body_center = [(right_shoulder[0] + left_shoulder[0]) / 2, 
                      (right_shoulder[1] + left_shoulder[1]) / 2]
        club_angle = self._calculate_club_angle(club_pos, body_center)
        
        # State machine for swing phases
        if self.swing_phase == "address":
            if club_angle > self.sport_specific_config["backswing_threshold"]:
                self.swing_phase = "backswing"
                self.swing_started = True
                self.swing_start_time = current_time
                self.swing_trajectory = [club_pos]
                self.phase_timestamps["backswing_start"] = current_time
                
        elif self.swing_phase == "backswing":
            self.swing_trajectory.append(club_pos)
            
            # Check for peak of backswing (velocity near zero)
            if self.club_velocity < 0.5 and club_angle > 60:
                self.swing_phase = "downswing"
                self.backswing_peak = club_pos
                self.phase_timestamps["top_of_swing"] = current_time
                
        elif self.swing_phase == "downswing":
            self.swing_trajectory.append(club_pos)
            
            # Check for impact (club near ball position - assume low point)
            if club_pos[1] > body_center[1] + 50:  # Club below body level
                self.swing_phase = "follow_through"
                self.phase_timestamps["impact"] = current_time
                
        elif self.swing_phase == "follow_through":
            self.swing_trajectory.append(club_pos)
            
            # Check for end of swing (club velocity decreases significantly)
            if self.club_velocity < 1.0 and len(self.swing_trajectory) > 10:
                self.swing_phase = "address"
                self.swing_started = False
                self.phase_timestamps["swing_end"] = current_time
                
                # Analyze completed swing
                swing_analysis = self._analyze_swing()
                swing_type = self._classify_swing_type()
                
                # Reset for next swing
                self._reset_swing_tracking()
                
                return {
                    "action": swing_type,
                    "timestamp": current_time,
                    "success": swing_analysis["success"],
                    "analysis": swing_analysis,
                    "confidence": 0.88
                }
                
        return None
        
    def _calculate_club_angle(self, club_pos, body_center) -> float:
        """Calculate angle of club relative to body."""
        # Vector from body center to club
        club_vector = np.array(club_pos) - np.array(body_center)
        
        # Vertical reference vector (pointing down)
        vertical = np.array([0, 1])
        
        # Calculate angle
        if np.linalg.norm(club_vector) > 0:
            dot_product = np.dot(club_vector, vertical) / np.linalg.norm(club_vector)
            angle = np.degrees(np.arccos(np.clip(dot_product, -1, 1)))
            return angle
        return 0
        
    def _analyze_swing(self) -> Dict:
        """Analyze golf swing technique and tempo."""
        if len(self.swing_trajectory) < 10:
            return {"success": False, "reason": "Incomplete swing"}
            
        # Calculate swing tempo
        tempo_analysis = self._analyze_tempo()
        
        # Calculate swing plane consistency
        plane_analysis = self._analyze_swing_plane()
        
        # Analyze swing speed
        speed_analysis = self._analyze_swing_speed()
        
        # Overall technique score
        technique_score = 75  # Base score
        feedback = []
        
        # Tempo evaluation
        if tempo_analysis["tempo_ratio"] > 4.0:
            technique_score -= 10
            feedback.append("Slow down your downswing for better control")
        elif tempo_analysis["tempo_ratio"] < 2.0:
            technique_score -= 5
            feedback.append("Take more time in your backswing")
        else:
            technique_score += 5
            
        # Swing plane evaluation
        if plane_analysis["consistency"] < 0.7:
            technique_score -= 15
            feedback.append("Keep your swing plane more consistent")
        else:
            technique_score += 5
            
        # Speed evaluation
        if speed_analysis["peak_speed"] < 3.0:
            technique_score -= 10
            feedback.append("Generate more clubhead speed")
        elif speed_analysis["peak_speed"] > 8.0:
            feedback.append("Great clubhead speed!")
            technique_score += 5
            
        return {
            "success": True,
            "technique_score": min(100, technique_score),
            "tempo": tempo_analysis,
            "swing_plane": plane_analysis,
            "speed": speed_analysis,
            "feedback": feedback,
            "swing_duration": self.phase_timestamps.get("swing_end", 0) - self.swing_start_time
        }
        
    def _analyze_tempo(self) -> Dict:
        """Analyze swing tempo and timing."""
        backswing_start = self.phase_timestamps.get("backswing_start", 0)
        top_of_swing = self.phase_timestamps.get("top_of_swing", backswing_start + 1)
        impact = self.phase_timestamps.get("impact", top_of_swing + 0.5)
        
        backswing_time = top_of_swing - backswing_start
        downswing_time = impact - top_of_swing
        
        if downswing_time > 0:
            tempo_ratio = backswing_time / downswing_time
        else:
            tempo_ratio = 3.0  # Default
            
        # Ideal tempo is around 3:1 (backswing:downswing)
        tempo_score = max(0, 100 - abs(tempo_ratio - 3.0) * 20)
        
        return {
            "tempo_ratio": tempo_ratio,
            "backswing_time": backswing_time,
            "downswing_time": downswing_time,
            "tempo_score": tempo_score
        }
        
    def _analyze_swing_plane(self) -> Dict:
        """Analyze consistency of swing plane."""
        if len(self.swing_trajectory) < 5:
            return {"consistency": 0.5, "deviation": 20}
            
        # Calculate angles throughout swing
        angles = []
        for i in range(1, len(self.swing_trajectory)):
            p1, p2 = self.swing_trajectory[i-1], self.swing_trajectory[i]
            vector = np.array(p2) - np.array(p1)
            
            if np.linalg.norm(vector) > 0:
                angle = np.degrees(np.arctan2(vector[1], vector[0]))
                angles.append(angle)
                
        if not angles:
            return {"consistency": 0.5, "deviation": 20}
            
        # Calculate consistency (lower variance = more consistent)
        angle_variance = np.var(angles)
        consistency = max(0, 1 - (angle_variance / 1000))  # Normalize
        deviation = np.sqrt(angle_variance)
        
        return {
            "consistency": consistency,
            "deviation": deviation,
            "avg_plane_angle": np.mean(angles)
        }
        
    def _analyze_swing_speed(self) -> Dict:
        """Analyze clubhead speed throughout swing."""
        speeds = []
        
        for i in range(1, len(self.swing_trajectory)):
            p1, p2 = self.swing_trajectory[i-1], self.swing_trajectory[i]
            speed = np.linalg.norm(np.array(p2) - np.array(p1))
            speeds.append(speed)
            
        if not speeds:
            return {"peak_speed": 0, "avg_speed": 0, "speed_progression": []}
            
        peak_speed = max(speeds)
        avg_speed = np.mean(speeds)
        
        # Find speed at impact (should be near peak)
        impact_index = min(len(speeds) - 1, int(len(speeds) * 0.7))  # ~70% through swing
        impact_speed = speeds[impact_index] if impact_index < len(speeds) else avg_speed
        
        return {
            "peak_speed": peak_speed,
            "avg_speed": avg_speed,
            "impact_speed": impact_speed,
            "speed_progression": speeds[-10:]  # Last 10 measurements
        }
        
    def _classify_swing_type(self) -> str:
        """Classify the type of golf swing."""
        if not self.swing_trajectory:
            return "swing"
            
        # Simple classification based on swing characteristics
        swing_duration = (self.phase_timestamps.get("swing_end", 0) - 
                         self.swing_start_time)
        peak_speed = max([self.club_velocity] + [1.0])
        
        # Putt: slower speed, shorter duration
        if peak_speed < self.sport_specific_config["putt_speed_threshold"] and swing_duration < 2.0:
            return "putt"
        # Full swing: higher speed, longer duration  
        elif peak_speed > 5.0 and swing_duration > 2.5:
            return "drive"
        # Chip/pitch: moderate speed and duration
        elif swing_duration < 2.0:
            return "chip"
        else:
            return "iron_shot"
            
    def _reset_swing_tracking(self):
        """Reset tracking variables for next swing."""
        self.swing_trajectory = []
        self.backswing_peak = None
        self.swing_start_time = None
        self.phase_timestamps = {}
        
    def get_sport_info(self) -> Dict:
        """Get golf-specific information."""
        return {
            "name": "Golf",
            "actions": ["drive", "iron_shot", "chip", "putt"],
            "metrics": [
                "swing_tempo", "swing_plane", "clubhead_speed",
                "consistency", "technique_score"
            ],
            "equipment": ["golf_club", "golf_ball"],
            "feedback_types": ["tempo", "plane", "speed", "technique"]
        }
        
    def get_feedback_template(self, action_result: Dict) -> Dict:
        """Get golf-specific feedback template."""
        action = action_result.get("action", "swing")
        analysis = action_result.get("analysis", {})
        
        if action == "putt":
            return self._get_putt_feedback(analysis)
        else:
            return self._get_swing_feedback(action, analysis)
            
    def _get_putt_feedback(self, analysis: Dict) -> Dict:
        """Generate putting-specific feedback."""
        if not analysis.get("success", False):
            return {
                "message": "Complete your putting stroke",
                "type": "instruction",
                "audio": "putt_incomplete.wav"
            }
            
        technique_score = analysis.get("technique_score", 0)
        
        if technique_score > 85:
            return {
                "message": "Excellent putt! Great stroke technique!",
                "type": "success",
                "audio": "excellent_putt.wav"
            }
        elif technique_score > 70:
            return {
                "message": "Good putting stroke! Keep it smooth!",
                "type": "success",
                "audio": "good_putt.wav"
            }
        else:
            feedback_text = ", ".join(analysis.get("feedback", []))
            return {
                "message": f"Putting: {feedback_text}",
                "type": "improvement",
                "audio": "putt_tips.wav"
            }
            
    def _get_swing_feedback(self, action: str, analysis: Dict) -> Dict:
        """Generate swing-specific feedback."""
        if not analysis.get("success", False):
            return {
                "message": f"Complete your {action} for analysis",
                "type": "instruction",
                "audio": "swing_incomplete.wav"
            }
            
        technique_score = analysis.get("technique_score", 0)
        tempo = analysis.get("tempo", {})
        speed = analysis.get("speed", {})
        
        if technique_score > 90:
            return {
                "message": f"Perfect {action}! Excellent technique!",
                "type": "success",
                "audio": "perfect_swing.wav",
                "visual_effect": "perfect_swing"
            }
        elif technique_score > 80:
            return {
                "message": f"Great {action}! Tempo: {tempo.get('tempo_ratio', 0):.1f}:1",
                "type": "success",
                "audio": "great_swing.wav"
            }
        elif technique_score > 70:
            return {
                "message": f"Good {action}! Speed: {speed.get('peak_speed', 0):.1f}",
                "type": "success",
                "audio": "good_swing.wav"
            }
        else:
            feedback_text = ", ".join(analysis.get("feedback", []))
            return {
                "message": feedback_text,
                "type": "improvement",
                "audio": "swing_tips.wav"
            }
