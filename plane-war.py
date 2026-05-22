import pygame
import random
import sys

pygame.init()

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

# 字体（尝试中文字体，回退到默认）
_FONT_NAMES = "simhei,microsoftyahei,notosanscjksc,wenquanyimicrohei,arial"
font_big = pygame.font.SysFont(_FONT_NAMES, 48)
font_mid = pygame.font.SysFont(_FONT_NAMES, 28)
font_sm = pygame.font.SysFont(_FONT_NAMES, 20)


# ── 绘制飞机的辅助函数 ───────────────────────────────────────────
def draw_player(surf, cx, cy):
    """绘制玩家飞机（蓝色三角形 + 机翼）"""
    body = [(cx, cy - 20), (cx - 16, cy + 16), (cx + 16, cy + 16)]
    pygame.draw.polygon(surf, CYAN, body)
    pygame.draw.polygon(surf, WHITE, body, 2)
    # 机翼
    lw = [(cx - 16, cy + 10), (cx - 30, cy + 22), (cx - 8, cy + 14)]
    rw = [(cx + 16, cy + 10), (cx + 30, cy + 22), (cx + 8, cy + 14)]
    pygame.draw.polygon(surf, (60, 180, 240), lw)
    pygame.draw.polygon(surf, (60, 180, 240), rw)
    # 尾焰
    flame_h = random.randint(6, 14)
    pygame.draw.polygon(surf, YELLOW,
                        [(cx - 5, cy + 16), (cx, cy + 16 + flame_h), (cx + 5, cy + 16)])


def draw_enemy(surf, cx, cy, kind):
    """绘制敌机: kind=0 小型(红), kind=1 中型(橙), kind=2 大型(紫)"""
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
    """绘制爆炸效果"""
    progress = frame / max_frames
    radius = int(10 + 30 * progress)
    color = (255, max(0, 200 - int(200 * progress)), 0)
    pygame.draw.circle(surf, color, (cx, cy), radius, 3)
    for _ in range(6):
        angle = random.uniform(0, 2 * 3.14159)
        dist = radius * random.uniform(0.4, 1.0)
        px = cx + int(dist * pygame.math.Vector2(1, 0).rotate_rad(angle).x)
        py = cy + int(dist * pygame.math.Vector2(1, 0).rotate_rad(angle).y)
        pygame.draw.circle(surf, YELLOW, (px, py), random.randint(2, 5))


