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
EnemyBullet = namedtuple("EnemyBullet", ["x", "y"])

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

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("飞机大战")
clock = pygame.time.Clock()

_FONT_NAMES = "simhei,microsoftyahei,notosanscjksc,wenquanyimicrohei,arial"
font_big = pygame.font.SysFont(_FONT_NAMES, 48)
font_mid = pygame.font.SysFont(_FONT_NAMES, 28)
font_sm = pygame.font.SysFont(_FONT_NAMES, 20)
font_float = pygame.font.SysFont(_FONT_NAMES, 18, bold=True)


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


snd_shoot = _gen_shoot_sound()
snd_explosion = _gen_explosion_sound()
snd_hit = _gen_hit_sound()
snd_pickup = _gen_pickup_sound()


# ── 绘制飞机的辅助函数 ───────────────────────────────────────────
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
    colors = [RED, (255, 150, 30), (200, 60, 200)]
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
    color = (alpha, alpha, alpha)
    pygame.draw.circle(surf, color, (int(x), int(y)), radius)


# ── 游戏对象 ──────────────────────────────────────────────────────
class Player:
    def __init__(self):
        self.x = WIDTH // 2
        self.y = HEIGHT - 80
        self.speed = 5
        self.bullets = []
        self.shoot_cd = 0
        self.lives = 3
        self.invincible = 0
        self.power = 1

    def update(self, keys):
        dx = 0
        dy = 0
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
    def __init__(self, kind=0):
        self.kind = kind
        self.hp = [1, 3, 7][kind]
        self.max_hp = self.hp
        self.score = [100, 300, 600][kind]
        w_range = [(14, 14), (22, 20), (30, 26)]
        self.w, self.h = w_range[kind]
        self.x = random.randint(self.w + 10, WIDTH - self.w - 10)
        self.y = -self.h * 2
        self.speed = [3, 2, 1.2][kind] + random.uniform(-0.3, 0.3)
        self.sway = random.uniform(-0.5, 0.5)
        self.bullets = []
        self.shoot_timer = random.randint(30, 90)

    def update(self):
        self.y += self.speed
        self.x += self.sway
        if self.x < self.w + 5 or self.x > WIDTH - self.w - 5:
            self.sway = -self.sway
        self.shoot_timer -= 1
        if self.shoot_timer <= 0 and self.kind >= 1:
            self.shoot_timer = random.randint(40, 100)
            self.bullets.append(EnemyBullet(self.x, self.y + self.h))
        self.bullets = [EnemyBullet(b.x, b.y + 5) for b in self.bullets if b.y + 5 < HEIGHT + 10]

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
            color = YELLOW
            label = "P"
        else:
            color = GREEN
            label = "+"
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
        self.shake_timer = 0
        self.shake_offset = (0, 0)
        self.reset()

    def reset(self):
        self.player = Player()
        self.enemies = []
        self.explosions = []
        self.hit_flashes = []
        self.float_scores = []
        self.powerups = []
        self.score = 0
        self.wave_timer = 0
        self.difficulty = 1.0
        self.kills = 0
        self.shake_timer = 0
        self.shake_offset = (0, 0)

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

    def spawn_wave(self):
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
        self.enemies.append(Enemy(kind))
        if self.difficulty > 2 and random.random() < 0.3:
            self.enemies.append(Enemy(0))
        self.difficulty = min(self.difficulty + 0.05, 12.0)

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
                        self.score += e.score
                        self.kills += 1
                        self.explosions.append([e.x, e.y, 0])
                        self.float_scores.append([e.x, e.y - e.h, e.score, 0])
                        snd_explosion.play()
                        self.trigger_shake(6 if e.kind == 2 else 3)
                        if random.random() < 0.12:
                            pk = "power" if random.random() < 0.7 else "life"
                            self.powerups.append(PowerUp(e.x, e.y, pk))
                        dead_enemies.add(i)
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

            if not hit:
                for i, e in enumerate(self.enemies):
                    if e.hitbox().colliderect(self.player.hitbox()):
                        self.player_hit()
                        self.explosions.append([e.x, e.y, 0])
                        self.enemies.pop(i)
                        break

        remaining_pu = []
        for p in self.powerups:
            if p.hitbox().colliderect(self.player.hitbox()):
                if p.kind == "power":
                    self.player.power = min(3, self.player.power + 1)
                else:
                    self.player.lives += 1
                snd_pickup.play()
            else:
                remaining_pu.append(p)
        self.powerups = remaining_pu

    def player_hit(self):
        self.player.lives -= 1
        self.player.invincible = 90
        self.player.power = max(1, self.player.power - 1)
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
            if fs[3] < 40:
                new_fs.append(fs)
        self.float_scores = new_fs
        self.update_shake()

    def draw_hud(self, surf):
        txt = font_mid.render(f"分数: {self.score}", True, WHITE)
        surf.blit(txt, (10, 10))
        for i in range(self.player.lives):
            pygame.draw.polygon(surf, RED,
                                [(15 + i * 25, 50), (10 + i * 25, 60), (20 + i * 25, 60)])
        ptxt = font_sm.render(f"火力: {'★' * self.player.power}", True, YELLOW)
        surf.blit(ptxt, (10, 68))

    def draw_effects(self, surf):
        for x, y, f in self.hit_flashes:
            draw_hit_flash(surf, x, y, f)
        for x, y, f in self.explosions:
            draw_explosion(surf, x, y, f)
        for fx, fy, score, f in self.float_scores:
            alpha = max(0, 255 - int(255 * f / 40))
            color = (255, 255, min(255, 50 + alpha))
            txt = font_float.render(f"+{score}", True, color)
            surf.blit(txt, (fx - txt.get_width() // 2, fy))

    def draw_menu(self, surf):
        surf.fill(BLACK)
        self.starfield.draw(surf)
        title = font_big.render("飞机大战", True, CYAN)
        surf.blit(title, (WIDTH // 2 - title.get_width() // 2, 150))
        sub = font_mid.render("按 SPACE 开始游戏", True, WHITE)
        surf.blit(sub, (WIDTH // 2 - sub.get_width() // 2, 260))
        controls = [
            "方向键 / WASD - 移动",
            "空格键 - 射击",
            "P - 暂停",
        ]
        for i, line in enumerate(controls):
            t = font_sm.render(line, True, GRAY)
            surf.blit(t, (WIDTH // 2 - t.get_width() // 2, 340 + i * 30))
        draw_player(surf, WIDTH // 2, 500)

    def draw_gameover(self, surf):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        surf.blit(overlay, (0, 0))
        go = font_big.render("游戏结束", True, RED)
        surf.blit(go, (WIDTH // 2 - go.get_width() // 2, 200))
        sc = font_mid.render(f"最终分数: {self.score}", True, WHITE)
        surf.blit(sc, (WIDTH // 2 - sc.get_width() // 2, 280))
        kl = font_mid.render(f"击杀数: {self.kills}", True, YELLOW)
        surf.blit(kl, (WIDTH // 2 - kl.get_width() // 2, 320))
        rs = font_mid.render("按 R 重新开始", True, WHITE)
        surf.blit(rs, (WIDTH // 2 - rs.get_width() // 2, 400))
        ms = font_sm.render("按 ESC 返回菜单", True, GRAY)
        surf.blit(ms, (WIDTH // 2 - ms.get_width() // 2, 450))

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
                        if event.key == pygame.K_SPACE:
                            self.reset()
                            self.state = "playing"
                    elif self.state == "playing":
                        if event.key == pygame.K_p:
                            paused = not paused
                        if event.key == pygame.K_ESCAPE:
                            self.state = "menu"
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
                    for e in self.enemies:
                        e.update()
                    self.enemies = [e for e in self.enemies if not e.offscreen()]
                    for p in self.powerups:
                        p.update()
                    self.powerups = [p for p in self.powerups if not p.offscreen()]
                    self.check_collisions()
                    self.update_effects()

                render_surf = pygame.Surface((WIDTH, HEIGHT))
                render_surf.fill(BLACK)
                self.starfield.draw(render_surf)
                for e in self.enemies:
                    e.draw(render_surf)
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
                self.player.draw(screen)
                self.draw_hud(screen)
                self.draw_gameover(screen)

            pygame.display.flip()

        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    Game().run()
