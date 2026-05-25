import math
import struct
import random
import sys
from collections import namedtuple

import pygame
import pygame.mixer

pygame.init()
pygame.mixer.init(frequency=44100, size=-16, channels=1, buffer=512)

PlayerBullet = namedtuple("PlayerBullet", ["x", "y", "dx"])
EnemyBullet = namedtuple("EnemyBullet", ["x", "y", "dx", "dy"])

# ── 常量 ──────────────────────────────────────────────────────────
WIDTH, HEIGHT = 480, 640
FPS = 60

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 50, 50)
YELLOW = (255, 230, 50)
CYAN = (100, 220, 255)
GREEN = (50, 200, 80)
GRAY = (180, 180, 180)
ORANGE = (255, 165, 0)
PURPLE = (200, 60, 200)

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("飞机大战")
clock = pygame.time.Clock()

_FONT_NAMES = "simhei,microsoftyahei,notosanscjksc,wenquanyimicrohei,arial"
font_big = pygame.font.SysFont(_FONT_NAMES, 48)
font_mid = pygame.font.SysFont(_FONT_NAMES, 28)
font_sm = pygame.font.SysFont(_FONT_NAMES, 20)
font_float = pygame.font.SysFont(_FONT_NAMES, 18, bold=True)
font_xs = pygame.font.SysFont(_FONT_NAMES, 15)

# ── 难度配置 ──────────────────────────────────────────────────────
DIFFICULTY_SETTINGS = {
    "easy": {
        "label": "简 单",
        "lives": 5,
        "bombs": 3,
        "enemy_hp_mult": 0.7,
        "enemy_shoot_mult": 1.5,
        "boss_hp": 40,
        "boss_shoot_rate": 25,
        "boss_score": 2000,
        "combo_decay": 180,
        "color": GREEN,
    },
    "normal": {
        "label": "普 通",
        "lives": 3,
        "bombs": 2,
        "enemy_hp_mult": 1.0,
        "enemy_shoot_mult": 1.0,
        "boss_hp": 60,
        "boss_shoot_rate": 18,
        "boss_score": 3000,
        "combo_decay": 120,
        "color": YELLOW,
    },
    "hard": {
        "label": "困 难",
        "lives": 2,
        "bombs": 1,
        "enemy_hp_mult": 1.5,
        "enemy_shoot_mult": 0.6,
        "boss_hp": 90,
        "boss_shoot_rate": 12,
        "boss_score": 5000,
        "combo_decay": 90,
        "color": RED,
    },
}
DIFF_ORDER = ["easy", "normal", "hard"]


# ── 音效生成 ──────────────────────────────────────────────────────
def _make_sound(samples):
    buf = struct.pack(f"<{len(samples)}h", *samples)
    return pygame.mixer.Sound(buffer=buf)


def _gen_shoot_sound():
    sr = 44100
    dur = 0.08
    n = int(sr * dur)
    samples = []
    for i in range(n):
        t = i / sr
        freq = 1200 - 4000 * t
        amp = int(6000 * (1 - t / dur))
        samples.append(int(amp * math.sin(2 * math.pi * freq * t)))
    return _make_sound(samples)


def _gen_explosion_sound():
    sr = 44100
    dur = 0.25
    n = int(sr * dur)
    samples = []
    for i in range(n):
        t = i / sr
        amp = int(10000 * (1 - t / dur) ** 2)
        samples.append(int(amp * random.uniform(-1, 1)))
    return _make_sound(samples)


def _gen_hit_sound():
    sr = 44100
    dur = 0.04
    n = int(sr * dur)
    samples = []
    for i in range(n):
        t = i / sr
        amp = int(4000 * (1 - t / dur))
        samples.append(int(amp * math.sin(2 * math.pi * 2200 * t)))
    return _make_sound(samples)


def _gen_pickup_sound():
    sr = 44100
    dur = 0.15
    n = int(sr * dur)
    samples = []
    for i in range(n):
        t = i / sr
        freq = 600 + 1200 * (t / dur)
        amp = int(5000 * (1 - t / dur))
        samples.append(int(amp * math.sin(2 * math.pi * freq * t)))
    return _make_sound(samples)


def _gen_bomb_sound():
    sr = 44100
    dur = 0.5
    n = int(sr * dur)
    samples = []
    for i in range(n):
        t = i / sr
        freq = 100 + 50 * math.sin(2 * math.pi * 3 * t)
        amp = int(12000 * (1 - t / dur) ** 1.5)
        samples.append(int(amp * math.sin(2 * math.pi * freq * t)))
    return _make_sound(samples)


