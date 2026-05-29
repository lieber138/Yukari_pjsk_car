# bridge.py
import asyncio
import json
import logging

import websockets

from config import load_config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger("bridge")

car_lock = asyncio.Lock()


async def send_group_message(qq_ws, group_id, message):
    response = {
        "action": "send_group_msg",
        "params": {
            "group_id": group_id,
            "message": message,
        },
    }
    await qq_ws.send(json.dumps(response, ensure_ascii=False))


async def handle_message(data, car_ws, qq_ws, response_timeout):
    group_id = data.get("group_id")
    text = data.get("raw_message", "")

    if not isinstance(text, str):
        logger.warning("raw_message 不是字符串，已跳过：%r", text)
        return

    if not text.startswith("/发车"):
        return

    if group_id is None:
        logger.warning("收到 /发车 消息但缺少 group_id，已跳过：%r", data)
        return

    text = text.removeprefix("/发车").strip()

    try:
        # 核心：同一时间只允许一个人操作 car_ws，避免并发 recv 串包。
        async with car_lock:
            await car_ws.send(text)
            result = await asyncio.wait_for(car_ws.recv(), timeout=response_timeout)

        await send_group_message(qq_ws, group_id, result)
    except asyncio.TimeoutError:
        logger.warning("Server 响应超时，已通知群 %s", group_id)
        await send_group_message(qq_ws, group_id, "❌ 发车服务响应超时，请稍后重试")
    except websockets.ConnectionClosed:
        logger.warning("处理消息时 WebSocket 连接已断开")
    except Exception:
        logger.exception("处理 /发车 消息失败")
        try:
            await send_group_message(qq_ws, group_id, "❌ 发车服务处理失败，请稍后重试")
        except Exception:
            logger.exception("发送错误提示到群 %s 失败", group_id)


async def consume_messages(qq_ws, car_ws, response_timeout):
    pending_tasks = set()

    try:
        async for message in qq_ws:
            try:
                data = json.loads(message)
            except json.JSONDecodeError:
                logger.warning("收到无法解析的 JSON，已跳过：%r", message)
                continue
            except Exception:
                logger.exception("解析 NapCat 消息失败，已跳过")
                continue

            try:
                if data.get("post_type") != "message":
                    continue

                if data.get("message_type") != "group":
                    continue

                task = asyncio.create_task(
                    handle_message(data, car_ws, qq_ws, response_timeout)
                )
                pending_tasks.add(task)
                task.add_done_callback(pending_tasks.discard)
            except Exception:
                logger.exception("分发 NapCat 消息失败，已跳过")
    finally:
        if pending_tasks:
            logger.info("连接关闭，取消 %s 个未完成任务", len(pending_tasks))
            for task in pending_tasks:
                task.cancel()
            await asyncio.gather(*pending_tasks, return_exceptions=True)


async def bridge():
    reconnect_initial_delay = 1.0
    reconnect_max_delay = 30.0
    reconnect_delay = reconnect_initial_delay

    while True:
        try:
            config = load_config()
            bridge_config = config["bridge"]
            napcat_ws_url = bridge_config["napcat_ws_url"]
            server_ws_url = bridge_config["server_ws_url"]
            response_timeout = float(bridge_config["car_response_timeout"])
            reconnect_initial_delay = float(bridge_config["reconnect_initial_delay"])
            reconnect_max_delay = float(bridge_config["reconnect_max_delay"])
            reconnect_delay = max(reconnect_delay, reconnect_initial_delay)

            logger.info("正在连接 NapCat：%s", napcat_ws_url)
            async with websockets.connect(napcat_ws_url) as qq_ws:
                logger.info("正在连接 Server：%s", server_ws_url)
                async with websockets.connect(server_ws_url) as car_ws:
                    logger.info("🔗 桥梁已打通：NapCat <-> Server")
                    reconnect_delay = reconnect_initial_delay
                    await consume_messages(qq_ws, car_ws, response_timeout)
        except KeyboardInterrupt:
            logger.info("收到退出信号，桥梁关闭")
            raise
        except (OSError, asyncio.TimeoutError, websockets.ConnectionClosed) as exc:
            logger.warning("WebSocket 连接中断：%s", exc)
        except Exception:
            logger.exception("bridge 运行异常，将尝试重连")

        logger.info("%.1f 秒后尝试重连", reconnect_delay)
        await asyncio.sleep(reconnect_delay)
        reconnect_delay = min(reconnect_delay * 2, reconnect_max_delay)


if __name__ == "__main__":
    try:
        asyncio.run(bridge())
    except KeyboardInterrupt:
        logger.info("bridge 已退出")
