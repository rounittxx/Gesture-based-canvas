"""
Hand gesture orientation detection using MediaPipe landmarks.
Each function returns True if the specified gesture is detected, False otherwise.

Landmark reference:
  8  = Index finger tip
  6  = Index finger PIP (middle knuckle)
  12 = Middle finger tip
  10 = Middle finger PIP
  16 = Ring finger tip    / 14 = Ring finger PIP
  20 = Pinky tip          / 18 = Pinky PIP
"""

from typing import Any, List


def upper_orientation(lm: List[Any]) -> bool:
    """Index finger pointing up, middle finger down (pointing up gesture)."""
    return bool(lm[8].y < lm[6].y and lm[12].y > lm[10].y)


def left_orientation(lm: List[Any]) -> bool:
    """Index finger tip to the left of its knuckle while middle finger is to the right."""
    return bool(lm[8].x < lm[6].x and lm[12].x > lm[10].x)


def right_orientation(lm: List[Any]) -> bool:
    """Index finger tip to the right of its knuckle while middle finger is to the left."""
    return bool(lm[8].x > lm[6].x and lm[12].x < lm[10].x)


def erase_orientation(lm: List[Any]) -> bool:
    """Both index AND middle fingers raised (peace/scissors gesture → erase mode)."""
    return bool(lm[8].y < lm[6].y and lm[12].y < lm[10].y)


def reset_orientation(lm: List[Any]) -> bool:
    """All four fingers curled below their knuckles (closed fist)."""
    return bool(
        lm[8].y > lm[6].y and
        lm[12].y > lm[10].y and
        lm[16].y > lm[14].y and
        lm[20].y > lm[18].y
    )


def is_drawing_gesture(lm: List[Any]) -> bool:
    """True when any draw-triggering gesture is detected (up, left, or right)."""
    return upper_orientation(lm) or left_orientation(lm) or right_orientation(lm)
