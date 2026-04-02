import asyncio
import cv2
import requests
from aiortc import RTCPeerConnection, VideoStreamTrack, RTCSessionDescription
from av import VideoFrame

class CameraStreamTrack(VideoStreamTrack):
    def __init__(self):
        super().__init__()
        self.cap = cv2.VideoCapture(0)

    async def recv(self):
        pts, time_base = await self.next_timestamp()
        ret, frame = self.cap.read()
        if not ret:
            frame = np.zeros((480,640,3), dtype=np.uint8)
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        video_frame = VideoFrame.from_ndarray(frame_rgb, format="rgb24")
        video_frame.pts = pts
        video_frame.time_base = time_base
        return video_frame

async def main():
    pc = RTCPeerConnection()
    pc.addTrack(CameraStreamTrack())

    offer = await pc.createOffer()
    await pc.setLocalDescription(offer)

    response = requests.post(
        "http://127.0.0.1:8080/offer", 
        json={"sdp": pc.localDescription.sdp, "type": pc.localDescription.type}
    )
    answer = response.json()
    await pc.setRemoteDescription(RTCSessionDescription(sdp=answer["sdp"], type=answer["type"]))

    await asyncio.sleep(3600)

asyncio.run(main())