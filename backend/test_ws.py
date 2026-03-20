"""Quick test client — connects to the WebSocket server and prints 5 frames."""

import asyncio
import json

import websockets


async def main() -> None:
    async with websockets.connect("ws://localhost:8765/ws") as ws:
        for i in range(5):
            msg = json.loads(await ws.recv())
            gesture = msg["gesture"]["name"]
            hand = msg["hand_detected"]
            filt = msg["active_filter"]
            frame_kb = len(msg["frame"]) // 1024
            print(f"Frame {i + 1}: gesture={gesture}, hand={hand}, filter={filt}, frame~{frame_kb}KB")
    print("OK — WebSocket server is working!")


if __name__ == "__main__":
    asyncio.run(main())
