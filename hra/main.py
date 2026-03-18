import pygame
import random
import sys
import os
import glob
import math
from dataclasses import dataclass

# -----------------------------
# Okno / hra
# -----------------------------
WIDTH, HEIGHT = 900, 650
GROUND_Y = 520
FPS = 60

# Fyzika (skok)
GRAVITY = 1850
JUMP_VEL = -980
BOOST_JUMP_VEL = -1120

# Rychlost světa
BASE_SPEED = 320
BOOST_SPEED_ADD = 220
BOOST_DURATION = 3.5

# Rozestupy překážek
SPAWN_OBS_MIN = 1.9
SPAWN_OBS_MAX = 2.8
MIN_OBS_GAP_PX = 380

# Banány
SPAWN_BANANA_MIN = 2.5
SPAWN_BANANA_MAX = 4.3

# -----------------------------
# VELIKOSTI + HITBOX + ANIM
# -----------------------------
MONKEY_SCALE = 160
HITBOX_PAD = 8
ANIM_RUN_FPS = 12
ANIM_JUMP_FPS = 10

BANANA_SCALE = (110, 110)
BARRICADE_SCALE_FACTOR = 0.25  # překážka na 1/4 původní velikosti

# debug hitboxy
SHOW_DEBUG_HITBOX = True

# -----------------------------
# AUTO-NALEZENÍ ASSETŮ
# -----------------------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(SCRIPT_DIR)

def pick_existing(*paths):
    for p in paths:
        if os.path.exists(p):
            return p
    return paths[0]

SPRITES_DIR = pick_existing(
    os.path.join(SCRIPT_DIR, "sprites"),
    os.path.join(PARENT_DIR, "sprites"),
)

BANANA_FILE = pick_existing(
    os.path.join(SCRIPT_DIR, "banan.png"),
    os.path.join(PARENT_DIR, "banan.png"),
)
BARRICADE_FILE = pick_existing(
    os.path.join(SCRIPT_DIR, "prekazka.png"),
    os.path.join(PARENT_DIR, "prekazka.png"),
)

RUN_FRAMES = sorted(glob.glob(os.path.join(SPRITES_DIR, "opice_run_*.png")))
JUMP_FRAMES = sorted(glob.glob(os.path.join(SPRITES_DIR, "opice_jump_*.png")))

# -----------------------------
# Pomocné
# -----------------------------
def load_sprite(path, scale=None):
    """Načte PNG, ořízne prázdné okraje, škáluje a znovu ořízne."""
    if not os.path.exists(path):
        print(f"[CHYBA] Soubor neexistuje: {path}")
        return None
    try:
        img = pygame.image.load(path).convert_alpha()

        bbox = img.get_bounding_rect()
        if bbox.width > 0 and bbox.height > 0:
            img = img.subsurface(bbox).copy()

        if scale:
            if isinstance(scale, int):
                img = pygame.transform.smoothscale(img, (scale, scale))
            else:
                img = pygame.transform.smoothscale(img, scale)

        bbox2 = img.get_bounding_rect()
        if bbox2.width > 0 and bbox2.height > 0:
            img = img.subsurface(bbox2).copy()

        return img
    except Exception as e:
        print(f"[CHYBA] Nelze načíst obrázek {path}: {e}")
        return None

def load_obstacle_sprite(path, alpha_threshold=10):
    """
    Načte překážku a tvrdě ji ořízne podle neprůhledných pixelů.
    To řeší problém, kdy je obsah PNG malý uvnitř velkého průhledného plátna.
    """
    if not os.path.exists(path):
        print(f"[CHYBA] Soubor neexistuje: {path}")
        return None

    try:
        img = pygame.image.load(path).convert_alpha()
        w, h = img.get_size()

        min_x, min_y = w, h
        max_x, max_y = -1, -1

        for y in range(h):
            for x in range(w):
                if img.get_at((x, y)).a > alpha_threshold:
                    if x < min_x:
                        min_x = x
                    if y < min_y:
                        min_y = y
                    if x > max_x:
                        max_x = x
                    if y > max_y:
                        max_y = y

        if max_x >= min_x and max_y >= min_y:
            img = img.subsurface(
                pygame.Rect(min_x, min_y, max_x - min_x + 1, max_y - min_y + 1)
            ).copy()

        return img
    except Exception as e:
        print(f"[CHYBA] Nelze načíst obstacle {path}: {e}")
        return None

