import cv2
import time

def draw(prev_x, prev_y, x, y,canvas):
    if prev_x is None:
        prev_x, prev_y = x, y
    cv2.line(canvas, (prev_x, prev_y), (x, y), (0, 0, 0), 10)
    prev_x, prev_y = x, y

def erase_with_circle(prev_x, prev_y, x, y,canvas):
    cv2.circle(canvas, (x, y), 30, (255, 255, 255), -1)
    prev_x, prev_y = None, None

def reset(prev_x, prev_y, x, y,canvas,lm):
    fist_closed = (
            lm[8].y > lm[6].y and
            lm[12].y > lm[10].y and
            lm[16].y > lm[14].y and
            lm[20].y > lm[18].y
    )

    fist_count = 0
    fist_detected = False
    first_fist_time = 0
    time_between_fist = 2.0

    current_time = time.time()

    if fist_closed and not fist_detected:
        fist_detected = True

        if fist_count == 0:
            fist_count = 1
            first_fist_time = current_time

        elif fist_count == 1:
            if current_time - first_fist_time <= time_between_fist:

                canvas[:] = 255
                prev_x, prev_y = None, None
                fist_count = 0
            else:
                fist_count = 1
                first_fist_time = current_time
    if not fist_closed:
        fist_detected = False

def colors():
    colors = [
        (0, 100, (0, 0, 0)),  # Black
        (100, 200, (0, 0, 255)),  # Red
        (200, 300, (0, 255, 0)),  # Green
        (300, 400, (255, 0, 0)),  # Blue
        (400, 500, (255, 255, 255))  # Eraser
    ]

    draw_color = (0, 0, 0)
    brush_thickness = 5
    return colors




