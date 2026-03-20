"""Geometric helper functions for landmark processing."""

import math
from typing import Any


def signed_distance(p1: Any, p2: Any) -> float:
    """Euclidean distance with sign based on the Y axis.

    The sign is positive when p1 is above p2 (p1.y < p2.y in screen
    coordinates where Y grows downward), negative otherwise.  This is
    used for the finger-state ratio described in PRD section 11.6.

    Args:
        p1: Object with .x and .y attributes (e.g. MediaPipe landmark).
        p2: Object with .x and .y attributes.

    Returns:
        Signed euclidean distance.
    """
    sign = 1 if p1.y < p2.y else -1
    dist = math.sqrt((p1.x - p2.x) ** 2 + (p1.y - p2.y) ** 2)
    return dist * sign


def euclidean_distance(p1: Any, p2: Any) -> float:
    """Standard 2-D euclidean distance between two landmark-like objects.

    Args:
        p1: Object with .x and .y attributes.
        p2: Object with .x and .y attributes.

    Returns:
        Non-negative euclidean distance.
    """
    return math.sqrt((p1.x - p2.x) ** 2 + (p1.y - p2.y) ** 2)


def normalize_value(value: float, min_val: float, max_val: float) -> float:
    """Linearly map *value* into the 0-1 range and clamp.

    Args:
        value: Raw value to normalize.
        min_val: Value that maps to 0.
        max_val: Value that maps to 1.

    Returns:
        Clamped float in [0.0, 1.0].
    """
    if max_val == min_val:
        return 0.0
    normalized = (value - min_val) / (max_val - min_val)
    return max(0.0, min(1.0, normalized))