def load_anim(paths, scale=None):
    frames = []
    for p in paths:
        img = load_sprite(p, scale=scale)
        if img:
            frames.append(img)
    return frames

# -----------------------------
# Futuristické pozadí
# -----------------------------
def draw_stars(screen, rect, t):
    for i in range(140):
        x = rect.x + (i * 73) % rect.w
        y = rect.y + (i * 41) % rect.h

        tw = 1.6 + (i % 7) * 0.18
        a = 0.5 + 0.5 * math.sin((t + i * 0.13) * tw)
        bright = 110 + int(120 * a)
        bright = max(0, min(255, bright))

        if i % 11 == 0:
            pygame.draw.circle(screen, (bright, bright, bright), (x, y), 2)
        else:
            if 0 <= x < WIDTH and 0 <= y < HEIGHT:
                screen.set_at((x, y), (bright, bright, bright))

def draw_futuristic_ship_background(screen, t):
    screen.fill((12, 14, 22))

    for y in range(0, HEIGHT, 6):
        v = 10 + (y * 35) // HEIGHT
        pygame.draw.rect(screen, (v, v + 6, v + 14), (0, y, WIDTH, 6))

    win = pygame.Rect(70, 60, WIDTH - 140, 210)
    pygame.draw.rect(screen, (18, 22, 36), win, border_radius=18)
    pygame.draw.rect(screen, (90, 140, 255), win, 3, border_radius=18)
    draw_stars(screen, win, t)

    for x in range(90, WIDTH - 90, 110):
        pygame.draw.line(screen, (40, 48, 70), (x, 0), (x, HEIGHT), 2)

    pygame.draw.line(screen, (80, 220, 255), (0, 330), (WIDTH, 330), 2)
    pygame.draw.line(screen, (255, 90, 200), (0, 360), (WIDTH, 360), 2)

# -----------------------------
# Entity
# -----------------------------
@dataclass
class Player:
    x: float
    y: float
    vy: float = 0.0
    on_ground: bool = True
    anim_time: float = 0.0
    frame: int = 0
    img: pygame.Surface | None = None

    def jump(self, boosted: bool):
        if self.on_ground:
            self.vy = BOOST_JUMP_VEL if boosted else JUMP_VEL
            self.on_ground = False
            self.anim_time = 0.0
            self.frame = 0

    def update(self, dt: float):
        self.vy += GRAVITY * dt
        self.y += self.vy * dt

        h = self.img.get_height() if self.img else MONKEY_SCALE
        ground_top = GROUND_Y - h

        if self.y >= ground_top:
            self.y = ground_top
            self.vy = 0.0
            self.on_ground = True

        self.anim_time += dt

    def rect(self):
        if not self.img:
            return pygame.Rect(int(self.x), int(self.y), MONKEY_SCALE, MONKEY_SCALE)

        bbox = self.img.get_bounding_rect()
        r = pygame.Rect(int(self.x) + bbox.x, int(self.y) + bbox.y, bbox.w, bbox.h)
        r.inflate_ip(-HITBOX_PAD * 2, -HITBOX_PAD * 2)

        if r.w < 2:
            r.w = 2
        if r.h < 2:
            r.h = 2

        return r

    def draw(self, screen):
        if self.img:
            screen.blit(self.img, (int(self.x), int(self.y)))
        else:
            pygame.draw.rect(screen, (210, 140, 90), (int(self.x), int(self.y), MONKEY_SCALE, MONKEY_SCALE))

@dataclass
class Obstacle:
    x: float
    y: float
    w: int
    h: int
    img: pygame.Surface | None = None

    def rect(self):
        return pygame.Rect(int(self.x), int(self.y), self.w, self.h)

    def update(self, dt: float, world_speed: float):
        self.x -= world_speed * dt

@dataclass
class Banana:
    x: float
    y: float
    w: int
    h: int

    def rect(self):
        return pygame.Rect(int(self.x), int(self.y), self.w, self.h)

    def update(self, dt: float, world_speed: float):
        self.x -= world_speed * dt

