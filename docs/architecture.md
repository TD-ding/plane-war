# 代码架构

单文件 pygame 游戏，所有源码集中在 `plane-war.py`。设计上把渲染、状态、行为分别封装到独立的类，主循环 (`Game.run`) 串起整套流程。

## 模块图

```
┌──────────────────────────────────────────────────────┐
│                       plane-war.py                    │
│                                                       │
│  ┌─────────────┐    ┌────────────┐    ┌────────────┐ │
│  │  常量与字体  │    │  音效合成  │    │  绘制函数  │ │
│  │ WIDTH/HEIGHT │    │ snd_*       │    │ draw_*     │ │
│  │ COLORS/FONTS │    │ (struct PCM)│    │            │ │
│  └─────────────┘    └────────────┘    └────────────┘ │
│         ▲                  ▲                  ▲       │
│         └──────────────────┴──────────────────┘       │
│                            │                           │
│  ┌────────┐   ┌────────┐   │   ┌──────┐  ┌───────┐    │
│  │ Player │   │ Enemy  │   │   │ Boss │  │PowerUp│    │
│  └────────┘   └────────┘   │   └──────┘  └───────┘    │
│         ▲          ▲       │       ▲          ▲       │
│         └──────────┴───────┴───────┴──────────┘       │
│                            │                           │
│                       ┌────┴─────┐                     │
│                       │   Game   │ ◀── 主循环         │
│                       └──────────┘                     │
└──────────────────────────────────────────────────────┘
```

## 核心类

### `Player`（玩家战机）

- 状态：位置、速度、子弹列表、命数、炸弹数、火力等级、无敌帧、射击冷却
- 关键方法：
  - `update(keys)`：根据按键移动 + 边界 clip + 冷却倒计时
  - `shoot()`：按 `power` 等级生成 1/2/3 路子弹，命名元组 `PlayerBullet`
  - `update_bullets()`：子弹位移 + 出屏过滤
  - `hitbox()`：返回 `pygame.Rect`，由碰撞检测使用

### `Enemy`（普通敌机）

- 三种类型 `kind=0/1/2`，对应小/中/大型机，血量、分值、尺寸、速度、出弹频率不同
- `update()` 自动左右晃动（`sway`），到边界反弹；`kind >= 1` 才会射击
- 子弹使用 `EnemyBullet` 命名元组，含位置 + 速度向量

### `Boss`

- 进场动画 (`entering=True`) 后切换到巡逻 + 弹幕模式
- 三种弹幕模式 (`pattern=0/1/2`) 由 `pattern_timer` 自动切换
- `hit(damage)` 返回 `True` 表示被击败，触发掉落 3 个不同道具

### `PowerUp`

- 三种 `kind`：`power` / `life` / `bomb`
- 自上而下匀速下落，玩家碰到则触发对应效果

### `Starfield`

- 背景星空，80 颗星按各自速度向下移动，出屏后回到顶部并随机 x

### `Game`（控制器）

聚合所有子系统：

- 状态机：`menu` → `playing` → `gameover`
- 难度配置由 `reset(diff_key)` 应用到 Player 和后续敌机/Boss 生成参数
- 子系统：连击 (`combo` / `combo_multiplier`)、屏幕震动 (`shake_timer`)、爆炸/命中闪光/分数飘字三组特效列表
- 主循环 `run()`：事件处理 → 更新 → 碰撞检测 → 绘制 → `pygame.display.flip()`

## 关键数据结构

```python
PlayerBullet = namedtuple("PlayerBullet", ["x", "y", "dx"])
EnemyBullet  = namedtuple("EnemyBullet",  ["x", "y", "dx", "dy"])
```

子弹用 namedtuple 不用 dict / class：内存紧凑、不可变、批处理时只需用列表推导式过滤即可。

```python
DIFFICULTY_SETTINGS = {
    "easy":   {...},
    "normal": {...},
    "hard":   {...},
}
```

每档配置成员见 `docs/gameplay.md` 的难度表。

## 主循环执行顺序

每帧（FPS=60）依次：

1. `pygame.event.get()` 处理输入事件（按键、退出）
2. 当前状态分支：
   - `menu`: 绘制菜单界面，等待 Enter
   - `playing`:
     1. `Player.update(keys)`：移动 + 冷却
     2. `spawn_wave()`：按时间和难度系数生成敌机
     3. `check_boss_spawn()`：到时刷 Boss
     4. 各单位 `update()`：敌机移动+射击、Boss 移动+弹幕、道具下落
     5. `check_collisions()`：玩家子弹 vs 敌机/Boss、敌弹 vs 玩家、玩家 vs 道具
     6. `update_effects()`：爆炸帧、命中闪光、分数飘字、屏幕震动
     7. 全部 `draw_*()` + HUD
   - `gameover`: 结算面板
3. `clock.tick(FPS)` 锁帧

## 音效合成

为了零外部资源，所有音效都用 `struct.pack` 生成 PCM 数据，再 `pygame.mixer.Sound(buffer=...)` 播放：

- `_gen_shoot_sound`：方波 + 衰减
- `_gen_explosion_sound`：噪声 + 衰减
- `_gen_hit_sound`：短促正弦
- `_gen_pickup_sound`：上扬正弦
- `_gen_bomb_sound`：低频噪声 + 长衰减
- `_gen_boss_alert_sound`：交替正弦警报

## 文件结构

```
plane-war/
├── plane-war.py               # 唯一源文件（944 行）
├── tests/
│   ├── conftest.py            # 配置 SDL dummy 驱动 + 模块加载 fixture
│   └── test_game_logic.py     # 25 个核心逻辑单元测试
├── requirements.txt           # 运行依赖
├── requirements-dev.txt       # 开发 + 测试依赖
├── .flake8                    # lint 配置
├── Dockerfile                 # python:3.12-slim + SDL 库
├── docker-compose.yml         # test / dev / play 三种服务
├── .env.example               # 环境变量示例
├── .github/workflows/ci.yml   # GitHub Actions CI
├── docs/
│   ├── deployment.md          # 部署 + 运行说明
│   ├── gameplay.md            # 玩法说明
│   └── architecture.md        # 本文档
├── README.md                  # 快速上手
└── collab-log.md              # 协作开发迭代记录
```

## 测试策略

`tests/conftest.py` 提供 `game_module` fixture：

1. 在 import pygame 前设置 `SDL_VIDEODRIVER=dummy` / `SDL_AUDIODRIVER=dummy`
2. 用 `importlib.util` 按文件路径加载 `plane-war.py`（因为文件名含连字符不能直接 import）
3. fixture scope=session，整个测试会话只加载一次

测试覆盖纯逻辑（不依赖渲染）：连击倍率、道具掉落判断、Boss 受击、Player 火力分支、难度配置完整性。这些是迭代过程中最容易引入回归的部分。
