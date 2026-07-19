"""
XInput Racing Game (Horizontal)
=================================
Layout: landscape. The player car sits toward the left of the screen,
faces right, and now actually moves - it eases forward when you boost
and eases back when you brake, on top of the road scrolling beneath it,
so acceleration reads as real motion instead of a static car on a
treadmill.

Controls (Xbox controller, via Windows XInput):
    Left Stick Y / D-Pad Up-Down     -> Steer (change lanes / move up-down)
    RT (Right Trigger)               -> Boost (limited meter, recharges)
    LT (Left Trigger)                -> Brake
    Y                                 -> Show the controls screen
    START                            -> Pause / Resume
    B                                -> Exit game (works anytime)
    A                                -> Restart after crash, resume from pause

A full controls reference is also its own screen - press Y anytime
(including from the pause menu) to bring it up, and any button/Enter/Esc
to close it. Since a single pygame process can't reliably open a second
real OS window on Windows, this is implemented as a dedicated full-screen
view instead of a second window - functionally the same "here are all the
controls" screen, just inside the same window.

Assets required (same names as you already have):
    background.png   - scrolls infinitely
    Car.png           - player car (source art can face any direction;
                         it's rotated in code to face right)
    EnemyCAR.png      - oncoming traffic (rotated in code to face left)

WHERE TO PUT THE IMAGES
------------------------
This script never hardcodes a path like "C:/Users/Iremide/...".
Instead, at startup it searches these folders, in order, for each image:
    1. An "assets" folder next to this .py file
    2. An "xboxos/assets" folder next to this .py file
    3. The folder this .py file is saved in
    4. The current working directory (wherever you launched it from)
    5. Your Windows home folder, and home/xboxos/assets, and home/assets
       (found via os.path.expanduser("~"), so it works on any machine or
       username without ever naming "Iremide" in the code)

REQUIREMENTS
------------
    pip install pygame

This game talks to XInput directly through ctypes (Windows only), so
it will not run on macOS/Linux.

STRUCTURE
---------
The main play loop - input polling, movement, scrolling, spawning,
collisions, drawing, pause, game-over/restart - lives in the single
run() function at the bottom. The only things defined outside of it are
things Python *requires* to be their own class (the ctypes structs
describing XInput's data layout), small stateless helpers (polling the
pad, finding an asset, loading/saving the high score), and the controls
screen function - which is its own function because it really is a
separate screen/view, not part of the play loop.

WHAT'S NEW IN THIS VERSION
---------------------------
    - The player car now actually moves forward/back with accel/brake,
      instead of sitting still while only the road scrolls.
    - Boost is now a limited meter that drains while boosting and
      recharges when you let off - shown as a bar on the HUD.
    - Near misses (an enemy passing close without a crash) award bonus
      points with an on-screen "NICE! +50" popup.
    - A short exhaust/speed trail trails the car while boosting.
    - A dedicated Controls screen (Y button) lists every control.
"""

import ctypes
import json
import os
import random
import sys
import time

import pygame

# --------------------------------------------------------------------------
# XInput ctypes plumbing
# (these structs must mirror the Windows XInput.h layout exactly - they
# can't be folded into run(), ctypes needs real classes for this)
# --------------------------------------------------------------------------

if os.name != "nt":
    print("This game uses the Windows XInput API and can only run on Windows.")
    sys.exit(1)

_XINPUT_DLL_NAMES = ("xinput1_4.dll", "xinput1_3.dll", "xinput9_1_0.dll")

_xinput = None
for _name in _XINPUT_DLL_NAMES:
    try:
        _xinput = ctypes.WinDLL(_name)
        break
    except OSError:
        continue

if _xinput is None:
    print("Could not load any XInput DLL. Is this really Windows with a controller driver installed?")
    sys.exit(1)


class XINPUT_GAMEPAD(ctypes.Structure):
    _fields_ = [
        ("wButtons", ctypes.c_ushort),
        ("bLeftTrigger", ctypes.c_ubyte),
        ("bRightTrigger", ctypes.c_ubyte),
        ("sThumbLX", ctypes.c_short),
        ("sThumbLY", ctypes.c_short),
        ("sThumbRX", ctypes.c_short),
        ("sThumbRY", ctypes.c_short),
    ]


class XINPUT_STATE(ctypes.Structure):
    _fields_ = [
        ("dwPacketNumber", ctypes.c_ulong),
        ("Gamepad", XINPUT_GAMEPAD),
    ]


