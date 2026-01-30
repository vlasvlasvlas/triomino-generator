"""
Assets and Constants for Pygame UI.
"""
import pygame

# Premium Colors
BLACK = (10, 10, 15)
WHITE = (245, 245, 250)
DARK_BG = (20, 20, 30) # Default
GRID_COLOR = (40, 40, 50)
TEXT_COLOR = (240, 240, 240)
HIGHLIGHT_COLOR = (255, 215, 0)
GHOST_COLOR = (255, 255, 100)

# Curated Palettes (Name -> [P1, P2, Accent])
THEMES = {
    "Classic": [(229, 57, 53), (30, 136, 229)],       # Red / Blue
    "Ocean":   [(0, 150, 136), (33, 150, 243)],       # Teal / Blue
    "Sunset":  [(255, 87, 34), (103, 58, 183)],       # Deep Orange / Deep Purple
    "Nature":  [(67, 160, 71), (255, 193, 7)],        # Green / Amber
    "Cyber":   [(255, 0, 128), (0, 255, 255)],        # Neon Pink / Cyan
    "Pastel":  [(255, 179, 186), (186, 225, 255)],    # Pastel Pink / Blue
}

# Background Options (Name -> Color)
BACKGROUNDS = {
    "Midnight": (20, 20, 30),      # Dark Blue-Grey
    "Deep Ocean": (10, 25, 40),    # Stronger Blue
    "Forest": (15, 30, 20),        # Dark Green
    "Void": (5, 5, 5),             # Almost Black
    "Slate": (30, 35, 40),         # Neutral Gray
}

PLAYER_COLORS = THEMES["Classic"] # Default legacy for direct access if needed

# Values for rendering
TRIANGLE_SIZE = 50 
FONT_SIZE_MAIN = 24
FONT_SIZE_SMALL = 16

class Assets:
    def __init__(self):
        pygame.font.init()
        # Try to find a modern font
        start_fonts = ["avenir", "arial", "helvetica", "robotobold"]
        self.font_main_name = pygame.font.match_font(start_fonts[0])
        
        self.font_title = pygame.font.SysFont(self.font_main_name, 60, bold=True)
        self.font_subtitle = pygame.font.SysFont(self.font_main_name, 36)
        self.font_main = pygame.font.SysFont(self.font_main_name, 24)
        self.font_small = pygame.font.SysFont(self.font_main_name, 18, bold=True)

