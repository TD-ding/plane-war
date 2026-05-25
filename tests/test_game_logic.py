"""飞机大战 - 核心游戏逻辑单元测试。

覆盖：
- 难度配置完整性
- Player 初始化、子弹发射、火力档位
- Enemy 初始化和血量
- Boss 受击与击败
- Game 连击倍率、加分、计分
- PowerUp 拾取掉落
"""


def test_difficulty_settings_have_three_levels(game_module):
    # 三档难度都必须存在，主菜单依赖这个键集
    cfgs = game_module.DIFFICULTY_SETTINGS
    assert set(cfgs.keys()) == {"easy", "normal", "hard"}


def test_difficulty_settings_required_fields(game_module):
    # 每档难度都必须包含 Game.reset() 用到的字段，缺一会在切换难度时崩溃
    required = {
        "label", "lives", "bombs", "enemy_hp_mult",
        "enemy_shoot_mult", "boss_hp", "boss_shoot_rate",
        "boss_score", "combo_decay", "color",
    }
    for key, cfg in game_module.DIFFICULTY_SETTINGS.items():
        missing = required - set(cfg.keys())
        assert not missing, f"{key} 难度缺少字段: {missing}"


def test_difficulty_progression(game_module):
    # 难度递增：简单 lives 应当多于困难 lives，简单 boss_hp 应当少于困难
    cfgs = game_module.DIFFICULTY_SETTINGS
    assert cfgs["easy"]["lives"] >= cfgs["normal"]["lives"] >= cfgs["hard"]["lives"]
    assert cfgs["easy"]["boss_hp"] <= cfgs["hard"]["boss_hp"]


# ── Player ────────────────────────────────────────────────────────
def test_player_initial_state(game_module):
    p = game_module.Player(lives=5, bombs=3)
    assert p.lives == 5
    assert p.bombs == 3
    assert p.power == 1
    assert p.bullets == []
    assert p.shoot_cd == 0


def test_player_shoot_single_bullet_on_power1(game_module):
    p = game_module.Player()
    assert p.power == 1
    p.shoot()
    # 1 级火力发射 1 颗直射子弹
    assert len(p.bullets) == 1


def test_player_shoot_dual_bullets_on_power2(game_module):
    p = game_module.Player()
    p.power = 2
    p.shoot()
    # 2 级火力发射 2 颗子弹
    assert len(p.bullets) == 2


def test_player_shoot_three_way_on_power3(game_module):
    p = game_module.Player()
    p.power = 3
    p.shoot()
    # 3 级火力为三路散射
    assert len(p.bullets) == 3
    # 中间一颗向上直射，左右两颗水平偏移分布
    xs = sorted(b.x for b in p.bullets)
    assert xs[0] < xs[1] <= xs[2]


def test_player_shoot_respects_cooldown(game_module):
    # 冷却中再调用 shoot 不应增加子弹数
    p = game_module.Player()
    p.shoot()
    initial = len(p.bullets)
    p.shoot()  # 冷却期内
    assert len(p.bullets) == initial


def test_player_bullets_move_upward(game_module):
    p = game_module.Player()
    p.shoot()
    initial_y = p.bullets[0].y
    p.update_bullets()
    # 子弹必须向上飞（y 减小）
    assert p.bullets[0].y < initial_y


# ── Enemy ─────────────────────────────────────────────────────────
def test_enemy_kinds_have_distinct_hp(game_module):
    # 不同种类敌机血量阶梯递增
    e0 = game_module.Enemy(kind=0, hp_mult=1.0)
    e1 = game_module.Enemy(kind=1, hp_mult=1.0)
    e2 = game_module.Enemy(kind=2, hp_mult=1.0)
    assert e0.hp < e1.hp < e2.hp


def test_enemy_hp_multiplier_applied(game_module):
    # 难度血量倍率应当生效
    base = game_module.Enemy(kind=2, hp_mult=1.0).hp
    weak = game_module.Enemy(kind=2, hp_mult=0.5).hp
    strong = game_module.Enemy(kind=2, hp_mult=2.0).hp
    assert weak < base < strong


