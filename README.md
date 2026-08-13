# Gesture AI Desk

Control your computer with hand gestures through a webcam. Volume, playback,
track skipping and screenshots, recognized locally on the CPU, with no video
leaving the machine.

[Case study](https://luantaraschi.dev/en/projeto-gesture.html)

![Hand landmarks tracked in real time, with the detected gesture and hold progress](docs/gesture.webp)

## Overview

MediaPipe gives you 21 landmarks per hand, per frame. Turning that into a
control surface is where the actual problems start, and they are not
computer vision problems:

A hand is never still. Landmark noise makes a classifier flicker between two
gestures several times a second, so raw per frame classification is unusable
for triggering anything.

A gesture you make on the way to another gesture is not a command. Passing
through an open palm while reaching for the keyboard should not pause your
music.

And a hand is rarely presented straight to the camera. Deciding whether a
finger is extended by comparing Y coordinates works until someone tilts their
wrist.

The pipeline below is built around those three problems.

## Architecture

```
CameraCapture (OpenCV)
     |  BGR frames
HandTracker (MediaPipe Hand Landmarker)
     |  21 landmarks
GestureDetector
     |    +-- finger states -> 5 bit mask
     |    +-- GestureStabilizer (consecutive frame agreement)
     |    +-- PinchController / PinchSmoother
     |    +-- wrist history -> swipe detection
     |  stable gesture
HoldManager (hold duration + cooldown)
     |  action_triggered
actions.py -> pycaw / pynput -> the OS
```

Two entry points share that pipeline:

- `backend/ws_server.py` is the product. FastAPI serves a WebSocket that
  streams the annotated frame as base64 JPEG plus the current gesture state,
  and receives control messages back. The panel at `frontend/index.html` is a
  single HTML file with no build step and no dependencies: it renders the
  incoming frames into an `<img>` and shows the numbers.
- `backend/main.py` runs the same pipeline against a local OpenCV window,
  which is the faster loop when working on detection itself.

## Engineering Highlights

### Gestures as a 5 bit mask

Each finger is either extended or not, so a hand pose is five bits:
`THUMB | INDEX | MID | RING | PINKY`. A fist is `0b00000`, an open palm is
`0b11111`, pointing is `0b01000`, peace is `0b01100`. The `Gesture` enum in
[`backend/gesture_engine.py`](backend/gesture_engine.py) stores those bit
patterns as its values, so classifying a pose is computing one integer and
looking it up, with no branching chain of conditions.

Poses that a mask cannot express get values above 31, outside the 5 bit
space, so they never collide with a real mask: pinch, the two swipes, and
thumbs down, which is the same mask as thumbs up and is separated by a
vertical position check.

### Finger extension that survives a rotated hand

Comparing the fingertip's Y against the knuckle's Y is the obvious test, and
it fails the moment the hand tilts.

`_is_finger_extended` uses a ratio of signed distances instead: tip to PIP
joint, divided by PIP joint to wrist. Because both distances rotate together,
their ratio does not depend on hand orientation, and a finger counts as
extended above `0.3`. The near zero denominator is guarded rather than
allowed to blow up.

The thumb needs its own rule, since it moves in a different plane from the
other four. It counts as extended when the tip is laterally far from its MCP
joint *or* clearly above it vertically. The lateral test alone works for a
thumb pointing sideways but fails on a palm facing the camera with the thumb
up, which is exactly the pose used for volume control.

### Two independent filters against accidental triggers

`GestureStabilizer` requires the same gesture across five consecutive frames
before reporting it, which absorbs landmark jitter. Until that threshold is
met it keeps returning the last stable gesture rather than `NONE`, so a single
bad frame cannot drop a pose the user is still holding.

`HoldManager` then requires the stable gesture to be held for 0.5 seconds
before firing the action, and enforces a 1 second cooldown afterwards so one
gesture cannot fire twice. Changing gesture resets the hold timer, so a pose
you pass through on the way to another never accumulates progress. Hold
progress is reported as a 0 to 1 value, which is what the panel renders as a
filling bar, so the interface can tell you a command is about to fire before
it fires.

Continuous gestures bypass the hold entirely: pinch and swipes are listed in
`_CONTINUOUS_GESTURES` and act immediately, because holding a pinch for half a
second before the volume responds would feel broken.

### Swipes from a time bounded wrist history

Swipes are motion, not pose, so they cannot come from a mask. The detector
keeps a rolling list of wrist positions with timestamps, discards anything
older than one second, and looks for enough horizontal travel inside a short
window. The history is cleared the moment a swipe fires, so a single motion
cannot register twice as it decelerates.

## Tech Stack

| Layer | Choice | Role in this project |
|---|---|---|
| Tracking | MediaPipe Hand Landmarker | 21 3D landmarks per hand |
| Vision | OpenCV | Capture, annotation, visual filters |
| Server | FastAPI, uvicorn, websockets | Frame and state stream to the panel |
| OS control | pycaw, comtypes, pynput | System volume, media keys, screenshots |
| Panel | One static HTML file | No framework, no build, no dependencies |

## Testing & Reliability

There is no automated test suite in this repository, and no CI. This is the
project's weakest point, and it is worth being specific about why it matters
here: the gesture engine is full of pure, easily testable functions.
`_is_finger_extended`, the mask to `Gesture` mapping, `HoldManager.update` and
the swipe detector all take plain numbers and timestamps and return plain
values, and `HoldManager` already takes its timestamp as a parameter rather
than calling the clock itself, which is exactly what makes it testable.

`backend/test_ws.py` and `backend/test_ws.html` exist but are manual
connection probes for the WebSocket, not automated tests.

The code is fully type annotated and `pyrightconfig.json` is checked in.

## Running Locally

Requires Python 3.10+, a webcam, and Windows for the audio control path
(`pycaw` and `comtypes` are Windows only). Everything else in the pipeline is
cross platform.

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Panel plus backend together:

```bash
npm install     # only pulls in concurrently
npm start       # WebSocket server, and the panel on http://localhost:3000
```

Detection only, in an OpenCV window:

```bash
python backend/main.py
```

## Known Limitations

- Volume control is Windows only, as described above. The other actions and
  the whole detection pipeline are not.
- Detection is single hand.
- The gesture set is fixed in code. `GESTURE_AI_DESK_PRD.md` documents the
  intended behaviour of each gesture and the thresholds behind it.
- Performance depends on the CPU, since nothing is offloaded to a GPU. That is
  the trade for the video never leaving the machine.

## License

MIT. See [`LICENSE`](LICENSE).
