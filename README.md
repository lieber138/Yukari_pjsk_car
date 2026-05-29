# PJSK 发车 QQ 机器人

这是一个给 NapCat 反向 WebSocket 直连的 QQ 群发车转换服务。

最推荐的使用方式是：

```text
NapCat 反向 WebSocket -> ws://frp-bus.com:30041/ws -> server.py
``
只要在自己的 NapCat 里新增一个反向 WebSocket，连接到你提供的 WebSocket 地址即可。


下面的不用管！
ーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーー

## 每个文件是干什么的

如果你是新手，可以先记住一句话：**平时启动主要用 `run_all.py`，真正处理 NapCat 消息的是 `server.py`，文本转换规则在 `main.py`。**

| 文件 | 新手理解 | 什么时候会用到 |
| --- | --- | --- |
| `main.py` | 发车文本转换器 | 只想测试“输入中文发车内容会变成什么日文”时用 |
| `server.py` | 机器人主服务 | NapCat 反向 WebSocket 实际连接的服务 |
| `run_all.py` | 一键启动器 | 平时推荐运行它：`python run_all.py` |
| `config.json` | 配置文件 | 改端口、监听地址、是否启用旧 bridge 模式时改它 |
| `config.py` | 读取配置的工具 | 一般不用手动运行，也不建议新手改 |
| `bridge.py` | 旧版桥接器 | 默认不用；只有想走 `NapCat -> bridge.py -> server.py` 才用 |
| `README.md` | 使用说明书 | 忘了怎么部署、怎么填地址时看它 |

### `main.py`：转换规则

`main.py` 没丢，也不是被替代了。它仍然是整个项目的“文案生成核心”。

它里面放的是“怎么把中文发车内容变成日文募集文案”的规则。比如：

- `DICTIONARY`：把 `虾`、`龙`、`omks`、`mv车` 这类关键词换成日文/符号。
- `MODE_RULES`：把 `清火`、`消火`、`长途`、`高速` 换成日文模式。
- `do_transform(text)`：真正执行转换的函数，`server.py` 收到 `/发车` 后会调用它。

也就是说：

```text
NapCat -> server.py -> main.py 的 do_transform() -> server.py -> NapCat -> QQ 群
```

如果你以后想改“输出文案长什么样”“关键词怎么识别”“随机句子有哪些”，主要就是改 `main.py`。

如果你只想测试转换效果，可以运行：

```bash
python main.py
```

这个模式不需要 NapCat，也不会真的发 QQ 消息，只会在终端里打印转换结果。

### `server.py`：真正给 NapCat 连的服务

`server.py` 是现在最重要的文件。它会启动一个 WebSocket 服务，默认端口是 `8765`。NapCat 的反向 WebSocket 就是连接它。

它负责：

1. 接收 NapCat 发来的群消息。
2. 判断消息是不是以 `/发车` 开头。
3. 调用 `main.py` 里的转换逻辑。
4. 把转换结果通过 `send_group_msg` 发回群里。

### `run_all.py`：一键启动

你平时不用记很多命令，直接运行：

```bash
python run_all.py
```

现在默认情况下，它只会帮你启动 `server.py`。所以对你来说，可以把它理解成“启动机器人服务”的按钮。

### `config.json`：你可能会改的配置

这个文件是给新手最可能需要改的地方。比如：

- `server.port`：服务端口，默认 `8765`。
- `server.host`：监听地址，默认 `0.0.0.0`，表示允许其他设备连接。
- `runner.start_bridge`：默认 `false`，表示不启动旧版 `bridge.py`。

如果你只是 Termux 本机测试，一般不用改。

### `config.py`：帮程序读取配置

`config.py` 是程序内部用的工具文件，用来读取 `config.json`，并在你漏填配置时补默认值。

新手通常不用打开它，也不需要运行它。

### `bridge.py`：旧版桥接模式，默认不用

现在推荐 NapCat 直接连 `server.py`，所以一般不需要 `bridge.py`。

所谓“两段式结构”，就是 NapCat 不直接连最终处理消息的 `server.py`，中间多放一个 `bridge.py` 当“转发员”：

```text
NapCat -> bridge.py -> server.py
```

可以把它理解成：

1. NapCat 先把 QQ 消息交给 `bridge.py`。
2. `bridge.py` 再把 `/发车` 后面的文字转交给 `server.py`。
3. `server.py` 生成日文文案后交回 `bridge.py`。
4. `bridge.py` 再让 NapCat 发回群里。

但你现在不需要这么绕。你现在的目标是“一段式直连”：

```text
NapCat -> server.py
```

也就是 NapCat 直接把消息发给 `server.py`，`server.py` 自己处理并回复群消息。这样文件更少、配置更简单，更适合你现在用 Termux 跑服务。

所以 `bridge.py` 可以先不用管。

## 现在的架构

默认直连链路是：

```text
QQ 群 -> NapCat -> server.py -> NapCat -> QQ 群
```

各文件作用：

- `server.py`：主服务。直接接收 NapCat 反向 WebSocket 事件，识别群里的 `/发车`，转换后通过同一条 WebSocket 发 `send_group_msg` 动作回群。
- `main.py`：纯文本转换逻辑。
- `config.py` / `config.json`：配置监听地址、端口和运行参数。
- `run_all.py`：本机启动器。默认只启动 `server.py`，适合“NapCat 反向 WebSocket 直接连 `server.py`”的模式。
- `bridge.py`：兼容旧的桥接模式，通常不需要使用。

## 给别人用：对方不下载代码怎么接入

如果你已经在一台服务器上运行了本项目，对方只需要配置自己的 NapCat。

假设你给别人的地址是：

```text
ws://你的服务器IP:8765
```

对方在 NapCat 里新增/启用 **反向 WebSocket**，地址填写：

```text
ws://你的服务器IP:8765
```

如果 NapCat 和你的服务跑在同一台机器上，就可以填：

```text
ws://127.0.0.1:8765
```

连接成功后，对方在 QQ 群里发送：

```text
/发车 12345 q2 清火 150 主120
```

机器人就会自动回复转换后的日文募集文案。

> 注意：如果你要给别人远程连接，不应该让别人填 `ws://127.0.0.1:8765`，因为 `127.0.0.1` 永远表示“对方自己的电脑”。远程用户应该填你的公网 IP、域名或内网可访问地址，例如 `ws://example.com:8765` 或 `ws://192.168.1.10:8765`。

