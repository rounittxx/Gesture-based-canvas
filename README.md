# Gesture-Based Virtual Drawing Canvas 

A real-time gesture-controlled drawing application that allows users to draw, erase, and reset a virtual canvas using hand gestures captured via webcam.

---

## Features
- Real-time hand tracking using MediaPipe
- Gesture-based drawing and erasing
- Double-fist gesture to reset canvas
- Smooth drawing with persistent canvas
- Secure webcam access using HTTPS

---

## Tech Stack
- Python
- OpenCV
- MediaPipe
- Streamlit
- Docker
- ngrok

---

## How It Works
- Index finger movement is tracked for drawing
- Specific hand gestures trigger erase and reset actions
- Canvas is overlaid on live webcam feed

---

## Run Locally with Docker (Recommended)

### 1. Build Docker Image
```bash
docker build -t gesture-canvas .
