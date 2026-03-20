"""Gesture detection engine with bitmask encoding, stabilization, and pinch control."""

from __future__ import annotations

import time
from enum import IntEnum
from typing import Any

from utils import euclidean_distance, signed_distance


# ---------------------------------------------------------------------------
# Gesture enum (bitmask encoding — PRD 11.1)
# ---------------------------------------------------------------------------

class Gesture(IntEnum):
    """Gestures encoded as a 5-bit bitmask: THUMB | INDEX | MID | RING | PINKY.

    Special gestures that cannot be resolved by bitmask alone use values > 31.
    """

    NONE        = -1
    FIST        = 0b00000   # 0  — Mute toggle
    POINT       = 0b01000   # 8  — Screenshot
    PEACE       = 0b01100   # 12 — Next track
    THUMB_UP    = 0b10000   # 16 — Volume up
    HANG_LOOSE  = 0b10001   # 17 — Pause detection
    PALM        = 0b11111   # 31 — Play / Pause
    PINCH       = 33        # Pinch (thumb + index, axis-based)
    SWIPE_LEFT  = 35
    SWIPE_RIGHT = 36
    THUMB_DOWN  = 37        # Requires extra Y-position check


# ---------------------------------------------------------------------------
# Helpers — finger state (PRD 11.6 signed distance ratio)
# ---------------------------------------------------------------------------

def _is_finger_extended(
    landmarks: list[Any],
    tip_id: int,
    pip_id: int,
    wrist_id: int = 0,
) -> bool:
    """Check if a finger is extended using the signed-distance ratio.

    More robust than a simple Y comparison for rotated hands.
    """
    dist_tip_pip = signed_distance(landmarks[tip_id], landmarks[pip_id])
    dist_pip_wrist = signed_distance(landmarks[pip_id], landmarks[wrist_id])

    if abs(dist_pip_wrist) < 0.01:
        return False

    ratio = dist_tip_pip / dist_pip_wrist
    return ratio > 0.3


def _is_thumb_extended(landmarks: list[Any]) -> bool:
    """Thumb is extended if tip is far from MCP laterally OR well above it vertically.

    The lateral check (PRD 4.2) works when the thumb points sideways,
    but when the palm faces the camera with thumb pointing up the
    lateral gap shrinks.  Adding a vertical check fixes open-palm
    detection in that pose.
    """
    lateral = abs(landmarks[4].x - landmarks[2].x) > 0.04
    vertical = (landmarks[2].y - landmarks[4].y) > 0.04
    return lateral or vertical


# ---------------------------------------------------------------------------
# PinchSmoother (PRD 11.3 — dampening)
# ---------------------------------------------------------------------------

class PinchSmoother:
    """Dampens pinch values to eliminate jitter while preserving intent."""

    def __init__(self) -> None:
        self.prev_value: float = 0.0

    def smooth(self, raw_value: float) -> float:
        """Apply velocity-proportional dampening."""
        delta = raw_value - self.prev_value
        abs_delta = abs(delta)

        if abs_delta < 0.01:
            ratio = 0.0
        elif abs_delta < 0.05:
            ratio = 0.3
        else:
            ratio = 0.8

        smoothed = self.prev_value + delta * ratio
        self.prev_value = smoothed
        return smoothed

    def reset(self) -> None:
        """Reset smoother state."""
        self.prev_value = 0.0


# ---------------------------------------------------------------------------
# PinchController (PRD 11.4 — axis-based X/Y)
# ---------------------------------------------------------------------------