def _gen_boss_alert_sound():
    sr = 44100
    dur = 0.6
    n = int(sr * dur)
    samples = []
    for i in range(n):
        t = i / sr
        freq = 400 if int(t * 6) % 2 == 0 else 300
        amp = int(5000 * (1 - t / dur))
        samples.append(int(amp * math.sin(2 * math.pi * freq * t)))
    return _make_sound(samples)


snd_shoot = _gen_shoot_sound()
snd_explosion = _gen_explosion_sound()
snd_hit = _gen_hit_sound()
snd_pickup = _gen_pickup_sound()
snd_bomb = _gen_bomb_sound()
snd_boss_alert = _gen_boss_alert_sound()


# ── 绘制函数 ──────────────────────────────────────────────────────
def draw_player(surf, cx, cy):
    body = [(cx, cy - 20), (cx - 16, cy + 16), (cx + 16, cy + 16)]
    pygame.draw.polygon(surf, CYAN, body)
    pygame.draw.polygon(surf, WHITE, body, 2)
    lw = [(cx - 16, cy + 10), (cx - 30, cy + 22), (cx - 8, cy + 14)]
    rw = [(cx + 16, cy + 10), (cx + 30, cy + 22), (cx + 8, cy + 14)]
    pygame.draw.polygon(surf, (60, 180, 240), lw)
    pygame.draw.polygon(surf, (60, 180, 240), rw)
    flame_h = random.randint(6, 14)
    pygame.draw.polygon(surf, YELLOW,
                        [(cx - 5, cy + 16), (cx, cy + 16 + flame_h), (cx + 5, cy + 16)])