## 你现在用 Termux：按这个步骤来

你现在在手机 Termux 上跑服务的话，可以先按“手机就是服务器”理解。

### 1. 在 Termux 安装环境

在 Termux 里依次运行：

```bash
pkg update
pkg install python git
python -m pip install --upgrade pip
pip install websockets
```

如果你是从 GitHub 拉代码，继续运行：

```bash
git clone 你的仓库地址
cd Yukari_pjsk_car
python run_all.py
```

如果你已经把文件放进 Termux 了，就进入项目目录后直接运行：

```bash
python run_all.py
```

看到服务启动后，Termux 这个窗口不要关，手机也尽量不要锁屏杀后台。

### 2. NapCat 地址怎么填

看 NapCat 跑在哪里：

| NapCat 在哪里 | NapCat 反向 WebSocket 填什么 |
| --- | --- |
| NapCat 和 Termux 在同一台手机 | `ws://127.0.0.1:8765` |
| NapCat 在同一个 Wi-Fi 里的电脑上，服务在手机 Termux | `ws://手机局域网IP:8765` |
| 别人从互联网连接你的手机 Termux | 不推荐直接这样做，建议用云服务器或内网穿透 |

如果 NapCat 在电脑上，而服务跑在手机 Termux，需要先查手机的局域网 IP。可以在 Termux 里运行：

```bash
ip -4 addr show wlan0
```

找到类似下面这一段：

```text
inet 192.168.1.23/24
```

那电脑上的 NapCat 反向 WebSocket 就填：

```text
ws://192.168.1.23:8765
```

注意：手机和电脑必须在同一个 Wi-Fi/局域网里。手机网络环境变化后，这个 IP 可能会变。

### 3. 以后迁移到电脑

迁移到电脑时不用改核心代码，思路一样：

1. 在电脑安装 Python。
2. 把项目文件复制/克隆到电脑。
3. 在项目目录运行 `pip install websockets`。
4. 运行 `python run_all.py`。
5. 如果 NapCat 也在这台电脑，反向 WebSocket 填 `ws://127.0.0.1:8765`。

## 你自己部署服务端

### 1. 安装依赖

项目需要 Python 3.10+，并安装 `websockets`：

```bash
pip install websockets
```

### 2. 配置监听地址

编辑 `config.json`：

