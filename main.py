# Author: Atanu Sarkar (original idea) – revised & fixed version
# Space Invaders (my version) – Fixed/Improved
# v2.0
# Notes:
# - Robust to missing assets (images/sounds): falls back to colored shapes & no-op sounds
# - Correct collision math (use height for Y)
# - Proper mixer init and graceful audio handling
# - FPS limited to 60, improved pause/mute/restart controls
# - Same general gameplay & variables preserved

import pygame
import random
import math
from pygame import mixer
import time
import os
from typing import Optional

# -------------------------------
# game constants
# -------------------------------
WIDTH = 800
HEIGHT = 600
TARGET_FPS = 60

# -------------------------------
# global game state
# -------------------------------
running = True
paused = False
muted = False

score = 0
highest_score = 0
life = 3
kills = 0
difficulty = 1
level = 1
max_kills_to_difficulty_up = 5
max_difficulty_to_level_up = 5

initial_player_velocity = 3.0
initial_enemy_velocity = 1.0
weapon_shot_velocity = 5.0

# metrics
single_frame_rendering_time = 0.0
total_time = 0.0
frame_count = 0
fps = 0

enemies = []
lasers = []

# -------------------------------
# initialize pygame + mixer safe
# -------------------------------
pygame.mixer.pre_init(44100, -16, 2, 512)
pygame.init()
try:
    mixer.init()
except Exception:
    # if mixer fails (e.g., no audio device), continue without sounds
    pass

window = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Space Invaders (fixed)")

# -------------------------------
# helpers for assets with fallback
# -------------------------------
def safe_load_image(path: str, size: Optional[tuple[int, int]] = None, fill=(120, 200, 120)) -> pygame.Surface:
    """
    Load an image or return a fallback rectangle surface if missing.
    """
    surf = None
    try:
        if os.path.exists(path):
            surf = pygame.image.load(path).convert_alpha()
        else:
            raise FileNotFoundError(path)
    except Exception:
        # fallback: simple colored surface
        w, h = size if size else (64, 64)
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        surf.fill((*fill, 255))
        # add a simple border
        pygame.draw.rect(surf, (30, 60, 30), surf.get_rect(), 3)
    if size and surf.get_size() != size:
        surf = pygame.transform.smoothscale(surf, size)
    return surf

class NoOpSound:
    def play(self): pass
    def stop(self): pass

def safe_load_sound(path: str):
    """
    Load a sound or return a no-op sound if missing or mixer unavailable.
    """
    try:
        if mixer.get_init() and os.path.exists(path):
            return mixer.Sound(path)
        else:
            return NoOpSound()
    except Exception:
        return NoOpSound()

def safe_music_load_and_play(path: str, loop: int = -1, volume: float = 1.0):
    """
    Load and play music if possible; ignore errors gracefully.
    """
    try:
        if mixer.get_init() and os.path.exists(path):
            mixer.music.load(path)
            mixer.music.set_volume(volume)
            mixer.music.play(loop)
    except Exception:
        pass

def safe_music_pause():
    try:
        mixer.music.pause()
    except Exception:
        pass

def safe_music_unpause():
    try:
        mixer.music.unpause()
    except Exception:
        pass

def safe_music_stop():
    try:
        mixer.music.stop()
    except Exception:
        pass

# -------------------------------
# input states
# -------------------------------
LEFT = RIGHT = UP = SPACE = ENTER = ESC = False

# -------------------------------
# UI fonts
# -------------------------------
FONT_UI = pygame.font.SysFont("calibri", 16)
FONT_BIG = pygame.font.SysFont("freesansbold", 64)

# -------------------------------
# background & icon
# -------------------------------
BACKGROUND_IMG = safe_load_image("res/images/background.jpg", (WIDTH, HEIGHT), fill=(10, 10, 30))
ICON_IMG = safe_load_image("res/images/alien.png", (32, 32))
pygame.display.set_icon(ICON_IMG)

background_music_paths = [
    "res/sounds/Space_Invaders_Music.ogg",
    "res/sounds/Space_Invaders_Music_x2.ogg",
    "res/sounds/Space_Invaders_Music_x4.ogg",
    "res/sounds/Space_Invaders_Music_x8.ogg",
    "res/sounds/Space_Invaders_Music_x16.ogg",
    "res/sounds/Space_Invaders_Music_x32.ogg",
]

def init_background_music():
    idx = min(max(difficulty - 1, 0), 5)
    safe_music_load_and_play(background_music_paths[idx], loop=-1, volume=0.6 if not muted else 0.0)

