import pygame
import sys
import time
import argparse
import random
import math
import os
import logging
from datetime import datetime
from typing import Optional, List, Tuple

from src.engine.game import TriominoGame, TurnResult
from src.engine.rules import calculate_pass_penalty, calculate_draw_failure_penalty
from src.ai.strategies import get_strategy, AIStrategy, ScoredMove
from src.gui.assets import (
    Assets,
    DARK_BG,
    WHITE,
    BLACK,
    THEMES,
    BACKGROUNDS,
    HIGHLIGHT_COLOR,
    GRID_COLOR,
    UI_TOP,
    UI_TOP_ACCENT,
    UI_PANEL,
    UI_PANEL_LIGHT,
    UI_TEXT_MUTED,
    draw_gradient_background,
)
from src.gui.pygame_board import PygameBoard
from src.gui.sound_engine import get_sound_engine
from src.models import Player, PlacedTile, Triomino, GameBoard


# Constants
WIDTH, HEIGHT = 1100, 800
FPS = 60

# Hand Panel Layout
HAND_PANEL_HEIGHT = 200
HAND_START_X = 340
HAND_START_Y_OFFSET = 30
HAND_TILE_W = 60
HAND_TILE_H = 55
HAND_MARGIN_X = 12
HAND_MARGIN_Y = 10

# --- Helper Classes ---

class HumanStrategy(AIStrategy):
    """Marker class for human players in GUI."""
    def choose_move(self, player: Player, board: GameBoard) -> Optional[ScoredMove]:
        return None

class Button:
    def __init__(self, x, y, w, h, text, callback, color=(50, 50, 60), text_col=WHITE, active=True):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.callback = callback
        self.base_color = color
        self.text_col = text_col
        self.active = active
        self.hover = False

    def draw(self, surface, font):
        if not self.active: return
        
        # Ensure base_color is valid RGB tuple
        try:
            bc = self.base_color if isinstance(self.base_color, tuple) and len(self.base_color) >= 3 else (50, 50, 60)
            # Hover effect with clamping to valid range
            col = (min(255, bc[0]+30), min(255, bc[1]+30), min(255, bc[2]+30)) if self.hover else bc
        except (TypeError, IndexError):
            col = (80, 80, 90)
        
        # Shadow
        pygame.draw.rect(surface, (10, 10, 10), self.rect.move(2, 4), border_radius=8)
        # Main
        pygame.draw.rect(surface, col, self.rect, border_radius=8)
        # Outline
        pygame.draw.rect(surface, (100, 100, 120) if self.hover else (60, 60, 70), self.rect, 2, border_radius=8)
        
        txt_surf = font.render(self.text, True, self.text_col)
        surface.blit(txt_surf, txt_surf.get_rect(center=self.rect.center))

    def handle_event(self, event):
        if not self.active: return
        if event.type == pygame.MOUSEMOTION:
            self.hover = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.hover and event.button == 1:
                self.callback()


class InputBox:
    def __init__(self, x, y, w, h, text="", placeholder="", max_len=12):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.placeholder = placeholder
        self.max_len = max_len
        self.active = False

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.active = self.rect.collidepoint(event.pos)
        elif event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_RETURN:
                self.active = False
            elif event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            else:
                if len(self.text) < self.max_len and event.unicode.isprintable():
                    self.text += event.unicode

    def draw(self, surface, font):
        bg = UI_PANEL_LIGHT if self.active else UI_PANEL
        pygame.draw.rect(surface, bg, self.rect, border_radius=8)
        pygame.draw.rect(surface, HIGHLIGHT_COLOR if self.active else (80, 90, 110), self.rect, 2, border_radius=8)
        display_text = self.text if self.text else self.placeholder
        color = WHITE if self.text else UI_TEXT_MUTED
        txt = font.render(display_text, True, color)
        surface.blit(txt, txt.get_rect(midleft=(self.rect.x + 10, self.rect.centery)))

class Dropdown:
    def __init__(self, x, y, w, h, options, selected=None, color_previews=None):
        self.rect = pygame.Rect(x, y, w, h)
        self.options = options
        self.selected = selected or (options[0] if options else "")
        self.open = False
        # color_previews: dict mapping option name -> (color1, color2) for gradient-style preview
        self.color_previews = color_previews or {}

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.open = not self.open
                return None
            if self.open:
                for i, opt in enumerate(self.options):
                    opt_rect = pygame.Rect(
                        self.rect.x,
                        self.rect.y + (i + 1) * self.rect.height,
                        self.rect.width,
                        self.rect.height
                    )
                    if opt_rect.collidepoint(event.pos):
                        self.selected = opt
                        self.open = False
                        return opt
                self.open = False
        return None

    def _draw_color_preview(self, surface, x, y, radius, colors):
        """Draw a split circle with 2 colors (outer/inner or top/bottom)."""
        if len(colors) >= 2:
            # Draw outer color as ring, inner color as center
            pygame.draw.circle(surface, colors[0], (x, y), radius)
            pygame.draw.circle(surface, colors[1], (x, y), radius - 4)
        else:
            pygame.draw.circle(surface, colors[0], (x, y), radius)

    def draw(self, surface, font):
        pygame.draw.rect(surface, UI_PANEL, self.rect, border_radius=8)
        pygame.draw.rect(surface, UI_PANEL_LIGHT, self.rect, 2, border_radius=8)
        
        # Draw color preview for selected item
        if self.selected in self.color_previews:
            colors = self.color_previews[self.selected]
            self._draw_color_preview(surface, self.rect.x + 24, self.rect.centery, 10, colors)
            txt = font.render(self.selected, True, WHITE)
            surface.blit(txt, txt.get_rect(midleft=(self.rect.x + 42, self.rect.centery)))
        else:
            txt = font.render(self.selected, True, WHITE)
            surface.blit(txt, txt.get_rect(midleft=(self.rect.x + 12, self.rect.centery)))
        
        pygame.draw.polygon(surface, WHITE, [
            (self.rect.right - 18, self.rect.centery - 4),
            (self.rect.right - 8, self.rect.centery - 4),
            (self.rect.right - 13, self.rect.centery + 4),
        ])

        if self.open:
            mx, my = pygame.mouse.get_pos()
            for i, opt in enumerate(self.options):
                opt_rect = pygame.Rect(
                    self.rect.x,
                    self.rect.y + (i + 1) * self.rect.height,
                    self.rect.width,
                    self.rect.height
                )
                hovered = opt_rect.collidepoint((mx, my))
                pygame.draw.rect(surface, UI_PANEL_LIGHT if hovered else UI_PANEL, opt_rect, border_radius=6)
                pygame.draw.rect(surface, (70, 80, 100), opt_rect, 1, border_radius=6)
                
                # Draw color preview if available
                if opt in self.color_previews:
                    colors = self.color_previews[opt]
                    self._draw_color_preview(surface, opt_rect.x + 24, opt_rect.centery, 10, colors)
                    opt_txt = font.render(opt, True, WHITE)
                    surface.blit(opt_txt, opt_txt.get_rect(midleft=(opt_rect.x + 42, opt_rect.centery)))
                else:
                    opt_txt = font.render(opt, True, WHITE)
                    surface.blit(opt_txt, opt_txt.get_rect(midleft=(opt_rect.x + 12, opt_rect.centery)))

# --- Main Application ---

