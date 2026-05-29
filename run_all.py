import subprocess
import sys
import time
import signal

processes = []

def start_process(name, file):
    print(f"🚀 启动 {name}...")

    p = subprocess.Popen(
        [sys.executable, file],
        stdout=sys.stdout,
        stderr=sys.stderr
    )

    processes.append((name, p))

    print(f"✅ {name} 已启动 PID={p.pid}")

    return p


def stop_all():
    print("\n🛑 正在关闭所有服务...")

    for name, p in processes:

        try:
            print(f"🔻 关闭 {name}")

            p.terminate()

            p.wait(timeout=5)

        except subprocess.TimeoutExpired:

            print(f"⚠️ 强制结束 {name}")

            p.kill()

    print("✅ 所有服务已关闭")


def check_processes():
    for name, p in processes:

        # poll() != None 代表进程已经死了
        if p.poll() is not None:

            print(f"❌ {name} 已崩溃")
            return False

    return True


def main():

    try:

        # 先启动 server
        start_process("server", "server.py")

        # 等 2 秒确保 8765 启动完成
        time.sleep(2)

        # 再启动 bridge
        start_process("bridge", "bridge.py")

        print("\n✨ PJSK 发车系统已启动")
        print("💬 现在可以在群里发送 /发车")
        print("🛑 Ctrl+C 关闭服务\n")

        while True:

            alive = check_processes()

            if not alive:
                print("⚠️ 检测到子进程崩溃")
                break

            time.sleep(2)

    except KeyboardInterrupt:

        print("\n⌨️ 收到 Ctrl+C")

    finally:

        stop_all()


if __name__ == "__main__":
    main()