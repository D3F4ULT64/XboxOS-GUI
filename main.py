"""
XboxOS GUI Launcher
--------------------
A tile-based launcher for small pygame apps/games stored under ./apps
and ./apps/games. Click, arrow-key, or gamepad your way to an app and
press Enter / A / left-click to launch it.
"""

from __future__ import annotations

import importlib.util
import os
import sys
import traceback
from dataclasses import dataclass
from types import ModuleType

import pygame

# =============================================================
# Config
# =============================================================
WIDTH, HEIGHT = 900, 600
FPS = 60

BG_COLOR = (18, 18, 26)
TITLE_COLOR = (255, 255, 255)
SUBTITLE_COLOR = (150, 155, 170)
TILE_COLOR = (28, 32, 46)
TILE_HOVER_COLOR = (0, 120, 255)
TILE_FOCUS_BORDER = (0, 200, 255)
TILE_TEXT_COLOR = (235, 238, 245)
ERROR_COLOR = (255, 90, 90)

TILE_W, TILE_H = 260, 100
TILE_GAP_X, TILE_GAP_Y = 40, 28
GRID_COLS = 2
GRID_TOP = 140

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
APPS_DIR = os.path.join(BASE_DIR, "apps")
GAMES_DIR = os.path.join(APPS_DIR, "games")


@dataclass(frozen=True)
class App:
    key: str          # filename / lookup key
    label: str         # shown on the tile
    icon: str          # single glyph shown in the icon circle


APP_LIST: list[App] = [
    App("help", "Help", "?"),
    App("mouse", "Mouse", "M"),
    App("sound", "Sound", "S"),
    App("vibrate", "Vibrate", "V"),
    App("pong", "Pong", "P"),
    App("racing", "Racing", "R"),
]


# =============================================================
# App discovery / launching
# =============================================================
def find_app_file(key: str) -> str | None:
    """Look for `<key>.py` in the apps dir, then the games dir."""
    for folder in (APPS_DIR, GAMES_DIR):
        candidate = os.path.join(folder, key + ".py")
        if os.path.isfile(candidate):
            return candidate
    return None


