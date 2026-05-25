# 部署与运行说明

## 系统要求

- Python 3.10+（推荐 3.12）
- 操作系统：Windows / macOS / Linux 均可
- 显示器或者 X11 转发（无头服务器仅可运行测试，不能玩游戏）

## 本地运行

### 1. 安装依赖

```bash
# 仅运行游戏
pip install -r requirements.txt

# 含开发与测试工具
pip install -r requirements-dev.txt
```

主要依赖：

| 包 | 用途 |
|----|------|
| pygame >= 2.5.0 | 图形渲染、输入、音频 |
| flake8 >= 6.0.0 | 代码 lint（开发） |
| pytest >= 7.0.0 | 单元测试（开发） |

### 2. 启动游戏

```bash
python plane-war.py
```

中文字体：游戏会按顺序尝试 `simhei`、`microsoftyahei`、`notosanscjksc`、`wenquanyimicrohei`、`arial`。Linux 环境如缺少中文字体，可安装：

```bash
# Ubuntu / Debian
sudo apt-get install fonts-wqy-microhei

# Fedora / RHEL
sudo dnf install wqy-microhei-fonts
```

## 环境变量

复制示例文件后修改：

```bash
cp .env.example .env
```

| 变量 | 默认 | 说明 |
|------|------|------|
| `SDL_VIDEODRIVER` | `dummy` | SDL 视频驱动。无显示器环境（CI、容器测试）使用 `dummy`；桌面运行游戏建议清空或用 `x11`/`cocoa`/`windows` |
| `SDL_AUDIODRIVER` | `dummy` | SDL 音频驱动。无声卡用 `dummy`；Linux 桌面用 `pulse` 或 `alsa` |
| `DISPLAY` | `:0` | X11 显示号，仅 Linux 桌面/容器需要 |
| `PYTHONUNBUFFERED` | `1` | 关闭 Python 输出缓冲，方便容器日志 |

> 直接在桌面运行 `python plane-war.py` 时不需要设置任何变量，pygame 会自动选择合适的驱动。

## Docker 运行

仓库提供 `Dockerfile` 与 `docker-compose.yml`，含三种服务：

```bash
# 1. 单元测试 + lint（默认服务，CI 也跑这个）
docker compose up test

# 2. 进入容器交互调试
docker compose run --rm dev

# 3. 在 Linux 桌面通过 X11 转发实际玩游戏
xhost +local:docker
DISPLAY=$DISPLAY docker compose run --rm play
```

镜像基于 `python:3.12-slim`，安装了 SDL2 系列原生库（`libsdl2-2.0-0`、`libsdl2-mixer-2.0-0` 等）和文泉驿微米黑中文字体。容器以非 root 用户 `app` 运行，并配置了 HEALTHCHECK 验证游戏模块可正常导入。

## 测试

### 运行单元测试

```bash
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python -m pytest tests/ -v
```

`tests/conftest.py` 会自动设置 dummy 驱动并通过 `importlib` 加载 `plane-war.py`（文件名含连字符无法直接 import）。

测试覆盖：

- 三档难度配置完整性与递进关系
- Player 子弹发射 / 火力档位 / 冷却 / 子弹移动
- Enemy 三种类型血量梯度 / 难度倍率 / 分值
- Boss 受击 / 击败检测 / 闪光帧
- Game 连击倍率 / 加分 / 计分 / reset
- PowerUp 三种类型 / 掉落 / 出屏检测

### 运行 lint

```bash
python -m flake8 plane-war.py tests/
```

零错误为通过标准。

## CI

GitHub Actions 工作流位于 `.github/workflows/ci.yml`，每次 push 到 `master` 或对 `master` 提交 PR 时自动触发：

1. 安装 Python 3.12 + SDL 系统库
2. 安装 pip 依赖（带缓存）
3. flake8 lint
4. pytest 测试
5. 健康检查：通过 importlib 加载游戏模块
6. 构建 Docker 镜像并在容器内重新跑 lint + 测试（烟测）

## 故障排查

| 现象 | 原因 | 解决 |
|------|------|------|
| `pygame.error: No available video device` | 无显示器或 X11 未连接 | 设置 `SDL_VIDEODRIVER=dummy`（仅测试用）或开启 X11 转发 |
| 中文显示成方块 | 系统缺中文字体 | 安装 `fonts-wqy-microhei` 或类似中文字体 |
| Docker 容器内播放游戏黑屏 | DISPLAY 未传递 / xhost 未授权 | 执行 `xhost +local:docker`，确认 `DISPLAY` 环境变量 |
| 无声 | 容器或服务器无声卡 | 设置 `SDL_AUDIODRIVER=dummy`，正常现象 |
