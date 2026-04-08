import cv2
import numpy as np
import mediapipe as mp
import time
import threading
from collections import deque
from datetime import datetime
from typing import Optional, Tuple

import streamlit as st
from streamlit_webrtc import webrtc_streamer, VideoProcessorBase
import av

from Utils.coordinate_control import (
    is_drawing_gesture,
    erase_orientation,
    reset_orientation,
)
from Utils.features import (
    draw as canvas_draw,
    erase as canvas_erase,
    reset_canvas,
    add_status_overlay,
    COLOR_PALETTE,
)

# Page configuration
st.set_page_config(
    page_title="Gesture Canvas",
    page_icon="https://raw.githubusercontent.com/googlesamples/mediapipe/main/assets/hand.png",
    layout="wide",
)

st.title("Gesture-Based Drawing Canvas")
st.caption("Draw on the canvas using your hand gestures — no mouse or stylus required.")

# Sidebar controls
with st.sidebar:
    st.header("Drawing Controls")

    color_name = st.selectbox(
        "Brush Color",
        list(COLOR_PALETTE.keys()),
        index=0,
        help="Select the color to draw with.",
    )
    selected_color: Tuple[int, int, int] = COLOR_PALETTE[color_name]

    brush_size = st.slider(
        "Brush Size",
        min_value=2,
        max_value=40,
        value=10,
        step=1,
        help="Stroke thickness in pixels.",
    )

    eraser_size = st.slider(
        "Eraser Size",
        min_value=10,
        max_value=80,
        value=35,
        step=5,
        help="Eraser radius in pixels.",
    )

    canvas_opacity = st.slider(
        "Canvas Opacity",
        min_value=0.1,
        max_value=1.0,
        value=0.55,
        step=0.05,
        help="Blend ratio of canvas over camera feed.",
    )

    st.divider()
    st.header("Gesture Guide")
    st.markdown(
        """
        | Gesture | Action |
        |---------|--------|
        | Index finger up | Draw |
        | Index finger left | Draw |
        | Index finger right | Draw |
        | Two fingers up (peace) | Erase |
        | Double fist (within 1 s) | Clear canvas |
        """
    )

    st.divider()
    st.header("Canvas Actions")
    clear_area   = st.empty()   # Clear Canvas button
    undo_area    = st.empty()   # Undo button
    st.divider()
    st.header("Save Canvas")
    save_area    = st.empty()   # Snapshot / download button


# MediaPipe initialisation
mp_hands = mp.solutions.hands
mp_draw  = mp.solutions.drawing_utils

# Constants
DOUBLE_FIST_WINDOW  = 1.0   # seconds between two fists to trigger a canvas reset
SMOOTH_BUFFER_SIZE  = 5     # number of frames averaged for coordinate smoothing
UNDO_STACK_SIZE     = 10    # maximum number of undo snapshots kept in memory