def test_enemy_score_progression(game_module):
    # 高级敌机分数更高
    scores = [game_module.Enemy(kind=k).score for k in range(3)]
    assert scores == sorted(scores)


# ── Boss ──────────────────────────────────────────────────────────
def test_boss_hit_reduces_hp(game_module):
    boss = game_module.Boss(hp=10)
    defeated = boss.hit(damage=3)
    assert boss.hp == 7
    assert defeated is False


def test_boss_hit_returns_true_when_defeated(game_module):
    boss = game_module.Boss(hp=2)
    defeated = boss.hit(damage=5)
    # hp 跌到 0 以下，返回 True 表示被击败
    assert boss.hp <= 0
    assert defeated is True


def test_boss_flash_timer_set_on_hit(game_module):
    # 命中后应触发闪光帧，给玩家反馈
    boss = game_module.Boss(hp=10)
    assert boss.flash_timer == 0
    boss.hit()
    assert boss.flash_timer > 0


# ── Game / 连击系统 ───────────────────────────────────────────────
def test_game_initial_state(game_module):
    g = game_module.Game()
    # 新建游戏默认进入菜单，得分为 0，无连击
    assert g.state == "menu"
    assert g.score == 0
    assert g.combo == 0
    assert g.kills == 0


def test_combo_multiplier_thresholds(game_module):
    g = game_module.Game()
    # 连击倍率档位：< 5 = 1.0， 5~9 = 1.25， 10~19 = 1.5， 20~29 = 2.0， 30+ = 2.5
    g.combo = 0
    assert g.combo_multiplier() == 1.0
    g.combo = 4
    assert g.combo_multiplier() == 1.0
    g.combo = 5
    assert g.combo_multiplier() == 1.25
    g.combo = 10
    assert g.combo_multiplier() == 1.5
    g.combo = 20
    assert g.combo_multiplier() == 2.0
    g.combo = 30
    assert g.combo_multiplier() == 2.5


def test_add_kill_increments_combo_and_score(game_module):
    g = game_module.Game()
    g.add_kill(100, x=240, y=300, h=10)
    assert g.combo == 1
    assert g.kills == 1
    # 1 连击倍率为 1.0，得分应为基础分
    assert g.score == 100


def test_add_kill_applies_multiplier(game_module):
    g = game_module.Game()
    # 把连击调到刚好触发 1.5 倍档（10），下一击应该按 1.5 倍计算
    g.combo = 9
    g.add_kill(200, x=100, y=100)
    # 第 10 击触发 1.5x
    assert g.combo == 10
    assert g.score == int(200 * 1.5)


def test_max_combo_tracks_peak(game_module):
    g = game_module.Game()
    for _ in range(7):
        g.add_kill(100, x=0, y=0)
    assert g.max_combo == 7
    # 重置连击不应清掉历史最大值
    g.combo = 0
    g.add_kill(100, x=0, y=0)
    assert g.max_combo == 7


def test_reset_clears_score_and_state(game_module):
    g = game_module.Game()
    g.score = 5000
    g.combo = 15
    g.kills = 30
    g.reset()
    assert g.score == 0
    assert g.combo == 0
    assert g.kills == 0


def test_reset_with_difficulty_changes_lives(game_module):
    # 切换难度应应用对应 lives / bombs
    g = game_module.Game()
    g.reset("hard")
    hard_lives = g.player.lives
    g.reset("easy")
    assert g.player.lives >= hard_lives


# ── PowerUp ───────────────────────────────────────────────────────
def test_powerup_kinds(game_module):
    # 三种道具：火力（power）、生命（life）、炸弹（bomb）
    for kind in ("power", "life", "bomb"):
        p = game_module.PowerUp(100, 100, kind=kind)
        assert p.kind == kind


def test_powerup_falls_down(game_module):
    p = game_module.PowerUp(100, 100)
    initial_y = p.y
    p.update()
    # 道具应当从上往下掉落
    assert p.y > initial_y


def test_powerup_offscreen_detection(game_module):
    p = game_module.PowerUp(100, 100)
    assert p.offscreen() is False
    p.y = game_module.HEIGHT + 50
    assert p.offscreen() is True
