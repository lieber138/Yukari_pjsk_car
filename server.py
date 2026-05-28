import asyncio
import websockets
from main import do_transform

async def handler(websocket, path):
    print("📡 侦测到连接")
    async for raw_message in websocket:
        result_text = do_transform(raw_message)
        await websocket.send(result_text)

async def main():
    async with websockets.serve(handler, "0.0.0.0", 8765):
        print("🚀 服务端已启动")
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())