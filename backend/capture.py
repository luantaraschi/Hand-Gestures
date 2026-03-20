"""Webcam capture wrapper using OpenCV."""

import cv2
import numpy as np

from config import Config


class CameraCapture:
    """Thin wrapper around cv2.VideoCapture with automatic horizontal flip."""

    def __init__(self, config: Config) -> None:
        """Open the camera device and apply resolution settings.

        Args:
            config: Application configuration.
        """
        self._cap = cv2.VideoCapture(config.camera_index)
        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.camera_width)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.camera_height)

    def read_frame(self) -> np.ndarray | None:
        """Read a single frame from the camera.

        The frame is horizontally flipped so it behaves like a mirror,
        which feels more natural for gesture control.

        Returns:
            BGR numpy array, or None if the read failed.
        """
        success, frame = self._cap.read()
        if not success:
            return None
        return cv2.flip(frame, 1)

    def release(self) -> None:
        """Release the underlying VideoCapture resource."""
        self._cap.release()
