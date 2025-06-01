"""
Pose Detector - MediaPipe-based pose estimation for sports action tracking

Detects human pose landmarks and provides utilities for sports-specific analysis.
"""

import cv2
import mediapipe as mp
import numpy as np
import logging
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class PoseConfig:
    """Configuration for pose detection"""
    static_image_mode: bool = False
    model_complexity: int = 1  # 0, 1, or 2
    smooth_landmarks: bool = True
    enable_segmentation: bool = False
    smooth_segmentation: bool = True
    min_detection_confidence: float = 0.5
    min_tracking_confidence: float = 0.5

class PoseDetector:
    """MediaPipe-based pose detection for sports analysis"""
    
    def __init__(self):
        self.mp_pose = mp.solutions.pose
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles
        
        self.pose = None
        self.config = PoseConfig()
        
        # Landmark indices for common body parts
        self.landmark_indices = {
            "nose": 0,
            "left_eye_inner": 1, "left_eye": 2, "left_eye_outer": 3,
            "right_eye_inner": 4, "right_eye": 5, "right_eye_outer": 6,
            "left_ear": 7, "right_ear": 8,
            "mouth_left": 9, "mouth_right": 10,
            "left_shoulder": 11, "right_shoulder": 12,
            "left_elbow": 13, "right_elbow": 14,
            "left_wrist": 15, "right_wrist": 16,
            "left_pinky": 17, "right_pinky": 18,
            "left_index": 19, "right_index": 20,
            "left_thumb": 21, "right_thumb": 22,
            "left_hip": 23, "right_hip": 24,
            "left_knee": 25, "right_knee": 26,
            "left_ankle": 27, "right_ankle": 28,
            "left_heel": 29, "right_heel": 30,
            "left_foot_index": 31, "right_foot_index": 32
        }
        
        logger.info("PoseDetector initialized")
    
    def initialize(self):
        """Initialize MediaPipe pose detection"""
        try:
            self.pose = self.mp_pose.Pose(
                static_image_mode=self.config.static_image_mode,
                model_complexity=self.config.model_complexity,
                smooth_landmarks=self.config.smooth_landmarks,
                enable_segmentation=self.config.enable_segmentation,
                smooth_segmentation=self.config.smooth_segmentation,
                min_detection_confidence=self.config.min_detection_confidence,
                min_tracking_confidence=self.config.min_tracking_confidence
            )
            
            logger.info("MediaPipe pose detection initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize pose detection: {e}")
            raise
    
    def configure(self, config: Dict[str, Any]):
        """Configure pose detection settings"""
        try:
            # Update configuration
            if "min_detection_confidence" in config:
                self.config.min_detection_confidence = config["min_detection_confidence"]
            if "min_tracking_confidence" in config:
                self.config.min_tracking_confidence = config["min_tracking_confidence"]
            if "model_complexity" in config:
                self.config.model_complexity = config["model_complexity"]
            
            # Reinitialize with new config
            self.initialize()
            
            logger.info(f"Pose detector reconfigured: {config}")
            
        except Exception as e:
            logger.error(f"Error configuring pose detector: {e}")
    
    def detect_pose(self, frame: np.ndarray):
        """Detect pose landmarks in frame"""
        try:
            if self.pose is None:
                self.initialize()
            
            # Convert BGR to RGB
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Process with MediaPipe
            results = self.pose.process(rgb_frame)
            
            return results
            
        except Exception as e:
            logger.error(f"Error detecting pose: {e}")
            return None
    
    def draw_landmarks(self, frame: np.ndarray, results, connections: bool = True) -> np.ndarray:
        """Draw pose landmarks on frame"""
        try:
            if results and results.pose_landmarks:
                # Draw landmarks
                self.mp_drawing.draw_landmarks(
                    frame,
                    results.pose_landmarks,
                    self.mp_pose.POSE_CONNECTIONS if connections else None,
                    landmark_drawing_spec=self.mp_drawing_styles.get_default_pose_landmarks_style()
                )
            
            return frame
            
        except Exception as e:
            logger.error(f"Error drawing landmarks: {e}")
            return frame
    
    def get_landmark_coordinates(self, results, landmark_name: str) -> Optional[Tuple[float, float, float]]:
        """Get 3D coordinates of a specific landmark"""
        try:
            if not results or not results.pose_landmarks:
                return None
            
            landmark_index = self.landmark_indices.get(landmark_name)
            if landmark_index is None:
                return None
            
            landmark = results.pose_landmarks.landmark[landmark_index]
            return (landmark.x, landmark.y, landmark.z)
            
        except Exception as e:
            logger.error(f"Error getting landmark coordinates: {e}")
            return None
    
    def get_landmark_pixel_coordinates(self, results, landmark_name: str, frame_shape: Tuple[int, int]) -> Optional[Tuple[int, int]]:
        """Get pixel coordinates of a landmark"""
        try:
            coords = self.get_landmark_coordinates(results, landmark_name)
            if coords is None:
                return None
            
            height, width = frame_shape[:2]
            x_pixel = int(coords[0] * width)
            y_pixel = int(coords[1] * height)
            
            return (x_pixel, y_pixel)
            
        except Exception as e:
            logger.error(f"Error getting pixel coordinates: {e}")
            return None
    
    def calculate_angle(self, point1: Tuple[float, float], point2: Tuple[float, float], point3: Tuple[float, float]) -> float:
        """Calculate angle between three points"""
        try:
            # Convert to numpy arrays
            p1 = np.array(point1[:2])  # Use only x, y coordinates
            p2 = np.array(point2[:2])
            p3 = np.array(point3[:2])
            
            # Calculate vectors
            v1 = p1 - p2
            v2 = p3 - p2
            
            # Calculate angle
            cos_angle = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))
            cos_angle = np.clip(cos_angle, -1.0, 1.0)  # Clamp to valid range
            angle = np.arccos(cos_angle)
            
            return np.degrees(angle)
            
        except Exception as e:
            logger.error(f"Error calculating angle: {e}")
            return 0.0
    
    def calculate_distance(self, point1: Tuple[float, float, float], point2: Tuple[float, float, float]) -> float:
        """Calculate 3D distance between two points"""
        try:
            p1 = np.array(point1)
            p2 = np.array(point2)
            
            return np.linalg.norm(p1 - p2)
            
        except Exception as e:
            logger.error(f"Error calculating distance: {e}")
            return 0.0
    
    def get_body_angles(self, results) -> Dict[str, float]:
        """Calculate common body angles for sports analysis"""
        angles = {}
        
        try:
            if not results or not results.pose_landmarks:
                return angles
            
            # Helper function to get landmark coords
            def get_coords(name):
                return self.get_landmark_coordinates(results, name)
            
            # Elbow angles
            left_shoulder = get_coords("left_shoulder")
            left_elbow = get_coords("left_elbow")
            left_wrist = get_coords("left_wrist")
            
            if all([left_shoulder, left_elbow, left_wrist]):
                angles["left_elbow"] = self.calculate_angle(left_shoulder, left_elbow, left_wrist)
            
            right_shoulder = get_coords("right_shoulder")
            right_elbow = get_coords("right_elbow")
            right_wrist = get_coords("right_wrist")
            
            if all([right_shoulder, right_elbow, right_wrist]):
                angles["right_elbow"] = self.calculate_angle(right_shoulder, right_elbow, right_wrist)
            
            # Knee angles
            left_hip = get_coords("left_hip")
            left_knee = get_coords("left_knee")
            left_ankle = get_coords("left_ankle")
            
            if all([left_hip, left_knee, left_ankle]):
                angles["left_knee"] = self.calculate_angle(left_hip, left_knee, left_ankle)
            
            right_hip = get_coords("right_hip")
            right_knee = get_coords("right_knee")
            right_ankle = get_coords("right_ankle")
            
            if all([right_hip, right_knee, right_ankle]):
                angles["right_knee"] = self.calculate_angle(right_hip, right_knee, right_ankle)
            
            # Shoulder angle (arm to torso)
            if all([left_shoulder, left_elbow, left_hip]):
                angles["left_shoulder"] = self.calculate_angle(left_elbow, left_shoulder, left_hip)
            
            if all([right_shoulder, right_elbow, right_hip]):
                angles["right_shoulder"] = self.calculate_angle(right_elbow, right_shoulder, right_hip)
            
        except Exception as e:
            logger.error(f"Error calculating body angles: {e}")
        
        return angles
    
    def get_pose_metrics(self, results) -> Dict[str, Any]:
        """Get comprehensive pose metrics for sports analysis"""
        metrics = {}
        
        try:
            if not results or not results.pose_landmarks:
                return metrics
            
            # Basic pose detection info
            metrics["pose_detected"] = True
            metrics["landmark_count"] = len(results.pose_landmarks.landmark)
            
            # Body angles
            metrics["angles"] = self.get_body_angles(results)
            
            # Body part positions
            key_points = ["nose", "left_wrist", "right_wrist", "left_ankle", "right_ankle"]
            positions = {}
            
            for point in key_points:
                coords = self.get_landmark_coordinates(results, point)
                if coords:
                    positions[point] = {
                        "x": coords[0],
                        "y": coords[1],
                        "z": coords[2]
                    }
            
            metrics["positions"] = positions
            
            # Calculate center of mass (approximate)
            if all(self.get_landmark_coordinates(results, part) for part in ["left_shoulder", "right_shoulder", "left_hip", "right_hip"]):
                left_shoulder = self.get_landmark_coordinates(results, "left_shoulder")
                right_shoulder = self.get_landmark_coordinates(results, "right_shoulder")
                left_hip = self.get_landmark_coordinates(results, "left_hip")
                right_hip = self.get_landmark_coordinates(results, "right_hip")
                
                center_x = (left_shoulder[0] + right_shoulder[0] + left_hip[0] + right_hip[0]) / 4
                center_y = (left_shoulder[1] + right_shoulder[1] + left_hip[1] + right_hip[1]) / 4
                
                metrics["center_of_mass"] = {"x": center_x, "y": center_y}
            
        except Exception as e:
            logger.error(f"Error calculating pose metrics: {e}")
        
        return metrics
    
    def cleanup(self):
        """Cleanup pose detection resources"""
        try:
            if self.pose:
                self.pose.close()
                self.pose = None
            
            logger.info("Pose detector cleanup complete")
            
        except Exception as e:
            logger.error(f"Error during pose detector cleanup: {e}")
    
    def is_pose_stable(self, results_history: List, threshold: float = 0.1) -> bool:
        """Check if pose is stable across multiple frames"""
        try:
            if len(results_history) < 3:
                return False
            
            # Compare key landmarks across frames
            key_landmarks = ["left_wrist", "right_wrist", "nose"]
            
            for landmark_name in key_landmarks:
                positions = []
                
                for results in results_history[-3:]:
                    coords = self.get_landmark_coordinates(results, landmark_name)
                    if coords:
                        positions.append(coords[:2])  # x, y only
                
                if len(positions) < 3:
                    continue
                
                # Calculate variance
                positions = np.array(positions)
                variance = np.var(positions, axis=0)
                
                if np.any(variance > threshold):
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking pose stability: {e}")
            return False
