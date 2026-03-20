"""Application configuration dataclass."""

from dataclasses import dataclass


@dataclass
class Config:
    """Central configuration for the Gesture AI Desk backend."""

    # Camera
    camera_index: int = 0
    camera_width: int = 1280
    camera_height: int = 720

    # MediaPipe
    mediapipe_min_detection: float = 0.7
    mediapipe_min_tracking: float = 0.7
    max_hands: int = 1

    # Performance
    target_fps: int = 30
