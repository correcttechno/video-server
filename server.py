import asyncio
from aiohttp import web
from aiortc import RTCPeerConnection, RTCSessionDescription
from aiortc.contrib.media import MediaRelay
import cv2
import os
pcs = set()
relay = MediaRelay()
latest_frame = None  # global frame

# MJPEG stream handler
async def mjpeg(request):
    global latest_frame
    response = web.StreamResponse(
        status=200,
        reason='OK',
        headers={
            'Content-Type': 'multipart/x-mixed-replace; boundary=frame'
        }
    )
    await response.prepare(request)

    while True:
        if latest_frame is not None:
            ret, jpeg = cv2.imencode('.jpg', latest_frame)
            frame = jpeg.tobytes()
            await response.write(b"--frame\r\n")
            await response.write(b"Content-Type: image/jpeg\r\n\r\n" + frame + b"\r\n")
        await asyncio.sleep(0.03)  # ~30 fps

# Browser HTML
async def index(request):
    # HTML dosyasını oku
    file_path = os.path.join(os.path.dirname(__file__), "templates/index.html")
    with open(file_path, "r", encoding="utf-8") as f:
        html = f.read()
    return web.Response(content_type="text/html", text=html)

# WebRTC offer handler
async def offer(request):
    global latest_frame
    params = await request.json()
    pc = RTCPeerConnection()
    pcs.add(pc)

    @pc.on("track")
    def on_track(track):
        global latest_frame
        print("Track geldi:", track.kind)
        if track.kind == "video":
            local_video = relay.subscribe(track)
            async def update_frame():
                global latest_frame
                while True:
                    frame = await local_video.recv()
                    latest_frame = frame.to_ndarray(format="bgr24")
            asyncio.ensure_future(update_frame())

    offer = RTCSessionDescription(sdp=params["sdp"], type=params["type"])
    await pc.setRemoteDescription(offer)
    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)
    return web.json_response(
        {"sdp": pc.localDescription.sdp, "type": pc.localDescription.type}
    )

app = web.Application()
app.router.add_get("/", index)
app.router.add_get("/mjpeg", mjpeg)
app.router.add_post("/offer", offer)

web.run_app(app, host="0.0.0.0", port=8080)