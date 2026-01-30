import pygame
import sys
import time
import argparse
import random
import math
from typing import Optional, List, Tuple

from src.engine.game import TriominoGame, TurnResult
from src.ai.strategies import get_strategy, AIStrategy, ScoredMove
from src.gui.assets import Assets, DARK_BG, WHITE, BLACK, THEMES, BACKGROUNDS, HIGHLIGHT_COLOR, GRID_COLOR
from src.gui.pygame_board import PygameBoard
from src.models import Player, PlacedTile, Triomino, GameBoard

# Constants
WIDTH, HEIGHT = 1100, 800
FPS = 60

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
        
        # Hover effect
        col = (self.base_color[0]+30, self.base_color[1]+30, self.base_color[2]+30) if self.hover else self.base_color
        
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


# --- Main Application ---

class TriominoApp:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Triominó Professional Edition - v2.0")
        self.clock = pygame.time.Clock()
        self.assets = Assets()
        
        # State Management
        self.scene = "MENU" # MENU, GAME
        
        # Global Settings
        self.selected_theme = "Classic"
        self.player_colors = THEMES[self.selected_theme]
        
        self.selected_bg_name = "Midnight"
        self.bg_color = BACKGROUNDS[self.selected_bg_name]
        
        self.game_mode = "PvAI" # PvP, PvAI, AIvAI
        self.difficulty = "greedy"
        
        # Menu UI
        self.setup_menu_ui()
        
        # Game Objects (Init later)
        self.game = None
        self.board_view = None
        self.game_ui_buttons = []
        
        # Game State
        self.selected_tile_idx = None
        self.valid_ghosts = []
        self.message = ""
        self.game_state = "TURN" 
        self.draws_made = 0

    def setup_menu_ui(self):
        cx = WIDTH // 2
        cy = HEIGHT // 2
        
        self.menu_buttons = []
        
        # Mode Selection
        self.menu_buttons.append(Button(cx - 250, 250, 200, 60, "HUMAN VS AI", lambda: self.set_mode("PvAI"), color=(0, 100, 200)))
        self.menu_buttons.append(Button(cx + 50, 250, 200, 60, "HUMAN VS HUMAN", lambda: self.set_mode("PvP"), color=(200, 100, 0)))
        self.menu_buttons.append(Button(cx - 100, 330, 200, 50, "BOT VS BOT (WATCH)", lambda: self.set_mode("AIvAI"), color=(100, 100, 100)))

        # Start
        self.btn_start = Button(cx - 100, 650, 200, 80, "START GAME", self.start_game, color=(50, 150, 50))
        self.menu_buttons.append(self.btn_start)

    def set_mode(self, mode):
        self.game_mode = mode
        print(f"Mode set to: {mode}")

    def set_theme(self, theme_name):
        self.selected_theme = theme_name
        self.player_colors = THEMES[theme_name]
        
    def set_bg(self, bg_name):
        self.selected_bg_name = bg_name
        self.bg_color = BACKGROUNDS[bg_name]

    def start_game(self):
        # Configure Game based on Mode
        p1_name = "Player 1"
        p2_name = "Player 2"
        strat1 = HumanStrategy()
        strat2 = HumanStrategy()
        
        if self.game_mode == "PvAI":
            p1_name = "You"
            p2_name = f"Bot-{self.difficulty.title()}"
            strat2 = get_strategy(self.difficulty)
        elif self.game_mode == "AIvAI":
            p1_name = "Bot-Alpha"
            p2_name = "Bot-Beta"
            strat1 = get_strategy("greedy")
            strat2 = get_strategy("greedy")
        
        # Init Engine
        self.game = TriominoGame(
            player_names=[p1_name, p2_name],
            strategies=[strat1, strat2],
            seed=random.randint(1, 10000)
        )
        self.game.setup_round()
        print("Playing opening...")
        self.game.play_opening()
        self.game.next_player()
        
        # Init View
        self.board_view = PygameBoard(self.screen, self.assets)
        self.board_view.offset_x = 0
        self.board_view.center_camera(self.game.board, WIDTH, HEIGHT)
        
        # GUI
        self.btn_draw = Button(50, HEIGHT - 120, 120, 50, "DRAW", self.action_draw, color=(204, 102, 0))
        self.btn_pass = Button(180, HEIGHT - 120, 120, 50, "PASS", self.action_pass, color=(150, 50, 50))
        self.btn_next = Button(WIDTH//2 - 120, HEIGHT//2 + 80, 240, 80, "START TURN", self.action_start_turn, color=(0, 120, 200))
        
        # Game Over Buttons
        self.btn_menu_return = Button(WIDTH//2 - 100, HEIGHT//2 + 80, 200, 60, "MAIN MENU", self.return_to_menu, color=(100, 50, 150))

        self.scene = "GAME"
        self.game_state = "TURN"
        self.message = f"Game Start! {self.game.current_player.name}'s turn."
        
        # Check initial state for AI
        if not self.is_human_turn():
             self.game_state = "AI_THINK"

    def return_to_menu(self):
        self.scene = "MENU"
        self.game = None

    # --- Game Actions ---
    def action_draw(self):
        if not self.is_human_turn(): return
        if self.draws_made >= 3:
            self.message = "Max draws reached!"
            return
        if len(self.game.pool) == 0:
            self.message = "Pool empty!"
            return
        
        self.game.execute_draw(self.game.current_player)
        self.draws_made += 1
        self.message = "Tile drawn."
        self.selected_tile_idx = None
        self.valid_ghosts = []

    def action_pass(self):
        if not self.is_human_turn(): return
        if self.draws_made < 3 and len(self.game.pool) > 0:
            self.message = "Cannot pass (Draw more)"
            return
        
        self.game.next_player()
        self.end_turn_logic("Passed")

    def action_start_turn(self):
        self.game_state = "TURN"
        self.message = f"Turn: {self.game.current_player.name}"
        # Re-center on turn start
        self.board_view.center_camera(self.game.board, WIDTH, HEIGHT)

    def is_human_turn(self):
        if not self.game: return False
        return isinstance(self.game.strategies[self.game.current_player_idx], HumanStrategy)

    def end_turn_logic(self, reason=""):
        self.selected_tile_idx = None
        self.valid_ghosts = []
        self.draws_made = 0
        self.board_view.center_camera(self.game.board, WIDTH, HEIGHT)
        
        winner = self.game.check_round_end()
        if winner:
            self.game_state = "GAME_OVER"
            self.message = f"Winner: {winner.winner.name} ({reason})"
            return

        next_is_human = isinstance(self.game.strategies[self.game.current_player_idx], HumanStrategy)
        
        if self.game_mode == "PvP":
             self.game_state = "HOTSEAT_WAIT"
        elif self.game_mode == "PvAI":
            if next_is_human:
                self.game_state = "TURN"
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
                
                if self.scene == "MENU":
                    for btn in self.menu_buttons:
                        btn.handle_event(event)
                    
                    # Handle Theme Selection Clicks (Custom Logic)
                    if event.type == pygame.MOUSEBUTTONDOWN:
                         self.handle_theme_click(event.pos)
                         self.handle_bg_click(event.pos)

                elif self.scene == "GAME":
                    # Global Inputs (Camera)
                    self.handle_game_input(event)
                    
                    if self.game_state == "TURN":
                        self.btn_draw.handle_event(event)
                        self.btn_pass.handle_event(event)
                        
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
                # Only run logic every X frames or use timer
                # For smooth UI, we check random chance or timer
                if random.random() < 0.05: # Quick delay
                    # CRASH FIX: Ensure we catch errors during turn
                    try:
                        turn_res = self.game.play_turn()
                        self.message = f"AI: {turn_res.message}"
                        self.game.next_player()
                        self.end_turn_logic()
                    except Exception as e:
                        print(f"AI Error: {e}")
                        self.message = "AI Error (See Console)"
                        self.game_state = "TURN" # Recover

    def draw(self):
        self.screen.fill(self.bg_color)
        
        if self.scene == "MENU":
            self.draw_menu()
        elif self.scene == "GAME":
            self.draw_game()

    def draw_menu(self):
        # Background Pattern
        # Title
        title = self.assets.font_title.render("TRIOMINÓ", True, WHITE)
        shadow = self.assets.font_title.render("TRIOMINÓ", True, (0,0,0))
        cx = WIDTH // 2
        
        self.screen.blit(shadow, shadow.get_rect(center=(cx+4, 104)))
        self.screen.blit(title, title.get_rect(center=(cx, 100)))
        
        sub = self.assets.font_subtitle.render("Professional Edition", True, HIGHLIGHT_COLOR)
        self.screen.blit(sub, sub.get_rect(center=(cx, 160)))
        
        # Buttons
        for btn in self.menu_buttons:
            # Highlight Selected Mode
            if btn.text == "HUMAN VS AI" and self.game_mode == "PvAI":
                 pygame.draw.rect(self.screen, HIGHLIGHT_COLOR, btn.rect.inflate(6,6), 3, 8)
            elif btn.text == "HUMAN VS HUMAN" and self.game_mode == "PvP":
                 pygame.draw.rect(self.screen, HIGHLIGHT_COLOR, btn.rect.inflate(6,6), 3, 8)
            elif btn.text == "BOT VS BOT (WATCH)" and self.game_mode == "AIvAI":
                 pygame.draw.rect(self.screen, HIGHLIGHT_COLOR, btn.rect.inflate(6,6), 3, 8)
            
            btn.draw(self.screen, self.assets.font_main)

        # Theme Selector
        self.draw_theme_selector()
        self.draw_bg_selector()

    def draw_theme_selector(self):
        start_y = 420
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
        start_y = 530
        cx = WIDTH // 2
        
        lbl = self.assets.font_main.render("Board Background:", True, (150, 150, 150))
        self.screen.blit(lbl, lbl.get_rect(center=(cx, start_y)))
        
        start_x = cx - (len(BACKGROUNDS) * 60) // 2
        for i, (name, color) in enumerate(BACKGROUNDS.items()):
            x = start_x + i * 60
            y = start_y + 60
            
            mx, my = pygame.mouse.get_pos()
            hover = math.hypot(mx-x, my-y) < 20
            
            if name == self.selected_bg_name:
                pygame.draw.circle(self.screen, WHITE, (x, y), 28, 3)
            elif hover:
                pygame.draw.circle(self.screen, (100,100,100), (x, y), 25)
            
            pygame.draw.circle(self.screen, color, (x, y), 20)
            pygame.draw.circle(self.screen, (200,200,200), (x, y), 20, 1) # Outline
            
            if name == self.selected_bg_name or hover:
                nm = self.assets.font_small.render(name, True, WHITE)
                self.screen.blit(nm, nm.get_rect(center=(x, y + 35)))

    def handle_theme_click(self, pos):
        start_y = 420
        cx = WIDTH // 2
        start_x = cx - (len(THEMES) * 60) // 2
        
        for i, name in enumerate(THEMES.keys()):
            x = start_x + i * 60
            y = start_y + 60
            if math.hypot(pos[0]-x, pos[1]-y) < 25:
                self.set_theme(name)
                return

    def handle_bg_click(self, pos):
        start_y = 530
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
        # Ideally we pass this config to board view, here we hack-inject or use global
        # We stored self.player_colors. We need to pass it to draw_tile.
        
        self.board_view.player_colors_override = self.player_colors
        self.board_view.draw(self.game.board)
        
        # Ghosts
        valid_list_for_view = [(g, l) for g, l, _ in self.valid_ghosts]
        if valid_list_for_view:
            self.board_view.draw_ghosts(valid_list_for_view)

        # UI State Draw
        if self.game_state == "HOTSEAT_WAIT":
             txt = self.assets.font_title.render(f"Ready {self.game.current_player.name}?", True, WHITE)
             self.screen.blit(txt, txt.get_rect(center=(WIDTH//2, HEIGHT//2 - 50)))
             self.btn_next.draw(self.screen, self.assets.font_main)
             
        elif self.game_state == "GAME_OVER":
             txt = self.assets.font_title.render(self.message, True, HIGHLIGHT_COLOR)
             self.screen.blit(txt, txt.get_rect(center=(WIDTH//2, HEIGHT//2)))
             
        else:
             # HUD
             self.draw_hud()
             
             if self.is_human_turn():
                  self.draw_hand_panel(self.game.current_player)
                  self.btn_draw.draw(self.screen, self.assets.font_main)
                  self.btn_pass.draw(self.screen, self.assets.font_main)

    def draw_hud(self):
        # Top Panel
        pygame.draw.rect(self.screen, (30,30,40), (0,0,WIDTH, 50))
        pygame.draw.line(self.screen, (60,60,70), (0,50), (WIDTH, 50))
        
        # Players
        y = 15
        x = 20
        for i, p in enumerate(self.game.players):
             col = self.player_colors[i % len(self.player_colors)]
             name = p.name
             score = p.score
             label = f"{name}: {score}"
             
             # Active indicator
             if p == self.game.current_player:
                 pygame.draw.circle(self.screen, col, (x - 10, y+10), 5)
                 label = f"[ {label} ]"
             
             txt = self.assets.font_main.render(label, True, col if p == self.game.current_player else (150,150,150))
             self.screen.blit(txt, (x, y))
             x += 300
        
        # Message
        msg = self.assets.font_main.render(self.message, True, WHITE)
        self.screen.blit(msg, msg.get_rect(midright=(WIDTH-20, 25)))

    def draw_hand_panel(self, player):
        panel_y = HEIGHT - 140
        pygame.draw.rect(self.screen, (25, 25, 30), (0, panel_y, WIDTH, 140))
        pygame.draw.line(self.screen, HIGHLIGHT_COLOR, (0, panel_y), (WIDTH, panel_y), 2)
        
        start_x = 320
        y = panel_y + 40
        
        for i, tile in enumerate(player.hand):
            rect = pygame.Rect(start_x + i*70, y, 60, 50)
            
            # Hover/Selected
            is_sel = (i == self.selected_tile_idx)
            bg = (255, 230, 200) if is_sel else (220, 220, 230)
            
            pygame.draw.polygon(self.screen, bg, [(rect.centerx, rect.top), (rect.right, rect.bottom), (rect.left, rect.bottom)])
            if is_sel:
                 pygame.draw.polygon(self.screen, HIGHLIGHT_COLOR, [(rect.centerx, rect.top), (rect.right, rect.bottom), (rect.left, rect.bottom)], 3)
            
            # Values
            v_font = self.assets.font_small
            vals = tile.values
            s1 = v_font.render(str(vals[0]), True, BLACK)
            s2 = v_font.render(str(vals[1]), True, BLACK)
            s3 = v_font.render(str(vals[2]), True, BLACK)
            
            self.screen.blit(s1, (rect.centerx-5, rect.top+10))
            self.screen.blit(s2, (rect.right-15, rect.bottom-15))
            self.screen.blit(s3, (rect.left+5, rect.bottom-15))

    # --- Input Handlers ---
    
    def handle_game_input(self, event):
        """Pass input to board view for camera control."""
        if self.board_view:
            self.board_view.handle_input(event)
            
    # --- Input Handlers (Duplicated logic from previous implementation for Game) ---
    def handle_hand_click(self, pos):
         # Adjusted for new layout
         if pos[1] > HEIGHT - 140:
            player = self.game.current_player
            start_x = 320
            idx = (pos[0] - start_x) // 70
            if 0 <= idx < len(player.hand):
                self.selected_tile_idx = idx
                self.compute_ghosts(player.hand[idx])
    
    def compute_ghosts(self, tile: Triomino):
        self.valid_ghosts = []
        placements = self.game.board.find_valid_placements(tile)
        for i, p in enumerate(placements):
            t_copy = tile.copy()
            t_copy.rotation = p.rotation
            ghost = PlacedTile(t_copy, (p.row, p.col, p.orientation), 0)
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
                self.game.execute_place(player, tile, placement, self.draws_made)
                self.game.next_player()
                self.end_turn_logic("Placed")
                return


if __name__ == "__main__":
    TriominoApp().run()
