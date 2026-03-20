"""MediaPipe hand landmark detection wrapper (tasks API)."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

import cv2
import mediapipe as mp
import numpy as np
from mediapipe.tasks.python import BaseOptions
from mediapipe.tasks.python.vision import (
    HandLandmarker,
    HandLandmarkerOptions,
    HandLandmarkerResult,
    RunningMode,
)

from config import Config

_MODEL_PATH = os.path.join(os.path.dirname(__file__), "hand_landmarker.task")


@dataclass
class HandResult:
    """Result of a single-hand detection.

    Attributes:
        landmarks: List of 21 NormalizedLandmark objects.
        handedness: Label string, e.g. "Left" or "Right".
        raw_result: Full HandLandmarkerResult (used by drawing utils).
    """

    landmarks: list[Any]
    handedness: str
    raw_result: HandLandmarkerResult


class HandTracker:
    """Wrapper around MediaPipe HandLandmarker for single-hand detection."""

    def __init__(self, config: Config) -> None:
        """Initialize the MediaPipe HandLandmarker.

        Args:
            config: Application configuration.
        """
        options = HandLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=_MODEL_PATH),
            running_mode=RunningMode.VIDEO,
            num_hands=config.max_hands,
            min_hand_detection_confidence=config.mediapipe_min_detection,
            min_tracking_confidence=config.mediapipe_min_tracking,
        )
        self._landmarker = HandLandmarker.create_from_options(options)
        self._timestamp_ms = 0

    def process(self, frame: np.ndarray) -> HandResult | None:
        """Run hand landmark detection on a BGR frame.

        Args:
            frame: BGR image as a numpy array.

        Returns:
            HandResult for the first detected hand, or None.
        """
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)

        self._timestamp_ms += 33  # ~30 fps
        result = self._landmarker.detect_for_video(mp_image, self._timestamp_ms)

        if not result.hand_landmarks:
            return None

        handedness_label = result.handedness[0][0].category_name

        return HandResult(
            landmarks=result.hand_landmarks[0],
            handedness=handedness_label,
            raw_result=result,
        )
