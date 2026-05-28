import subprocess
import sys
import time

def run_services():
    # 只需要拉起你写的那两个核心 Python 进程
    # 使用 sys.executable 确保调用的是你当前 Termux 环境的 Python
    services = [
        [sys.executable, "server.py"], 
        [sys.executable, "bridge.py"]
    ]
    
    processes = []
    print("🚀 正在启动 PJSK 核心发车服务...")
    
    try:
        for cmd in services:
            # 以后台进程方式启动
            p = subprocess.Popen(cmd)
            processes.append(p)
            print(f"✅ 已拉起进程: {cmd[1]}")
            time.sleep(1) # 给 server.py 一点启动时间，确保它先守住 8765 端口
            
        print("\n✨ 服务已就绪！NapCat 正在运行中。")
        print("💡 桥梁已打通，现在可以直接在群里发送 /发车 指令。")
        print("🛑 按 Ctrl+C 即可一键停止这两个进程。")
        
        # 保持此脚本运行，等待你手动关闭
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n🛑 正在关闭服务...")
        for p in processes:
            p.terminate()
        print("✅ 服务已安全关闭。")

if __name__ == "__main__":
    run_services()