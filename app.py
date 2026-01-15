import cv2
import numpy as np
import mediapipe as mp
import time
import streamlit as st
from streamlit_webrtc import webrtc_streamer, VideoProcessorBase
import av

from Utils.coordinate_control import (
    upper_orienation,
    left_orienation,
    right_orienation,
    erase_orienation,
    reset_orienation
)
from Utils.features import draw, erase_with_circle, reset, colors

st.set_page_config(page_title="Gesture Canvas", layout="wide")
st.title("Gesture Based Drawing Canvas")

mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils


class GestureCanvas(VideoProcessorBase):
    def __init__(self):
        self.hands = mp_hands.Hands(max_num_hands=1)
        self.canvas = None
        self.prev_x, self.prev_y = None, None

        self.fist_count = 0
        self.fist_detected = True
        self.first_fist_time = 0
        self.time_between_fist = 1

    def recv(self, frame):
        frame = frame.to_ndarray(format="bgr24")
        frame = cv2.flip(frame, 1)
        h, w, _ = frame.shape

        if self.canvas is None:
            self.canvas = np.ones((h, w, 3), dtype=np.uint8) * 255

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = self.hands.process(rgb_frame)

        if result.multi_hand_landmarks:
            for hand_landmarks in result.multi_hand_landmarks:
                lm = hand_landmarks.landmark

                x = int(lm[8].x * w)
                y = int(lm[8].y * h)

                up = upper_orienation(lm)
                left = left_orienation(lm)
                right = right_orienation(lm)
                erase = erase_orienation(lm)

                # DRAW
                if up or left or right:
                    if self.prev_x is None:
                        self.prev_x, self.prev_y = x, y
                    cv2.line(self.canvas,
                             (self.prev_x, self.prev_y),
                             (x, y),
                             (0, 0, 0), 10)
                    self.prev_x, self.prev_y = x, y
                else:
                    self.prev_x, self.prev_y = None, None

                # ERASE
                if erase:
                    cv2.circle(self.canvas, (x, y), 35, (255, 255, 255), -1)
                    self.prev_x, self.prev_y = None, None

                # RESET (double fist)
                fist_closed = (
                    lm[8].y > lm[6].y and
                    lm[12].y > lm[10].y and
                    lm[16].y > lm[14].y and
                    lm[20].y > lm[18].y
                )

                current_time = time.time()

                if fist_closed and self.fist_detected:
                    self.fist_detected = False

                    if self.fist_count == 0:
                        self.fist_count = 1
                        self.first_fist_time = current_time

                    elif self.fist_count == 1:
                        if current_time - self.first_fist_time <= self.time_between_fist:
                            self.canvas[:] = 255
                            self.prev_x, self.prev_y = None, None
                            self.fist_count = 0
                        else:
                            self.first_fist_time = current_time

                if not fist_closed:
                    self.fist_detected = True

                if self.fist_count == 1 and (current_time - self.first_fist_time) > self.time_between_fist:
                    self.fist_count = 0

                mp_draw.draw_landmarks(
                    frame,
                    hand_landmarks,
                    mp_hands.HAND_CONNECTIONS
                )

        combined = cv2.addWeighted(frame, 0.5, self.canvas, 0.5, 0)
        return av.VideoFrame.from_ndarray(combined, format="bgr24")


webrtc_streamer(
    key="gesture-canvas",
    video_processor_factory=GestureCanvas,
    media_stream_constraints={"video": True, "audio": False},
)
