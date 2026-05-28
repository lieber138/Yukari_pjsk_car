# bridge.py - 极简拦截者
import asyncio
import websockets
import json

async def bridge():
    # 1. 连接你的 QQ 底层 (假设 NapCat/Lagrange 在 3001)
    async with websockets.connect("ws://localhost:3001") as qq_ws:
        # 2. 同时连接你的发车服务 (你刚才写的 server.py)
        async with websockets.connect("ws://localhost:8765") as car_ws:
            print("🔗 桥梁已打通：NapCat <-> Server")
            async for message in qq_ws:
                data = json.loads(message)
                if data.get("post_type") == "message":

                    if data.get("message_type") != "group":
                       continue

                    text = data.get("raw_message", "")
                    
                    # 拦截：如果检测到指令，直接转给 car_ws
                    if text.startswith("/发车"):

                        text = text.removeprefix("/发车").strip()

                        await car_ws.send(text) # 发给你的 8765
                        result = await car_ws.recv() # 等结果
                        
                        # 把结果直接发回 QQ，不经过任何 AI 框架
                        response = {
                            "action": "send_group_msg",
                            "params": {
                                "group_id": data["group_id"],
                                "message": result
                            }
                        }
                        await qq_ws.send(json.dumps(response))
if __name__ == "__main__":
    asyncio.run(bridge())                        