class GestureCanvas(VideoProcessorBase):
    """
    Real-time video processor that:
    - Detects hand landmarks using MediaPipe
    - Interprets drawing, erasing, and reset gestures
    - Applies temporal smoothing to reduce finger-tip jitter
    - Overlays the persistent canvas on the live camera feed
    - Supports undo (up to 10 strokes) and one-click clear
    """

    def __init__(self) -> None:
        self.hands = mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        )

        # Canvas shared between the video thread and the Streamlit main thread
        self.canvas: Optional[np.ndarray] = None
        self._canvas_lock = threading.Lock()

        # Last confirmed drawing position
        self.prev_x: Optional[int] = None
        self.prev_y: Optional[int] = None

        # Rolling average buffers for smoothing
        self._buf_x: deque = deque(maxlen=SMOOTH_BUFFER_SIZE)
        self._buf_y: deque = deque(maxlen=SMOOTH_BUFFER_SIZE)

        # Double-fist detection state
        self._fist_count: int = 0
        self._fist_open:  bool  = True
        self._first_fist_time: float = 0.0

        # Stroke-start tracking for undo snapshot timing
        self._was_drawing: bool = False
        self._was_erasing: bool = False

        # Undo history: deque of canvas snapshots (uint8 copies)
        self._undo_stack: deque = deque(maxlen=UNDO_STACK_SIZE)

        # Flags set by the Streamlit thread, consumed by the video thread
        self._undo_requested:  bool = False
        self._clear_requested: bool = False

        # Configurable properties pushed from the Streamlit thread
        self.draw_color:     Tuple[int, int, int] = (0, 0, 0)
        self.brush_size:     int   = 10
        self.eraser_size:    int   = 35
        self.canvas_opacity: float = 0.55

    # -- Private helpers -------------------------------------------------------

    def _smooth(self, x: int, y: int) -> Tuple[int, int]:
        """Return a moving-average smoothed position."""
        self._buf_x.append(x)
        self._buf_y.append(y)
        return int(np.mean(self._buf_x)), int(np.mean(self._buf_y))

    def _clear_smooth(self) -> None:
        self._buf_x.clear()
        self._buf_y.clear()

    def _save_undo_snapshot(self) -> None:
        """Push a copy of the current canvas onto the undo stack (must be called inside lock)."""
        if self.canvas is not None:
            self._undo_stack.append(self.canvas.copy())

    # -- Public API (called from the Streamlit thread) -------------------------

    def get_canvas_snapshot(self) -> Optional[np.ndarray]:
        """Return a thread-safe copy of the current canvas."""
        with self._canvas_lock:
            return self.canvas.copy() if self.canvas is not None else None

    def request_undo(self) -> None:
        """Signal the video thread to restore the previous canvas state."""
        with self._canvas_lock:
            self._undo_requested = True

    def request_clear(self) -> None:
        """Signal the video thread to clear the canvas."""
        with self._canvas_lock:
            self._clear_requested = True

    # -- Frame processing -----------------------------------------------------

    def recv(self, frame: av.VideoFrame) -> av.VideoFrame:
        img = frame.to_ndarray(format="bgr24")
        img = cv2.flip(img, 1)
        h, w, _ = img.shape

        # Lazy canvas initialisation (size known only after first frame)
        with self._canvas_lock:
            if self.canvas is None:
                self.canvas = np.full((h, w, 3), 255, dtype=np.uint8)

        # Run MediaPipe hand detection on an RGB copy
        rgb    = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        result = self.hands.process(rgb)

        status = "Idle"
        cursor_pos: Optional[Tuple[int, int]] = None  # fingertip for idle cursor

        if result.multi_hand_landmarks:
            for hand_landmarks in result.multi_hand_landmarks:
                lm = hand_landmarks.landmark

                # Smooth index-finger-tip position
                raw_x = int(lm[8].x * w)
                raw_y = int(lm[8].y * h)
                x, y  = self._smooth(raw_x, raw_y)
                cursor_pos = (x, y)

                is_draw  = is_drawing_gesture(lm)
                is_erase = erase_orientation(lm)
                is_fist  = reset_orientation(lm)

                with self._canvas_lock:
                    # Handle deferred undo / clear requests
                    if self._clear_requested:
                        self._save_undo_snapshot()
                        reset_canvas(self.canvas)
                        self.prev_x, self.prev_y = None, None
                        self._clear_smooth()
                        self._clear_requested = False

                    if self._undo_requested:
                        if self._undo_stack:
                            self.canvas[:] = self._undo_stack.pop()
                            self.prev_x, self.prev_y = None, None
                            self._clear_smooth()
                        self._undo_requested = False

                    # Drawing mode
                    if is_draw and not is_erase:
                        status = "Drawing"
                        # Save undo snapshot at the start of each new stroke
                        if not self._was_drawing:
                            self._save_undo_snapshot()
                        self._was_drawing = True
                        self._was_erasing = False

                        prev = (self.prev_x, self.prev_y) if self.prev_x is not None else None
                        canvas_draw(self.canvas, prev, (x, y), self.draw_color, self.brush_size)
                        self.prev_x, self.prev_y = x, y

                    # Erasing mode
                    elif is_erase:
                        status = "Erasing"
                        # Save undo snapshot at the start of each new erase action
                        if not self._was_erasing:
                            self._save_undo_snapshot()
                        self._was_erasing = True
                        self._was_drawing = False

                        canvas_erase(self.canvas, (x, y), self.eraser_size)
                        self.prev_x, self.prev_y = None, None
                        self._clear_smooth()

                    # Idle — release the last draw position
                    else:
                        self._was_drawing = False
                        self._was_erasing = False
                        self.prev_x, self.prev_y = None, None
                        self._clear_smooth()

                    # Double-fist canvas reset
                    current_time = time.monotonic()

                    if is_fist and self._fist_open:
                        self._fist_open = False
                        if self._fist_count == 0:
                            self._fist_count      = 1
                            self._first_fist_time = current_time
                        elif self._fist_count == 1:
                            if current_time - self._first_fist_time <= DOUBLE_FIST_WINDOW:
                                self._save_undo_snapshot()
                                reset_canvas(self.canvas)
                                self.prev_x, self.prev_y = None, None
                                self._clear_smooth()
                                self._fist_count = 0
                                status = "Canvas Reset"
                            else:
                                self._fist_count      = 1
                                self._first_fist_time = current_time

                    if not is_fist:
                        self._fist_open = True

                    # Expire a first fist that was never followed up
                    if (self._fist_count == 1 and
                            current_time - self._first_fist_time > DOUBLE_FIST_WINDOW):
                        self._fist_count = 0

                mp_draw.draw_landmarks(img, hand_landmarks, mp_hands.HAND_CONNECTIONS)

        # Blend camera feed and canvas
        with self._canvas_lock:
            canvas_snap = self.canvas.copy()

        alpha    = self.canvas_opacity
        combined = cv2.addWeighted(img, 1.0 - alpha, canvas_snap, alpha, 0)

        add_status_overlay(combined, status, self.draw_color)

        # Draw a fingertip cursor when hand is visible but not actively drawing/erasing
        if cursor_pos is not None and status == "Idle":
            cx, cy = cursor_pos
            cv2.circle(combined, (cx, cy), self.brush_size + 4, (180, 180, 180), 2)
            cv2.circle(combined, (cx, cy), 3, (255, 255, 255), -1)

        return av.VideoFrame.from_ndarray(combined, format="bgr24")


