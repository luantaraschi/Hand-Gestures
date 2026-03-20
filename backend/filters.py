"""OpenCV visual filters (PRD 4.4)."""

from __future__ import annotations

import cv2
import numpy as np

FILTER_LIST: list[str] = [
    "normal",
    "grayscale",
    "edge_detection",
    "blur",
    "landmark_highlight",
]


def apply_filter(
    frame: np.ndarray,
    filter_name: str,
    intensity: float = 1.0,
) -> np.ndarray:
    """Apply a named visual filter to *frame*.

    Args:
        frame: BGR image.
        filter_name: One of FILTER_LIST.
        intensity: 0.0–1.0 scaling factor (used by blur).

    Returns:
        Transformed BGR image (same shape).
    """
    if filter_name == "normal" or filter_name == "landmark_highlight":
        return frame

    if filter_name == "grayscale":
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        return cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)

    if filter_name == "edge_detection":
        edges = cv2.Canny(frame, 50, 150)
        return cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)

    if filter_name == "blur":
        ksize = int(15 * max(intensity, 0.1)) | 1  # must be odd, min 1
        return cv2.GaussianBlur(frame, (ksize, ksize), 0)

    return frame


def get_filter_list() -> list[str]:
    """Return the ordered list of available filter names."""
    return list(FILTER_LIST)


def next_filter(current_index: int) -> int:
    """Return the index of the next filter (wraps around)."""
    return (current_index + 1) % len(FILTER_LIST)


def prev_filter(current_index: int) -> int:
    """Return the index of the previous filter (wraps around)."""
    return (current_index - 1) % len(FILTER_LIST)
