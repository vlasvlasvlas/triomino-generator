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
HIGHLIGHT_COLOR = (255, 200, 80)
GHOST_COLOR = (255, 255, 100)

# UI Colors
UI_TOP = (22, 28, 40)
UI_TOP_ACCENT = (34, 42, 60)
UI_PANEL = (24, 26, 34)
UI_PANEL_LIGHT = (40, 44, 56)
UI_TEXT_MUTED = (160, 170, 185)

# Tile Styling
TILE_SHADOW = (30, 20, 10)
TILE_OUTLINE = (30, 30, 35)
TILE_TEXT = (248, 248, 248)
TILE_TEXT_OUTLINE = (20, 20, 20)

# Curated Palettes (Name -> [P1, P2, Accent])
THEMES = {
    "Classic": [(229, 57, 53), (30, 136, 229)],       # Red / Blue
    "Ocean":   [(0, 150, 136), (33, 150, 243)],       # Teal / Blue
    "Sunset":  [(255, 87, 34), (103, 58, 183)],       # Deep Orange / Deep Purple
    "Nature":  [(67, 160, 71), (255, 193, 7)],        # Green / Amber
    "Cyber":   [(255, 0, 128), (0, 255, 255)],        # Neon Pink / Cyan
    "Pastel":  [(255, 179, 186), (186, 225, 255)],    # Pastel Pink / Blue
}

# Background Options - Gradient Pairs (Name -> (outer_color, inner_color))
BACKGROUNDS = {
    "Ocean":    ((15, 45, 75), (60, 140, 180)),    # Deep blue → vibrant blue
    "Midnight": ((15, 15, 25), (35, 40, 60)),      # Dark → slightly lighter
    "Forest":   ((10, 30, 20), (30, 80, 50)),      # Dark green → brighter
    "Sunset":   ((40, 20, 50), (120, 60, 100)),    # Purple tones
    "Night":    ((30, 20, 50), (80, 60, 120)),     # Purple night mode with grid
    "Void":     ((5, 5, 8), (20, 20, 30)),         # Almost black
}

# Grid settings for Night mode
GRID_COLOR = (100, 80, 140, 60)  # Translucent purple

def draw_gradient_background(surface, outer_color, inner_color):
    """Draw a radial gradient from center (inner) to edges (outer)."""
    import pygame
    w, h = surface.get_size()
    cx, cy = w // 2, h // 2
    max_radius = int((w**2 + h**2) ** 0.5 / 2) + 50
    
    # Create gradient by drawing concentric circles
    for r in range(max_radius, 0, -4):
        t = r / max_radius
        color = (
            int(outer_color[0] * t + inner_color[0] * (1 - t)),
            int(outer_color[1] * t + inner_color[1] * (1 - t)),
            int(outer_color[2] * t + inner_color[2] * (1 - t)),
        )
        pygame.draw.circle(surface, color, (cx, cy), r)

PLAYER_COLORS = THEMES["Classic"] # Default legacy for direct access if needed

# Values for rendering
TRIANGLE_SIZE = 50 
FONT_SIZE_MAIN = 24
FONT_SIZE_SMALL = 16

class Assets:
    def __init__(self):
        pygame.font.init()
        self.font_path = self._pick_font([
            "avenir",
            "futura",
            "trebuchetms",
            "gillsans",
            "helvetica",
            "arial",
        ])

        # UI fonts
        self.font_title = pygame.font.Font(self.font_path, 56)
        self.font_title.set_bold(True)
        self.font_subtitle = pygame.font.Font(self.font_path, 32)
        self.font_main = pygame.font.Font(self.font_path, 22)
        self.font_small = pygame.font.Font(self.font_path, 16)
        self.font_score = pygame.font.Font(self.font_path, 24)
        self.font_score.set_bold(True)

        # Tile fonts - kept small to avoid overlap on adjacent tiles
        self.font_tile_small = pygame.font.Font(self.font_path, 12)
        self.font_tile_small.set_bold(True)
        self.font_tile_large = pygame.font.Font(self.font_path, 16)
        self.font_tile_large.set_bold(True)

    def _pick_font(self, names):
        for name in names:
            path = pygame.font.match_font(name)
            if path:
                return path
        return None