class PinchController:
    """Single pinch (thumb + index) with axis lock-in.

    Vertical movement controls volume, horizontal controls filter intensity.
    """

    ACTIVATE_DIST: float = 0.05
    DEACTIVATE_DIST: float = 0.12

    def __init__(self, threshold: float = 0.3) -> None:
        self.active: bool = False
        self.start_x: float = 0.0
        self.start_y: float = 0.0
        self.direction: str | None = None
        self.threshold = threshold
        self._smoother = PinchSmoother()

    def update(self, landmarks: list[Any]) -> dict[str, Any]:
        """Evaluate pinch state from current landmarks.

        Returns:
            Dict with keys: active, value (float), axis ("volume" | "filter_intensity" | None).
        """
        thumb_tip = landmarks[4]
        index_tip = landmarks[8]
        dist = euclidean_distance(thumb_tip, index_tip)

        # Activation
        if dist < self.ACTIVATE_DIST and not self.active:
            self.active = True
            self.start_x = index_tip.x
            self.start_y = index_tip.y
            self.direction = None
            self._smoother.reset()
            return {"active": True, "value": 0.0, "axis": None}

        # Deactivation
        if dist > self.DEACTIVATE_DIST and self.active:
            self.active = False
            self.direction = None
            return {"active": False, "value": 0.0, "axis": None}

        if self.active:
            dx = (index_tip.x - self.start_x) * 10
            dy = (self.start_y - index_tip.y) * 10  # Y inverted

            # Lock-in direction on first significant movement
            if self.direction is None:
                if abs(dy) > abs(dx) and abs(dy) > self.threshold:
                    self.direction = "vertical"
                elif abs(dx) > self.threshold:
                    self.direction = "horizontal"

            if self.direction == "vertical":
                smoothed = self._smoother.smooth(dy)
                return {"active": True, "value": smoothed, "axis": "volume"}
            elif self.direction == "horizontal":
                smoothed = self._smoother.smooth(dx)
                return {"active": True, "value": smoothed, "axis": "filter_intensity"}

            return {"active": True, "value": 0.0, "axis": None}

        return {"active": False, "value": 0.0, "axis": None}


# ---------------------------------------------------------------------------
# GestureStabilizer (PRD 11.2 — frame counter)
# ---------------------------------------------------------------------------

class GestureStabilizer:
    """Require a gesture to persist for N consecutive frames before accepting it."""

    def __init__(self, threshold: int = 5) -> None:
        self.threshold = threshold
        self._prev_gesture: Gesture = Gesture.NONE
        self._frame_count: int = 0
        self._stable_gesture: Gesture = Gesture.NONE

    def update(self, detected: Gesture) -> Gesture:
        """Feed a per-frame detection and return the stabilized gesture."""
        if detected == self._prev_gesture:
            self._frame_count += 1
        else:
            self._frame_count = 0

        self._prev_gesture = detected

        if self._frame_count >= self.threshold:
            self._stable_gesture = detected

        return self._stable_gesture


# ---------------------------------------------------------------------------
# GestureDetector (main façade)
# ---------------------------------------------------------------------------

