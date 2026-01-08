import cv2
import numpy as np
import mediapipe as mp
import time
from Utils.coordinate_control import upper_orienation,left_orienation,right_orienation,erase_orienation,reset_orienation
from Utils.features import draw,erase_with_circle,reset,colors
import streamlit as st




cap = cv2.VideoCapture(0)

# Read one frame to get size
ret, frame = cap.read()
if not ret:
    print("Failed to access camera")
    exit()

h, w, _ = frame.shape


canvas = np.ones((h, w, 3), dtype=np.uint8) * 255


mp_hands = mp.solutions.hands
hand = mp_hands.Hands(max_num_hands=1)
mp_draw = mp.solutions.drawing_utils

prev_x, prev_y = None, None

fist_count = 0
fist_detected = True
first_fist_time = 0
time_between_fist = 1


while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = hand.process(rgb_frame)


    if result.multi_hand_landmarks:
        for hand_landmarks in result.multi_hand_landmarks:
            lm = hand_landmarks.landmark



            x = int(lm[8].x * w)
            y = int(lm[8].y * h)

            up=upper_orienation(lm)
            left=left_orienation(lm)
            right=right_orienation(lm)
            erase=erase_orienation(lm)



            if up or left or right:
                if prev_x is None:
                    prev_x, prev_y = x, y
                cv2.line(canvas, (prev_x, prev_y), (x, y), (0, 0, 0), 10)
                prev_x, prev_y = x, y


            if erase:
                cv2.circle(canvas, (x, y), 35, (255, 255, 255), -1)
                prev_x, prev_y = None, None

            fist_closed = (
                    lm[8].y > lm[6].y and
                    lm[12].y > lm[10].y and
                    lm[16].y > lm[14].y and
                    lm[20].y > lm[18].y
            )



            current_time = time.time()

            if fist_closed and fist_detected:
                fist_detected = False

                if fist_count == 0:
                    fist_count = 1
                    first_fist_time = current_time
                    print("First squeeze")
                    print(fist_count)

                elif fist_count == 1:
                    if current_time - first_fist_time <= time_between_fist:
                        print("RESET")

                        canvas = np.ones((h, w, 3), dtype=np.uint8) * 255
                        prev_x, prev_y = None, None
                        fist_count = 0
                    else:
                        fist_count = 1
                        first_fist_time = current_time
            if not fist_closed:
                fist_detected = True

            if fist_count == 1 and (current_time - first_fist_time) > time_between_fist:
                fist_count = 0



            mp_draw.draw_landmarks(
                frame,
                hand_landmarks,
                mp_hands.HAND_CONNECTIONS
            )

    combined = cv2.addWeighted(frame, 0.5, canvas, 0.5, 0)
    cv2.imshow("Gesture Canvas", combined)

    key = cv2.waitKey(1)
    if key == 27:  # ESC
        break
    if key == ord('c'):  # Clear canvas
        canvas[:] = 255

cap.release()
cv2.destroyAllWindows()
#
