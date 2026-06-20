import asyncio
import json
import logging
from typing import Any

import websockets

from config import load_config
from main import do_transform
from twitter import post_tweet
from ycm import search_cars

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger("server")

# 暂存待确认的推文，key 是 group_id，value 是推文内容
# 原理：用户发 /发推 时先存在这里，等 /确认发推 再真正发出去
pending_tweets: dict[int, str] = {}


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

    # ── /发车 命令（原有逻辑不变）──────────────────────────
    if text.startswith("/发车"):
        car_text = text.removeprefix("/发车").strip()
        try:
            result_text = do_transform(car_text)
        except Exception:
            logger.exception("处理 /发车 消息失败")
            result_text = "❌ 消息处理失败，请检查输入格式后重试"
        await websocket.send(build_group_message(group_id, result_text))
        return

    # ── /发推 命令：预览推文，等待确认 ────────────────────
    if text.startswith("/发推"):
        tweet_text = text.removeprefix("/发推").strip()

        if not tweet_text:
            reply = "❌ 请在 /发推 后面写上推文内容\n例如：/发推 今天天气真好"
            await websocket.send(build_group_message(group_id, reply))
            return

        if len(tweet_text) > 280:
            reply = f"❌ 推文内容超过280字符（当前 {len(tweet_text)} 字符），请缩短后重试"
            await websocket.send(build_group_message(group_id, reply))
            return

        # 把推文内容暂存起来，等用户确认
        pending_tweets[group_id] = tweet_text

        reply = (
            f"📝 准备发送以下推文：\n"
            f"───────────────\n"
            f"{tweet_text}\n"
            f"───────────────\n"
            f"发送 /确认发推 确认发送\n"
            f"发送 /取消发推 取消"
        )
        await websocket.send(build_group_message(group_id, reply))
        return

    # ── /确认发推 命令：真正发推 ───────────────────────────
    if text.strip() == "/确认发推":
        if group_id not in pending_tweets:
            reply = "❌ 没有待发送的推文，请先使用 /发推 命令"
            await websocket.send(build_group_message(group_id, reply))
            return

        tweet_text = pending_tweets.pop(group_id)  # 取出并删除暂存

        try:
            url = post_tweet(tweet_text)
            reply = f"✅ 推文发送成功！\n{url}"
        except Exception:
            logger.exception("发推失败")
            reply = "❌ 发推失败，请检查 API Key 或网络连接"

        await websocket.send(build_group_message(group_id, reply))
        return

    # ── /ycm 命令：搜索发车推文 ───────────────────────────
    if text.startswith("/ycm"):
        filter_word = text.removeprefix("/ycm").strip()
        await websocket.send(build_group_message(group_id, "🔍 搜索中，请稍候..."))
        try:
            result = search_cars(filter_word)
        except Exception:
            logger.exception("ycm 搜索失败")
            result = "❌ 搜索失败，请稍后重试"
        await websocket.send(build_group_message(group_id, result))
        return

    # ── /取消发推 命令 ─────────────────────────────────────
    if text.strip() == "/取消发推":
        if group_id in pending_tweets:
            pending_tweets.pop(group_id)
            reply = "🚫 已取消发推"
        else:
            reply = "❌ 没有待取消的推文"
        await websocket.send(build_group_message(group_id, reply))
        return


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