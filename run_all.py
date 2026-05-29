from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from config import load_config

ROOT_DIR = Path(__file__).resolve().parent
PROCESSES: list[tuple[str, subprocess.Popen[bytes]]] = []


def _get_runner_config(config: dict[str, Any]) -> dict[str, Any]:
    return config.get("runner", {})


def start_process(name: str, script_name: str) -> subprocess.Popen[bytes]:
    script_path = ROOT_DIR / script_name
    print(f"🚀 启动 {name}: {script_path.name}...")

    process = subprocess.Popen(
        [sys.executable, str(script_path)],
        cwd=ROOT_DIR,
        stdout=sys.stdout,
        stderr=sys.stderr,
    )

    PROCESSES.append((name, process))
    print(f"✅ {name} 已启动 PID={process.pid}")

    return process


def stop_all(shutdown_timeout: float) -> None:
    print("\n🛑 正在关闭所有服务...")

    for name, process in PROCESSES:
        if process.poll() is not None:
            print(f"ℹ️ {name} 已退出，退出码={process.returncode}")
            continue

        try:
            print(f"🔻 关闭 {name}")
            process.terminate()
            process.wait(timeout=shutdown_timeout)
        except subprocess.TimeoutExpired:
            print(f"⚠️ {name} 在 {shutdown_timeout:.1f} 秒内未退出，强制结束")
            process.kill()
            process.wait(timeout=shutdown_timeout)

    print("✅ 所有服务已关闭")


def check_processes() -> bool:
    for name, process in PROCESSES:
        return_code = process.poll()
        if return_code is not None:
            print(f"❌ {name} 已退出，退出码={return_code}")
            return False

    return True


def main() -> None:
    config = load_config()
    server_config = config["server"]
    bridge_config = config["bridge"]
    runner_config = _get_runner_config(config)

    start_bridge = bool(runner_config.get("start_bridge", False))
    startup_delay = float(runner_config.get("startup_delay", 2))
    health_check_interval = float(runner_config.get("health_check_interval", 2))
    shutdown_timeout = float(runner_config.get("shutdown_timeout", 5))

    try:
        print("📋 当前配置:")
        print(f"   Server 监听: {server_config['host']}:{server_config['port']}")
        print(f"   NapCat 反向 WebSocket 地址: ws://127.0.0.1:{server_config['port']}")
        if start_bridge:
            print(f"   Bridge 模式 NapCat 地址: {bridge_config['napcat_ws_url']}")
            print(f"   Bridge 模式 Server 地址: {bridge_config['server_ws_url']}")

        start_process("server", "server.py")

        if start_bridge:
            print(f"⏳ 等待 {startup_delay:.1f} 秒，确保 server 启动完成...")
            time.sleep(startup_delay)
            start_process("bridge", "bridge.py")
        else:
            print("ℹ️ 当前为 NapCat 反向 WebSocket 直连模式，不启动 bridge.py")

        print("\n✨ PJSK 发车系统已启动")
        print(f"🔌 请在 NapCat 反向 WebSocket 中连接 ws://127.0.0.1:{server_config['port']}")
        print("💬 连接后可以在群里发送 /发车")
        print("🛑 Ctrl+C 关闭服务\n")

        while True:
            if not check_processes():
                print("⚠️ 检测到子进程退出，将关闭其余服务")
                break

            time.sleep(health_check_interval)

    except KeyboardInterrupt:
        print("\n⌨️ 收到 Ctrl+C")
    finally:
        stop_all(shutdown_timeout)


if __name__ == "__main__":
    main()
