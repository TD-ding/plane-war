# Plane War

一个基于 Python pygame 的飞机大战游戏。

## 功能

- 3 种敌机类型（小型/中型/大型），随难度递增
- Boss 战系统：定时出现，3 种弹幕模式（扇形/瞄准/环形）
- 连击系统：连续击杀积累倍率（1.0x → 2.5x），超时归零
- 炸弹清屏：按 B 键清除所有敌机，对 Boss 造成伤害
- 3 档难度选择（简单/普通/困难），影响血量、火力、Boss 属性
- 道具系统：火力升级（P）、生命补给（+）、炸弹补给（B）
- 分数弹出文字动画
- 命中特效 + 屏幕震动
- 6 种程序化音效（射击、爆炸、命中、拾取、炸弹、Boss 警报）
- Boss 出场 WARNING 闪烁 + 炸弹白屏闪光
- 星空滚动背景
- 方向键 / WASD 移动，空格射击，P 暂停，ESC 菜单

## 运行

```bash
pip install -r requirements.txt
python plane-war.py
```

或使用 Docker：

```bash
docker compose up test          # 跑 lint + 单元测试
docker compose run --rm play    # X11 转发实际玩游戏（仅 Linux 桌面）
```

## 文档

- [部署与运行](docs/deployment.md) — 安装、环境变量、Docker、CI、故障排查
- [玩法说明](docs/gameplay.md) — 操作、难度、单位、连击、道具
- [代码架构](docs/architecture.md) — 类设计、主循环、数据结构、测试策略

## 测试

```bash
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python -m pytest tests/ -v
python -m flake8 plane-war.py tests/
```

25 个单元测试覆盖玩家火力、敌机血量、Boss 受击、连击倍率、难度配置等核心逻辑。

## 开发过程

本项目通过模拟真实协作开发流程完成，共经历 5 轮迭代：

| 轮次 | 类型 | 改动 |
|------|------|------|
| 第1轮 | feat | 初始版本 - pygame 飞机大战游戏 |
| 第2轮 | refactor | 代码质量优化 |
| 第3轮 | feat | 用户体验优化（命中特效、屏幕震动、音效） |
| 第4轮 | feat | 连击系统、Boss战、炸弹清屏、难度选择 |
| 第5轮 | fix | Boss崩溃修复、弹幕方向修复、最大连击显示、死代码清理 |