def draw_enemy(surf, cx, cy, kind):
    colors = [RED, ORANGE, PURPLE]
    sizes = [(14, 14), (22, 20), (30, 26)]
    w, h = sizes[kind]
    c = colors[kind]
    body = [(cx, cy + h), (cx - w, cy - h // 2), (cx + w, cy - h // 2)]
    pygame.draw.polygon(surf, c, body)
    pygame.draw.polygon(surf, WHITE, body, 1)
    lw = [(cx - w, cy - h // 4), (cx - w - 10, cy + 4), (cx - w // 2, cy)]
    rw = [(cx + w, cy - h // 4), (cx + w + 10, cy + 4), (cx + w // 2, cy)]
    pygame.draw.polygon(surf, c, lw)
    pygame.draw.polygon(surf, c, rw)


def draw_boss(surf, cx, cy, hp_ratio):
    body = [(cx, cy + 30), (cx - 40, cy - 10), (cx - 25, cy - 30),
            (cx + 25, cy - 30), (cx + 40, cy - 10)]
    pygame.draw.polygon(surf, (180, 40, 40), body)
    pygame.draw.polygon(surf, YELLOW, body, 2)
    lw = [(cx - 40, cy - 5), (cx - 60, cy + 15), (cx - 25, cy + 5)]
    rw = [(cx + 40, cy - 5), (cx + 60, cy + 15), (cx + 25, cy + 5)]
    pygame.draw.polygon(surf, (150, 30, 30), lw)
    pygame.draw.polygon(surf, (150, 30, 30), rw)
    pygame.draw.circle(surf, YELLOW, (cx, cy - 10), 8)
    pygame.draw.circle(surf, RED, (cx, cy - 10), 5)
    engine_offsets = [-20, -8, 8, 20]
    for ox in engine_offsets:
        fh = random.randint(8, 18)
        pygame.draw.polygon(surf, ORANGE,
                            [(cx + ox - 4, cy + 30), (cx + ox, cy + 30 + fh), (cx + ox + 4, cy + 30)])
    bar_w = 80
    pygame.draw.rect(surf, RED, (cx - bar_w // 2, cy - 45, bar_w, 6))
    pygame.draw.rect(surf, GREEN,
                     (cx - bar_w // 2, cy - 45, int(bar_w * hp_ratio), 6))
    pygame.draw.rect(surf, WHITE, (cx - bar_w // 2, cy - 45, bar_w, 6), 1)


def draw_explosion(surf, cx, cy, frame, max_frames=12):
    progress = frame / max_frames
    radius = int(10 + 30 * progress)
    color = (255, max(0, 200 - int(200 * progress)), 0)
    pygame.draw.circle(surf, color, (cx, cy), radius, 3)
    for _ in range(6):
        angle = random.uniform(0, 2 * math.pi)
        dist = radius * random.uniform(0.4, 1.0)
        px = cx + int(dist * math.cos(angle))
        py = cy + int(dist * math.sin(angle))
        pygame.draw.circle(surf, YELLOW, (px, py), random.randint(2, 5))


def draw_hit_flash(surf, x, y, frame, max_frames=6):
    progress = frame / max_frames
    radius = int(8 + 6 * progress)
    alpha = max(0, 255 - int(255 * progress))
    pygame.draw.circle(surf, (alpha, alpha, alpha), (int(x), int(y)), radius)


# ── 游戏对象 ──────────────────────────────────────────────────────
class Player:
    def __init__(self, lives=3, bombs=2):
        self.x = WIDTH // 2
        self.y = HEIGHT - 80
        self.speed = 5
        self.bullets = []
        self.shoot_cd = 0
        self.lives = lives
        self.bombs = bombs
        self.invincible = 0
        self.power = 1

    def update(self, keys):
        dx, dy = 0.0, 0.0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            dx -= 1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            dx += 1
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            dy -= 1
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            dy += 1
        length = math.hypot(dx, dy)
        if length > 0:
            dx = dx / length * self.speed
            dy = dy / length * self.speed
        self.x = max(20, min(WIDTH - 20, self.x + dx))
        self.y = max(40, min(HEIGHT - 20, self.y + dy))
        if self.shoot_cd > 0:
            self.shoot_cd -= 1
        if self.invincible > 0:
            self.invincible -= 1

    def shoot(self):
        if self.shoot_cd > 0:
            return
        self.shoot_cd = 8
        snd_shoot.play()
        if self.power >= 3:
            self.bullets.append(PlayerBullet(self.x, self.y - 20, -1))
            self.bullets.append(PlayerBullet(self.x - 12, self.y - 14, 0))
            self.bullets.append(PlayerBullet(self.x + 12, self.y - 14, 0))
        elif self.power >= 2:
            self.bullets.append(PlayerBullet(self.x - 8, self.y - 18, 0))
            self.bullets.append(PlayerBullet(self.x + 8, self.y - 18, 0))
        else:
            self.bullets.append(PlayerBullet(self.x, self.y - 20, 0))

    def update_bullets(self):
        self.bullets = [
            PlayerBullet(b.x + b.dx, b.y - 10, b.dx) for b in self.bullets if b.y - 10 > -10
        ]

    def draw(self, surf):
        if self.invincible > 0 and (self.invincible // 3) % 2 == 0:
            return
        draw_player(surf, self.x, self.y)
        for b in self.bullets:
            pygame.draw.rect(surf, YELLOW, (b.x - 2, b.y - 6, 4, 12))
            pygame.draw.rect(surf, WHITE, (b.x - 1, b.y - 6, 2, 12))

    def hitbox(self):
        return pygame.Rect(self.x - 10, self.y - 10, 20, 20)


class Enemy:
    def __init__(self, kind=0, hp_mult=1.0, shoot_mult=1.0):
        self.kind = kind
        self.hp = max(1, int([1, 3, 7][kind] * hp_mult))
        self.max_hp = self.hp
        self.score = [100, 300, 600][kind]
        w_range = [(14, 14), (22, 20), (30, 26)]
        self.w, self.h = w_range[kind]
        self.x = random.randint(self.w + 10, WIDTH - self.w - 10)
        self.y = -self.h * 2
        self.speed = [3, 2, 1.2][kind] + random.uniform(-0.3, 0.3)
        self.sway = random.uniform(-0.5, 0.5)
        self.bullets = []
        self.shoot_mult = shoot_mult
        self.shoot_timer = random.randint(30, 90)

    def update(self):
        self.y += self.speed
        self.x += self.sway
        if self.x < self.w + 5 or self.x > WIDTH - self.w - 5:
            self.sway = -self.sway
        self.shoot_timer -= 1
        if self.shoot_timer <= 0 and self.kind >= 1:
            self.shoot_timer = int(random.randint(40, 100) * self.shoot_mult)
            self.bullets.append(EnemyBullet(self.x, self.y + self.h, 0, 4))
        self.bullets = [EnemyBullet(b.x + b.dx, b.y + b.dy, b.dx, b.dy)
                        for b in self.bullets if b.y + b.dy < HEIGHT + 10]

    def draw(self, surf):
        draw_enemy(surf, self.x, self.y, self.kind)
        if self.hp < self.max_hp:
            bw = self.w * 2
            pygame.draw.rect(surf, RED, (self.x - bw // 2, self.y - self.h - 8, bw, 4))
            pygame.draw.rect(surf, GREEN,
                             (self.x - bw // 2, self.y - self.h - 8,
                              int(bw * self.hp / self.max_hp), 4))
        for b in self.bullets:
            pygame.draw.circle(surf, RED, (int(b.x), int(b.y)), 3)

    def hitbox(self):
        return pygame.Rect(self.x - self.w, self.y - self.h // 2,
                           self.w * 2, self.h + self.h // 2)

    def offscreen(self):
        return self.y > HEIGHT + 40


class Boss:
    def __init__(self, hp=60, shoot_rate=18, score=3000):
        self.x = WIDTH // 2
        self.y = -50
        self.target_y = 80
        self.hp = hp
        self.max_hp = hp
        self.score = score
        self.w, self.h = 40, 30
        self.speed = 0.8
        self.bullets = []
        self.shoot_rate = shoot_rate
        self.shoot_timer = 60
        self.pattern = 0
        self.pattern_timer = 0
        self.entering = True
        self.move_dir = 1
        self.flash_timer = 0

    def update(self):
        if self.entering:
            self.y += 1.5
            if self.y >= self.target_y:
                self.y = self.target_y
                self.entering = False
            return

        self.x += self.speed * self.move_dir
        if self.x < 60 or self.x > WIDTH - 60:
            self.move_dir *= -1

        self.shoot_timer -= 1
        self.pattern_timer += 1
        if self.pattern_timer > 180:
            self.pattern_timer = 0
            self.pattern = (self.pattern + 1) % 3

        if self.shoot_timer <= 0:
            self._shoot()
            self.shoot_timer = self.shoot_rate

        self.bullets = [EnemyBullet(b.x + b.dx, b.y + b.dy, b.dx, b.dy)
                        for b in self.bullets
                        if b.y + b.dy < HEIGHT + 10 and -20 < b.x + b.dx < WIDTH + 20]
        if self.flash_timer > 0:
            self.flash_timer -= 1

    def _shoot(self):
        speed = 3.5
        if self.pattern == 0:
            for angle_offset in [-0.3, -0.15, 0, 0.15, 0.3]:
                dx = math.sin(angle_offset) * speed
                dy = math.cos(angle_offset) * speed
                self.bullets.append(EnemyBullet(self.x, self.y + self.h, dx, dy))
        elif self.pattern == 1:
            for angle in [-0.2, -0.07, 0.07, 0.2]:
                dx = math.sin(angle) * speed
                dy = math.cos(angle) * speed
                self.bullets.append(EnemyBullet(self.x + math.sin(angle) * 30,
                                                self.y + self.h, dx, dy))
        else:
            num = 12
            for k in range(num):
                angle = 2 * math.pi * k / num + self.pattern_timer * 0.02
                dx = math.cos(angle) * speed * 0.8
                dy = math.sin(angle) * speed * 0.8
                self.bullets.append(EnemyBullet(self.x + dx * 5, self.y + self.h, dx, dy))

    def draw(self, surf):
        hp_ratio = max(0, self.hp / self.max_hp)
        draw_boss(surf, int(self.x), int(self.y), hp_ratio)
        if self.flash_timer > 0:
            s = pygame.Surface((80, 60), pygame.SRCALPHA)
            alpha = min(120, self.flash_timer * 15)
            s.fill((255, 255, 255, alpha))
            surf.blit(s, (int(self.x) - 40, int(self.y) - 30))
        for b in self.bullets:
            pygame.draw.circle(surf, ORANGE, (int(b.x), int(b.y)), 4)
            pygame.draw.circle(surf, RED, (int(b.x), int(b.y)), 2)

    def hitbox(self):
        return pygame.Rect(self.x - 40, self.y - 30, 80, 60)

    def hit(self, damage=1):
        self.hp -= damage
        self.flash_timer = 3
        return self.hp <= 0


class PowerUp:
    def __init__(self, x, y, kind="power"):
        self.x = x
        self.y = y
        self.kind = kind
        self.speed = 2
        self.timer = 0

    def update(self):
        self.y += self.speed
        self.timer += 1

    def draw(self, surf):
        if self.kind == "power":
            color, label = YELLOW, "P"
        elif self.kind == "life":
            color, label = GREEN, "+"
        else:
            color, label = ORANGE, "B"
        pygame.draw.circle(surf, color, (int(self.x), int(self.y)), 12)
        pygame.draw.circle(surf, WHITE, (int(self.x), int(self.y)), 12, 2)
        txt = font_sm.render(label, True, BLACK)
        surf.blit(txt, (self.x - txt.get_width() // 2, self.y - txt.get_height() // 2))

    def hitbox(self):
        return pygame.Rect(self.x - 12, self.y - 12, 24, 24)

    def offscreen(self):
        return self.y > HEIGHT + 20


# ── 星空背景 ──────────────────────────────────────────────────────
class Starfield:
    def __init__(self):
        self.stars = [[random.randint(0, WIDTH), random.randint(0, HEIGHT),
                       random.uniform(1, 3)] for _ in range(80)]

    def update(self):
        for s in self.stars:
            s[1] += s[2]
            if s[1] > HEIGHT:
                s[1] = 0
                s[0] = random.randint(0, WIDTH)

    def draw(self, surf):
        for s in self.stars:
            brightness = int(100 + 50 * s[2])
            pygame.draw.circle(surf, (brightness, brightness, brightness),
                               (int(s[0]), int(s[1])), 1)


# ── 主游戏类 ──────────────────────────────────────────────────────
class Game:
    def __init__(self):
        self.starfield = Starfield()
        self.state = "menu"
        self.menu_diff = 1
        self.shake_timer = 0
        self.shake_offset = (0, 0)
        self.max_combo = 0
        self.reset("normal")

    def reset(self, diff_key=None):
        if diff_key:
            self.diff_key = diff_key
        cfg = DIFFICULTY_SETTINGS[self.diff_key]
        self.player = Player(lives=cfg["lives"], bombs=cfg["bombs"])
        self.enemies = []
        self.boss = None
        self.boss_warning = 0
        self.explosions = []
        self.hit_flashes = []
        self.float_scores = []
        self.powerups = []
        self.score = 0
        self.wave_timer = 0
        self.difficulty = 1.0
        self.kills = 0
        self.combo = 0
        self.combo_timer = 0
        self.combo_decay = cfg["combo_decay"]
        self.game_time = 0
        self.next_boss_time = 1800
        self.shake_timer = 0
        self.shake_offset = (0, 0)
        self.bomb_flash = 0
        self.max_combo = 0

    def combo_multiplier(self):
        if self.combo < 5:
            return 1.0
        if self.combo < 10:
            return 1.25
        if self.combo < 20:
            return 1.5
        if self.combo < 30:
            return 2.0
        return 2.5

    def add_kill(self, base_score, x, y, h=0):
        self.combo += 1
        if self.combo > self.max_combo:
            self.max_combo = self.combo
        self.combo_timer = self.combo_decay
        mult = self.combo_multiplier()
        final_score = int(base_score * mult)
        self.score += final_score
        self.kills += 1
        label = f"+{final_score}"
        if mult > 1.0:
            label += f" x{mult:.1f}"
        self.float_scores.append([x, y - h, label, 0])

    def trigger_shake(self, intensity=4):
        self.shake_timer = 10
        self.shake_intensity = intensity

    def update_shake(self):
        if self.shake_timer > 0:
            self.shake_timer -= 1
            i = self.shake_intensity * self.shake_timer // 10
            self.shake_offset = (random.randint(-i, i), random.randint(-i, i))
        else:
            self.shake_offset = (0, 0)

    def use_bomb(self):
        if self.player.bombs <= 0:
            return
        self.player.bombs -= 1
        snd_bomb.play()
        self.bomb_flash = 20
        self.trigger_shake(10)
        for e in self.enemies:
            self.explosions.append([e.x, e.y, 0])
            self.add_kill(e.score, e.x, e.y, e.h)
        self.enemies.clear()
        if self.boss:
            for b in self.boss.bullets:
                self.explosions.append([b.x, b.y, 0])
            self.boss.bullets.clear()
            self.boss.hp -= 10
            if self.boss.hp <= 0:
                self._defeat_boss()
        self.player.bullets.clear()
        self.hit_flashes.clear()

    def _defeat_boss(self):
        self.add_kill(self.boss.score, self.boss.x, self.boss.y, 30)
        for _ in range(3):
            ox = random.randint(-40, 40)
            oy = random.randint(-20, 20)
            self.explosions.append([self.boss.x + ox, self.boss.y + oy, 0])
        snd_explosion.play()
        self.trigger_shake(12)
        self.powerups.append(PowerUp(self.boss.x - 20, self.boss.y, "bomb"))
        self.powerups.append(PowerUp(self.boss.x + 20, self.boss.y, "power"))
        self.powerups.append(PowerUp(self.boss.x, self.boss.y + 20, "life"))
        self.boss = None
        self.next_boss_time = self.game_time + random.randint(1500, 2400)

    def spawn_wave(self):
        if self.boss and not self.boss.entering:
            return
        cfg = DIFFICULTY_SETTINGS[self.diff_key]
        self.wave_timer += 1
        spawn_rate = max(20, 60 - int(self.difficulty * 3))
        if self.wave_timer % spawn_rate != 0:
            return
        r = random.random()
        if r < 0.1 and self.difficulty > 3:
            kind = 2
        elif r < 0.35:
            kind = 1
        else:
            kind = 0
        self.enemies.append(Enemy(kind, cfg["enemy_hp_mult"], cfg["enemy_shoot_mult"]))
        if self.difficulty > 2 and random.random() < 0.3:
            self.enemies.append(Enemy(0, cfg["enemy_hp_mult"], cfg["enemy_shoot_mult"]))
        self.difficulty = min(self.difficulty + 0.05, 12.0)

    def check_boss_spawn(self):
        if self.boss or self.game_time < self.next_boss_time:
            return
        cfg = DIFFICULTY_SETTINGS[self.diff_key]
        self.boss = Boss(cfg["boss_hp"], cfg["boss_shoot_rate"], cfg["boss_score"])
        self.boss_warning = 120
        snd_boss_alert.play()

    def check_collisions(self):
        dead_bullets = set()
        dead_enemies = set()

        for i, e in enumerate(self.enemies):
            for j, b in enumerate(self.player.bullets):
                if j in dead_bullets:
                    continue
                brect = pygame.Rect(b.x - 3, b.y - 6, 6, 12)
                if brect.colliderect(e.hitbox()):
                    e.hp -= 1
                    dead_bullets.add(j)
                    self.hit_flashes.append([b.x, b.y, 0])
                    snd_hit.play()
                    if e.hp <= 0:
                        self.explosions.append([e.x, e.y, 0])
                        self.add_kill(e.score, e.x, e.y, e.h)
                        snd_explosion.play()
                        self.trigger_shake(6 if e.kind == 2 else 3)
                        if random.random() < 0.12:
                            pk = random.choice(["power", "life"])
                            self.powerups.append(PowerUp(e.x, e.y, pk))
                        dead_enemies.add(i)
                    break

        if self.boss and not self.boss.entering:
            for j, b in enumerate(self.player.bullets):
                if j in dead_bullets:
                    continue
                brect = pygame.Rect(b.x - 3, b.y - 6, 6, 12)
                if brect.colliderect(self.boss.hitbox()):
                    dead_bullets.add(j)
                    self.hit_flashes.append([b.x, b.y, 0])
                    snd_hit.play()
                    if self.boss.hit():
                        self._defeat_boss()
                    break

        if dead_bullets:
            self.player.bullets = [b for j, b in enumerate(self.player.bullets)
                                   if j not in dead_bullets]
        if dead_enemies:
            self.enemies = [e for i, e in enumerate(self.enemies)
                            if i not in dead_enemies]

        if self.player.invincible <= 0:
            hit = False
            for e in self.enemies:
                remaining = []
                for b in e.bullets:
                    if hit:
                        remaining.append(b)
                        continue
                    brect = pygame.Rect(b.x - 3, b.y - 3, 6, 6)
                    if brect.colliderect(self.player.hitbox()):
                        self.player_hit()
                        hit = True
                    else:
                        remaining.append(b)
                e.bullets = remaining
                if hit:
                    break

            if not hit and self.boss:
                for k, b in enumerate(self.boss.bullets):
                    brect = pygame.Rect(b.x - 4, b.y - 4, 8, 8)
                    if brect.colliderect(self.player.hitbox()):
                        self.player_hit()
                        self.boss.bullets.pop(k)
                        hit = True
                        break

            if not hit:
                for i, e in enumerate(self.enemies):
                    if e.hitbox().colliderect(self.player.hitbox()):
                        self.player_hit()
                        self.explosions.append([e.x, e.y, 0])
                        self.enemies.pop(i)
                        break

            if not hit and self.boss:
                if self.boss.hitbox().colliderect(self.player.hitbox()):
                    self.player_hit()

        remaining_pu = []
        for p in self.powerups:
            if p.hitbox().colliderect(self.player.hitbox()):
                if p.kind == "power":
                    self.player.power = min(3, self.player.power + 1)
                elif p.kind == "life":
                    self.player.lives += 1
                elif p.kind == "bomb":
                    self.player.bombs += 1
                snd_pickup.play()
            else:
                remaining_pu.append(p)
        self.powerups = remaining_pu

    def player_hit(self):
        self.player.lives -= 1
        self.player.invincible = 90
        self.player.power = max(1, self.player.power - 1)
        self.combo = 0
        self.combo_timer = 0
        snd_explosion.play()
        self.trigger_shake(8)
        if self.player.lives <= 0:
            self.state = "gameover"

    def update_effects(self):
        self.explosions = [[x, y, f + 1] for x, y, f in self.explosions if f < 12]
        self.hit_flashes = [[x, y, f + 1] for x, y, f in self.hit_flashes if f < 6]
        new_fs = []
        for fs in self.float_scores:
            fs[1] -= 1
            fs[3] += 1
            if fs[3] < 50:
                new_fs.append(fs)
        self.float_scores = new_fs
        if self.combo_timer > 0:
            self.combo_timer -= 1
            if self.combo_timer <= 0:
                self.combo = 0
        if self.boss_warning > 0:
            self.boss_warning -= 1
        if self.bomb_flash > 0:
            self.bomb_flash -= 1
        self.update_shake()

    def draw_hud(self, surf):
        txt = font_mid.render(f"分数: {self.score}", True, WHITE)
        surf.blit(txt, (10, 10))
        for i in range(self.player.lives):
            pygame.draw.polygon(surf, RED,
                                [(15 + i * 25, 50), (10 + i * 25, 60), (20 + i * 25, 60)])
        ptxt = font_sm.render(f"火力: {'★' * self.player.power}", True, YELLOW)
        surf.blit(ptxt, (10, 68))
        for i in range(self.player.bombs):
            pygame.draw.circle(surf, ORANGE, (WIDTH - 20 - i * 28, 25), 10)
            pygame.draw.circle(surf, WHITE, (WIDTH - 20 - i * 28, 25), 10, 1)
            bt = font_xs.render("B", True, BLACK)
            surf.blit(bt, (WIDTH - 20 - i * 28 - bt.get_width() // 2,
                           25 - bt.get_height() // 2))
        if self.combo >= 2:
            mult = self.combo_multiplier()
            color = YELLOW if mult < 2.0 else ORANGE if mult < 2.5 else RED
            ct = font_sm.render(f"COMBO {self.combo}  x{mult:.1f}", True, color)
            surf.blit(ct, (WIDTH - ct.get_width() - 10, 50))
            bw = 60
            ratio = self.combo_timer / self.combo_decay if self.combo_decay > 0 else 0
            pygame.draw.rect(surf, GRAY, (WIDTH - bw - 10, 72, bw, 4))
            pygame.draw.rect(surf, color, (WIDTH - bw - 10, 72, int(bw * ratio), 4))
        cfg = DIFFICULTY_SETTINGS[self.diff_key]
        dt = font_xs.render(cfg["label"], True, cfg["color"])
        surf.blit(dt, (WIDTH - dt.get_width() - 10, 80))

    def draw_effects(self, surf):
        for x, y, f in self.hit_flashes:
            draw_hit_flash(surf, x, y, f)
        for x, y, f in self.explosions:
            draw_explosion(surf, x, y, f)
        for fx, fy, label, f in self.float_scores:
            alpha = max(0, 255 - int(255 * f / 50))
            color = (255, 255, min(255, 50 + alpha))
            txt = font_float.render(label, True, color)
            surf.blit(txt, (fx - txt.get_width() // 2, fy))
        if self.boss_warning > 0 and (self.boss_warning // 10) % 2 == 0:
            wt = font_big.render("WARNING!", True, RED)
            surf.blit(wt, (WIDTH // 2 - wt.get_width() // 2, HEIGHT // 2 - 60))
        if self.bomb_flash > 0:
            s = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            s.fill((255, 255, 255, min(180, self.bomb_flash * 12)))
            surf.blit(s, (0, 0))

    def draw_menu(self, surf):
        surf.fill(BLACK)
        self.starfield.draw(surf)
        title = font_big.render("飞机大战", True, CYAN)
        surf.blit(title, (WIDTH // 2 - title.get_width() // 2, 100))
        diff_label = font_mid.render("选择难度:", True, WHITE)
        surf.blit(diff_label, (WIDTH // 2 - diff_label.get_width() // 2, 220))
        for idx, key in enumerate(DIFF_ORDER):
            cfg = DIFFICULTY_SETTINGS[key]
            selected = idx == self.menu_diff
            c = cfg["color"] if selected else GRAY
            prefix = "▶ " if selected else "  "
            t = font_mid.render(f"{prefix}{cfg['label']}", True, c)
            surf.blit(t, (WIDTH // 2 - t.get_width() // 2, 270 + idx * 45))
        sub = font_sm.render("按 SPACE 开始", True, WHITE)
        surf.blit(sub, (WIDTH // 2 - sub.get_width() // 2, 420))
        controls = [
            "方向键 / WASD - 移动   空格 - 射击",
            "B - 炸弹清屏   P - 暂停   ESC - 菜单",
        ]
        for i, line in enumerate(controls):
            t = font_xs.render(line, True, GRAY)
            surf.blit(t, (WIDTH // 2 - t.get_width() // 2, 470 + i * 22))
        draw_player(surf, WIDTH // 2, 560)

    def draw_gameover(self, surf):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        surf.blit(overlay, (0, 0))
        go = font_big.render("游戏结束", True, RED)
        surf.blit(go, (WIDTH // 2 - go.get_width() // 2, 180))
        sc = font_mid.render(f"最终分数: {self.score}", True, WHITE)
        surf.blit(sc, (WIDTH // 2 - sc.get_width() // 2, 260))
        kl = font_mid.render(f"击杀数: {self.kills}", True, YELLOW)
        surf.blit(kl, (WIDTH // 2 - kl.get_width() // 2, 300))
        mc = font_sm.render(f"最大连击: {self.max_combo}", True, ORANGE)
        surf.blit(mc, (WIDTH // 2 - mc.get_width() // 2, 340))
        rs = font_mid.render("按 R 重新开始", True, WHITE)
        surf.blit(rs, (WIDTH // 2 - rs.get_width() // 2, 400))
        ms = font_sm.render("按 ESC 返回菜单", True, GRAY)
        surf.blit(ms, (WIDTH // 2 - ms.get_width() // 2, 445))

    def run(self):
        running = True
        paused = False

        while running:
            clock.tick(FPS)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.KEYDOWN:
                    if self.state == "menu":
                        if event.key == pygame.K_UP or event.key == pygame.K_w:
                            self.menu_diff = (self.menu_diff - 1) % 3
                        elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
                            self.menu_diff = (self.menu_diff + 1) % 3
                        elif event.key == pygame.K_SPACE:
                            self.reset(DIFF_ORDER[self.menu_diff])
                            self.state = "playing"
                    elif self.state == "playing":
                        if event.key == pygame.K_p:
                            paused = not paused
                        if event.key == pygame.K_ESCAPE:
                            self.state = "menu"
                        if event.key == pygame.K_b and not paused:
                            self.use_bomb()
                    elif self.state == "gameover":
                        if event.key == pygame.K_r:
                            self.reset()
                            self.state = "playing"
                        if event.key == pygame.K_ESCAPE:
                            self.state = "menu"

            screen.fill(BLACK)
            self.starfield.update()

            if self.state == "menu":
                self.draw_menu(screen)
            elif self.state == "playing":
                if not paused:
                    keys = pygame.key.get_pressed()
                    if keys[pygame.K_SPACE]:
                        self.player.shoot()
                    self.player.update(keys)
                    self.player.update_bullets()
                    self.spawn_wave()
                    self.check_boss_spawn()
                    for e in self.enemies:
                        e.update()
                    self.enemies = [e for e in self.enemies if not e.offscreen()]
                    if self.boss:
                        self.boss.update()
                    for p in self.powerups:
                        p.update()
                    self.powerups = [p for p in self.powerups if not p.offscreen()]
                    self.check_collisions()
                    self.update_effects()
                    self.game_time += 1

                render_surf = pygame.Surface((WIDTH, HEIGHT))
                render_surf.fill(BLACK)
                self.starfield.draw(render_surf)
                for e in self.enemies:
                    e.draw(render_surf)
                if self.boss:
                    self.boss.draw(render_surf)
                for p in self.powerups:
                    p.draw(render_surf)
                self.player.draw(render_surf)
                self.draw_effects(render_surf)
                self.draw_hud(render_surf)
                screen.blit(render_surf, self.shake_offset)
                if paused:
                    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                    overlay.fill((0, 0, 0, 120))
                    screen.blit(overlay, (0, 0))
                    pt = font_big.render("暂停", True, WHITE)
                    screen.blit(pt, (WIDTH // 2 - pt.get_width() // 2, HEIGHT // 2 - 30))
            elif self.state == "gameover":
                self.starfield.draw(screen)
                for e in self.enemies:
                    e.draw(screen)
                if self.boss:
                    self.boss.draw(screen)
                self.player.draw(screen)
                self.draw_hud(screen)
                self.draw_gameover(screen)

            pygame.display.flip()

        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    Game().run()