# -------------------------------
# game objects
# -------------------------------
class Player:
    def __init__(self, img_path, width, height, x, y, dx, dy, kill_sound_path):
        self.img = safe_load_image(img_path, (width, height), fill=(80, 160, 240))
        self.width = width
        self.height = height
        self.x = x
        self.y = y
        self.dx = dx
        self.dy = dy
        self.kill_sound = safe_load_sound(kill_sound_path)

    def draw(self, surface):
        surface.blit(self.img, (self.x, self.y))

class Enemy:
    def __init__(self, img_path, width, height, x, y, dx, dy, kill_sound_path):
        self.img = safe_load_image(img_path, (width, height), fill=(200, 80, 80))
        self.width = width
        self.height = height
        self.x = x
        self.y = y
        self.dx = dx
        self.dy = dy
        self.kill_sound = safe_load_sound(kill_sound_path)

    def draw(self, surface):
        surface.blit(self.img, (self.x, self.y))

class Bullet:
    def __init__(self, img_path, width, height, x, y, dx, dy, fire_sound_path):
        self.img = safe_load_image(img_path, (width, height), fill=(250, 250, 80))
        self.width = width
        self.height = height
        self.x = x
        self.y = y
        self.dx = dx
        self.dy = dy
        self.fired = False
        self.fire_sound = safe_load_sound(fire_sound_path)

    def draw(self, surface):
        if self.fired:
            surface.blit(self.img, (self.x, self.y))

class Laser:
    def __init__(self, img_path, width, height, x, y, dx, dy, shoot_probability, relaxation_time, beam_sound_path):
        self.img = safe_load_image(img_path, (width, height), fill=(120, 240, 120))
        self.width = width
        self.height = height
        self.x = x
        self.y = y
        self.dx = dx
        self.dy = dy
        self.beamed = False
        self.shoot_probability = shoot_probability
        self.shoot_timer = 0
        self.relaxation_time = relaxation_time
        self.beam_sound = safe_load_sound(beam_sound_path)

    def draw(self, surface):
        if self.beamed:
            surface.blit(self.img, (self.x, self.y))

# created later in init_game()
player: Player
bullet: Bullet

# -------------------------------
# sounds
# -------------------------------
pause_sound = safe_load_sound("res/sounds/pause.wav")
level_up_sound = safe_load_sound("res/sounds/1up.wav")
weapon_annihilation_sound = safe_load_sound("res/sounds/annihilation.wav")
game_over_sound = safe_load_sound("res/sounds/gameover.wav")

def set_sounds_volume(vol: float):
    """Set overall volume for SFX via Sound.set_volume (if supported)."""
    try:
        for s in (pause_sound, level_up_sound, weapon_annihilation_sound, game_over_sound,
                  getattr(player, "kill_sound", NoOpSound())):
            try:
                s.set_volume(vol)
            except Exception:
                pass
    except Exception:
        pass

# -------------------------------
# HUD / UI
# -------------------------------
def scoreboard(surface):
    global fps, single_frame_rendering_time
    x, y = 10, 10
    col = (255, 255, 255)

    def put(txt, dy):
        surface.blit(FONT_UI.render(txt, True, col), (x, y + dy))

    put(f"SCORE : {score}", 0)
    put(f"HI-SCORE : {highest_score}", 20)
    put(f"LEVEL : {level}", 40)
    put(f"DIFFICULTY : {difficulty}", 60)
    put(f"LIFE LEFT : {life} | " + ("@ " * life), 80)

    # perf
    frame_time_ms = f"{(single_frame_rendering_time*1000):.2f} ms"
    surface.blit(FONT_UI.render(f"FPS : {fps}", True, col), (WIDTH - 120, 10))
    surface.blit(FONT_UI.render(f"FT : {frame_time_ms}", True, col), (WIDTH - 120, 30))