# ── 游戏对象 ──────────────────────────────────────────────────────
class Player:
    def __init__(self):
        self.x = WIDTH // 2
        self.y = HEIGHT - 80
        self.speed = 5
        self.bullets = []
        self.shoot_cd = 0
        self.lives = 3
        self.invincible = 0  # 无敌帧数
        self.power = 1  # 火力等级 1-3

    def update(self, keys):
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.x = max(20, self.x - self.speed)
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.x = min(WIDTH - 20, self.x + self.speed)
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            self.y = max(40, self.y - self.speed)
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            self.y = min(HEIGHT - 20, self.y + self.speed)
        if self.shoot_cd > 0:
            self.shoot_cd -= 1
        if self.invincible > 0:
            self.invincible -= 1

    def shoot(self):
        if self.shoot_cd > 0:
            return
        self.shoot_cd = 8
        if self.power >= 3:
            self.bullets.append([self.x, self.y - 20, -1])
            self.bullets.append([self.x - 12, self.y - 14, 0])
            self.bullets.append([self.x + 12, self.y - 14, 0])
        elif self.power >= 2:
            self.bullets.append([self.x - 8, self.y - 18, 0])
            self.bullets.append([self.x + 8, self.y - 18, 0])
        else:
            self.bullets.append([self.x, self.y - 20, 0])

    def update_bullets(self):
        for b in self.bullets:
            b[1] -= 10
            b[0] += b[2]
        self.bullets = [b for b in self.bullets if b[1] > -10]

    def draw(self, surf):
        if self.invincible > 0 and (self.invincible // 3) % 2 == 0:
            return  # 闪烁效果
        draw_player(surf, self.x, self.y)
        for b in self.bullets:
            pygame.draw.rect(surf, YELLOW, (b[0] - 2, b[1] - 6, 4, 12))
            pygame.draw.rect(surf, WHITE, (b[0] - 1, b[1] - 6, 2, 12))

    def hitbox(self):
        return pygame.Rect(self.x - 10, self.y - 10, 20, 20)


class Enemy:
    def __init__(self, kind=0):
        self.kind = kind  # 0=小, 1=中, 2=大
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
            self.bullets.append([self.x, self.y + self.h])
        for b in self.bullets:
            b[1] += 5
        self.bullets = [b for b in self.bullets if b[1] < HEIGHT + 10]

    def draw(self, surf):
        draw_enemy(surf, self.x, self.y, self.kind)
        # 血条
        if self.hp < self.max_hp:
            bw = self.w * 2
            pygame.draw.rect(surf, RED, (self.x - bw // 2, self.y - self.h - 8, bw, 4))
            pygame.draw.rect(surf, GREEN,
                             (self.x - bw // 2, self.y - self.h - 8, int(bw * self.hp / self.max_hp), 4))
        for b in self.bullets:
            pygame.draw.circle(surf, RED, (int(b[0]), int(b[1])), 3)

    def hitbox(self):
        return pygame.Rect(self.x - self.w, self.y - self.h // 2, self.w * 2, self.h + self.h // 2)

    def offscreen(self):
        return self.y > HEIGHT + 40


class PowerUp:
    def __init__(self, x, y, kind="power"):
        self.x = x
        self.y = y
        self.kind = kind  # "power" or "life"
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
        self.stars = []
        for _ in range(80):
            self.stars.append([random.randint(0, WIDTH), random.randint(0, HEIGHT),
                               random.uniform(1, 3)])

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
        self.state = "menu"  # menu / playing / gameover
        self.reset()

    def reset(self):
        self.player = Player()
        self.enemies = []
        self.explosions = []  # (x, y, frame)
        self.powerups = []
        self.score = 0
        self.wave_timer = 0
        self.difficulty = 1.0
        self.kills = 0

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
        # 额外小怪
        if self.difficulty > 2 and random.random() < 0.3:
            self.enemies.append(Enemy(0))
        self.difficulty += 0.05

    def check_collisions(self):
        # 玩家子弹 vs 敌机
        for e in self.enemies:
            for b in self.player.bullets[:]:
                brect = pygame.Rect(b[0] - 3, b[1] - 6, 6, 12)
                if brect.colliderect(e.hitbox()):
                    e.hp -= 1
                    if b in self.player.bullets:
                        self.player.bullets.remove(b)
                    if e.hp <= 0:
                        self.score += e.score
                        self.kills += 1
                        self.explosions.append([e.x, e.y, 0])
                        # 道具掉落
                        if random.random() < 0.12:
                            pk = "power" if random.random() < 0.7 else "life"
                            self.powerups.append(PowerUp(e.x, e.y, pk))
                        self.enemies.remove(e)
                    break

        # 敌机子弹 vs 玩家
        if self.player.invincible <= 0:
            for e in self.enemies:
                for b in e.bullets[:]:
                    brect = pygame.Rect(b[0] - 3, b[1] - 3, 6, 6)
                    if brect.colliderect(self.player.hitbox()):
                        self.player_hit()
                        e.bullets.remove(b)
                        break

            # 敌机撞玩家
            for e in self.enemies[:]:
                if e.hitbox().colliderect(self.player.hitbox()):
                    self.player_hit()
                    self.explosions.append([e.x, e.y, 0])
                    self.enemies.remove(e)
                    break

        # 道具 vs 玩家
        for p in self.powerups[:]:
            if p.hitbox().colliderect(self.player.hitbox()):
                if p.kind == "power":
                    self.player.power = min(3, self.player.power + 1)
                else:
                    self.player.lives += 1
                self.powerups.remove(p)

    def player_hit(self):
        self.player.lives -= 1
        self.player.invincible = 90  # 1.5秒无敌
        self.player.power = max(1, self.player.power - 1)
        if self.player.lives <= 0:
            self.state = "gameover"

    def draw_hud(self, surf):
        # 分数
        txt = font_mid.render(f"分数: {self.score}", True, WHITE)
        surf.blit(txt, (10, 10))
        # 生命
        for i in range(self.player.lives):
            pygame.draw.polygon(surf, RED,
                                [(15 + i * 25, 50), (10 + i * 25, 60), (20 + i * 25, 60)])
        # 火力等级
        ptxt = font_sm.render(f"火力: {'★' * self.player.power}", True, YELLOW)
        surf.blit(ptxt, (10, 68))

    def draw_menu(self, surf):
        surf.fill(BLACK)
        self.starfield.update()
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
        # 装饰性飞机
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
                    # 更新爆炸
                    self.explosions = [[x, y, f + 1] for x, y, f in self.explosions if f < 12]

                self.starfield.draw(screen)
                for e in self.enemies:
                    e.draw(screen)
                for p in self.powerups:
                    p.draw(screen)
                self.player.draw(screen)
                for x, y, f in self.explosions:
                    draw_explosion(screen, x, y, f)
                self.draw_hud(screen)
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
