import asyncio
import cv2
import numpy as np
import requests
from aiortc import RTCPeerConnection, VideoStreamTrack, RTCSessionDescription
from av import VideoFrame

SERVER_URL = "http://video.correcttechno.com:8080/offer"

class CameraStreamTrack(VideoStreamTrack):
    def __init__(self):
        super().__init__()
        self.cap = cv2.VideoCapture(0)

    async def recv(self):
        pts, time_base = await self.next_timestamp()
        ret, frame = self.cap.read()

        if not ret:
            frame = np.zeros((480, 640, 3), dtype=np.uint8)

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        video_frame = VideoFrame.from_ndarray(frame_rgb, format="rgb24")
        video_frame.pts = pts
        video_frame.time_base = time_base
        return video_frame


async def start_connection():
    pc = RTCPeerConnection()

    @pc.on("connectionstatechange")
    async def on_state_change():
        print("Connection state:", pc.connectionState)

    pc.addTrack(CameraStreamTrack())

    offer = await pc.createOffer()
    await pc.setLocalDescription(offer)

    # HTTP ile SDP gonder
    response = requests.post(
        SERVER_URL,
        json={
            "sdp": pc.localDescription.sdp,
            "type": pc.localDescription.type
        },
        timeout=5
    )

    answer = response.json()

    await pc.setRemoteDescription(
        RTCSessionDescription(sdp=answer["sdp"], type=answer["type"])
    )

    return pc


async def main():
    reconnect_delay = 1
    max_delay = 10

    while True:
        pc = None
        try:
            print("Baglanti baslatiliyor...")

            pc = await start_connection()
            print("Video streaming basladi...")

            reconnect_delay = 1  # reset

            # baglanti yasadigi surece bekle
            while True:
                if pc.connectionState in ["failed", "closed", "disconnected"]:
                    print("Baglanti koptu!")
                    break
                await asyncio.sleep(1)

        except Exception as e:
            print("Hata:", e)

        finally:
            if pc:
                await pc.close()

        print(f"{reconnect_delay} saniye sonra tekrar denenecek...")
        await asyncio.sleep(reconnect_delay)

        reconnect_delay = min(reconnect_delay * 2, max_delay)


asyncio.run(main())