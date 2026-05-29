# bridge.py
import asyncio
import websockets
import json

car_lock = asyncio.Lock()

async def handle_message(data, car_ws, qq_ws):

    text = data.get("raw_message", "")

    if not text.startswith("/发车"):
        return

    text = text.removeprefix("/发车").strip()

    # 核心：
    # 同一时间只允许一个人操作 car_ws
    async with car_lock:

        await car_ws.send(text)

        result = await car_ws.recv()

    response = {
        "action": "send_group_msg",
        "params": {
            "group_id": data["group_id"],
            "message": result
        }
    }

    await qq_ws.send(json.dumps(response))


async def bridge():

    async with websockets.connect("ws://localhost:3001") as qq_ws:

        async with websockets.connect("ws://localhost:8765") as car_ws:

            print("🔗 桥梁已打通：NapCat <-> Server")

            async for message in qq_ws:

                try:
                    data = json.loads(message)

                    if data.get("post_type") != "message":
                        continue

                    if data.get("message_type") != "group":
                        continue

                    # 后台协程
                    asyncio.create_task(
                        handle_message(data, car_ws, qq_ws)
                    )

                except Exception as e:
                    print("❌ bridge错误:", e)


if __name__ == "__main__":
    asyncio.run(bridge())