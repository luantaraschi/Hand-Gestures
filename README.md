# Gesture AI Desk

> Control your computer with hand gestures in real time. No keyboard, no mouse, no touch.

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)
![Next.js](https://img.shields.io/badge/Next.js-16-000000?logo=next.js&logoColor=white)
![MediaPipe](https://img.shields.io/badge/MediaPipe-0.10-4285F4?logo=google&logoColor=white)
![OpenCV](https://img.shields.io/badge/OpenCV-4.9+-5C3EE8?logo=opencv&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)

<!-- Replace with your own demo GIF:
1. Record your screen with OBS or ScreenToGif
2. Trim to ~10-15 seconds showing 2-3 gestures
3. Save as demo.gif in the repo root
4. Uncomment the line below:
-->
<!-- ![Demo](demo.gif) -->

---

## Features

- **7 static gestures** detected in real time via MediaPipe Hand Landmarker
- **Pinch control** with axis lock-in (vertical = volume, horizontal = filter intensity)
- **Swipe detection** to cycle through visual filters
- **Hold-to-confirm** with radial progress ring (prevents accidental triggers)
- **System actions**: play/pause, mute, next track, volume, screenshot
- **Visual filters**: normal, grayscale, edge detection, blur, landmark highlight
- **React dashboard** with live camera feed, gesture HUD, log, and config panel
- **100% offline** - no external APIs, runs entirely on your machine

---

## How It Works

```
Webcam ──> OpenCV ──> MediaPipe ──> Gesture Engine ──> Actions
 30fps      capture    21 landmarks    bitmask rules    pynput/pycaw
                           |                |
                           v                v
                       WebSocket ──────> React Dashboard
                       (FastAPI)         (Next.js)
```

1. OpenCV captures frames from the webcam at 30fps
2. MediaPipe detects 21 hand landmarks in 3D
3. Gesture Engine encodes finger state as a 5-bit bitmask and resolves gestures
4. Hold Manager enforces a 0.5s hold before triggering actions
5. Actions execute via pynput (media keys) and pycaw (volume)
6. Frames + gesture state stream to the React frontend via WebSocket

---

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+ with pnpm
- Webcam
- Windows (for pycaw volume control)

### Install

```bash
# Clone
git clone https://github.com/YOUR_USERNAME/gesture-ai-desk.git
cd gesture-ai-desk

# Backend
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt

# Modelo do MediaPipe (~7,8 MB, não vai no Git)
curl -L -o backend/hand_landmarker.task https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task

# Frontend
cd frontend
pnpm install
cd ..
```

### Run

**Terminal 1 - Backend:**
```bash
.venv\Scripts\python backend\ws_server.py
```

**Terminal 2 - Frontend:**
```bash
cd frontend
pnpm dev
```

Open **http://localhost:3000**

**Standalone mode** (no frontend, just OpenCV window):
```bash
.venv\Scripts\python backend\main.py
```

---

## Gestures

| Gesture | Action | Type |
|---------|--------|------|
| Open Hand | Play / Pause | Hold 0.5s |
| Fist | Mute / Unmute | Hold 0.5s |
| Peace (V) | Next Track | Hold 0.5s |
| Point | Screenshot | Hold 0.5s |
| Thumb Up | Volume +5% | Hold 0.5s |
| Thumb Down | Volume -5% | Hold 0.5s |
| Hang Loose | Pause / Resume detection | Hold 0.5s |
| Pinch (vertical) | Volume control | Continuous |
| Pinch (horizontal) | Filter intensity | Continuous |
| Swipe Left/Right | Cycle filters | Instant |

---

## Tech Stack

**Backend (Python)**
- OpenCV - camera capture and visual filters
- MediaPipe - hand landmark detection (21 points, 3D)
- FastAPI + uvicorn - WebSocket server
- pynput - media key simulation
- pycaw - Windows volume control (COM API)
- NumPy - geometric calculations

**Frontend (React)**
- Next.js 16 - React framework
- TypeScript - type safety
- Tailwind CSS - styling
- WebSocket API - real-time communication

---

## Project Structure

```
gesture-ai-desk/
+-- backend/
|   +-- main.py              # Standalone mode (cv2 window)
|   +-- ws_server.py          # WebSocket server (FastAPI)
|   +-- capture.py            # Camera capture wrapper
|   +-- hand_tracker.py       # MediaPipe hand landmarker
|   +-- gesture_engine.py     # Gesture detection (bitmask + stabilizer)
|   +-- hold_manager.py       # Hold timer + cooldown
|   +-- actions.py            # System actions (pynput, pycaw)
|   +-- filters.py            # Visual filters (OpenCV)
|   +-- config.py             # Configuration dataclass
|   +-- utils.py              # Geometric helpers
|   +-- hand_landmarker.task  # MediaPipe model file
+-- frontend/
|   +-- src/
|       +-- app/page.tsx       # Main dashboard layout
|       +-- components/        # CameraFeed, GestureHUD, etc.
|       +-- hooks/             # useWebSocket
|       +-- lib/types.ts       # TypeScript interfaces
+-- requirements.txt
+-- GESTURE_AI_DESK_PRD.md     # Full product spec
+-- README.md
```

---

## Roadmap (Phase 2)

- [ ] Object scanner (YOLOv8 / MobileNet)
- [ ] Presenter mode (slide control + virtual laser)
- [ ] Usage profiles (streamer, productivity, custom)
- [ ] Left hand support
- [ ] Auto-calibration of thresholds
- [ ] Gesture analytics dashboard
- [ ] System tray icon

See the full [Product Requirements Document](GESTURE_AI_DESK_PRD.md) for details.

---

## License

MIT
