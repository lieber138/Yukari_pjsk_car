import asyncio
import json
import logging
from typing import Any

import websockets

from config import load_config
from main import do_transform

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger("server")


def build_group_message(group_id: int | str, message: str) -> str:
    response = {
        "action": "send_group_msg",
        "params": {
            "group_id": group_id,
            "message": message,
        },
    }
    return json.dumps(response, ensure_ascii=False)


def parse_napcat_event(raw_message: str) -> dict[str, Any] | None:
    try:
        event = json.loads(raw_message)
    except json.JSONDecodeError:
        return None

    if not isinstance(event, dict):
        logger.warning("收到非对象 JSON，已跳过：%r", event)
        return None

    return event


async def handle_plain_text_message(websocket, raw_message: str) -> None:
    result_text = do_transform(raw_message)
    await websocket.send(result_text)


async def handle_napcat_event(websocket, event: dict[str, Any]) -> None:
    if event.get("post_type") != "message":
        return

    if event.get("message_type") != "group":
        return

    group_id = event.get("group_id")
    text = event.get("raw_message", "")

    if group_id is None:
        logger.warning("收到群消息但缺少 group_id，已跳过：%r", event)
        return

    if not isinstance(text, str):
        logger.warning("raw_message 不是字符串，已跳过：%r", text)
        return

    if not text.startswith("/发车"):
        return

    car_text = text.removeprefix("/发车").strip()

    try:
        result_text = do_transform(car_text)
    except Exception:
        logger.exception("处理 /发车 消息失败，已向群 %s 返回错误提示", group_id)
        result_text = "❌ 消息处理失败，请检查输入格式后重试"

    await websocket.send(build_group_message(group_id, result_text))


async def handler(websocket, path=None):
    logger.info("📡 侦测到连接")

    try:
        async for raw_message in websocket:
            try:
                event = parse_napcat_event(raw_message)
                if event is None:
                    await handle_plain_text_message(websocket, raw_message)
                else:
                    await handle_napcat_event(websocket, event)
            except Exception:
                logger.exception("处理消息失败，已跳过本条消息")
                try:
                    await websocket.send("❌ 消息处理失败，请检查输入格式后重试")
                except Exception:
                    logger.exception("发送错误提示失败")
    except websockets.ConnectionClosed:
        logger.info("客户端连接已断开")
    except Exception:
        logger.exception("WebSocket 连接处理异常")


async def main():
    config = load_config()
    server_config = config["server"]
    host = server_config["host"]
    port = int(server_config["port"])

    async with websockets.serve(handler, host, port):
        logger.info("🚀 服务端已启动：ws://%s:%s", host, port)
        logger.info("NapCat 反向 WebSocket 可直接连接此地址")
        await asyncio.Future()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("收到退出信号，服务端关闭")
    except Exception:
        logger.exception("服务端启动失败")
        raise
