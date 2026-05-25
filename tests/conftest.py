"""测试运行时使用无头 SDL 驱动，避免实际打开窗口或音频设备。

CI 和本地测试都依赖这两个环境变量，必须在 import pygame 之前设置好。
"""
import importlib.util
import os
import sys
from pathlib import Path

# 使用 dummy 视频/音频驱动，让游戏代码在无显示器环境也能正常导入
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pytest  # noqa: E402  必须在设置环境变量之后再导入


@pytest.fixture(scope="session")
def game_module():
    """加载 plane-war.py 为 Python 模块。

    文件名包含连字符，无法直接 import，所以用 importlib 按路径加载。
    """
    project_root = Path(__file__).resolve().parent.parent
    src_path = project_root / "plane-war.py"
    spec = importlib.util.spec_from_file_location("plane_war", src_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["plane_war"] = module
    spec.loader.exec_module(module)
    return module