def load_app_module(path: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location("xboxos_app", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load spec for {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def launch(key: str) -> str | None:
    """
    Launch the app for `key`. Returns an error message string on
    failure, or None on success, so the caller can show it without
    crashing the whole launcher.
    """
    path = find_app_file(key)
    if path is None:
        return f"App not found: {key}"

    try:
        module = load_app_module(path)
    except Exception:
        traceback.print_exc()
        return f"Failed to load '{key}': {sys.exc_info()[1]}"

    run_fn = getattr(module, "run", None)
    if not callable(run_fn):
        return f"'{key}' has no run() function"

    try:
        run_fn()
    except Exception:
        traceback.print_exc()
        return f"'{key}' crashed: {sys.exc_info()[1]}"
    finally:
        # An app may have resized the window, changed the caption,
        # grabbed the mouse, etc. Restore the launcher's own state
        # so the menu looks right when we get control back.
        pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("XboxOS")
        pygame.mouse.set_visible(True)
        pygame.event.get()  # drop any stale input from the app

    return None


# =============================================================
# Layout
# =============================================================
def build_grid(apps: list[App]) -> list[pygame.Rect]:
    """Compute tile rects for an arbitrary number of apps, centered
    horizontally, instead of hardcoding positions per index."""
    rows = (len(apps) + GRID_COLS - 1) // GRID_COLS
    grid_w = GRID_COLS * TILE_W + (GRID_COLS - 1) * TILE_GAP_X
    start_x = (WIDTH - grid_w) // 2

    rects = []
    for i in range(len(apps)):
        col = i % GRID_COLS
        row = i // GRID_COLS
        x = start_x + col * (TILE_W + TILE_GAP_X)
        y = GRID_TOP + row * (TILE_H + TILE_GAP_Y)
        rects.append(pygame.Rect(x, y, TILE_W, TILE_H))
    return rects, rows


# =============================================================
# Drawing
# =============================================================
def draw_tile(screen, font, icon_font, rect, app: App, hovered: bool, focused: bool):
    color = TILE_HOVER_COLOR if hovered else TILE_COLOR
    pygame.draw.rect(screen, color, rect, border_radius=16)
    if focused:
        pygame.draw.rect(screen, TILE_FOCUS_BORDER, rect, width=3, border_radius=16)

    # icon circle
    icon_r = rect.height // 2 - 14
    icon_center = (rect.x + icon_r + 14, rect.centery)
    pygame.draw.circle(screen, BG_COLOR, icon_center, icon_r)
    icon_surf = icon_font.render(app.icon, True, TILE_TEXT_COLOR)
    screen.blit(icon_surf, icon_surf.get_rect(center=icon_center))

    # label
    label_surf = font.render(app.label, True, TILE_TEXT_COLOR)
    label_x = icon_center[0] + icon_r + 18
    screen.blit(label_surf, (label_x, rect.centery - label_surf.get_height() // 2))


def draw_footer(screen, font, message: str, message_timer: int):
    hint = "Arrows + Enter or click a tile  •  Esc to quit"
    hint_surf = font.render(hint, True, SUBTITLE_COLOR)
    screen.blit(hint_surf, (WIDTH // 2 - hint_surf.get_width() // 2, HEIGHT - 40))

    if message and message_timer > 0:
        err_surf = font.render(message, True, ERROR_COLOR)
        screen.blit(err_surf, (WIDTH // 2 - err_surf.get_width() // 2, HEIGHT - 70))


# =============================================================
# Main loop
# =============================================================
def main():
    pygame.init()
    pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("XboxOS")

    title_font = pygame.font.SysFont(None, 60)
    subtitle_font = pygame.font.SysFont(None, 24)
    tile_font = pygame.font.SysFont(None, 32)
    icon_font = pygame.font.SysFont(None, 40, bold=True)

    clock = pygame.time.Clock()
    rects, _rows = build_grid(APP_LIST)

    focused_index = 0
    status_message = ""
    status_timer = 0

    joystick = None
    if pygame.joystick.get_count() > 0:
        joystick = pygame.joystick.Joystick(0)
        joystick.init()

    running = True
    while running:
        screen = pygame.display.get_surface()
        mouse_pos = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key in (pygame.K_RIGHT, pygame.K_d):
                    focused_index = (focused_index + 1) % len(APP_LIST)
                elif event.key in (pygame.K_LEFT, pygame.K_a):
                    focused_index = (focused_index - 1) % len(APP_LIST)
                elif event.key in (pygame.K_DOWN, pygame.K_s):
                    focused_index = (focused_index + GRID_COLS) % len(APP_LIST)
                elif event.key in (pygame.K_UP, pygame.K_w):
                    focused_index = (focused_index - GRID_COLS) % len(APP_LIST)
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    status_message = launch(APP_LIST[focused_index].key) or ""
                    status_timer = FPS * 3

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for i, rect in enumerate(rects):
                    if rect.collidepoint(event.pos):
                        focused_index = i
                        status_message = launch(APP_LIST[i].key) or ""
                        status_timer = FPS * 3

            elif event.type == pygame.JOYBUTTONDOWN and event.button == 0:  # A button
                status_message = launch(APP_LIST[focused_index].key) or ""
                status_timer = FPS * 3

            elif event.type == pygame.JOYHATMOTION:
                hx, hy = event.value
                if hx == 1:
                    focused_index = (focused_index + 1) % len(APP_LIST)
                elif hx == -1:
                    focused_index = (focused_index - 1) % len(APP_LIST)
                if hy == -1:
                    focused_index = (focused_index + GRID_COLS) % len(APP_LIST)
                elif hy == 1:
                    focused_index = (focused_index - GRID_COLS) % len(APP_LIST)

        # ---- draw ----
        screen.fill(BG_COLOR)

        title_surf = title_font.render("XboxOS", True, TITLE_COLOR)
        screen.blit(title_surf, (WIDTH // 2 - title_surf.get_width() // 2, 36))
        subtitle_surf = subtitle_font.render(
            "Select an app", True, SUBTITLE_COLOR
        )
        screen.blit(subtitle_surf, (WIDTH // 2 - subtitle_surf.get_width() // 2, 100))

        for i, (rect, app) in enumerate(zip(rects, APP_LIST)):
            hovered = rect.collidepoint(mouse_pos)
            draw_tile(screen, tile_font, icon_font, rect, app, hovered, i == focused_index)

        if status_timer > 0:
            status_timer -= 1
        draw_footer(screen, subtitle_font, status_message, status_timer)

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()


if __name__ == "__main__":
    main()