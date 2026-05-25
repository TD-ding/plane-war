# ── 飞机大战 Dockerfile ──────────────────────────────────────────
# 提供两种使用方式：
# 1) 单元测试 + lint 运行环境（默认 CMD）
# 2) 通过 X11 转发实际运行游戏（需要在宿主机配置 DISPLAY，详见 docs/deployment.md）
FROM python:3.12-slim

# pygame 需要 SDL 相关原生库，即便用 dummy 驱动也要保留
# libSDL2 / libSDL2-mixer / libSDL2-image / libSDL2-ttf
RUN apt-get update && apt-get install -y --no-install-recommends \
        libsdl2-2.0-0 \
        libsdl2-mixer-2.0-0 \
        libsdl2-image-2.0-0 \
        libsdl2-ttf-2.0-0 \
        libfreetype6 \
        libportmidi0 \
        fonts-wqy-microhei \
    && rm -rf /var/lib/apt/lists/*

# 创建非 root 用户，避免容器以 root 运行
RUN useradd --create-home --shell /bin/bash app
WORKDIR /app

# 先复制依赖文件，利用 Docker 层缓存加速重复构建
COPY --chown=app:app requirements.txt requirements-dev.txt ./
RUN pip install --no-cache-dir -r requirements-dev.txt

# 再复制源码
COPY --chown=app:app . .

USER app

# 默认使用 dummy 驱动以便在无显示器环境（CI/容器）也可正常导入
ENV SDL_VIDEODRIVER=dummy \
    SDL_AUDIODRIVER=dummy \
    PYTHONUNBUFFERED=1

# 健康检查：尝试导入游戏模块，确保依赖完整
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import importlib.util; \
spec = importlib.util.spec_from_file_location('plane_war', 'plane-war.py'); \
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)" || exit 1

# 默认运行测试套件，证明环境可用
CMD ["python", "-m", "pytest", "tests/", "-v"]
