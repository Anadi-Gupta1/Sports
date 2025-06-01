"""
Camera Manager - Handles camera input and frame processing

Manages video capture from various sources (webcam, IP camera, video file)
with automatic camera selection and frame optimization.
"""

import cv2
import asyncio
import numpy as np
import logging
from typing import Optional, Tuple, Dict, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class CameraConfig:
    """Camera configuration settings"""
    camera_index: int = 0
    width: int = 1280
    height: int = 720
    fps: int = 30
    auto_exposure: bool = True
    brightness: float = 0.5
    contrast: float = 0.5

class CameraManager:
    """Manages camera input and video processing"""
    
    def __init__(self):
        self.cap = None
        self.is_capturing = False
        self.current_frame = None
        self.frame_lock = asyncio.Lock()
        self.config = CameraConfig()
        
        # Camera info
        self.available_cameras = []
        self.camera_info = {}
        
        logger.info("CameraManager initialized")
    
    async def initialize(self):
        """Initialize camera system and detect available cameras"""
        try:
            await self._detect_cameras()
            logger.info(f"Found {len(self.available_cameras)} available cameras")
            
        except Exception as e:
            logger.error(f"Failed to initialize camera manager: {e}")
            raise
    
    async def _detect_cameras(self):
        """Detect available cameras"""
        self.available_cameras = []
        
        # Test camera indices 0-5
        for index in range(6):
            cap = cv2.VideoCapture(index)
            if cap.isOpened():
                # Test if camera actually works
                ret, frame = cap.read()
                if ret and frame is not None:
                    self.available_cameras.append(index)
                    
                    # Get camera info
                    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                    fps = cap.get(cv2.CAP_PROP_FPS)
                    
                    self.camera_info[index] = {
                        "width": width,
                        "height": height,
                        "fps": fps,
                        "name": f"Camera {index}"
                    }
                    
                    logger.info(f"Camera {index}: {width}x{height} @ {fps} FPS")
                
                cap.release()
    
    def configure_camera(self, config: CameraConfig):
        """Configure camera settings"""
        self.config = config
        logger.info(f"Camera configured: {config}")
    
    async def start_capture(self, camera_index: Optional[int] = None):
        """Start video capture"""
        try:
            if camera_index is not None:
                self.config.camera_index = camera_index
            
            # Initialize video capture
            self.cap = cv2.VideoCapture(self.config.camera_index)
            
            if not self.cap.isOpened():
                raise RuntimeError(f"Failed to open camera {self.config.camera_index}")
            
            # Configure camera properties
            self._configure_capture_properties()
            
            self.is_capturing = True
            
            # Start capture loop
            asyncio.create_task(self._capture_loop())
            
            logger.info(f"Camera capture started on index {self.config.camera_index}")
            
        except Exception as e:
            logger.error(f"Failed to start camera capture: {e}")
            raise
    
    def _configure_capture_properties(self):
        """Configure camera capture properties"""
        try:
            # Set resolution
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.config.width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.config.height)
            
            # Set FPS
            self.cap.set(cv2.CAP_PROP_FPS, self.config.fps)
            
            # Set auto exposure
            if not self.config.auto_exposure:
                self.cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.25)  # Manual mode
            
            # Set brightness and contrast (if supported)
            self.cap.set(cv2.CAP_PROP_BRIGHTNESS, self.config.brightness)
            self.cap.set(cv2.CAP_PROP_CONTRAST, self.config.contrast)
            
            # Additional optimizations
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Reduce buffer size for real-time
            
            # Verify settings
            actual_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            actual_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            actual_fps = self.cap.get(cv2.CAP_PROP_FPS)
            
            logger.info(f"Camera configured: {actual_width}x{actual_height} @ {actual_fps} FPS")
            
        except Exception as e:
            logger.error(f"Error configuring camera properties: {e}")
    
    async def _capture_loop(self):
        """Main capture loop"""
        try:
            while self.is_capturing:
                if self.cap and self.cap.isOpened():
                    ret, frame = self.cap.read()
                    
                    if ret and frame is not None:
                        # Process frame
                        processed_frame = self._process_frame(frame)
                        
                        # Store frame with thread safety
                        async with self.frame_lock:
                            self.current_frame = processed_frame
                    else:
                        logger.warning("Failed to read frame from camera")
                        await asyncio.sleep(0.1)  # Wait before retrying
                else:
                    logger.error("Camera not available")
                    break
                
                # Small delay to prevent overwhelming CPU
                await asyncio.sleep(0.001)
                
        except Exception as e:
            logger.error(f"Error in capture loop: {e}")
            self.is_capturing = False
    
    def _process_frame(self, frame: np.ndarray) -> np.ndarray:
        """Process captured frame (preprocessing)"""
        try:
            # Flip frame horizontally for mirror effect (typical for webcams)
            frame = cv2.flip(frame, 1)
            
            # Apply any preprocessing here
            # - Color correction
            # - Noise reduction
            # - Stabilization
            
            return frame
            
        except Exception as e:
            logger.error(f"Error processing frame: {e}")
            return frame
    
    async def get_frame(self) -> Optional[np.ndarray]:
        """Get the latest frame"""
        try:
            async with self.frame_lock:
                if self.current_frame is not None:
                    return self.current_frame.copy()
                return None
                
        except Exception as e:
            logger.error(f"Error getting frame: {e}")
            return None
    
    async def stop_capture(self):
        """Stop video capture"""
        try:
            self.is_capturing = False
            
            if self.cap:
                self.cap.release()
                self.cap = None
            
            logger.info("Camera capture stopped")
            
        except Exception as e:
            logger.error(f"Error stopping capture: {e}")
    
    def cleanup(self):
        """Cleanup camera resources"""
        try:
            if self.cap:
                self.cap.release()
                self.cap = None
            
            logger.info("Camera manager cleanup complete")
            
        except Exception as e:
            logger.error(f"Error during camera cleanup: {e}")
    
    def get_camera_info(self) -> Dict[str, Any]:
        """Get information about available cameras"""
        return {
            "available_cameras": self.available_cameras,
            "camera_info": self.camera_info,
            "current_camera": self.config.camera_index,
            "is_capturing": self.is_capturing
        }
    
    async def test_camera(self, camera_index: int) -> bool:
        """Test if a camera is working"""
        try:
            test_cap = cv2.VideoCapture(camera_index)
            
            if test_cap.isOpened():
                ret, frame = test_cap.read()
                test_cap.release()
                return ret and frame is not None
            
            return False
            
        except Exception as e:
            logger.error(f"Error testing camera {camera_index}: {e}")
            return False
    
    def get_frame_info(self) -> Dict[str, Any]:
        """Get current frame information"""
        if self.cap and self.cap.isOpened():
            return {
                "width": int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                "height": int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
                "fps": self.cap.get(cv2.CAP_PROP_FPS),
                "brightness": self.cap.get(cv2.CAP_PROP_BRIGHTNESS),
                "contrast": self.cap.get(cv2.CAP_PROP_CONTRAST),
                "exposure": self.cap.get(cv2.CAP_PROP_EXPOSURE)
            }
        return {}