```json
{
  "server": {
    "host": "0.0.0.0",
    "port": 8765
  },
  "bridge": {
    "napcat_ws_url": "ws://localhost:3001",
    "server_ws_url": "ws://localhost:8765",
    "reconnect_initial_delay": 1,
    "reconnect_max_delay": 30,
    "car_response_timeout": 30
  },
  "runner": {
    "start_bridge": false,
    "startup_delay": 2,
    "health_check_interval": 2,
    "shutdown_timeout": 5
  }
}
```

关键配置：

| 配置项 | 推荐值 | 说明 |
| --- | --- | --- |
| `server.host` | `0.0.0.0` | 允许其他机器的 NapCat 连接进来 |
| `server.port` | `8765` | NapCat 反向 WebSocket 要连接的端口 |
| `runner.start_bridge` | `false` | 默认不启动旧版 `bridge.py`，因为 NapCat 可以直接连 `server.py` |

如果只允许本机 NapCat 使用，可以把 `server.host` 改成 `127.0.0.1`。

如果要让别人远程连接，需要：

1. `server.host` 使用 `0.0.0.0`。
2. 云服务器安全组/防火墙放行 `server.port`，默认 `8765`。
3. 把你的公网 IP、域名或内网 IP 发给对方，例如 `ws://你的服务器IP:8765`。

### 3. 启动

推荐运行：

```bash
python run_all.py
```

当前默认配置下，`run_all.py` 只会启动 `server.py`，不会启动 `bridge.py`。

也可以直接运行：

```bash
python server.py
```

启动后，NapCat 反向 WebSocket 填：

```text
ws://127.0.0.1:8765
```

如果 NapCat 在另一台机器，填服务端实际地址，例如：

```text
ws://192.168.1.10:8765
```

## QQ 群里怎么发

### 基本命令

```text
/发车 12345 q2 清火 150 主120
```

### 可识别内容

| 信息 | 示例 | 作用 |
| --- | --- | --- |
| 房间号 | `12345` | 识别 5 位数字作为房间号 |
| 缺几人 | `q1`、`q2`、`q3`、`q4` | 转成募集人数 `@1` 到 `@4` |
| 模式 | `清火`、`消火`、`长途`、`高速` | 转成对应日文模式 |
| 募集加成 | `150` | 转成 `募:150%↑` |
| 房主加成 | `主120`、`房主120`、`车头120` | 转成 `主:120%` |
| 支援 | `支援`、`推`、`实效` | 增加支援说明 |
| 指定时间 | `10:30`、`十点半` | 转成截止时间 |
| 指定次数 | `3把`、`十回` | 转成周回次数 |
| 歌曲/关键词 | `虾`、`龙`、`omks`、`mv车` | 转成预设日文关键词 |

### 示例

```text
/发车 54321 q1 长途 支援 160 十点半 虾
```

```text
/发车 67890 q3 高速 3把 omks
```

## 旧版 bridge.py 模式

一般不需要 `bridge.py`。

“两段式结构”指中间多一层 `bridge.py` 转发消息：

```text
NapCat -> bridge.py -> server.py
```

和现在推荐的“一段式直连”对比：

```text
NapCat -> server.py
```

两段式更绕，适合以后你想把“连接 NapCat 的程序”和“转换文本的程序”拆到不同位置时再研究。新手和 Termux 当前用法建议保持一段式直连。

只有在你不想让 NapCat 直接连 `server.py`，而是明确需要中间加 `bridge.py` 时，才需要启用 `bridge.py`。

启用方式是在 `config.json` 里设置：

```json
"runner": {
  "start_bridge": true
}
```

然后运行：

```bash
python run_all.py
```

这时 `run_all.py` 会先启动 `server.py`，再启动 `bridge.py`。

## 开发调试转换逻辑

如果只想调试文本转换，不需要启动 NapCat：

```bash
python main.py
```

然后在终端输入发车内容，查看转换结果。

## 排查问题

如果 NapCat 连接后没有回复，按这个顺序检查：

1. `server.py` 或 `python run_all.py` 是否正在运行。
2. NapCat 反向 WebSocket 地址是否填对。
3. 如果是远程连接，端口 `8765` 是否已在防火墙/安全组放行。
4. 群消息是否以 `/发车` 开头。
5. 服务端日志是否显示收到连接或异常。

## 停止服务

如果使用 `run_all.py` 启动，按：

```text
Ctrl+C
```

如果直接运行 `server.py`，同样按 `Ctrl+C` 停止。
