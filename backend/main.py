"""Standalone test script — webcam + landmarks + gestures + actions + filters."""

from __future__ import annotations

import logging
import time
from typing import Any, Callable

import cv2
import numpy as np
from mediapipe.tasks.python.vision import (
    HandLandmarksConnections,
    drawing_utils as mp_drawing,
)

import actions
import filters
from capture import CameraCapture
from config import Config
from gesture_engine import Gesture, GestureDetector
from hand_tracker import HandTracker
from hold_manager import HoldManager

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger(__name__)

_CONNECTIONS = HandLandmarksConnections.HAND_CONNECTIONS

# Gesture → action mapping (hold-based actions only)
_ACTION_MAP: dict[Gesture, Callable[[], None]] = {
    Gesture.PALM: actions.toggle_play_pause,
    Gesture.FIST: actions.toggle_mute,
    Gesture.PEACE: actions.next_track,
    Gesture.POINT: actions.take_screenshot,
    Gesture.THUMB_UP: actions.volume_up,
    Gesture.THUMB_DOWN: actions.volume_down,
}


def _draw_hold_ring(
    frame: np.ndarray,
    hand_center: tuple[int, int],
    progress: float,
    color: tuple[int, int, int] = (0, 200, 100),
) -> None:
    """Draw a radial progress ring around the hand (PRD 4.7)."""
    radius = 60
    # Background ring
    cv2.ellipse(frame, hand_center, (radius, radius), 0, 0, 360, (100, 100, 100), 1, cv2.LINE_AA)
    # Progress arc
    start_angle = -90
    end_angle = start_angle + int(360 * progress)
    cv2.ellipse(frame, hand_center, (radius, radius), 0, start_angle, end_angle, color, 4, cv2.LINE_AA)


def _hand_center_px(landmarks: list[Any], w: int, h: int) -> tuple[int, int]:
    """Compute the pixel centre of the hand from wrist + middle MCP."""
    wx, wy = landmarks[0].x * w, landmarks[0].y * h
    mx, my = landmarks[9].x * w, landmarks[9].y * h
    return int((wx + mx) / 2), int((wy + my) / 2)


def main() -> None:
    """Main capture-detect-act loop."""
    config = Config()
    camera = CameraCapture(config)
    tracker = HandTracker(config)
    detector = GestureDetector()
    hold = HoldManager()

    filter_index = 0
    filter_intensity = 1.0
    detection_paused = False

    log.info("Gesture AI Desk — press 'q' to quit")

    try:
        while True:
            frame = camera.read_frame()
            if frame is None:
                continue

            now = time.monotonic()
            h, w = frame.shape[:2]
            result = tracker.process(frame)
            gesture = Gesture.NONE
            label = ""

            if result is not None:
                # Draw landmarks
                for hand_lm in result.raw_result.hand_landmarks:
                    mp_drawing.draw_landmarks(frame, hand_lm, _CONNECTIONS)

                if not detection_paused:
                    gesture = detector.detect_gesture(result.landmarks)
                    hold_info = hold.update(gesture, now)

                    # ---- Handle pinch (continuous, no hold) ----
                    if gesture == Gesture.PINCH:
                        ps = detector.pinch_state
                        axis = ps["axis"]
                        val = ps["value"]
                        if axis == "volume":
                            new_vol = max(0.0, min(1.0, actions.get_volume() + val * 0.01))
                            actions.set_volume(new_vol)
                            label = f"PINCH vol {new_vol:.0%}"
                        elif axis == "filter_intensity":
                            filter_intensity = max(0.1, min(1.0, filter_intensity + val * 0.01))
                            label = f"PINCH filter {filter_intensity:.0%}"
                        else:
                            label = "PINCH ..."

                    # ---- Handle swipe (instant) ----
                    elif gesture == Gesture.SWIPE_RIGHT:
                        filter_index = filters.next_filter(filter_index)
                        label = f">> {filters.FILTER_LIST[filter_index]}"
                    elif gesture == Gesture.SWIPE_LEFT:
                        filter_index = filters.prev_filter(filter_index)
                        label = f"<< {filters.FILTER_LIST[filter_index]}"

                    # ---- Handle hang loose toggle ----
                    elif gesture == Gesture.HANG_LOOSE and hold_info["action_triggered"]:
                        detection_paused = True
                        label = "PAUSED"

                    # ---- Hold-based actions ----
                    elif hold_info["action_triggered"] and gesture in _ACTION_MAP:
                        _ACTION_MAP[gesture]()
                        label = f"{gesture.name} TRIGGERED"
                    else:
                        label = gesture.name

                    # Draw hold ring
                    if hold_info["hold_progress"] > 0 and gesture not in {
                        Gesture.PINCH, Gesture.SWIPE_LEFT, Gesture.SWIPE_RIGHT, Gesture.NONE,
                    }:
                        center = _hand_center_px(result.landmarks, w, h)
                        color = (0, 255, 0) if hold_info["action_triggered"] else (0, 200, 100)
                        _draw_hold_ring(frame, center, hold_info["hold_progress"], color)

                else:
                    # Detection is paused — only listen for hang_loose to unpause
                    gesture = detector.detect_gesture(result.landmarks)
                    hold_info = hold.update(gesture, now)
                    if gesture == Gesture.HANG_LOOSE and hold_info["action_triggered"]:
                        detection_paused = False
                        label = "RESUMED"
                    else:
                        label = "PAUSED"

            # Apply visual filter
            frame = filters.apply_filter(frame, filters.FILTER_LIST[filter_index], filter_intensity)

            # HUD overlay
            cv2.putText(frame, label, (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 3, cv2.LINE_AA)
            bitmask_label = f"Fingers: {detector.last_bitmask:05b}"
            cv2.putText(frame, bitmask_label, (10, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 200, 255), 2, cv2.LINE_AA)
            filter_label = f"Filter: {filters.FILTER_LIST[filter_index]}"
            cv2.putText(frame, filter_label, (10, h - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 200, 200), 2, cv2.LINE_AA)

            cv2.imshow("Gesture AI Desk", frame)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
    finally:
        camera.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Gesture AI Desk")
    parser.add_argument(
        "--mode",
        choices=["standalone", "ws"],
        default="standalone",
        help="standalone = cv2 window (default), ws = WebSocket server on port 8765",
    )
    args = parser.parse_args()

    if args.mode == "ws":
        import uvicorn
        from ws_server import app

        uvicorn.run(app, host="0.0.0.0", port=8765)
    else:
        main()