# -----------------------------
# Hlavní hra
# -----------------------------
def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Opice Runner 🐒🍌")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("arial", 24, bold=True)
    big = pygame.font.SysFont("arial", 44, bold=True)

    run_frames = load_anim(RUN_FRAMES, scale=MONKEY_SCALE)
    jump_frames = load_anim(JUMP_FRAMES, scale=MONKEY_SCALE)

    monkey_img = run_frames[0] if run_frames else (jump_frames[0] if jump_frames else None)

    banana_img = load_sprite(BANANA_FILE, scale=BANANA_SCALE)
    barricade_raw = load_obstacle_sprite(BARRICADE_FILE)

    missing = []
    if not run_frames:
        missing.append("sprites/opice_run_*.png")
    if not jump_frames:
        missing.append("sprites/opice_jump_*.png")
    if banana_img is None:
        missing.append("banan.png")
    if barricade_raw is None:
        missing.append("prekazka.png")

    player = Player(x=120, y=0, img=monkey_img)
    if player.img:
        player.y = GROUND_Y - player.img.get_height()
    else:
        player.y = GROUND_Y - MONKEY_SCALE

    obstacles: list[Obstacle] = []
    bananas: list[Banana] = []

    score = 0.0
    best = 0.0
    boost_time_left = 0.0

    next_obs_in = random.uniform(SPAWN_OBS_MIN, SPAWN_OBS_MAX)
    next_banana_in = random.uniform(SPAWN_BANANA_MIN, SPAWN_BANANA_MAX)

    running = True
    game_over = False

    def reset():
        nonlocal obstacles, bananas, score, boost_time_left, next_obs_in, next_banana_in, game_over
        obstacles = []
        bananas = []
        score = 0.0
        boost_time_left = 0.0

        player.vy = 0.0
        player.on_ground = True
        player.anim_time = 0.0
        player.frame = 0

        if player.img:
            player.y = GROUND_Y - player.img.get_height()
        else:
            player.y = GROUND_Y - MONKEY_SCALE

        next_obs_in = random.uniform(SPAWN_OBS_MIN, SPAWN_OBS_MAX)
        next_banana_in = random.uniform(SPAWN_BANANA_MIN, SPAWN_BANANA_MAX)
        game_over = False

    while running:
        dt = clock.tick(FPS) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

                if event.key in (pygame.K_SPACE, pygame.K_UP):
                    if not game_over:
                        player.jump(boosted=(boost_time_left > 0))
                    else:
                        reset()

        if not game_over:
            if boost_time_left > 0:
                boost_time_left = max(0.0, boost_time_left - dt)

            world_speed = BASE_SPEED + (BOOST_SPEED_ADD if boost_time_left > 0 else 0)

            # -----------------------------
            # spawn překážek
            # -----------------------------
            next_obs_in -= dt
            can_spawn_by_gap = True
            if obstacles:
                last = obstacles[-1]
                if last.x > WIDTH - MIN_OBS_GAP_PX:
                    can_spawn_by_gap = False

            if next_obs_in <= 0 and can_spawn_by_gap:
                monkey_h = player.img.get_height() if player.img else MONKEY_SCALE

                # překážka zmenšená na 1/4 původní velikosti
                base_h = max(100, int(monkey_h * 1.1))
                target_h = max(25, int(base_h * BARRICADE_SCALE_FACTOR))

                if barricade_raw:
                    aspect = barricade_raw.get_width() / barricade_raw.get_height()
                    hit_h = target_h
                    hit_w = max(15, int(hit_h * aspect))
                    obs_img = pygame.transform.smoothscale(barricade_raw, (hit_w, hit_h))
                else:
                    hit_h = target_h
                    hit_w = max(15, int(hit_h * 1.0))
                    obs_img = None

                obstacles.append(Obstacle(
                    x=WIDTH + 30,
                    y=GROUND_Y - hit_h,
                    w=hit_w,
                    h=hit_h,
                    img=obs_img
                ))
                next_obs_in = random.uniform(SPAWN_OBS_MIN, SPAWN_OBS_MAX)

            # -----------------------------
            # spawn banánů
            # -----------------------------
            next_banana_in -= dt
            if next_banana_in <= 0:
                bw = banana_img.get_width() if banana_img else BANANA_SCALE[0]
                bh = banana_img.get_height() if banana_img else BANANA_SCALE[1]
                spawn_x = WIDTH + 30

                y = GROUND_Y - bh

                if obstacles and random.random() < 0.55:
                    last = obstacles[-1]
                    if abs(last.x - spawn_x) < 200:
                        y = last.y - bh

                y = min(y, GROUND_Y - bh)
                y = max(0, y)

                bananas.append(Banana(x=spawn_x, y=y, w=bw, h=bh))
                next_banana_in = random.uniform(SPAWN_BANANA_MIN, SPAWN_BANANA_MAX)

            # -----------------------------
            # update
            # -----------------------------
            player.update(dt)

            for o in obstacles:
                o.update(dt, world_speed)
            for b in bananas:
                b.update(dt, world_speed)

            obstacles = [o for o in obstacles if o.x + o.w > -80]
            bananas = [b for b in bananas if b.x + b.w > -80]

            # -----------------------------
            # kolize
            # -----------------------------
            pr = player.rect()

            for o in obstacles:
                if pr.colliderect(o.rect()):
                    game_over = True
                    best = max(best, score)

            new_bananas = []
            for b in bananas:
                if pr.colliderect(b.rect()):
                    boost_time_left = BOOST_DURATION
                else:
                    new_bananas.append(b)
            bananas = new_bananas

            score += dt * 10

        # -----------------------------
        # ANIMACE
        # -----------------------------
        frames = None
        anim_fps = ANIM_RUN_FPS

        if not player.on_ground and jump_frames:
            frames = jump_frames
            anim_fps = ANIM_JUMP_FPS
        elif run_frames:
            frames = run_frames
            anim_fps = ANIM_RUN_FPS
        elif jump_frames:
            frames = jump_frames
            anim_fps = ANIM_JUMP_FPS

        if frames:
            player.frame = int(player.anim_time * anim_fps) % len(frames)
            player.img = frames[player.frame]
            if player.on_ground:
                player.y = GROUND_Y - player.img.get_height()

        # -----------------------------
        # Render
        # -----------------------------
        t = pygame.time.get_ticks() / 1000.0
        draw_futuristic_ship_background(screen, t)

        pygame.draw.rect(screen, (22, 26, 38), (0, GROUND_Y, WIDTH, HEIGHT - GROUND_Y))
        pygame.draw.line(screen, (80, 220, 255), (0, GROUND_Y), (WIDTH, GROUND_Y), 3)

        for x in range(0, WIDTH, 70):
            pygame.draw.line(screen, (45, 55, 80), (x, GROUND_Y), (x + 30, HEIGHT), 2)

        screen.blit(font.render(f"Skóre: {int(score)}", True, (230, 235, 245)), (18, 12))
        screen.blit(font.render(f"Best: {int(best)}", True, (210, 215, 230)), (18, 40))

        if boost_time_left > 0:
            screen.blit(font.render(f"BOOST: {boost_time_left:.1f}s", True, (255, 160, 230)), (18, 68))

        if missing:
            msg = "CHYBÍ: " + ", ".join(missing)
            screen.blit(font.render(msg, True, (255, 90, 90)), (18, 100))

        # banány
        for b in bananas:
            if banana_img:
                screen.blit(banana_img, (int(b.x), int(b.y)))
            else:
                pygame.draw.rect(screen, (255, 220, 80), b.rect())

            if SHOW_DEBUG_HITBOX:
                pygame.draw.rect(screen, (255, 0, 0), b.rect(), 2)

        # překážky
        for o in obstacles:
            if o.img:
                screen.blit(o.img, (int(o.x), int(o.y)))
            else:
                pygame.draw.rect(screen, (160, 160, 170), o.rect())

            if SHOW_DEBUG_HITBOX:
                pygame.draw.rect(screen, (255, 0, 0), o.rect(), 2)

        # opice
        player.draw(screen)
        if SHOW_DEBUG_HITBOX:
            pygame.draw.rect(screen, (0, 255, 0), player.rect(), 2)

        if game_over:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 160))
            screen.blit(overlay, (0, 0))
            t1 = big.render("GAME OVER", True, (255, 255, 255))
            t2 = font.render("SPACE pro restart", True, (240, 240, 240))
            screen.blit(t1, (WIDTH // 2 - t1.get_width() // 2, 170))
            screen.blit(t2, (WIDTH // 2 - t2.get_width() // 2, 235))

        pygame.display.flip()

    pygame.quit()
    sys.exit()

# -------------------------------------------------
AUTO_START = True

if __name__ == "__main__":
    if AUTO_START:
        main()
    else:
        print("AUTO_START=False -> hra se nespustila.")