class GestureDetector:
    """Detects gestures from hand landmarks following the priority rules in PRD 4.6."""

    # Bitmask values that map directly to a Gesture member
    _BITMASK_MAP: dict[int, Gesture] = {
        g.value: g
        for g in Gesture
        if 0 <= g.value <= 31
    }

    def __init__(self) -> None:
        self._pinch = PinchController()
        self._stabilizer = GestureStabilizer()
        self._wrist_history: list[dict[str, float]] = []
        self.pinch_state: dict[str, Any] = {"active": False, "value": 0.0, "axis": None}
        self.last_bitmask: int = 0

    # -- public API ---------------------------------------------------------

    def compute_finger_state(self, landmarks: list[Any]) -> int:
        """Return a 5-bit bitmask representing which fingers are extended."""
        state = 0
        if _is_thumb_extended(landmarks):
            state |= 0b10000
        if _is_finger_extended(landmarks, 8, 6):
            state |= 0b01000
        if _is_finger_extended(landmarks, 12, 10):
            state |= 0b00100
        if _is_finger_extended(landmarks, 16, 14):
            state |= 0b00010
        if _is_finger_extended(landmarks, 20, 18):
            state |= 0b00001
        return state

    def detect_gesture(self, landmarks: list[Any]) -> Gesture:
        """Run the full detection pipeline and return the current gesture.

        Priority order (PRD 4.6): pinch > swipe > static gestures.
        Fist-like poses (all non-thumb fingers closed) bypass pinch to
        prevent false activation when the thumb wraps over curled fingers.
        """
        # 1. Compute finger bitmask FIRST (needed for fist guard)
        bitmask = self.compute_finger_state(landmarks)
        self.last_bitmask = bitmask

        # 2. Fist guard — skip pinch when all non-thumb fingers are closed
        fist_like = (bitmask & 0b01111) == 0
        if fist_like:
            if self._pinch.active:
                self._pinch.active = False
                self._pinch.direction = None
            self.pinch_state = {"active": False, "value": 0.0, "axis": None}
        else:
            # 3. Pinch — highest priority among non-fist poses
            self.pinch_state = self._pinch.update(landmarks)
            if self.pinch_state["active"]:
                return Gesture.PINCH

        # 4. Swipe — open hand (at least 4 fingers extended)
        self._update_wrist_history(landmarks)
        if bin(bitmask).count("1") >= 4:
            swipe = self._detect_swipe()
            if swipe is not None:
                return swipe

        # 5. Thumb down — special Y-position check (PRD 4.3)
        if self._is_thumb_down(landmarks, bitmask):
            return self._stabilizer.update(Gesture.THUMB_DOWN)

        # 6. Thumb up — bitmask 0b10000 + extra distance check (PRD 4.3)
        if bitmask == Gesture.THUMB_UP and self._is_thumb_up(landmarks):
            return self._stabilizer.update(Gesture.THUMB_UP)

        # 7. Resolve bitmask → Gesture
        gesture = self._BITMASK_MAP.get(bitmask, Gesture.NONE)
        return self._stabilizer.update(gesture)

    # -- private helpers ----------------------------------------------------

    def _is_thumb_down(self, landmarks: list[Any], bitmask: int) -> bool:
        """Thumb tip is below the wrist and all four fingers are closed."""
        all_fingers_closed = (bitmask & 0b01111) == 0
        thumb_below_wrist = landmarks[4].y > landmarks[0].y
        return thumb_below_wrist and all_fingers_closed

    def _is_thumb_up(self, landmarks: list[Any]) -> bool:
        """Thumb above MCP and far enough from index to avoid pinch conflict."""
        thumb_above_mcp = landmarks[4].y < landmarks[2].y
        thumb_far_from_index = euclidean_distance(landmarks[4], landmarks[8]) > 0.06
        return thumb_above_mcp and thumb_far_from_index

    def _update_wrist_history(self, landmarks: list[Any]) -> None:
        """Append current wrist position to the rolling history buffer."""
        now = time.monotonic()
        self._wrist_history.append({"x": landmarks[0].x, "t": now})
        # Keep only entries within the last second
        self._wrist_history = [
            p for p in self._wrist_history if now - p["t"] < 1.0
        ]

    def _detect_swipe(
        self,
        threshold: float = 0.08,
        time_window: float = 0.4,
    ) -> Gesture | None:
        """Detect a horizontal swipe from wrist movement history.

        Args:
            threshold: Minimum normalized horizontal displacement.
            time_window: Maximum duration of the swipe in seconds.

        Returns:
            Gesture.SWIPE_LEFT, Gesture.SWIPE_RIGHT, or None.
        """
        now = time.monotonic()
        recent = [p for p in self._wrist_history if now - p["t"] < time_window]
        if len(recent) < 2:
            return None

        dx = recent[-1]["x"] - recent[0]["x"]

        if dx > threshold:
            self._wrist_history.clear()
            return Gesture.SWIPE_RIGHT
        if dx < -threshold:
            self._wrist_history.clear()
            return Gesture.SWIPE_LEFT

        return None
