import asyncio
import websockets

clients = set()

async def handler(websocket):
    clients.add(websocket)
    print("Yeni client baglandi")

    try:
        async for message in websocket:
            print("Gelen msg:", message)

            # tum clientlara gonder
            for client in clients:
                if client != websocket:
                    await client.send(message)

    except:
        print("Client ayrildi")

    finally:
        clients.remove(websocket)

async def main():
    async with websockets.serve(handler, "0.0.0.0", 2086):
        print("Server basladi: ws://localhost:1883")
        await asyncio.Future()  # sonsuz calis

asyncio.run(main())