class XINPUT_VIBRATION(ctypes.Structure):
    _fields_ = [
        ("wLeftMotorSpeed", ctypes.c_ushort),
        ("wRightMotorSpeed", ctypes.c_ushort),
    ]


_xinput.XInputGetState.argtypes = [ctypes.c_ulong, ctypes.POINTER(XINPUT_STATE)]
_xinput.XInputGetState.restype = ctypes.c_ulong
_xinput.XInputSetState.argtypes = [ctypes.c_ulong, ctypes.POINTER(XINPUT_VIBRATION)]
_xinput.XInputSetState.restype = ctypes.c_ulong

ERROR_SUCCESS = 0

XINPUT_GAMEPAD_DPAD_UP = 0x0001
XINPUT_GAMEPAD_DPAD_DOWN = 0x0002
XINPUT_GAMEPAD_DPAD_LEFT = 0x0004
XINPUT_GAMEPAD_DPAD_RIGHT = 0x0008
XINPUT_GAMEPAD_START = 0x0010
XINPUT_GAMEPAD_BACK = 0x0020
XINPUT_GAMEPAD_A = 0x1000
XINPUT_GAMEPAD_B = 0x2000
XINPUT_GAMEPAD_X = 0x4000
XINPUT_GAMEPAD_Y = 0x8000

LEFT_THUMB_DEADZONE = 7849
TRIGGER_THRESHOLD = 30

# --------------------------------------------------------------------------
# Small helper functions (called from inside run(), kept outside it only
# because they're pure utilities with no game state of their own)
# --------------------------------------------------------------------------


def poll_controller(user_index, state_struct):
    """Read the current XInput state. Returns a plain dict - easy to use
    inline inside run() without needing a class."""
    ctypes.memset(ctypes.byref(state_struct), 0, ctypes.sizeof(state_struct))
    ret = _xinput.XInputGetState(user_index, ctypes.byref(state_struct))

    if ret != ERROR_SUCCESS:
        return {
            "connected": False, "buttons": 0,
            "stick_x": 0.0, "stick_y": 0.0,
            "left_trigger": 0.0, "right_trigger": 0.0,
        }

    pad = state_struct.Gamepad
    lx, ly = pad.sThumbLX, pad.sThumbLY
    magnitude = (lx * lx + ly * ly) ** 0.5
    if magnitude < LEFT_THUMB_DEADZONE:
        stick_x, stick_y = 0.0, 0.0
    else:
        stick_x = max(-1.0, min(1.0, lx / 32767.0))
        stick_y = max(-1.0, min(1.0, ly / 32767.0))  # positive = stick pushed up

    rt, lt = pad.bRightTrigger, pad.bLeftTrigger
    right_trigger = 0.0 if rt < TRIGGER_THRESHOLD else (rt - TRIGGER_THRESHOLD) / (255 - TRIGGER_THRESHOLD)
    left_trigger = 0.0 if lt < TRIGGER_THRESHOLD else (lt - TRIGGER_THRESHOLD) / (255 - TRIGGER_THRESHOLD)

    return {
        "connected": True, "buttons": pad.wButtons,
        "stick_x": stick_x, "stick_y": stick_y,
        "left_trigger": left_trigger, "right_trigger": right_trigger,
    }


def set_vibration(user_index, left, right):
    vib = XINPUT_VIBRATION()
    vib.wLeftMotorSpeed = int(max(0.0, min(1.0, left)) * 65535)
    vib.wRightMotorSpeed = int(max(0.0, min(1.0, right)) * 65535)
    _xinput.XInputSetState(user_index, ctypes.byref(vib))


