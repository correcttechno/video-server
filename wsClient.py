import asyncio
import websockets

URI = "ws://video.correcttechno.com:2086"

async def connect():
    reconnect_delay = 1
    max_delay = 10

    while True:
        try:
            print("Baglanmaya calisiliyor...")

            async with websockets.connect(URI) as websocket:
                print("Servere baglandi")

                reconnect_delay = 1  # reset

                async def send():
                    while False:  # ister acarsin
                        msg = input("Mesaj yaz: ")
                        await websocket.send("Python: " + msg)

                async def receive():
                    while True:
                        msg = await websocket.recv()
                        print("Gelen:", msg)

                await asyncio.gather(send(), receive())

        except Exception as e:
            print("Baglanti koptu:", e)

        # reconnect bekleme
        print(f"{reconnect_delay} saniye sonra tekrar denenecek...")
        await asyncio.sleep(reconnect_delay)

        # exponential backoff
        reconnect_delay = min(reconnect_delay * 2, max_delay)


asyncio.run(connect())