# WebRTC video streamer
ctx = webrtc_streamer(
    key="gesture-canvas",
    video_processor_factory=GestureCanvas,
    media_stream_constraints={"video": True, "audio": False},
    async_processing=True,
    rtc_configuration={
        "iceServers": [
            {"urls": ["stun:stun.l.google.com:19302"]},
            {"urls": ["stun:stun1.l.google.com:19302"]},
            {"urls": ["stun:stun2.l.google.com:19302"]},
        ]
    },
)

# Push sidebar settings into the running video processor
if ctx.video_processor:
    ctx.video_processor.draw_color     = selected_color
    ctx.video_processor.brush_size     = brush_size
    ctx.video_processor.eraser_size    = eraser_size
    ctx.video_processor.canvas_opacity = canvas_opacity

    # Clear Canvas button
    with clear_area:
        if st.button("🗑️ Clear Canvas", help="Erase everything (undo-able)"):
            ctx.video_processor.request_clear()

    # Undo button
    with undo_area:
        if st.button("↩️ Undo Last Stroke", help="Restore the previous canvas state (up to 10 steps)"):
            ctx.video_processor.request_undo()

    # Canvas snapshot / download
    with save_area:
        if st.button("📷 Capture Canvas Snapshot"):
            snapshot = ctx.video_processor.get_canvas_snapshot()
            if snapshot is not None:
                timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
                filename  = f"canvas_{timestamp}.png"
                _, buf = cv2.imencode(".png", snapshot)
                st.download_button(
                    label=f"⬇️ Download {filename}",
                    data=buf.tobytes(),
                    file_name=filename,
                    mime="image/png",
                )
            else:
                st.warning("Start drawing first — no canvas to save yet.")
