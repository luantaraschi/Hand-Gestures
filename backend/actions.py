"""System actions — media keys, volume control, screenshot (PRD 4.3 / 11.5)."""

from __future__ import annotations

import logging
import os
from datetime import datetime

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Media keys via pynput
# ---------------------------------------------------------------------------

def toggle_play_pause() -> None:
    """Simulate the media play/pause key."""
    try:
        from pynput.keyboard import Controller, Key
        Controller().tap(Key.media_play_pause)
        log.info("Action: play/pause toggled")
    except Exception:
        log.exception("Failed to toggle play/pause")


def next_track() -> None:
    """Simulate the media next-track key."""
    try:
        from pynput.keyboard import Controller, Key
        Controller().tap(Key.media_next)
        log.info("Action: next track")
    except Exception:
        log.exception("Failed to skip track")


# ---------------------------------------------------------------------------
# Volume via pycaw (Windows COM API)
# ---------------------------------------------------------------------------

def _get_volume_interface():
    """Return the IAudioEndpointVolume COM pointer."""
    from ctypes import POINTER, cast
    from comtypes import CLSCTX_ALL
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

    devices = AudioUtilities.GetSpeakers()
    interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
    return cast(interface, POINTER(IAudioEndpointVolume))


def get_volume() -> float:
    """Return the current master volume as a float in [0.0, 1.0]."""
    try:
        return _get_volume_interface().GetMasterVolumeLevelScalar()
    except Exception:
        log.exception("Failed to get volume")
        return 0.0


def set_volume(level: float) -> None:
    """Set master volume to *level* (clamped to 0.0–1.0)."""
    try:
        clamped = max(0.0, min(1.0, level))
        _get_volume_interface().SetMasterVolumeLevelScalar(clamped, None)
        log.info("Action: volume set to %.0f%%", clamped * 100)
    except Exception:
        log.exception("Failed to set volume")


def volume_up(step: float = 0.05) -> None:
    """Increase master volume by *step*."""
    set_volume(get_volume() + step)


def volume_down(step: float = 0.05) -> None:
    """Decrease master volume by *step*."""
    set_volume(get_volume() - step)


def toggle_mute() -> None:
    """Toggle the system mute state."""
    try:
        vol = _get_volume_interface()
        vol.SetMute(not vol.GetMute(), None)
        log.info("Action: mute toggled")
    except Exception:
        log.exception("Failed to toggle mute")


# ---------------------------------------------------------------------------
# Screenshot via Pillow
# ---------------------------------------------------------------------------

def take_screenshot(save_dir: str | None = None) -> str | None:
    """Capture a screenshot and save it as a timestamped PNG.

    Args:
        save_dir: Directory to save into.  Defaults to ~/Pictures/gesture_screenshots.

    Returns:
        The saved file path, or None on failure.
    """
    try:
        from PIL import ImageGrab

        if save_dir is None:
            save_dir = os.path.join(os.path.expanduser("~"), "Pictures", "gesture_screenshots")
        os.makedirs(save_dir, exist_ok=True)

        filename = datetime.now().strftime("screenshot_%Y%m%d_%H%M%S.png")
        filepath = os.path.join(save_dir, filename)

        ImageGrab.grab().save(filepath)
        log.info("Action: screenshot saved to %s", filepath)
        return filepath
    except Exception:
        log.exception("Failed to take screenshot")
        return None
