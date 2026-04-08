"""
Drawing and canvas utility functions for the Gesture-Based Canvas application.
All drawing operations modify the NumPy canvas array in-place.
"""

import cv2
import numpy as np
from typing import Optional, Tuple

# Default drawing constants
DEFAULT_DRAW_COLOR: Tuple[int, int, int] = (0, 0, 0)   # BGR black
DEFAULT_BRUSH_SIZE: int = 10
DEFAULT_ERASER_SIZE: int = 35

# Color palette mapping display name to BGR tuple
COLOR_PALETTE: dict = {
    "Black":  (0,   0,   0),
    "Blue":   (255, 0,   0),
    "Green":  (0,   180, 0),
    "Red":    (0,   0,   220),
    "Orange": (0,   140, 255),
    "Purple": (180, 0,   180),
    "Pink":   (147, 20,  255),
    "Yellow": (0,   215, 255),
}


def draw(
    canvas: np.ndarray,
    prev_point: Optional[Tuple[int, int]],
    curr_point: Tuple[int, int],
    color: Tuple[int, int, int] = DEFAULT_DRAW_COLOR,
    thickness: int = DEFAULT_BRUSH_SIZE,
) -> None:
    """
    Draw a line from prev_point to curr_point on the canvas.
    If prev_point is None, a single dot is drawn at curr_point.
    """
    if prev_point is None:
        cv2.circle(canvas, curr_point, max(thickness // 2, 1), color, -1)
    else:
        cv2.line(canvas, prev_point, curr_point, color, thickness, lineType=cv2.LINE_AA)


def erase(
    canvas: np.ndarray,
    point: Tuple[int, int],
    radius: int = DEFAULT_ERASER_SIZE,
) -> None:
    """Fill a circular region with white to simulate erasing."""
    cv2.circle(canvas, point, radius, (255, 255, 255), -1)


def reset_canvas(canvas: np.ndarray) -> None:
    """Clear the entire canvas by setting all pixels to white."""
    canvas[:] = 255


def add_status_overlay(
    frame: np.ndarray,
    status: str,
    draw_color: Tuple[int, int, int] = DEFAULT_DRAW_COLOR,
) -> None:
    """
    Render a translucent status bar at the bottom-left corner of the frame
    showing the current drawing mode and a color swatch.
    """
    h, w = frame.shape[:2]
    overlay = frame.copy()

    x1, y1, x2, y2 = 10, h - 52, 270, h - 10
    cv2.rectangle(overlay, (x1, y1), (x2, y2), (40, 40, 40), -1)
    cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)
    cv2.rectangle(frame, (x1, y1), (x2, y2), (160, 160, 160), 1)

    cv2.putText(
        frame,
        f"Mode: {status}",
        (x1 + 8, y2 - 14),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.60,
        (255, 255, 255),
        2,
        cv2.LINE_AA,
    )

    # Small color swatch in the bottom-right corner of the status bar
    sw_x1, sw_y1 = x2 - 32, y1 + 6
    sw_x2, sw_y2 = x2 - 8,  y2 - 6
    cv2.rectangle(frame, (sw_x1, sw_y1), (sw_x2, sw_y2), draw_color, -1)
    cv2.rectangle(frame, (sw_x1, sw_y1), (sw_x2, sw_y2), (200, 200, 200), 1)
