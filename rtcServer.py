import asyncio
from aiohttp import web
from aiortc import RTCPeerConnection, RTCSessionDescription
from aiortc.contrib.media import MediaRelay
import cv2

pcs = set()
relay = MediaRelay()
latest_frame = None


# ================= MJPEG STREAM =================
async def mjpeg(request):
    global latest_frame

    response = web.StreamResponse(
        status=200,
        reason='OK',
        headers={'Content-Type': 'multipart/x-mixed-replace; boundary=frame'}
    )
    await response.prepare(request)

    try:
        while True:
            if latest_frame is not None:
                ret, jpeg = cv2.imencode('.jpg', latest_frame)
                frame = jpeg.tobytes()

                await response.write(b"--frame\r\n")
                await response.write(
                    b"Content-Type: image/jpeg\r\n\r\n" + frame + b"\r\n"
                )

            await asyncio.sleep(0.03)

    except (asyncio.CancelledError, ConnectionResetError, BrokenPipeError):
        print("MJPEG client disconnected (normal)")

    except Exception as e:
        print("MJPEG unknown error:", e)

    finally:
        try:
            await response.write_eof()
        except:
            pass

    return response


# ================= HTML =================
async def index(request):
    with open("templates/index.html", "r", encoding="utf-8") as f:
        html = f.read()
    return web.Response(content_type="text/html", text=html)


async def test(request):
    with open("templates/test.html", "r", encoding="utf-8") as f:
        html = f.read()
    return web.Response(content_type="text/html", text=html)


# ================= WEBRTC =================
async def offer(request):
    global latest_frame

    # 🔥 eski bağlantıları temizle
    for pc in pcs:
        await pc.close()
    pcs.clear()

    latest_frame = None

    params = await request.json()
    pc = RTCPeerConnection()
    pcs.add(pc)

    @pc.on("connectionstatechange")
    async def on_connectionstatechange():
        print("State:", pc.connectionState)
        if pc.connectionState in ["failed", "closed", "disconnected"]:
            await pc.close()
            pcs.discard(pc)

    @pc.on("track")
    def on_track(track):
        global latest_frame

        print("Track geldi:", track.kind)

        if track.kind == "video":
            local_video = relay.subscribe(track)

            async def update_frame():
                global latest_frame
                try:
                    while True:
                        frame = await local_video.recv()
                        latest_frame = frame.to_ndarray(format="bgr24")
                except Exception as e:
                    print("Frame loop stopped:", e)

            asyncio.create_task(update_frame())

    offer = RTCSessionDescription(sdp=params["sdp"], type=params["type"])
    await pc.setRemoteDescription(offer)

    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)

    return web.json_response({
        "sdp": pc.localDescription.sdp,
        "type": pc.localDescription.type
    })


# ================= APP =================
app = web.Application()
app.router.add_get("/", index)
app.router.add_get("/mjpeg", mjpeg)
app.router.add_post("/offer", offer)
app.router.add_get("/test", test)

web.run_app(app, host="0.0.0.0", port=8080)