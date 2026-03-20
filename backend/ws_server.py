"""FastAPI WebSocket server — streams frames + gesture state to the frontend."""

from __future__ import annotations

import asyncio
import base64
import json
import logging
import time
from contextlib import asynccontextmanager
from typing import Any

import cv2
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

import actions
import filters
from capture import CameraCapture
from config import Config
from gesture_engine import Gesture, GestureDetector
from hand_tracker import HandTracker
from hold_manager import HoldManager

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger(__name__)

# Gesture → action mapping
_ACTION_MAP: dict[Gesture, Any] = {
    Gesture.PALM: actions.toggle_play_pause,
    Gesture.FIST: actions.toggle_mute,
    Gesture.PEACE: actions.next_track,
    Gesture.POINT: actions.take_screenshot,
    Gesture.THUMB_UP: actions.volume_up,
    Gesture.THUMB_DOWN: actions.volume_down,
}

# Gesture enum → protocol name (PRD 3.2)
_GESTURE_NAMES: dict[Gesture, str] = {
    Gesture.NONE: "none",
    Gesture.FIST: "fist",
    Gesture.PALM: "open_hand",
    Gesture.PEACE: "peace",
    Gesture.POINT: "point",
    Gesture.THUMB_UP: "thumb_up",
    Gesture.THUMB_DOWN: "thumb_down",
    Gesture.HANG_LOOSE: "hang_loose",
    Gesture.PINCH: "pinch",
    Gesture.SWIPE_LEFT: "swipe_left",
    Gesture.SWIPE_RIGHT: "swipe_right",
}


# ---------------------------------------------------------------------------
# GestureServer — owns all backend components
# ---------------------------------------------------------------------------

class GestureServer:
    """Encapsulates camera, tracker, gesture engine, actions, and filters."""

    def __init__(self) -> None:
        self.config = Config()
        self.camera = CameraCapture(self.config)
        self.tracker = HandTracker(self.config)
        self.detector = GestureDetector()
        self.hold = HoldManager()

        self.filter_index: int = 0
        self.filter_intensity: float = 1.0
        self.detection_paused: bool = False

    def process_frame(self) -> dict[str, Any] | None:
        """Capture one frame, run the full pipeline, return a JSON-ready dict."""
        frame = self.camera.read_frame()
        if frame is None:
            return None

        now = time.monotonic()
        result = self.tracker.process(frame)

        gesture = Gesture.NONE
        hold_info = {"hold_progress": 0.0, "action_triggered": False, "in_cooldown": False}
        landmarks_list: list[list[float]] = []

        if result is not None:
            landmarks_list = [[lm.x, lm.y, lm.z] for lm in result.landmarks]

            if not self.detection_paused:
                gesture = self.detector.detect_gesture(result.landmarks)
                hold_info = self.hold.update(gesture, now)

                # -- execute actions --
                if gesture == Gesture.PINCH:
                    ps = self.detector.pinch_state
                    if ps["axis"] == "volume":
                        new_vol = max(0.0, min(1.0, actions.get_volume() + ps["value"] * 0.01))
                        actions.set_volume(new_vol)
                    elif ps["axis"] == "filter_intensity":
                        self.filter_intensity = max(0.1, min(1.0, self.filter_intensity + ps["value"] * 0.01))
                elif gesture == Gesture.SWIPE_RIGHT:
                    self.filter_index = filters.next_filter(self.filter_index)
                elif gesture == Gesture.SWIPE_LEFT:
                    self.filter_index = filters.prev_filter(self.filter_index)
                elif gesture == Gesture.HANG_LOOSE and hold_info["action_triggered"]:
                    self.detection_paused = True
                elif hold_info["action_triggered"] and gesture in _ACTION_MAP:
                    _ACTION_MAP[gesture]()
            else:
                gesture = self.detector.detect_gesture(result.landmarks)
                hold_info = self.hold.update(gesture, now)
                if gesture == Gesture.HANG_LOOSE and hold_info["action_triggered"]:
                    self.detection_paused = False

        # Apply visual filter
        frame = filters.apply_filter(frame, filters.FILTER_LIST[self.filter_index], self.filter_intensity)

        # Encode frame: resize to 640x480 + JPEG quality 75 + base64
        small = cv2.resize(frame, (640, 480))
        _, buf = cv2.imencode(".jpg", small, [cv2.IMWRITE_JPEG_QUALITY, 75])
        frame_b64 = base64.b64encode(buf.tobytes()).decode("ascii")

        return {
            "frame": frame_b64,
            "timestamp": time.time(),
            "hand_detected": result is not None,
            "gesture": {
                "name": _GESTURE_NAMES.get(gesture, "none"),
                "confidence": 1.0,
                "hold_progress": hold_info["hold_progress"],
                "action_triggered": hold_info["action_triggered"],
            },
            "pinch": {
                "active": self.detector.pinch_state["active"],
                "type": self.detector.pinch_state["axis"],
                "value": self.detector.pinch_state["value"],
            },
            "active_filter": filters.FILTER_LIST[self.filter_index],
            "landmarks": landmarks_list,
        }

    def update_config(self, payload: dict[str, Any]) -> None:
        """Apply runtime config changes from the frontend."""
        if "hold_duration" in payload:
            self.hold.hold_duration = float(payload["hold_duration"])
        if "cooldown" in payload:
            self.hold.cooldown = float(payload["cooldown"])

    def release(self) -> None:
        """Release hardware resources."""
        self.camera.release()


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------

server: GestureServer | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Open camera on startup, release on shutdown."""
    global server
    server = GestureServer()
    log.info("GestureServer started — camera open")
    yield
    server.release()
    log.info("GestureServer stopped — camera released")


app = FastAPI(title="Gesture AI Desk", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    """Stream gesture data to a single frontend client."""
    await websocket.accept()
    log.info("WebSocket client connected")

    # Background task: listen for config commands from the frontend
    async def receive_commands() -> None:
        try:
            while True:
                raw = await websocket.receive_text()
                msg = json.loads(raw)
                if msg.get("command") == "update_config":
                    server.update_config(msg.get("payload", {}))
                    log.info("Config updated: %s", msg["payload"])
        except WebSocketDisconnect:
            pass
        except json.JSONDecodeError:
            log.warning("Received invalid JSON from client")

    receiver = asyncio.create_task(receive_commands())

    try:
        while True:
            payload = await asyncio.to_thread(server.process_frame)
            if payload is not None:
                await websocket.send_json(payload)
            await asyncio.sleep(1 / server.config.target_fps)
    except WebSocketDisconnect:
        log.info("WebSocket client disconnected")
    finally:
        receiver.cancel()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8765)