def center_text(surface, text, font, color=(255,255,255), y=HEIGHT//2):
    surf = font.render(text, True, color)
    rect = surf.get_rect(center=(WIDTH//2, y))
    surface.blit(surf, rect)

# -------------------------------
# collision
# -------------------------------
def collision_check(obj1, obj2) -> bool:
    # FIX: use height for Y center (original used width by mistake)
    x1_cm = obj1.x + obj1.width / 2
    y1_cm = obj1.y + obj1.height / 2
    x2_cm = obj2.x + obj2.width / 2
    y2_cm = obj2.y + obj2.height / 2
    distance = math.hypot(x2_cm - x1_cm, y2_cm - y1_cm)
    return distance < ((obj1.width + obj2.width) / 2)

# -------------------------------
# game behaviors
# -------------------------------
def level_up():
    global life, level, difficulty, max_difficulty_to_level_up
    level_up_sound.play()
    level += 1
    life += 1
    difficulty = 1

    # Extra progression
    if level % 3 == 0:
        player.dx += 1
        bullet.dy += 1
        max_difficulty_to_level_up += 1
        for lz in lasers:
            lz.shoot_probability = min(1.0, lz.shoot_probability + 0.1)
    max_difficulty_to_level_up = min(max_difficulty_to_level_up, 7)

    # brief feedback
    center_text(window, "LEVEL UP", FONT_BIG, (255,255,255), y=HEIGHT//2)
    pygame.display.update()
    init_game(reset_positions=True)
    time.sleep(0.8)

def respawn(enemy_obj: Enemy):
    enemy_obj.x = random.randint(0, (WIDTH - enemy_obj.width))
    enemy_obj.y = random.randint(((HEIGHT // 10) * 1 - (enemy_obj.height // 2)),
                                 ((HEIGHT // 10) * 4 - (enemy_obj.height // 2)))

def kill_enemy(player_obj: Player, bullet_obj: Bullet, enemy_obj: Enemy):
    global score, kills, difficulty
    bullet_obj.fired = False
    enemy_obj.kill_sound.play()
    bullet_obj.x = player_obj.x + player_obj.width / 2 - bullet_obj.width / 2
    bullet_obj.y = player_obj.y + bullet_obj.height / 2
    score += 10 * difficulty * level
    kills += 1
    if kills % max_kills_to_difficulty_up == 0:
        difficulty += 1
        if (difficulty == max_difficulty_to_level_up) and (life > 0):
            level_up()
        init_background_music()
    respawn(enemy_obj)

def rebirth(player_obj: Player):
    player_obj.x = (WIDTH / 2) - (player_obj.width / 2)
    player_obj.y = (HEIGHT // 10) * 9 - (player_obj.height // 2)

def gameover_screen():
    scoreboard(window)
    center_text(window, "GAME OVER", FONT_BIG, (255,255,255), y=HEIGHT//2)
    pygame.display.update()
    safe_music_stop()
    game_over_sound.play()

def gameover():
    global running, score, highest_score
    if score > highest_score:
        highest_score = score
    running = False
    gameover_screen()
    # Short wait to let SFX play if available; press a key to exit sooner
    end_time = time.time() + 4.0
    while time.time() < end_time:
        for ev in pygame.event.get():
            if ev.type in (pygame.KEYDOWN, pygame.QUIT, pygame.MOUSEBUTTONDOWN):
                return
        time.sleep(0.05)

def kill_player(player_obj: Player, enemy_obj: Enemy, laser_obj: Laser):
    global life
    laser_obj.beamed = False
    player_obj.kill_sound.play()
    laser_obj.x = enemy_obj.x + enemy_obj.width / 2 - laser_obj.width / 2
    laser_obj.y = enemy_obj.y + laser_obj.height / 2
    life -= 1
    if life > 0:
        rebirth(player_obj)
    else:
        gameover()

def destroy_weapons(player_obj: Player, bullet_obj: Bullet, enemy_obj: Enemy, laser_obj: Laser):
    bullet_obj.fired = False
    laser_obj.beamed = False
    weapon_annihilation_sound.play()
    bullet_obj.x = player_obj.x + player_obj.width / 2 - bullet_obj.width / 2
    bullet_obj.y = player_obj.y + bullet_obj.height / 2
    laser_obj.x = enemy_obj.x + enemy_obj.width / 2 - laser_obj.width / 2
    laser_obj.y = enemy_obj.y + laser_obj.height / 2

def pause_game():
    pause_sound.play()
    scoreboard(window)
    center_text(window, "PAUSED", FONT_BIG, (255,255,255), y=HEIGHT//2)
    pygame.display.update()
    safe_music_pause()

# -------------------------------
# init game world
# -------------------------------
def init_game(reset_positions: bool = False):
    global player, bullet, enemies, lasers, kills, score, difficulty

    if reset_positions:
        # do not reset score/kills/difficulty on level up
        pass
    else:
        # full reset at start
        kills = 0
        score = 0
        difficulty = 1

    # player
    player_img_path = "res/images/spaceship.png"
    player_width, player_height = 64, 64
    player_x = (WIDTH / 2) - (player_width / 2)
    player_y = (HEIGHT // 10) * 9 - (player_height // 2)
    player_dx = initial_player_velocity
    player_dy = 0
    player_kill_sound_path = "res/sounds/explosion.wav"
    player = Player(player_img_path, player_width, player_height, player_x, player_y, player_dx, player_dy,
                    player_kill_sound_path)

    # bullet
    bullet_img_path = "res/images/bullet.png"
    bullet_width, bullet_height = 32, 32
    bullet_x = player_x + player_width / 2 - bullet_width / 2
    bullet_y = player_y + bullet_height / 2
    bullet_dx = 0
    bullet_dy = weapon_shot_velocity
    bullet_fire_sound_path = "res/sounds/gunshot.wav"
    bullet = Bullet(bullet_img_path, bullet_width, bullet_height, bullet_x, bullet_y, bullet_dx, bullet_dy,
                    bullet_fire_sound_path)

    # enemy template
    enemy_img_path = "res/images/enemy.png"
    enemy_width, enemy_height = 64, 64
    enemy_dx = initial_enemy_velocity
    enemy_dy = (HEIGHT / 10) / 2
    enemy_kill_sound_path = "res/sounds/enemykill.wav"

    # laser template
    laser_img_path = "res/images/beam.png"
    laser_width, laser_height = 24, 24
    laser_dx = 0
    laser_dy = weapon_shot_velocity
    shoot_probability = 0.3
    relaxation_time = 100
    laser_beam_sound_path = "res/sounds/laser.wav"

    enemies.clear()
    lasers.clear()

    # number of enemies = level
    for _ in range(level):
        enemy_x = random.randint(0, (WIDTH - enemy_width))
        enemy_y = random.randint(((HEIGHT // 10) * 1 - (enemy_height // 2)), ((HEIGHT // 10) * 4 - (enemy_height // 2)))
        laser_x = enemy_x + enemy_width / 2 - laser_width / 2
        laser_y = enemy_y + laser_height / 2

        enemies.append(Enemy(enemy_img_path, enemy_width, enemy_height, enemy_x, enemy_y, enemy_dx, enemy_dy,
                             enemy_kill_sound_path))
        lasers.append(Laser(laser_img_path, laser_width, laser_height, laser_x, laser_y, laser_dx, laser_dy,
                            shoot_probability, relaxation_time, laser_beam_sound_path))

    # (re)start music for current difficulty
    init_background_music()

# -------------------------------
# main loop
# -------------------------------
def main():
    global running, paused, muted
    global LEFT, RIGHT, UP, SPACE, ENTER, ESC
    global single_frame_rendering_time, total_time, frame_count, fps, life, level

    clock = pygame.time.Clock()

    init_game()
    runned_once_pause_overlay = False

    while running:
        # frame start time
        t0 = time.time()

        # ---------------- events ----------------
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:   LEFT = True
                if event.key == pygame.K_RIGHT:  RIGHT = True
                if event.key == pygame.K_UP:     UP = True
                if event.key == pygame.K_SPACE:  SPACE = True
                if event.key == pygame.K_RETURN: ENTER = True
                if event.key == pygame.K_ESCAPE: ESC = True

                # Extras
                if event.key == pygame.K_p:  # Pause toggle
                    paused = not paused
                    if paused:
                        pause_game()
                        runned_once_pause_overlay = True
                    else:
                        safe_music_unpause()
                if event.key == pygame.K_m:  # Mute toggle
                    muted = not muted
                    vol = 0.0 if muted else 1.0
                    try:
                        mixer.music.set_volume(0.0 if muted else 0.6)
                    except Exception:
                        pass
                    set_sounds_volume(vol)
                if event.key == pygame.K_r:  # Restart
                    # reset global game
                    life = 3
                    level = 1
                    init_game(reset_positions=False)

            elif event.type == pygame.KEYUP:
                if event.key == pygame.K_LEFT:   LEFT = False
                if event.key == pygame.K_RIGHT:  RIGHT = False
                if event.key == pygame.K_UP:     UP = False
                if event.key == pygame.K_SPACE:  SPACE = False
                if event.key == pygame.K_RETURN: ENTER = False
                if event.key == pygame.K_ESCAPE: ESC = False

        # old pause system (Enter/Esc) preserved:
        if (ENTER or ESC) and not paused:
            paused = True
            pause_game()
            runned_once_pause_overlay = True
        elif (ENTER or ESC) and paused:
            paused = False
            safe_music_unpause()

        # ---------------- drawing background ----------------
        window.blit(BACKGROUND_IMG, (0, 0))

        if paused:
            # keep the overlay once, then freeze updates until unpaused
            if not runned_once_pause_overlay:
                pause_game()
                runned_once_pause_overlay = True
            pygame.display.update()
            clock.tick(TARGET_FPS)
            continue
        else:
            runned_once_pause_overlay = False

        # ---------------- gameplay updates ----------------
        # player movement
        if RIGHT: player.x += player.dx
        if LEFT:  player.x -= player.dx

        # fire bullet
        if (SPACE or UP) and not bullet.fired:
            bullet.fired = True
            bullet.fire_sound.play()
            bullet.x = player.x + player.width / 2 - bullet.width / 2
            bullet.y = player.y + bullet.height / 2

        # bullet movement
        if bullet.fired:
            bullet.y -= bullet.dy

        # enemies & lasers
        for i in range(len(enemies)):
            # laser beaming
            if not lasers[i].beamed:
                lasers[i].shoot_timer += 1
                if lasers[i].shoot_timer >= lasers[i].relaxation_time:
                    lasers[i].shoot_timer = 0
                    if random.random() <= lasers[i].shoot_probability:
                        lasers[i].beamed = True
                        lasers[i].beam_sound.play()
                        lasers[i].x = enemies[i].x + enemies[i].width / 2 - lasers[i].width / 2
                        lasers[i].y = enemies[i].y + lasers[i].height / 2

            # enemy movement (speed scales with difficulty)
            enemies[i].x += enemies[i].dx * float(2 ** (difficulty - 1))

            # laser movement
            if lasers[i].beamed:
                lasers[i].y += lasers[i].dy

        # ---------------- collisions ----------------
        # bullet vs enemies
        for i in range(len(enemies)):
            if bullet.fired and collision_check(bullet, enemies[i]):
                kill_enemy(player, bullet, enemies[i])

        # lasers vs player
        for i in range(len(lasers)):
            if lasers[i].beamed and collision_check(lasers[i], player):
                kill_player(player, enemies[i], lasers[i])
                break

        # enemy vs player (ram)
        for i in range(len(enemies)):
            if collision_check(enemies[i], player):
                kill_enemy(player, bullet, enemies[i])
                kill_player(player, enemies[i], lasers[i])
                break

        # bullet vs lasers
        for i in range(len(lasers)):
            if bullet.fired and lasers[i].beamed and collision_check(bullet, lasers[i]):
                destroy_weapons(player, bullet, enemies[i], lasers[i])

        # ---------------- boundaries ----------------
        # player
        player.x = max(0, min(player.x, WIDTH - player.width))

        # enemies bounce and descend
        for e in enemies:
            if e.x <= 0:
                e.dx = abs(e.dx) * 1
                e.y += e.dy
            if e.x >= WIDTH - e.width:
                e.dx = -abs(e.dx) * 1
                e.y += e.dy
            # if enemies reach too low, penalize (optional)
            if e.y > HEIGHT - 120:
                # force collision/penalty
                kill_player(player, e, lasers[enemies.index(e)])
                break

        # bullet reset
        if bullet.y < -bullet.height:
            bullet.fired = False
            bullet.x = player.x + player.width / 2 - bullet.width / 2
            bullet.y = player.y + bullet.height / 2

        # lasers reset
        for i in range(len(lasers)):
            if lasers[i].y > HEIGHT + lasers[i].height:
                lasers[i].beamed = False
                lasers[i].x = enemies[i].x + enemies[i].width / 2 - lasers[i].width / 2
                lasers[i].y = enemies[i].y + lasers[i].height / 2

        # ---------------- render ----------------
        scoreboard(window)
        for lz in lasers:
            lz.draw(window)
        for e in enemies:
            e.draw(window)
        bullet.draw(window)
        player.draw(window)

        pygame.display.update()

        # ---------------- timing / fps ----------------
        frame_time = time.time() - t0
        single_frame_rendering_time = frame_time
        frame_count += 1
        total_time_acc = getattr(main, "_acc", 0.0) + frame_time
        if total_time_acc >= 1.0:
            fps = frame_count
            frame_count = 0
            total_time_acc = 0.0
        main._acc = total_time_acc

        clock.tick(TARGET_FPS)

    # exit cleanup
    safe_music_stop()
    pygame.quit()


if __name__ == "__main__":
    main()