def find_asset(filename):
    """Search a small set of sensible folders for an asset file, without
    ever hardcoding a specific user's path or username."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    home = os.path.expanduser("~")
    candidates = [
        os.path.join(script_dir, "assets"),
        os.path.join(script_dir, "xboxos", "assets"),
        script_dir,
        os.getcwd(),
        os.path.join(home, "xboxos", "assets"),   # e.g. C:\Users\<you>\xboxos\assets
        os.path.join(home, "assets"),
        home,
        os.path.join(home, "Desktop"),
        os.path.join(home, "Downloads"),
    ]
    for folder in candidates:
        path = os.path.join(folder, filename)
        if os.path.isfile(path):
            return path
    searched = "\n  ".join(candidates)
    raise FileNotFoundError(
        f"Could not find '{filename}'. Searched:\n  {searched}\n"
        f"Put the image in one of those folders (e.g. your xboxos\\assets folder)."
    )


def load_high_score(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return float(data.get("high_score", 0.0))
    except (OSError, ValueError, json.JSONDecodeError):
        return 0.0


def save_high_score(path, value):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"high_score": value}, f)
    except OSError:
        pass  # not worth crashing the game over a failed save


def show_controls_screen(screen, clock, user_index, xinput_state, font_big, font_med, font_small):
    """A dedicated 'window' listing every control. Blocks until the
    player dismisses it, then hands control back to run()."""
    width, height = screen.get_size()
    rows = [
        ("Left Stick Y / D-Pad Up-Down", "Steer up / down"),
        ("RT (Right Trigger)", "Boost (drains a meter, recharges over time)"),
        ("LT (Left Trigger)", "Brake"),
        ("START", "Pause / Resume"),
        ("A", "Restart after a crash / Resume from pause"),
        ("B", "Exit the game (works anywhere)"),
        ("Y", "Open this controls screen"),
        ("Keyboard fallback", "Arrows/W-S steer, Shift boost, Ctrl brake, Enter/Space=A, Esc=exit"),
    ]

    waiting = True
    while waiting:
        clock.tick(60)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit(0)
            elif event.type == pygame.KEYDOWN:
                waiting = False

        pad = poll_controller(user_index, xinput_state)
        if pad["connected"] and (pad["buttons"] & (
            XINPUT_GAMEPAD_A | XINPUT_GAMEPAD_B | XINPUT_GAMEPAD_Y |
            XINPUT_GAMEPAD_START | XINPUT_GAMEPAD_BACK
        )):
            waiting = False

        screen.fill((14, 14, 20))

        title = font_big.render("CONTROLS", True, (250, 210, 60))
        screen.blit(title, title.get_rect(center=(width // 2, 70)))

        row_y = 150
        for control, description in rows:
            control_text = font_med.render(control, True, (90, 220, 230))
            screen.blit(control_text, (width * 0.08, row_y))
            desc_text = font_small.render(description, True, (235, 235, 235))
            screen.blit(desc_text, (width * 0.08, row_y + 32))
            row_y += 62

        hint = font_small.render("Press any button or key to continue", True, (140, 140, 140))
        screen.blit(hint, hint.get_rect(center=(width // 2, height - 40)))

        pygame.display.flip()


# --------------------------------------------------------------------------
# Constants
# --------------------------------------------------------------------------

SCREEN_WIDTH = 960
SCREEN_HEIGHT = 540
FPS = 60

BASE_SCROLL_SPEED = 300.0
BOOST_SCROLL_SPEED = 620.0
BRAKE_SCROLL_SPEED = 140.0
STEER_SPEED = 380.0

ROTATE_PLAYER_DEGREES = 0
ROTATE_ENEMY_DEGREES = 0

TILT_MAX_DEGREES = 19.0
TILT_RESPONSIVENESS = 9.0

# Player's on-screen x position now actually moves with accel/brake,
# easing between these three marks instead of sitting fixed.
PLAYER_HOME_X_FRAC = 0.18
PLAYER_MAX_X_FRAC = 0.40   # eases toward this while boosting
PLAYER_MIN_X_FRAC = 0.08   # eases toward this while braking
PLAYER_X_RESPONSIVENESS = 5.0

BOOST_METER_MAX = 100.0
BOOST_DRAIN_PER_SEC = 55.0
BOOST_REGEN_PER_SEC = 28.0

NEAR_MISS_BONUS = 50
NEAR_MISS_MARGIN = 34  # extra pixels around the player's hitbox that counts as "close"

TRAIL_SPAWN_INTERVAL = 0.035
TRAIL_LIFETIME = 0.35

ENEMY_MIN_INTERVAL = 0.55
ENEMY_MAX_INTERVAL = 1.35

COUNTDOWN_SECONDS = 3.0

WHITE = (255, 255, 255)
BLACK = (10, 10, 10)
RED = (220, 40, 40)
YELLOW = (250, 210, 60)
GREEN = (60, 200, 100)
CYAN = (90, 220, 230)
ORANGE = (240, 150, 60)


# --------------------------------------------------------------------------
# The whole game
# --------------------------------------------------------------------------

def run():
    # ---- pygame + window setup ----
    pygame.init()
    pygame.display.set_caption("XInput Racing")
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    clock = pygame.time.Clock()

    font_huge = pygame.font.SysFont("consolas", 72, bold=True)
    font_big = pygame.font.SysFont("consolas", 46, bold=True)
    font_med = pygame.font.SysFont("consolas", 26, bold=True)
    font_small = pygame.font.SysFont("consolas", 18)

    # ---- load + scale assets ----
    try:
        bg_raw = pygame.image.load(find_asset("background.png")).convert()
        car_raw = pygame.image.load(find_asset("Car.png")).convert_alpha()
        enemy_raw = pygame.image.load(find_asset("EnemyCAR.png")).convert_alpha()
    except FileNotFoundError as e:
        print(str(e))
        input("Press Enter to close...")
        pygame.quit()
        return

    bg_image = pygame.transform.smoothscale(bg_raw, (SCREEN_WIDTH, SCREEN_HEIGHT))
    bg_width = bg_image.get_width()

    car_base_w = int(SCREEN_HEIGHT * 0.16)
    car_base_h = int(car_base_w * (car_raw.get_height() / car_raw.get_width()))
    car_image = pygame.transform.smoothscale(car_raw, (car_base_w, car_base_h))
    car_facing_ref = pygame.transform.rotate(car_image, ROTATE_PLAYER_DEGREES)
    car_disp_w, car_disp_h = car_facing_ref.get_size()

    enemy_base_w = int(SCREEN_HEIGHT * 0.16)
    enemy_base_h = int(enemy_base_w * (enemy_raw.get_height() / enemy_raw.get_width()))
    enemy_scaled = pygame.transform.smoothscale(enemy_raw, (enemy_base_w, enemy_base_h))
    enemy_image = pygame.transform.rotate(enemy_scaled, ROTATE_ENEMY_DEGREES)
    enemy_disp_w, enemy_disp_h = enemy_image.get_size()

    # ---- persistent high score ----
    highscore_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "xinput_racing_highscore.json")
    high_score = load_high_score(highscore_path)

    # ---- XInput state (reused every frame to avoid reallocating) ----
    user_index = 0
    xinput_state = XINPUT_STATE()
    rumble_until = 0.0

    world_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))

    player_home_x = SCREEN_WIDTH * PLAYER_HOME_X_FRAC
    player_min_x = SCREEN_WIDTH * PLAYER_MIN_X_FRAC
    player_max_x = SCREEN_WIDTH * PLAYER_MAX_X_FRAC
    player_y_home = SCREEN_HEIGHT // 2

    def reset_round():
        player_rect = pygame.Rect(0, 0, car_disp_w, car_disp_h)
        player_rect.center = (int(player_home_x), player_y_home)
        player_hit = player_rect.inflate(-car_disp_w * 0.22, -car_disp_h * 0.30)
        return {
            "bg_x1": 0.0,
            "bg_x2": -bg_width,
            "player_x": player_home_x,   # float, eased toward a target each frame
            "player_rect": player_rect,
            "player_hit": player_hit,
            "tilt": 0.0,
            "boost_meter": BOOST_METER_MAX,
            "trail": [],               # list of {"pos": (x, y), "age": 0.0}
            "trail_timer": 0.0,
            "popups": [],              # list of {"text", "pos", "timer", "color"}
            "enemies": [],
            "score": 0.0,
            "distance": 0.0,
            "time_to_next_spawn": 0.8,
            "game_over": False,
            "paused": False,
            "crash_flash_timer": 0.0,
            "shake_timer": 0.0,
            "countdown": COUNTDOWN_SECONDS,
            "new_high_score": False,
        }

    state = reset_round()

    # Show the controls screen once before the first round starts.
    show_controls_screen(screen, clock, user_index, xinput_state, font_big, font_med, font_small)

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0
        dt = min(dt, 0.05)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_F1:
                show_controls_screen(screen, clock, user_index, xinput_state, font_big, font_med, font_small)

        pad = poll_controller(user_index, xinput_state)

        if rumble_until and time.time() >= rumble_until:
            set_vibration(user_index, 0.0, 0.0)
            rumble_until = 0.0

        if pad["connected"] and (pad["buttons"] & XINPUT_GAMEPAD_B):
            running = False
            break

        keys = pygame.key.get_pressed()
        start_pressed = pad["connected"] and (pad["buttons"] & XINPUT_GAMEPAD_START)
        a_pressed = (pad["connected"] and (pad["buttons"] & XINPUT_GAMEPAD_A)) or keys[pygame.K_RETURN] or keys[pygame.K_SPACE]
        y_pressed = (pad["connected"] and (pad["buttons"] & XINPUT_GAMEPAD_Y))

        if y_pressed and not state.get("_y_was_down", False):
            show_controls_screen(screen, clock, user_index, xinput_state, font_big, font_med, font_small)
            state["_y_was_down"] = True
            continue
        state["_y_was_down"] = y_pressed

        if state["countdown"] > 0:
            state["countdown"] -= dt
            if state["countdown"] < 0:
                state["countdown"] = 0

        elif state["game_over"]:
            if state["crash_flash_timer"] > 0:
                state["crash_flash_timer"] -= dt
            if state["shake_timer"] > 0:
                state["shake_timer"] -= dt

            if a_pressed:
                state = reset_round()

        elif start_pressed and not state.get("_start_was_down", False):
            state["paused"] = not state["paused"]

        elif state["paused"]:
            if a_pressed:
                state["paused"] = False

        else:
            # ---- normal gameplay tick ----

            steer_dy = 0.0
            if pad["connected"]:
                if abs(pad["stick_y"]) > 0.001:
                    steer_dy = pad["stick_y"]
                elif pad["buttons"] & XINPUT_GAMEPAD_DPAD_UP:
                    steer_dy = 1.0
                elif pad["buttons"] & XINPUT_GAMEPAD_DPAD_DOWN:
                    steer_dy = -1.0
            if keys[pygame.K_UP] or keys[pygame.K_w]:
                steer_dy = 1.0
            elif keys[pygame.K_DOWN] or keys[pygame.K_s]:
                steer_dy = -1.0

            boost_held = pad["right_trigger"] if pad["connected"] else (1.0 if keys[pygame.K_LSHIFT] else 0.0)
            brake_amount = pad["left_trigger"] if pad["connected"] else (1.0 if keys[pygame.K_LCTRL] else 0.0)

            # boost is gated by the meter - no meter, no boost, until it recharges
            if boost_held > 0.02 and state["boost_meter"] > 0:
                boost_amount = boost_held
                state["boost_meter"] = max(0.0, state["boost_meter"] - BOOST_DRAIN_PER_SEC * boost_amount * dt)
            else:
                boost_amount = 0.0
                state["boost_meter"] = min(BOOST_METER_MAX, state["boost_meter"] + BOOST_REGEN_PER_SEC * dt)

            net = boost_amount - brake_amount

            # ---- the player now actually moves: ease toward a forward/back
            #      target position based on current accel/brake input ----
            if net >= 0:
                target_x = player_home_x + net * (player_max_x - player_home_x)
            else:
                target_x = player_home_x + net * (player_home_x - player_min_x)
            state["player_x"] += (target_x - state["player_x"]) * min(1.0, dt * PLAYER_X_RESPONSIVENESS)
            state["player_rect"].centerx = int(round(state["player_x"]))

            # vertical steering (lane changes)
            state["player_rect"].y -= int(steer_dy * STEER_SPEED * dt)
            half_h = state["player_rect"].height // 2
            state["player_rect"].y = max(half_h // 2, min(SCREEN_HEIGHT - half_h - half_h // 2, state["player_rect"].y))
            state["player_hit"].center = state["player_rect"].center

            target_tilt = steer_dy * TILT_MAX_DEGREES
            state["tilt"] += (target_tilt - state["tilt"]) * min(1.0, dt * TILT_RESPONSIVENESS)

            if net >= 0:
                scroll_speed = BASE_SCROLL_SPEED + (BOOST_SCROLL_SPEED - BASE_SCROLL_SPEED) * net
            else:
                scroll_speed = BASE_SCROLL_SPEED + (BASE_SCROLL_SPEED - BRAKE_SCROLL_SPEED) * net

            state["bg_x1"] -= scroll_speed * dt
            state["bg_x2"] -= scroll_speed * dt
            if state["bg_x1"] <= -bg_width:
                state["bg_x1"] = state["bg_x2"] + bg_width
            if state["bg_x2"] <= -bg_width:
                state["bg_x2"] = state["bg_x1"] + bg_width

            state["distance"] += scroll_speed * dt
            state["score"] += dt * (10.0 + boost_amount * 12.0)

            # ---- exhaust/speed trail while boosting ----
            state["trail_timer"] -= dt
            if boost_amount > 0.1 and state["trail_timer"] <= 0:
                tail_x = state["player_rect"].left
                tail_y = state["player_rect"].centery + random.randint(-6, 6)
                state["trail"].append({"pos": (tail_x, tail_y), "age": 0.0})
                state["trail_timer"] = TRAIL_SPAWN_INTERVAL
            for particle in state["trail"]:
                particle["age"] += dt
                particle["pos"] = (particle["pos"][0] - scroll_speed * dt, particle["pos"][1])
            state["trail"] = [p for p in state["trail"] if p["age"] < TRAIL_LIFETIME]

            # ---- popups (near-miss bonus text etc.) ----
            for popup in state["popups"]:
                popup["timer"] -= dt
                popup["pos"] = (popup["pos"][0], popup["pos"][1] - 40 * dt)
            state["popups"] = [p for p in state["popups"] if p["timer"] > 0]

            # ---- enemy spawning ----
            state["time_to_next_spawn"] -= dt
            if state["time_to_next_spawn"] <= 0:
                margin = enemy_disp_h
                y = random.randint(margin, SCREEN_HEIGHT - margin)
                x = SCREEN_WIDTH + enemy_disp_w
                speed = scroll_speed * random.uniform(0.8, 1.5)
                rect = enemy_image.get_rect(center=(x, y))
                hit = rect.inflate(-rect.width * 0.22, -rect.height * 0.30)
                state["enemies"].append({"rect": rect, "hit": hit, "speed": speed, "near_miss_awarded": False})

                difficulty = min(state["score"] / 3000.0, 1.0)
                low = ENEMY_MIN_INTERVAL - difficulty * 0.30
                high = ENEMY_MAX_INTERVAL - difficulty * 0.65
                state["time_to_next_spawn"] = random.uniform(max(0.22, low), max(0.35, high))

            # ---- enemy movement + cleanup ----
            for enemy in state["enemies"]:
                enemy["rect"].x -= int(enemy["speed"] * dt)
                enemy["hit"].center = enemy["rect"].center
            state["enemies"] = [e for e in state["enemies"] if e["rect"].right >= 0]

            # ---- near-miss bonus + crash detection ----
            player_near_zone = state["player_hit"].inflate(NEAR_MISS_MARGIN * 2, NEAR_MISS_MARGIN * 2)
            crashed = False
            for enemy in state["enemies"]:
                if state["player_hit"].colliderect(enemy["hit"]):
                    crashed = True
                    break
                if not enemy["near_miss_awarded"] and player_near_zone.colliderect(enemy["hit"]):
                    enemy["near_miss_awarded"] = True
                    state["score"] += NEAR_MISS_BONUS
                    state["popups"].append({
                        "text": f"NICE! +{NEAR_MISS_BONUS}",
                        "pos": (state["player_rect"].centerx, state["player_rect"].top - 10),
                        "timer": 0.8,
                        "color": GREEN,
                    })

            if crashed:
                state["game_over"] = True
                state["crash_flash_timer"] = 0.35
                state["shake_timer"] = 0.30
                if state["score"] > high_score:
                    high_score = state["score"]
                    state["new_high_score"] = True
                    save_high_score(highscore_path, high_score)
                if pad["connected"]:
                    set_vibration(user_index, 1.0, 1.0)
                    rumble_until = time.time() + 0.6

        state["_start_was_down"] = start_pressed

        # ------------------------------------------------------------
        # Drawing
        # ------------------------------------------------------------

        world_surface.blit(bg_image, (state["bg_x1"], 0))
        world_surface.blit(bg_image, (state["bg_x2"], 0))

        for particle in state["trail"]:
            fade = max(0.0, 1.0 - particle["age"] / TRAIL_LIFETIME)
            radius = max(1, int(6 * fade))
            trail_surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(trail_surf, (*ORANGE, int(180 * fade)), (radius, radius), radius)
            world_surface.blit(trail_surf, (particle["pos"][0] - radius, particle["pos"][1] - radius))

        for enemy in state["enemies"]:
            world_surface.blit(enemy_image, enemy["rect"])

        rotated_car = pygame.transform.rotate(car_image, ROTATE_PLAYER_DEGREES + state["tilt"])
        rotated_rect = rotated_car.get_rect(center=state["player_rect"].center)
        world_surface.blit(rotated_car, rotated_rect)

        for popup in state["popups"]:
            fade = max(0.0, min(1.0, popup["timer"] / 0.8))
            popup_text = font_small.render(popup["text"], True, popup["color"])
            popup_text.set_alpha(int(255 * fade))
            world_surface.blit(popup_text, popup_text.get_rect(center=popup["pos"]))

        if state["crash_flash_timer"] > 0:
            flash = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            flash.fill(RED)
            flash.set_alpha(int(140 * (state["crash_flash_timer"] / 0.35)))
            world_surface.blit(flash, (0, 0))

        shake_x, shake_y = 0, 0
        if state["shake_timer"] > 0:
            strength = int(10 * (state["shake_timer"] / 0.30))
            shake_x = random.randint(-strength, strength)
            shake_y = random.randint(-strength, strength)

        screen.fill(BLACK)
        screen.blit(world_surface, (shake_x, shake_y))

        # -- HUD (never shakes) --
        score_text = font_med.render(f"SCORE {int(state['score']):06d}", True, WHITE)
        screen.blit(score_text, (14, 12))

        high_text = font_small.render(f"BEST {int(high_score):06d}", True, CYAN)
        screen.blit(high_text, (14, 44))

        # boost meter bar
        bar_x, bar_y, bar_w, bar_h = 14, 68, 160, 14
        pygame.draw.rect(screen, (60, 60, 60), (bar_x, bar_y, bar_w, bar_h), border_radius=4)
        fill_w = int(bar_w * (state["boost_meter"] / BOOST_METER_MAX))
        bar_color = ORANGE if state["boost_meter"] > 20 else RED
        if fill_w > 0:
            pygame.draw.rect(screen, bar_color, (bar_x, bar_y, fill_w, bar_h), border_radius=4)
        pygame.draw.rect(screen, WHITE, (bar_x, bar_y, bar_w, bar_h), width=1, border_radius=4)
        boost_label = font_small.render("BOOST", True, WHITE)
        screen.blit(boost_label, (bar_x + bar_w + 10, bar_y - 3))

        controls_hint = font_small.render("Y = Controls", True, (150, 150, 150))
        screen.blit(controls_hint, (SCREEN_WIDTH - controls_hint.get_width() - 14, 14))

        if not pad["connected"]:
            hint = font_small.render(
                "No Xbox controller detected - keyboard: arrows/W-S, Shift=boost, Ctrl=brake, F1=controls, Esc=exit",
                True, YELLOW,
            )
            hint_bg = pygame.Surface((hint.get_width() + 16, hint.get_height() + 10))
            hint_bg.fill(BLACK)
            hint_bg.set_alpha(180)
            screen.blit(hint_bg, (8, SCREEN_HEIGHT - hint.get_height() - 18))
            screen.blit(hint, (16, SCREEN_HEIGHT - hint.get_height() - 13))

        if state["countdown"] > 0:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            overlay.fill(BLACK)
            overlay.set_alpha(110)
            screen.blit(overlay, (0, 0))

            remaining = state["countdown"]
            label = "GO!" if remaining < 1.0 else str(int(remaining) + 1)
            color = GREEN if remaining < 1.0 else WHITE
            count_text = font_huge.render(label, True, color)
            screen.blit(count_text, count_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)))

        if state["paused"]:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            overlay.fill(BLACK)
            overlay.set_alpha(160)
            screen.blit(overlay, (0, 0))

            paused_text = font_big.render("PAUSED", True, WHITE)
            screen.blit(paused_text, paused_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 30)))

            resume_hint = font_small.render("START or A = Resume      Y = Controls      B = Exit", True, GREEN)
            screen.blit(resume_hint, resume_hint.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 20)))

        if state["game_over"]:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            overlay.fill(BLACK)
            overlay.set_alpha(170)
            screen.blit(overlay, (0, 0))

            title = font_big.render("CRASHED", True, RED)
            screen.blit(title, title.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 70)))

            score_line = font_med.render(f"Survival Score: {int(state['score'])}", True, WHITE)
            screen.blit(score_line, score_line.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 15)))

            if state["new_high_score"]:
                new_best = font_small.render("NEW HIGH SCORE!", True, YELLOW)
                screen.blit(new_best, new_best.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 20)))

            hint2 = font_small.render("A = Restart      B = Exit", True, GREEN)
            screen.blit(hint2, hint2.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 55)))

        pygame.display.flip()

    set_vibration(user_index, 0.0, 0.0)
    pygame.quit()


if __name__ == "__main__":
    run()