class TriominoApp:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Triominó")
        self.clock = pygame.time.Clock()
        self.assets = Assets()
        self._setup_logging()
        
        # State Management
        self.scene = "MENU" # MENU, GAME
        self.is_fullscreen = False
        self.fullscreen_variant = "standard"  # standard, clean
        self.terminal_mode = False
        
        # Global Settings
        self.selected_theme = "Classic"
        self.player_colors = THEMES[self.selected_theme]
        
        self.selected_bg_name = "Ocean"
        self.bg_gradient = BACKGROUNDS[self.selected_bg_name]  # Now a tuple (outer, inner)
        self.dynamic_bg_enabled = True
        self.dynamic_bg_intensity = 0.18
        self.dynamic_bg_speed = 1.2
        
        self.game_mode = "PvAI" # PvP, PvAI, AIvAI
        self.difficulty = "greedy"
        self.difficulty_labels = {
            "Greedy": "greedy",
            "Balanced": "balanced",
            "Defensive": "defensive",
            "Random": "random",
            "RL (Trained)": "rl",
        }
        
        # Sonic Mode State
        self.sonic_mode = False
        self.sonic_start_time = 0

        
        # Menu UI
        self.setup_menu_ui()
        
        # Game Objects (Init later)
        self.game = None
        self.board_view = None
        self.game_ui_buttons = []
        self.btn_quit = None
        
        # Game State
        self.selected_tile_idx = None
        self.valid_ghosts = []
        self.message = ""
        self.game_state = "TURN" 
        self.draws_made = 0
        
        # Training Mode State
        self.training_mode = False
        self.training_iterations = 10
        self.training_speed = 5  # 1-10 (1=slow, 10=instant)
        self._reset_bot_session_stats()
        
        self.logger.info("GUI initialized")

    def _truncate_text(self, text, font, max_width):
        if max_width <= 0:
            return ""
        if font.size(text)[0] <= max_width:
            return text
        suffix = "..."
        available = max_width - font.size(suffix)[0]
        if available <= 0:
            return suffix
        trimmed = text
        while trimmed and font.size(trimmed)[0] > available:
            trimmed = trimmed[:-1]
        return trimmed + suffix

    def _draw_text_outline(self, text, font, color, outline_color, center):
        base = font.render(text, True, color)
        outline = font.render(text, True, outline_color)
        cx, cy = center
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            self.screen.blit(outline, outline.get_rect(center=(cx + dx, cy + dy)))
        self.screen.blit(base, base.get_rect(center=center))

    def _setup_logging(self):
        os.makedirs("logs/gui", exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d-%H%M%S")
        log_path = os.path.join("logs", "gui", f"gui-{ts}.log")
        self.logger = logging.getLogger(f"triomino_gui_{ts}")
        self.logger.setLevel(logging.INFO)
        handler = logging.FileHandler(log_path, encoding="utf-8")
        formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.propagate = False

    def setup_menu_ui(self):
        cx = WIDTH // 2
        cy = HEIGHT // 2
        
        self.menu_buttons = []
        
        # Mode Selection
        self.menu_buttons.append(Button(cx - 300, 170, 180, 55, "HUMAN VS AI", lambda: self.set_mode("PvAI"), color=(0, 100, 200)))
        self.menu_buttons.append(Button(cx - 90, 170, 180, 55, "HUMAN VS HUMAN", lambda: self.set_mode("PvP"), color=(200, 100, 0)))
        self.menu_buttons.append(Button(cx + 120, 170, 180, 55, "BOT VS BOT", lambda: self.set_mode("AIvAI"), color=(100, 100, 100)))
        self.menu_buttons.append(Button(cx, 240, 180, 40, "🎵 SONIC MODE", lambda: self.set_mode("SONIC"), color=(150, 50, 150)))


        # Name inputs
        self.input_p1 = InputBox(cx - 260, 330, 220, 44, text="Player 1", placeholder="Player 1")
        self.input_p2 = InputBox(cx + 40, 330, 220, 44, text="Player 2", placeholder="Player 2")
        
        # Training iterations input (shown when AIvAI selected)
        self.input_iterations = InputBox(cx - 90, 278, 180, 40, text="10", placeholder="Games", max_len=4)

        # Dropdowns with color previews
        self.dropdown_theme = Dropdown(cx - 260, 390, 220, 44, list(THEMES.keys()), self.selected_theme, color_previews=THEMES)
        self.dropdown_bg = Dropdown(cx + 40, 390, 220, 44, list(BACKGROUNDS.keys()), self.selected_bg_name, color_previews=BACKGROUNDS)
        self.dropdown_diff = Dropdown(cx - 110, 450, 220, 44, list(self.difficulty_labels.keys()), "Greedy")

        # Start
        self.btn_start = Button(cx - 120, 530, 240, 70, "START GAME", self.start_game, color=(50, 150, 50))
        self.menu_buttons.append(self.btn_start)
        
        # Training Button
        self.btn_train = Button(cx - 120, 620, 240, 50, "🧠 Train RL Agent", self.launch_training, color=(80, 50, 120))
        self.menu_buttons.append(self.btn_train)

    def set_mode(self, mode):
        self.game_mode = mode
        self.logger.info("Mode set: %s", mode)

    def set_theme(self, theme_name):
        self.selected_theme = theme_name
        self.player_colors = THEMES[theme_name]
        self.logger.info("Theme set: %s", theme_name)
        
    def set_bg(self, bg_name):
        self.selected_bg_name = bg_name
        self.bg_gradient = BACKGROUNDS[bg_name]  # Gradient tuple (outer, inner)
        self.logger.info("Background set: %s", bg_name)

    def _is_clean_fullscreen(self) -> bool:
        return self.is_fullscreen and self.fullscreen_variant == "clean"

    def _ui_text_color(self):
        return (160, 255, 160) if self.terminal_mode else WHITE

    def _ui_muted_color(self):
        return (90, 180, 90) if self.terminal_mode else UI_TEXT_MUTED

    def _ui_highlight_color(self):
        return (120, 255, 120) if self.terminal_mode else HIGHLIGHT_COLOR

    def _ui_panel_color(self):
        return (8, 18, 8) if self.terminal_mode else (25, 25, 35)

    def _ui_panel_line_color(self):
        return (28, 90, 28) if self.terminal_mode else (50, 50, 60)

    def _display_player_colors(self):
        if self.terminal_mode:
            return [(110, 255, 110), (45, 190, 80)]
        return self.player_colors

    def _terminal_bg_gradient(self):
        now = pygame.time.get_ticks() / 1000.0
        pulse = (math.sin(now * 1.2) + 1.0) * 0.5
        outer = (0, 5, 0)
        inner = (
            8,
            int(36 + 24 * pulse),
            8,
        )
        return outer, inner

    def set_fullscreen(self, enabled: bool, variant: str = "standard"):
        self.is_fullscreen = enabled
        self.fullscreen_variant = variant if enabled else "standard"
        flags = pygame.FULLSCREEN if enabled else 0
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT), flags)
        if self.board_view:
            self.board_view.surface = self.screen
        if enabled:
            self.logger.info("Fullscreen: ON (%s)", self.fullscreen_variant)
        else:
            self.logger.info("Fullscreen: OFF")

    def toggle_fullscreen(self, variant: str = "standard"):
        if self.is_fullscreen and self.fullscreen_variant == variant:
            self.set_fullscreen(False)
            return
        self.set_fullscreen(True, variant)

    def _menu_input_active(self) -> bool:
        if self.scene != "MENU":
            return False
        if self.input_p1.active or self.input_p2.active:
            return True
        if self.game_mode == "AIvAI" and self.input_iterations.active:
            return True
        return False

    def _reset_bot_session_stats(self):
        self.training_current = 0
        self.training_stats = {
            "p1_wins": 0,
            "p2_wins": 0,
            "draws": 0,
            "total_games": 0,
            "p1_total_score": 0,
            "p2_total_score": 0,
        }

    def _is_ai_music_mode(self) -> bool:
        return self.game_mode in ("AIvAI", "SONIC")

    def cycle_background(self, direction: int = 1) -> str:
        names = list(BACKGROUNDS.keys())
        if not names:
            return self.selected_bg_name
        try:
            idx = names.index(self.selected_bg_name)
        except ValueError:
            idx = 0
        new_name = names[(idx + direction) % len(names)]
        self.set_bg(new_name)
        return new_name

    def _blend_rgb(self, color_a, color_b, t: float):
        clamped_t = max(0.0, min(1.0, t))
        return (
            int(color_a[0] + (color_b[0] - color_a[0]) * clamped_t),
            int(color_a[1] + (color_b[1] - color_a[1]) * clamped_t),
            int(color_a[2] + (color_b[2] - color_a[2]) * clamped_t),
        )

    def _animated_bg_gradient(self):
        if self.scene != "GAME" or not self._is_ai_music_mode() or not self.dynamic_bg_enabled:
            return self.bg_gradient
        now_sec = pygame.time.get_ticks() / 1000.0
        wave_outer = (math.sin(now_sec * self.dynamic_bg_speed) + 1.0) * 0.5
        wave_inner = (math.sin(now_sec * (self.dynamic_bg_speed * 0.7) + 1.7) + 1.0) * 0.5
        intensity = self.dynamic_bg_intensity
        outer = self._blend_rgb(self.bg_gradient[0], self.bg_gradient[1], wave_outer * intensity)
        inner = self._blend_rgb(self.bg_gradient[1], self.bg_gradient[0], wave_inner * intensity)
        return outer, inner

    def _apply_sound_controls(self, event):
        if event.type != pygame.KEYDOWN or not self._is_ai_music_mode():
            return

        sound_engine = get_sound_engine()
        if event.key in (pygame.K_UP, pygame.K_w):
            sound_engine.adjust_tempo(faster=True)
            self.message = f"Tempo: {sound_engine.base_bpm} BPM ({sound_engine.tempo_ms}ms)"
        elif event.key in (pygame.K_DOWN, pygame.K_s):
            sound_engine.adjust_tempo(faster=False)
            self.message = f"Tempo: {sound_engine.base_bpm} BPM ({sound_engine.tempo_ms}ms)"
        elif event.key in (pygame.K_LEFT, pygame.K_a):
            sound_engine.next_preset(-1)
            self.message = f"Timbre: {sound_engine.preset_name}"
        elif event.key in (pygame.K_RIGHT, pygame.K_d):
            sound_engine.next_preset(1)
            self.message = f"Timbre: {sound_engine.preset_name}"
        elif event.key == pygame.K_q:
            self.message = f"Background: {self.cycle_background(-1)}"
        elif event.key == pygame.K_e:
            self.message = f"Background: {self.cycle_background(1)}"
        elif event.key == pygame.K_b:
            self.dynamic_bg_enabled = not self.dynamic_bg_enabled
            self.message = f"Dynamic BG: {'ON' if self.dynamic_bg_enabled else 'OFF'}"
        elif event.key == pygame.K_m:
            sound_engine.toggle_mute()
            self.message = "Muted" if sound_engine.muted else f"Sound: {sound_engine.preset_name}"
        elif event.key == pygame.K_g and self.board_view:
            self.board_view.ghost_enabled = not self.board_view.ghost_enabled
            if not self.board_view.ghost_enabled:
                self.board_view.clear_ghosts()
            self.message = f"Ghost Trail: {'ON' if self.board_view.ghost_enabled else 'OFF'}"
        elif event.key == pygame.K_n and self.board_view:
            self.board_view.transparent_mode = not self.board_view.transparent_mode
            self.board_view.show_grid = self.board_view.transparent_mode
            self.board_view.tile_alpha = 180 if self.board_view.transparent_mode else 255
            self.message = f"Night Mode: {'ON' if self.board_view.transparent_mode else 'OFF'}"
        elif event.key == pygame.K_r and self.game_mode == "SONIC":
            sound_engine.reload_config()
            self.message = "Config reloaded"

    def _sound_shortcuts_text(self) -> str:
        text = "W/S tempo | A/D timbre | Q/E fondo | B dyn | M mute | G ghost | N night | T terminal"
        if self.game_mode == "SONIC":
            return f"{text} | R reload"
        return text

    def draw_ai_control_hud(self):
        if not self._is_ai_music_mode() or self._is_clean_fullscreen():
            return

        sound_engine = get_sound_engine()
        screen_w, screen_h = self.screen.get_size()
        compact = screen_w < 980 or screen_h < 720

        panel_w = screen_w - 24 if compact else min(560, screen_w - 24)
        panel_h = 78 if compact else 92
        panel_x = 12 if compact else screen_w - panel_w - 12
        panel_y = screen_h - panel_h - 58 if compact else 68

        panel_rect = pygame.Rect(panel_x, panel_y, panel_w, panel_h)
        panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        panel_color = (10, 25, 10, 215) if self.terminal_mode else (16, 20, 30, 205)
        border_color = (45, 140, 60) if self.terminal_mode else (90, 102, 120)
        panel.fill(panel_color)
        self.screen.blit(panel, panel_rect.topleft)
        pygame.draw.rect(self.screen, border_color, panel_rect, 1, border_radius=10)

        dyn = "ON" if self.dynamic_bg_enabled else "OFF"
        audio = "MUTED" if sound_engine.muted else "LIVE"
        status_1 = f"Tempo {sound_engine.base_bpm} BPM ({sound_engine.tempo_ms}ms) | Timbre: {sound_engine.preset_name}"
        status_2 = f"Background: {self.selected_bg_name} | Dynamic: {dyn} | Audio: {audio}"
        shortcuts = self._sound_shortcuts_text()
        max_w = panel_w - 14

        t1 = self.assets.font_small.render(self._truncate_text(status_1, self.assets.font_small, max_w), True, self._ui_text_color())
        t2 = self.assets.font_small.render(self._truncate_text(status_2, self.assets.font_small, max_w), True, self._ui_muted_color())
        t3 = self.assets.font_small.render(self._truncate_text(shortcuts, self.assets.font_small, max_w), True, self._ui_highlight_color())

        self.screen.blit(t1, (panel_x + 7, panel_y + 8))
        self.screen.blit(t2, (panel_x + 7, panel_y + 30))
        self.screen.blit(t3, (panel_x + 7, panel_y + 52))

    def draw_clean_score_hud(self):
        """Minimal score strip for clean fullscreen mode."""
        if not self.game:
            return

        p1 = self.game.players[0]
        p2 = self.game.players[1]
        display_cols = self._display_player_colors()
        p1_col = display_cols[0]
        p2_col = display_cols[1]
        p1_name = self._truncate_text(p1.name, self.assets.font_small, 120)
        p2_name = self._truncate_text(p2.name, self.assets.font_small, 120)

        screen_w, _ = self.screen.get_size()
        show_session_stats = self._is_ai_music_mode()
        panel_w = min(620, max(340, screen_w - 24))
        panel_h = 62 if show_session_stats else 42
        panel_x = (screen_w - panel_w) // 2
        panel_y = 10

        panel_rect = pygame.Rect(panel_x, panel_y, panel_w, panel_h)
        panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        panel_color = (8, 20, 8, 185) if self.terminal_mode else (14, 18, 28, 175)
        border_color = (45, 140, 60) if self.terminal_mode else (90, 102, 120)
        panel.fill(panel_color)
        self.screen.blit(panel, panel_rect.topleft)
        pygame.draw.rect(self.screen, border_color, panel_rect, 1, border_radius=10)

        p1_active = p1 == self.game.current_player
        p2_active = p2 == self.game.current_player
        left = f"{'>' if p1_active else ' '} {p1_name}: {p1.score}"
        right = f"{'>' if p2_active else ' '} {p2_name}: {p2.score}"
        left_txt = self.assets.font_small.render(left, True, p1_col)
        right_txt = self.assets.font_small.render(right, True, p2_col)
        pool_txt = self.assets.font_small.render(f"Pool {len(self.game.pool)}", True, self._ui_muted_color())

        if not show_session_stats:
            self.screen.blit(left_txt, left_txt.get_rect(midleft=(panel_x + 10, panel_y + panel_h // 2)))
            self.screen.blit(right_txt, right_txt.get_rect(midright=(panel_x + panel_w - 10, panel_y + panel_h // 2)))
            self.screen.blit(pool_txt, pool_txt.get_rect(center=(panel_x + panel_w // 2, panel_y + panel_h // 2)))
            return

        stats = self.training_stats
        left_acc = self.assets.font_small.render(
            f"W:{stats['p1_wins']} Total:{stats['p1_total_score']}",
            True,
            self._ui_muted_color(),
        )
        right_acc = self.assets.font_small.render(
            f"W:{stats['p2_wins']} Total:{stats['p2_total_score']}",
            True,
            self._ui_muted_color(),
        )
        center_acc = self.assets.font_small.render(
            f"Games:{stats['total_games']} Draws:{stats['draws']} | Pool {len(self.game.pool)}",
            True,
            self._ui_muted_color(),
        )

        self.screen.blit(left_txt, left_txt.get_rect(midleft=(panel_x + 10, panel_y + 20)))
        self.screen.blit(right_txt, right_txt.get_rect(midright=(panel_x + panel_w - 10, panel_y + 20)))
        self.screen.blit(left_acc, left_acc.get_rect(midleft=(panel_x + 10, panel_y + 44)))
        self.screen.blit(right_acc, right_acc.get_rect(midright=(panel_x + panel_w - 10, panel_y + 44)))
        self.screen.blit(center_acc, center_acc.get_rect(center=(panel_x + panel_w // 2, panel_y + 44)))

    def launch_training(self):
        """Launch RL training in a new terminal window."""
        import subprocess
        import shutil
        
        # Check if sb3-contrib is available
        try:
            import sb3_contrib
        except ImportError:
            self.message = "Install sb3-contrib first: pip install sb3-contrib"
            self.logger.warning("Training launch failed: sb3-contrib not installed")
            return
        
        # Get project root (where run.sh is)
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        script = "source venv/bin/activate && python3 -m src.rl.train"
        
        # Launch training in new terminal (macOS)
        if sys.platform == "darwin":
            cmd = f'tell app "Terminal" to do script "cd {project_root} && {script}"'
            subprocess.Popen(["osascript", "-e", cmd])
            self.message = "🧠 Training launched in Terminal!"
            self.logger.info("Launched RL training in new terminal")
        else:
            # Linux fallback
            if shutil.which("gnome-terminal"):
                subprocess.Popen(["gnome-terminal", "--", "bash", "-c", f"cd {project_root} && {script}; exec bash"])
            elif shutil.which("xterm"):
                subprocess.Popen(["xterm", "-e", f"cd {project_root} && {script}"])
            else:
                self.message = "No terminal emulator found"
                return
            self.message = "🧠 Training launched!"

    def start_game(self):
        # Configure Game based on Mode
        p1_name = self.input_p1.text.strip() or "Player 1"
        p2_name_input = self.input_p2.text.strip()
        p2_name = p2_name_input or "Player 2"
        strat1 = HumanStrategy()
        strat2 = HumanStrategy()
        self.training_mode = False
        self.sonic_mode = False
        if self.game_mode in ("AIvAI", "SONIC"):
            self._reset_bot_session_stats()
        
        if self.game_mode == "PvAI":
            p1_name = p1_name or "You"
            if self.difficulty == "rl":
                p2_name = p2_name_input or "Bot-RL"
            else:
                p2_name = p2_name_input or f"Bot-{self.difficulty.title()}"
            strat2 = get_strategy(self.difficulty)
        elif self.game_mode == "AIvAI":
            p1_name = p1_name or "Bot-Alpha"
            p2_name = p2_name_input or "Bot-Beta"
            strat1 = get_strategy("greedy")
            strat2 = get_strategy("greedy")
            # Parse iteration count for training
            try:
                self.training_iterations = max(1, int(self.input_iterations.text.strip()))
            except ValueError:
                self.training_iterations = 10
            self.training_mode = True
            self.logger.info("Training mode: %d iterations", self.training_iterations)
        elif self.game_mode == "SONIC":
            p1_name = "Sonic-Alpha"
            p2_name = "Sonic-Beta"
            strat1 = get_strategy("greedy")
            strat2 = get_strategy("greedy")
            self.sonic_mode = True
            self.sonic_start_time = pygame.time.get_ticks()
            self.logger.info("Sonic Mode Activated")


        # Init Engine
        self.game = TriominoGame(
            player_names=[p1_name, p2_name],
            strategies=[strat1, strat2],
            seed=random.randint(1, 10000)
        )
        self.game.setup_round()
        self.logger.info("Game start mode=%s p1=%s p2=%s theme=%s bg=%s",
                         self.game_mode, p1_name, p2_name, self.selected_theme, self.selected_bg_name)
        self.game.play_opening()
        self.game.next_player()
        
        # Init View
        self.board_view = PygameBoard(self.screen, self.assets)
        self.board_view.offset_x = 0
        self.board_view.center_camera(self.game.board, WIDTH, HEIGHT)
        
        if self.game_mode == "SONIC":
            self.board_view.transparent_mode = True
            self.board_view.show_grid = True # Night mode implies grid
            self.board_view.tile_alpha = 180
            self.board_view.ghost_enabled = True
        
        # GUI
        self.btn_draw = Button(40, HEIGHT - 150, 130, 50, "DRAW", self.action_draw, color=(204, 140, 60))
        self.btn_pass = Button(190, HEIGHT - 150, 130, 50, "PASS", self.action_pass, color=(160, 70, 70))
        self.btn_quit = Button(20, 12, 90, 36, "MENU", self.return_to_menu, color=(230, 180, 90), text_col=(40, 20, 10))
        self.btn_next = Button(WIDTH//2 - 120, HEIGHT//2 + 80, 240, 80, "START TURN", self.action_start_turn, color=(0, 120, 200))
        
        # Game Over Buttons
        self.btn_menu_return = Button(WIDTH//2 - 100, HEIGHT//2 + 80, 200, 60, "MAIN MENU", self.return_to_menu, color=(100, 50, 150))

        self.scene = "GAME"
        self.game_state = "TURN"
        self.message = "Your Turn! Select a tile."
        if self._is_ai_music_mode():
            sound_engine = get_sound_engine()
            self.message = f"Ready: {sound_engine.base_bpm} BPM | {sound_engine.preset_name}"
        
        # Check initial state for AI
        if not self.is_human_turn():
             self.game_state = "AI_THINK"

    def return_to_menu(self):
        if self.logger:
            self.logger.info("Return to menu")
        self.scene = "MENU"
        self.game = None
        self.game_state = "MENU" # Reset state
        self.board_view = None
        self.selected_tile_idx = None
        self.valid_ghosts = []
        self.draws_made = 0

    def _restart_aivai_game(self):
        """Quickly restart a new AIvAI game for infinite/training mode."""
        strat1 = get_strategy("greedy")
        strat2 = get_strategy("greedy")
        p1_name = self.game.players[0].name if self.game else "Bot-Alpha"
        p2_name = self.game.players[1].name if self.game else "Bot-Beta"
        
        self.game = TriominoGame(
            player_names=[p1_name, p2_name],
            strategies=[strat1, strat2],
            seed=random.randint(1, 10000)
        )
        self.game.setup_round()
        self.game.play_opening()
        self.game.next_player()
        
        self.board_view.center_camera(self.game.board, WIDTH, HEIGHT)
        self.game_state = "AI_THINK"
        self.selected_tile_idx = None
        self.valid_ghosts = []
        self.draws_made = 0
        if self.game_mode == "SONIC":
            self.sonic_start_time = pygame.time.get_ticks()

    # --- Game Actions ---
    def action_draw(self):
        if not self.is_human_turn(): return
        if self.game.can_player_move(self.game.current_player):
            self.message = "You must play if you can."
            return
        if self.draws_made >= 3:
            self.message = "Max draws (3) reached! You must Pass."
            return
        if len(self.game.pool) == 0:
            self.message = "Pool empty!"
            return
        
        self.game.execute_draw(self.game.current_player)
        self.draws_made += 1
        self.message = f"Tile drawn. {3 - self.draws_made} draw(s) left."
        self.selected_tile_idx = None
        self.valid_ghosts = []
        self.logger.info("Draw tile: player=%s draws_made=%s pool=%s",
                         self.game.current_player.name, self.draws_made, len(self.game.pool))

    def action_pass(self):
        if not self.is_human_turn(): return
        player = self.game.current_player
        can_play = self.game.can_player_move(player)
        if can_play:
            self.message = "You must play if you can."
            return
        # Rule: Must draw 3 times before passing, UNLESS pool is empty
        if self.draws_made < 3 and len(self.game.pool) > 0:
            self.message = f"Draw 3 times before passing! ({3 - self.draws_made} left)"
            return

        if self.draws_made > 0:
            points, _ = calculate_draw_failure_penalty(self.draws_made)
        else:
            points, _ = calculate_pass_penalty()
        player.add_score(points)
        self.message = f"Passed ({points} pts)"
        self.logger.info("Pass: player=%s points=%s draws_made=%s",
                         player.name, points, self.draws_made)
        self.end_turn_logic("Passed")

    def action_start_turn(self):
        self.game_state = "TURN"
        self.message = f"Your Turn! Select a tile."
        # Re-center on turn start
        self.board_view.center_camera(self.game.board, WIDTH, HEIGHT)
        self.logger.info("Start turn: player=%s", self.game.current_player.name)

    def is_human_turn(self):
        if not self.game: return False
        return isinstance(self.game.strategies[self.game.current_player_idx], HumanStrategy)

    def audio_feedback_click(self):
        """Placeholder for click sound."""
        pass

    def end_turn_logic(self, reason=""):
        self.selected_tile_idx = None
        self.valid_ghosts = []
        self.draws_made = 0
        self.board_view.center_camera(self.game.board, WIDTH, HEIGHT)
        
        winner = self.game.check_round_end()
        if winner:
            self.logger.info("Round end: winner=%s reason=%s scores=%s",
                             winner.winner.name, winner.reason, winner.final_scores)

            if self._is_ai_music_mode():
                if self.board_view.ghost_enabled:
                    self.board_view.add_ghost_snapshot(self.game.board)
                stats = self.training_stats
                if winner.winner == self.game.players[0]:
                    stats["p1_wins"] += 1
                elif winner.winner == self.game.players[1]:
                    stats["p2_wins"] += 1
                else:
                    stats["draws"] += 1
                stats["total_games"] += 1
                stats["p1_total_score"] += self.game.players[0].score
                stats["p2_total_score"] += self.game.players[1].score
            
            # Infinite mode for AIvAI: Auto-restart after a brief delay
            if self.game_mode == "AIvAI" and self.training_mode:
                self.training_current += 1
                
                # Check if more games to play (or infinite if 0)
                if self.training_iterations == 0 or self.training_current < self.training_iterations:
                    stats = self.training_stats
                    self.message = f"Game {stats['total_games']} | P1:{stats['p1_wins']}W {stats['p1_total_score']}pts | P2:{stats['p2_wins']}W {stats['p2_total_score']}pts"
                    # Auto-restart: Create new game
                    self._restart_aivai_game()
                    return
                else:
                    stats = self.training_stats
                    self.message = f"Complete! P1:{stats['p1_wins']}W {stats['p1_total_score']}pts | P2:{stats['p2_wins']}W {stats['p2_total_score']}pts"
            
            # Sonic Mode Infinite Loop
            if self.game_mode == "SONIC":
                # Instant restart for continuous flow
                stats = self.training_stats
                self.message = (
                    f"Game {stats['total_games']} | "
                    f"Wins P1:{stats['p1_wins']} P2:{stats['p2_wins']} | "
                    f"Total Pts P1:{stats['p1_total_score']} P2:{stats['p2_total_score']}"
                )
                self._restart_aivai_game()
                return

            self.game_state = "GAME_OVER"

            self.message = f"Winner: {winner.winner.name} ({reason})"
            return

        self.game.next_player()

        next_is_human = isinstance(self.game.strategies[self.game.current_player_idx], HumanStrategy)
        
        if self.game_mode == "PvP":
             self.game_state = "HOTSEAT_WAIT"
        elif self.game_mode == "PvAI":
            if next_is_human:
                self.game_state = "TURN"
                self.message = f"Your Turn! Select a tile."
            else:
                self.game_state = "AI_THINK"
        else: 
             self.game_state = "AI_THINK"

    # --- Loop ---
    def run(self):
        running = True
        while running:
            dt = self.clock.tick(FPS)
            events = pygame.event.get()
            
            for event in events:
                if event.type == pygame.QUIT:
                    running = False

                if event.type == pygame.KEYDOWN:
                    if not self._menu_input_active():
                        if event.key == pygame.K_t:
                            self.terminal_mode = not self.terminal_mode
                            state = "ON" if self.terminal_mode else "OFF"
                            self.message = f"Terminal mode: {state}"
                            self.logger.info("Terminal mode: %s", state)
                            continue
                        if event.key == pygame.K_z:
                            self.toggle_fullscreen("standard")
                            continue
                        if event.key == pygame.K_x:
                            self.toggle_fullscreen("clean")
                            continue
                    if event.key == pygame.K_ESCAPE and self.is_fullscreen:
                        self.set_fullscreen(False)
                        continue
                
                if self.scene == "MENU":
                    for btn in self.menu_buttons:
                        btn.handle_event(event)
                    self.input_p1.handle_event(event)
                    self.input_p2.handle_event(event)
                    
                    # Handle iteration input when AIvAI mode selected
                    if self.game_mode == "AIvAI":
                        self.input_iterations.handle_event(event)
                    
                    theme_sel = self.dropdown_theme.handle_event(event)
                    if theme_sel:
                        self.set_theme(theme_sel)
                    bg_sel = self.dropdown_bg.handle_event(event)
                    if bg_sel:
                        self.set_bg(bg_sel)
                    if self.game_mode == "PvAI":
                        diff_sel = self.dropdown_diff.handle_event(event)
                        if diff_sel:
                            self.difficulty = self.difficulty_labels.get(diff_sel, "greedy")
                            self.logger.info("Difficulty set: %s", self.difficulty)

                elif self.scene == "GAME":
                    # Global Inputs (Camera)
                    self.handle_game_input(event)
                    # AIvAI / SONIC shortcuts for tempo, timbre and visuals
                    self._apply_sound_controls(event)

                    
                    if self.btn_quit:
                        self.btn_quit.handle_event(event)
                    
                    if self.game_state == "TURN":
                        self.btn_draw.handle_event(event)
                        self.btn_pass.handle_event(event)
                        
                        # Hand scrolling could be added here purely via logic if needed
                        
                        if event.type == pygame.MOUSEBUTTONDOWN:
                             if event.button == 1: # Left Click
                                 if self.is_human_turn():
                                     self.handle_hand_click(event.pos)
                                     self.handle_board_click(event.pos)

                    elif self.game_state == "HOTSEAT_WAIT":
                         self.btn_next.handle_event(event)

                    elif self.game_state == "GAME_OVER":
                        self.btn_menu_return.handle_event(event)

            self.update_game_logic()
            self.draw()
            pygame.display.flip()
        
        pygame.quit()

    def update_game_logic(self):
        if self.scene == "GAME" and self.game:
            if self.game_state == "AI_THINK":
                # In AIvAI mode, use sound engine tempo for timing
                sound_engine = get_sound_engine() if self.game_mode in ["AIvAI", "SONIC"] else None
                delay_factor = 0.05  # Default
                if sound_engine and self.game_mode in ["AIvAI", "SONIC"]:
                    # Use exact tempo for SONIC mode
                    if self.game_mode == "SONIC":
                        now = pygame.time.get_ticks()
                        if now - self.sonic_start_time > sound_engine.tempo_ms:
                            self.sonic_start_time = now
                            delay_factor = 2.0 # Force move
                        else:
                            delay_factor = 0.0 # Wait
                    else:
                        # Convert tempo_ms to probability (higher tempo = more frequent moves)
                        delay_factor = 30 / max(sound_engine.tempo_ms, 100)

                
                if random.random() < delay_factor:
                    try:
                        turn_res = self.game.play_turn()
                        points = turn_res.points_earned
                        
                        # Play sound on tile placement (AIvAI only)
                        if self.game_mode in ["AIvAI", "SONIC"] and turn_res.tile_placed:
                            sound_engine.play_tile_sound(turn_res.tile_placed.values)

                        
                        # Better message
                        if points > 0:
                             self.message = f"AI played: {turn_res.message} (+{points} pts)"
                        else:
                             self.message = f"AI {turn_res.message}"
                        self.logger.info("AI turn: player=%s action=%s points=%s",
                                         turn_res.player.name, turn_res.action.value, points)
                        self.end_turn_logic()
                    except Exception as e:
                        print(f"AI Error: {e}")
                        self.message = "AI Error (See Console)"
                        self.game_state = "TURN" # Recover

    def draw(self):
        # Draw gradient background
        if self.terminal_mode:
            outer_bg, inner_bg = self._terminal_bg_gradient()
        else:
            outer_bg, inner_bg = self._animated_bg_gradient()
        draw_gradient_background(self.screen, outer_bg, inner_bg)
        
        if self.scene == "MENU":
            self.draw_menu()
        elif self.scene == "GAME":
            self.draw_game()

    def draw_menu(self):
        # Background Pattern
        # Title
        title_col = self._ui_text_color()
        shadow_col = (0, 40, 0) if self.terminal_mode else (0, 0, 0)
        highlight_col = self._ui_highlight_color()
        muted_col = self._ui_muted_color()
        title = self.assets.font_title.render("TRIOMINÓ", True, title_col)
        shadow = self.assets.font_title.render("TRIOMINÓ", True, shadow_col)
        cx = WIDTH // 2
        
        self.screen.blit(shadow, shadow.get_rect(center=(cx+4, 104)))
        self.screen.blit(title, title.get_rect(center=(cx, 100)))
        
        # Subtitle removed by request
        
        # Buttons
        for btn in self.menu_buttons:
            orig_btn_color = btn.base_color
            orig_txt_color = btn.text_col
            if self.terminal_mode:
                btn.base_color = (20, 50, 20)
                btn.text_col = self._ui_text_color()

            # Highlight Selected Mode
            if btn.text == "HUMAN VS AI" and self.game_mode == "PvAI":
                 pygame.draw.rect(self.screen, highlight_col, btn.rect.inflate(6,6), 3, 8)
            elif btn.text == "HUMAN VS HUMAN" and self.game_mode == "PvP":
                 pygame.draw.rect(self.screen, highlight_col, btn.rect.inflate(6,6), 3, 8)
            elif btn.text == "BOT VS BOT" and self.game_mode == "AIvAI":
                  pygame.draw.rect(self.screen, highlight_col, btn.rect.inflate(6,6), 3, 8)
            elif btn.text == "🎵 SONIC MODE" and self.game_mode == "SONIC":
                  pygame.draw.rect(self.screen, highlight_col, btn.rect.inflate(6,6), 3, 8)

            
            btn.draw(self.screen, self.assets.font_main)
            btn.base_color = orig_btn_color
            btn.text_col = orig_txt_color

        mode_label = {
            "PvAI": "Mode: Human vs AI",
            "PvP": "Mode: Human vs Human",
            "AIvAI": "Mode: Bot vs Bot",
            "SONIC": "Mode: Sonic Instrument (Infinite)"
        }.get(self.game_mode, "Mode")
        mode_txt = self.assets.font_small.render(mode_label, True, muted_col)
        mode_y = 255 if self.game_mode not in ["AIvAI", "SONIC"] else 235

        self.screen.blit(mode_txt, mode_txt.get_rect(center=(cx, mode_y)))

        # Training Options (only when AIvAI selected)
        if self.game_mode == "AIvAI":
            lbl = self.assets.font_small.render("Number of Games:", True, muted_col)
            self.screen.blit(lbl, lbl.get_rect(midright=(self.input_iterations.rect.x - 10, self.input_iterations.rect.centery)))
            self.input_iterations.draw(self.screen, self.assets.font_main)

        # Inputs & Dropdowns
        self.draw_name_inputs()
        self.draw_dropdowns()

        hint_label = "T: Terminal  |  Z: Fullscreen UI  |  X: Fullscreen limpio  |  Wheel: Zoom  |  Right Drag: Pan"
        if self.is_fullscreen:
            mode_name = "LIMPIO" if self.fullscreen_variant == "clean" else "UI"
            hint_label = f"Fullscreen {mode_name}  |  T: Terminal  |  Z: UI  |  X: Limpio  |  ESC: salir fullscreen"
        hint = self.assets.font_small.render(hint_label, True, muted_col)
        self.screen.blit(hint, hint.get_rect(center=(cx, HEIGHT - 30)))

    def draw_name_inputs(self):
        cx = WIDTH // 2
        label = self.assets.font_main.render("Player Names:", True, self._ui_muted_color())
        self.screen.blit(label, label.get_rect(center=(cx, 305)))

        # Labels
        lbl1 = self.assets.font_small.render("Player 1", True, self._ui_text_color())
        lbl2 = self.assets.font_small.render("Player 2 / AI", True, self._ui_text_color())
        self.screen.blit(lbl1, (self.input_p1.rect.x, self.input_p1.rect.y - 18))
        self.screen.blit(lbl2, (self.input_p2.rect.x, self.input_p2.rect.y - 18))

        self.input_p1.draw(self.screen, self.assets.font_main)
        self.input_p2.draw(self.screen, self.assets.font_main)

        if self.game_mode == "AIvAI":
            lbl = self.assets.font_small.render("Games (Auto):", True, self._ui_text_color())
            self.screen.blit(lbl, (self.input_iterations.rect.x, self.input_iterations.rect.y - 18))
            self.input_iterations.draw(self.screen, self.assets.font_main)

        if self.game_mode == "PvAI":
            lbl = self.assets.font_small.render("AI Difficulty:", True, self._ui_text_color())
            self.screen.blit(lbl, (self.dropdown_diff.rect.x, self.dropdown_diff.rect.y - 18))
            self.dropdown_diff.draw(self.screen, self.assets.font_main)

    def draw_dropdowns(self):
        cx = WIDTH // 2
        lbl_theme = self.assets.font_small.render("Player Colors:", True, self._ui_muted_color())
        lbl_bg = self.assets.font_small.render("Board Background:", True, self._ui_muted_color())
        self.screen.blit(lbl_theme, (self.dropdown_theme.rect.x, self.dropdown_theme.rect.y - 18))
        self.screen.blit(lbl_bg, (self.dropdown_bg.rect.x, self.dropdown_bg.rect.y - 18))
        self.dropdown_theme.draw(self.screen, self.assets.font_main)
        self.dropdown_bg.draw(self.screen, self.assets.font_main)

    def draw_theme_selector(self):
        start_y = 500
        cx = WIDTH // 2
        
        lbl = self.assets.font_main.render("Player Colors:", True, (150, 150, 150))
        self.screen.blit(lbl, lbl.get_rect(center=(cx, start_y)))
        
        # Draw circles for themes
        start_x = cx - (len(THEMES) * 60) // 2
        for i, (name, colors) in enumerate(THEMES.items()):
            x = start_x + i * 60
            y = start_y + 60
            
            # Hover detection for simple objects
            mx, my = pygame.mouse.get_pos()
            hover = math.hypot(mx-x, my-y) < 20
            
            # Glow if selected
            if name == self.selected_theme:
                pygame.draw.circle(self.screen, WHITE, (x, y), 28, 3)
            elif hover:
                pygame.draw.circle(self.screen, (100,100,100), (x, y), 25)

            # Split Circle
            pygame.draw.circle(self.screen, colors[0], (x, y), 20, draw_top_right=True, draw_top_left=True)
            pygame.draw.circle(self.screen, colors[1], (x, y), 20, draw_bottom_left=True, draw_bottom_right=True)
            
            # Name
            if name == self.selected_theme or hover:
                nm = self.assets.font_small.render(name, True, WHITE)
                self.screen.blit(nm, nm.get_rect(center=(x, y + 35)))

    def draw_bg_selector(self):
        start_y = 610
        cx = WIDTH // 2
        
        lbl = self.assets.font_main.render("Board Background:", True, (150, 150, 150))
        self.screen.blit(lbl, lbl.get_rect(center=(cx, start_y)))
        
        start_x = cx - (len(BACKGROUNDS) * 60) // 2
        for i, (name, gradient) in enumerate(BACKGROUNDS.items()):
            x = start_x + i * 60
            y = start_y + 60
            
            # gradient is (outer_color, inner_color) - use inner for preview
            outer_col, inner_col = gradient
            
            mx, my = pygame.mouse.get_pos()
            hover = math.hypot(mx-x, my-y) < 20
            
            if name == self.selected_bg_name:
                pygame.draw.circle(self.screen, WHITE, (x, y), 28, 3)
            elif hover:
                pygame.draw.circle(self.screen, (100,100,100), (x, y), 25)
            
            # Draw mini gradient preview (outer ring, inner circle)
            pygame.draw.circle(self.screen, outer_col, (x, y), 20)
            pygame.draw.circle(self.screen, inner_col, (x, y), 14)
            pygame.draw.circle(self.screen, (200,200,200), (x, y), 20, 1) # Outline
            
            if name == self.selected_bg_name or hover:
                nm = self.assets.font_small.render(name, True, WHITE)
                self.screen.blit(nm, nm.get_rect(center=(x, y + 35)))

    def handle_theme_click(self, pos):
        start_y = 500
        cx = WIDTH // 2
        start_x = cx - (len(THEMES) * 60) // 2
        
        for i, name in enumerate(THEMES.keys()):
            x = start_x + i * 60
            y = start_y + 60
            if math.hypot(pos[0]-x, pos[1]-y) < 25:
                self.set_theme(name)
                return

    def handle_bg_click(self, pos):
        start_y = 610
        cx = WIDTH // 2
        start_x = cx - (len(BACKGROUNDS) * 60) // 2
        
        for i, name in enumerate(BACKGROUNDS.keys()):
            x = start_x + i * 60
            y = start_y + 60
            if math.hypot(pos[0]-x, pos[1]-y) < 25:
                self.set_bg(name)
                return

    def draw_game(self):
        # Override player colors in view for the selected theme
        display_colors = self._display_player_colors()
        self.board_view.player_colors_override = display_colors
        ui_text = self._ui_text_color()
        ui_muted = self._ui_muted_color()
        ui_highlight = self._ui_highlight_color()
        
        # Draw board with screen size for grid
        self.board_view.draw(self.game.board, screen_size=(WIDTH, HEIGHT))
        
        # Ghosts
        valid_list_for_view = [(g, l) for g, l, _ in self.valid_ghosts]
        if valid_list_for_view:
            self.board_view.draw_ghosts(valid_list_for_view)

        # === UI OVERLAYS ===
        
        # Special state overlays
        if self.game_state == "HOTSEAT_WAIT":
            s = pygame.Surface((WIDTH, HEIGHT))
            s.set_alpha(200)
            s.fill((0, 12, 0) if self.terminal_mode else (20, 20, 30))
            self.screen.blit(s, (0,0))
            txt = self.assets.font_title.render(f"Ready {self.game.current_player.name}?", True, ui_text)
            self.screen.blit(txt, txt.get_rect(center=(WIDTH//2, HEIGHT//2 - 50)))
            self.btn_next.draw(self.screen, self.assets.font_main)
            return
             
        if self.game_state == "GAME_OVER":
            s = pygame.Surface((WIDTH, HEIGHT))
            s.set_alpha(200)
            s.fill((0, 12, 0) if self.terminal_mode else (20, 20, 30))
            self.screen.blit(s, (0,0))
            txt = self.assets.font_title.render(self.message, True, ui_highlight)
            self.screen.blit(txt, txt.get_rect(center=(WIDTH//2, HEIGHT//2)))
            self.btn_menu_return.draw(self.screen, self.assets.font_main)
            return

        if self._is_clean_fullscreen():
            self.draw_clean_score_hud()
            return
        
        # === NORMAL GAME UI ===
        
        # 1. HUD Top Bar
        show_session_stats = self._is_ai_music_mode()
        HUD_HEIGHT = 78 if show_session_stats else 60
        hud_bg = pygame.Surface((WIDTH, HUD_HEIGHT))
        hud_bg.set_alpha(220)
        hud_bg.fill(self._ui_panel_color())
        self.screen.blit(hud_bg, (0, 0))
        pygame.draw.line(self.screen, self._ui_panel_line_color(), (0, HUD_HEIGHT), (WIDTH, HUD_HEIGHT), 2)
        
        # Player 1 Info
        p1 = self.game.players[0]
        p1_col = display_colors[0]
        p1_name = self._truncate_text(p1.name, self.assets.font_main, 140)
        if p1 == self.game.current_player:
            active_box = (12, 28, 12) if self.terminal_mode else (50, 50, 70)
            pygame.draw.rect(self.screen, active_box, (10, 5, 220, HUD_HEIGHT-10), border_radius=6)
            pygame.draw.rect(self.screen, p1_col, (10, 5, 220, HUD_HEIGHT-10), 2, border_radius=6)
        pygame.draw.circle(self.screen, p1_col, (35, HUD_HEIGHT//2), 8)
        self.screen.blit(self.assets.font_main.render(p1_name, True, ui_text), (55, 12))
        self.screen.blit(self.assets.font_score.render(f"{p1.score}", True, p1_col), (55, 32))
        if show_session_stats:
            stats = self.training_stats
            p1_session_txt = self.assets.font_small.render(
                f"W:{stats['p1_wins']}  Total:{stats['p1_total_score']}",
                True,
                ui_muted,
            )
            self.screen.blit(p1_session_txt, (55, 54))
        
        # Player 2 Info
        p2 = self.game.players[1]
        p2_col = display_colors[1]
        p2_name = self._truncate_text(p2.name, self.assets.font_main, 140)
        p2_x = 260
        if p2 == self.game.current_player:
            active_box = (12, 28, 12) if self.terminal_mode else (50, 50, 70)
            pygame.draw.rect(self.screen, active_box, (p2_x, 5, 220, HUD_HEIGHT-10), border_radius=6)
            pygame.draw.rect(self.screen, p2_col, (p2_x, 5, 220, HUD_HEIGHT-10), 2, border_radius=6)
        pygame.draw.circle(self.screen, p2_col, (p2_x + 25, HUD_HEIGHT//2), 8)
        self.screen.blit(self.assets.font_main.render(p2_name, True, ui_text), (p2_x + 45, 12))
        self.screen.blit(self.assets.font_score.render(f"{p2.score}", True, p2_col), (p2_x + 45, 32))
        if show_session_stats:
            stats = self.training_stats
            p2_session_txt = self.assets.font_small.render(
                f"W:{stats['p2_wins']}  Total:{stats['p2_total_score']}",
                True,
                ui_muted,
            )
            self.screen.blit(p2_session_txt, (p2_x + 45, 54))
        
        # Pool + Message
        pool_txt = self.assets.font_main.render(f"Pool: {len(self.game.pool)}", True, ui_muted)
        self.screen.blit(pool_txt, pool_txt.get_rect(midright=(WIDTH - 20, HUD_HEIGHT // 2)))
        msg_txt = self.assets.font_main.render(self._truncate_text(self.message, self.assets.font_main, 300), True, ui_highlight)
        self.screen.blit(msg_txt, msg_txt.get_rect(center=(WIDTH // 2 + 50, HUD_HEIGHT // 2)))
        if show_session_stats:
            stats = self.training_stats
            games_txt = self.assets.font_small.render(
                f"Games: {stats['total_games']} | Draws: {stats['draws']}",
                True,
                ui_muted,
            )
            self.screen.blit(games_txt, games_txt.get_rect(center=(WIDTH // 2 + 50, 62)))
        
        # 2. Hand Panel + Buttons (Human turn only)
        if self.is_human_turn():
            self.draw_hand_panel(self.game.current_player)
            
            # DRAW button
            can_play = self.game.can_player_move(self.game.current_player)
            orig_draw = self.btn_draw.base_color
            if self.terminal_mode:
                self.btn_draw.base_color = (28, 92, 36)
            if can_play or self.draws_made >= 3 or len(self.game.pool) == 0:
                self.btn_draw.base_color = (32, 44, 32) if self.terminal_mode else (80, 80, 80)
            self.btn_draw.draw(self.screen, self.assets.font_main)
            self.btn_draw.base_color = orig_draw
            
            # PASS button
            orig_pass = self.btn_pass.base_color
            if self.terminal_mode:
                self.btn_pass.base_color = (24, 78, 32)
            can_pass = (not can_play) and (self.draws_made >= 3 or len(self.game.pool) == 0)
            if not can_pass:
                self.btn_pass.base_color = (32, 44, 32) if self.terminal_mode else (80, 80, 80)
            self.btn_pass.draw(self.screen, self.assets.font_main)
            self.btn_pass.base_color = orig_pass
        
        # 3. Menu Button (always visible at bottom left)
        self.btn_quit.rect.topleft = (20, HEIGHT - 50)
        orig_quit = self.btn_quit.base_color
        orig_quit_txt = self.btn_quit.text_col
        if self.terminal_mode:
            self.btn_quit.base_color = (30, 80, 36)
            self.btn_quit.text_col = self._ui_text_color()
        self.btn_quit.draw(self.screen, self.assets.font_small)
        self.btn_quit.base_color = orig_quit
        self.btn_quit.text_col = orig_quit_txt
        self.draw_ai_control_hud()

    # draw_hud removed (integrated into draw_game)

    def draw_hand_panel(self, player):
        panel_y = HEIGHT - HAND_PANEL_HEIGHT
        panel_bg = (10, 18, 10) if self.terminal_mode else (25, 25, 30)
        panel_line = self._ui_highlight_color()
        label_col = self._ui_muted_color()
        
        # Background
        pygame.draw.rect(self.screen, panel_bg, (0, panel_y, WIDTH, HAND_PANEL_HEIGHT))
        pygame.draw.line(self.screen, panel_line, (0, panel_y), (WIDTH, panel_y), 3)
        
        # Label
        lbl = self.assets.font_small.render("YOUR HAND:", True, label_col)
        self.screen.blit(lbl, (20, panel_y + 10))

        # Grid Logic
        start_x = HAND_START_X
        start_y = panel_y + HAND_START_Y_OFFSET
        
        max_cols = (WIDTH - start_x - 20) // (HAND_TILE_W + HAND_MARGIN_X)
        max_cols = max(1, max_cols)
        
        for i, tile in enumerate(player.hand):
            row = i // max_cols
            col = i % max_cols
            
            x = start_x + col * (HAND_TILE_W + HAND_MARGIN_X)
            y = start_y + row * (HAND_TILE_H + HAND_MARGIN_Y)
            
            # Bounds check (simple clipping)
            if y + HAND_TILE_H > HEIGHT: continue 

            rect = pygame.Rect(x, y, HAND_TILE_W, HAND_TILE_H)
            
            # Hover/Selected Effect
            is_sel = (i == self.selected_tile_idx)
            
            # Draw Triangle Shape for UI
            p1 = (rect.centerx, rect.top)
            p2 = (rect.right, rect.bottom)
            p3 = (rect.left, rect.bottom)
            
            bg = (240, 240, 245) if is_sel else (200, 200, 210)
            
            pygame.draw.polygon(self.screen, bg, [p1, p2, p3])
            pygame.draw.aalines(self.screen, (50,50,60), True, [p1, p2, p3])
            
            if is_sel:
                 pygame.draw.aalines(self.screen, panel_line, True, [p1, p2, p3])
            
            # Show 3 numbers positioned correctly inside triangle
            vals = tile.values
            v_font = self.assets.font_tile_small  # Use tiny font
            
            # Calculate center and position each number closer to center
            cx = (p1[0] + p2[0] + p3[0]) / 3
            cy = (p1[1] + p2[1] + p3[1]) / 3
            
            # Position: 60% from vertex towards center
            t1 = (p1[0] + (cx - p1[0]) * 0.55, p1[1] + (cy - p1[1]) * 0.45)
            t2 = (p2[0] + (cx - p2[0]) * 0.55, p2[1] + (cy - p2[1]) * 0.45)
            t3 = (p3[0] + (cx - p3[0]) * 0.55, p3[1] + (cy - p3[1]) * 0.45)
            
            self._draw_text_outline(str(vals[0]), v_font, BLACK, WHITE, t1)
            self._draw_text_outline(str(vals[1]), v_font, BLACK, WHITE, t2)
            self._draw_text_outline(str(vals[2]), v_font, BLACK, WHITE, t3)

    # --- Input Handlers ---
    
    def handle_game_input(self, event):
        """Pass input to board view for camera control."""
        if self.board_view:
            self.board_view.handle_input(event)
            
    # --- Input Handlers (Duplicated logic from previous implementation for Game) ---
    # --- Input Handlers (Updated for Multi-Row) ---
    def handle_hand_click(self, pos):
        panel_y = HEIGHT - HAND_PANEL_HEIGHT
        if pos[1] > panel_y:
            start_x = HAND_START_X
            start_y = panel_y + HAND_START_Y_OFFSET
            
            max_cols = (WIDTH - start_x - 20) // (HAND_TILE_W + HAND_MARGIN_X)
            max_cols = max(1, max_cols)
            
            player = self.game.current_player
            for i in range(len(player.hand)):
                row = i // max_cols
                col = i % max_cols
                
                x = start_x + col * (HAND_TILE_W + HAND_MARGIN_X)
                y = start_y + row * (HAND_TILE_H + HAND_MARGIN_Y)
                
                # Bounds check
                if y + HAND_TILE_H > HEIGHT: continue
                
                rect = pygame.Rect(x, y, HAND_TILE_W, HAND_TILE_H)
                if rect.collidepoint(pos):
                    self.selected_tile_idx = i
                    self.compute_ghosts(player.hand[i])
                    self.audio_feedback_click() # Nice touch feedback
                    return
    
    def compute_ghosts(self, tile: Triomino):
        self.valid_ghosts = []
        placements = self.game.board.find_valid_placements(tile)
        self.message = f"Tile {tile.values}: {len(placements)} valid spots"
        for i, p in enumerate(placements):
            t_copy = tile.copy()
            t_copy.rotation = p.rotation
            ghost = PlacedTile(
                tile=t_copy,
                q=p.row,
                r=p.col,
                player_id=self.game.current_player_idx,
                orientation=p.orientation
            )
            self.valid_ghosts.append((ghost, i+1, p))

    def handle_board_click(self, pos):
        if not self.valid_ghosts: return
        for ghost, _, placement in self.valid_ghosts:
            row, col, ori = ghost.position
            verts = self.board_view.hex_to_pixel(row, col, ori)
            cx = sum(v[0] for v in verts) / 3
            cy = sum(v[1] for v in verts) / 3
            if math.hypot(pos[0]-cx, pos[1]-cy) < 25:
                player = self.game.current_player
                tile = player.hand[self.selected_tile_idx]
                turn_res = self.game.execute_place(player, tile, placement, self.draws_made)
                if not turn_res.success:
                    self.message = f"Invalid move: {turn_res.message}"
                    self.logger.info("Invalid place: player=%s tile=%s message=%s",
                                     player.name, tile, turn_res.message)
                    return
                self.logger.info("Place tile: player=%s tile=%s points=%s",
                                 player.name, tile, turn_res.points_earned)
                self.end_turn_logic("Placed")
                return


if __name__ == "__main__":
    TriominoApp().run()
