"""Hold timer and cooldown logic for gesture actions (PRD 4.3 / 4.7)."""

from __future__ import annotations

from gesture_engine import Gesture

# Gestures that bypass the hold mechanism entirely
_CONTINUOUS_GESTURES = {Gesture.PINCH, Gesture.SWIPE_LEFT, Gesture.SWIPE_RIGHT}


class HoldManager:
    """Track how long a gesture is held and enforce a cooldown after triggering.

    Static gestures must be held for *hold_duration* seconds before the
    corresponding action fires.  After firing, a *cooldown* period
    prevents accidental re-triggers.
    """

    def __init__(
        self,
        hold_duration: float = 0.5,
        cooldown: float = 1.0,
    ) -> None:
        self.hold_duration = hold_duration
        self.cooldown = cooldown

        self._current_gesture: Gesture = Gesture.NONE
        self._hold_start: float = 0.0
        self._last_trigger_time: float = 0.0
        self._triggered: bool = False

    def update(self, gesture: Gesture, timestamp: float) -> dict:
        """Evaluate hold progress for the current frame.

        Args:
            gesture: Stabilized gesture for this frame.
            timestamp: Monotonic clock value (seconds).

        Returns:
            Dict with hold_progress (0.0-1.0), action_triggered (bool),
            and in_cooldown (bool).
        """
        # Continuous gestures skip hold entirely
        if gesture in _CONTINUOUS_GESTURES:
            return {"hold_progress": 0.0, "action_triggered": False, "in_cooldown": False}

        # Cooldown check
        in_cooldown = (timestamp - self._last_trigger_time) < self.cooldown

        # Gesture changed — reset hold
        if gesture != self._current_gesture:
            self._current_gesture = gesture
            self._hold_start = timestamp
            self._triggered = False
            return {"hold_progress": 0.0, "action_triggered": False, "in_cooldown": in_cooldown}

        # No actionable gesture
        if gesture == Gesture.NONE:
            return {"hold_progress": 0.0, "action_triggered": False, "in_cooldown": in_cooldown}

        # Compute progress
        elapsed = timestamp - self._hold_start
        progress = min(elapsed / self.hold_duration, 1.0)

        # Already triggered for this hold — wait for gesture change
        if self._triggered:
            return {"hold_progress": 1.0, "action_triggered": False, "in_cooldown": in_cooldown}

        # Check if hold completed and not in cooldown
        if progress >= 1.0 and not in_cooldown:
            self._triggered = True
            self._last_trigger_time = timestamp
            return {"hold_progress": 1.0, "action_triggered": True, "in_cooldown": False}

        return {"hold_progress": progress, "action_triggered": False, "in_cooldown": in_cooldown}
