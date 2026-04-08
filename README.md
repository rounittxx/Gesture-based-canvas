# Gesture-Based Drawing Canvas

A real-time, hand gesture-controlled drawing application built with Python, MediaPipe, and Streamlit. Draw, erase, and clear a virtual canvas entirely through webcam-detected hand gestures — no mouse, stylus, or touch input required.

🚀 **Live Demo:** [gesture-based-canvas-nqeopczkeobn4heuwnaoje.streamlit.app](https://gesture-based-canvas-nqeopczkeobn4heuwnaoje.streamlit.app)

---

## Features

- Real-time hand tracking at up to 30 fps using MediaPipe's hand landmark model
- Multiple drawing gestures: point up, point left, point right
- Two-finger peace gesture for erasing
- Double closed-fist gesture to reset the entire canvas within a 1-second window
- **Undo** support — restores the previous canvas state (up to 10 steps)
- **Clear Canvas** button as a reliable non-gesture fallback
- **Fingertip cursor** visible in idle mode for visual feedback
- Eight selectable brush colors (Black, Blue, Green, Red, Orange, Purple, Pink, Yellow)
- Adjustable brush size, eraser size, and canvas opacity via sidebar sliders
- 5-frame rolling average coordinate smoothing to eliminate finger-tip jitter
- Canvas snapshot export as a **timestamped PNG** directly from the browser
- On-screen HUD showing current mode (Drawing / Erasing / Idle / Canvas Reset)
- Live hand skeleton overlay rendered on the camera feed
- Fully containerized with Docker for consistent local execution
- Deployed on Streamlit Community Cloud

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3.10 |
| Web framework | Streamlit |
| Computer vision | OpenCV |
| Hand tracking | MediaPipe |
| Real-time video | streamlit-webrtc (WebRTC) |
| Containerization | Docker |
| Deployment | Streamlit Community Cloud |

---

## Gesture Reference

| Hand gesture | Action |
|-------------|--------|
| ☝️ Index finger pointing up | Draw |
| 👈 Index finger pointing left | Draw |
| 👉 Index finger pointing right | Draw |
| ✌️ Index + middle fingers up (peace sign) | Erase |
| ✊ Close fist twice within 1 second | Clear canvas |

---

## Project Structure

```
Gesture-based-canvas/
├── app.py                      # Main Streamlit app & video processor
├── requirements.txt            # Python dependencies
├── packages.txt                # System-level apt dependencies (Streamlit Cloud)
├── runtime.txt                 # Python version pin for Streamlit Cloud
├── Dockerfile                  # Docker image definition
├── .streamlit/
│   └── config.toml             # Streamlit theme and server config
└── Utils/
    ├── coordinate_control.py   # MediaPipe landmark gesture detection
    ├── features.py             # Canvas drawing, erasing, and overlay utils
    └── __init__.py
```

---

## How It Works

1. The webcam feed is captured via WebRTC inside the browser and streamed to a Python `VideoProcessorBase` instance.
2. Each frame is passed through MediaPipe's hand landmark model, which returns 21 3D keypoints per detected hand.
3. Relative positions of specific landmarks (index tip, middle tip, knuckles) are compared to determine the active gesture.
4. A 5-frame rolling average smooths the index finger tip coordinates before they are used for drawing.
5. Drawing operations (`cv2.line`, `cv2.circle`) are applied to a persistent NumPy canvas that survives across frames.
6. The canvas and the camera frame are blended together using `cv2.addWeighted` at a configurable opacity.
7. Sidebar controls (color, brush size, eraser size, opacity) are pushed to the video processor at each Streamlit re-run via thread-safe attribute assignment.
8. Undo snapshots are saved at the start of each new stroke and consumed via flag-based signalling between the Streamlit and video threads.

---

## Run Locally

### Prerequisites

- Python 3.10 or later
- pip

### 1. Clone the repository

```bash
git clone https://github.com/rounittxx/Gesture-based-canvas.git
cd Gesture-based-canvas
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

> On Linux you may also need: `sudo apt-get install libgl1 libglib2.0-0t64`

### 3. Start the application

```bash
streamlit run app.py
```

Open `http://localhost:8501` in your browser and allow webcam access when prompted.

---

## Run with Docker

```bash
# Build
docker build -t gesture-canvas .

# Run
docker run -p 8501:8501 gesture-canvas
```

Then open `http://localhost:8501` in your browser.

---

## Configuration

The `.streamlit/config.toml` file controls the server behaviour and app theme:

```toml
[server]
headless = true          # required for cloud deployment
enableCORS = false       # handled by Streamlit Cloud

[theme]
primaryColor    = "#6C63FF"
backgroundColor = "#0E1117"
```

---

## Known Limitations

- Single-hand detection only (`max_num_hands=1`).
- WebRTC performance depends on network conditions; some corporate proxies may block the connection.
- Canvas is not persisted between page reloads or browser sessions.

---

## License

MIT
