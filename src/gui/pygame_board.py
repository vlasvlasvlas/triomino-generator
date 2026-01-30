"""
Pygame Board Renderer.
"""
import pygame
import math
from typing import Tuple, List, Optional
from src.models import GameBoard, PlacedTile
from src.models.board import get_triangle_vertices, SIDE, H
from src.gui.assets import (
    Assets,
    PLAYER_COLORS,
    GRID_COLOR,
    TEXT_COLOR,
    HIGHLIGHT_COLOR,
    BLACK,
    TILE_SHADOW,
    TILE_OUTLINE,
    TILE_TEXT,
    TILE_TEXT_OUTLINE,
)

class PygameBoard:
    def __init__(self, surface, assets):
        self.surface = surface
        self.assets = assets
        self.offset_x = 0
        self.offset_y = 0
        self.scale = 70.0 # Started larger
        self.camera_x = 400
        self.camera_y = 300
        self.player_colors_override = None 
        
        # Visual Mode Settings
        self.transparent_mode = False  # Semi-transparent tiles
        self.show_grid = False         # Visible triangle grid
        self.tile_alpha = 180          # Alpha for transparent mode (0-255)
        
        # Ghost Trail System (for Bot vs Bot visual mode)
        # List of (tile_data, alpha, timestamp) - fades over time
        self.ghost_trails = []
        self.ghost_fade_rate = 2       # Alpha reduction per frame
        self.ghost_enabled = False     # Enable ghost trail effect
        
        # Camera Interaction State
        self.dragging = False
        self.last_mouse_pos = (0, 0)
    
    def add_ghost_snapshot(self, board):
        """Capture current board state as ghost trails."""
        if not self.ghost_enabled:
            return
        for tile in board.tiles.values():
            # Store tile position and player_id with starting alpha
            self.ghost_trails.append({
                'position': tile.position,
                'values': tile.values,
                'player_id': tile.player_id,
                'alpha': 120  # Starting ghost alpha
            })
    
    def update_ghosts(self):
        """Fade and remove old ghosts."""
        new_ghosts = []
        for ghost in self.ghost_trails:
            ghost['alpha'] -= self.ghost_fade_rate
            if ghost['alpha'] > 5:  # Keep if still visible
                new_ghosts.append(ghost)
        self.ghost_trails = new_ghosts
    
    def clear_ghosts(self):
        """Clear all ghost trails."""
        self.ghost_trails = []

    def _shade(self, color, factor):
        return tuple(max(0, min(255, int(c * factor))) for c in color)

    def _draw_text_outline(self, text, font, color, outline_color, center):
        base = font.render(text, True, color)
        outline = font.render(text, True, outline_color)
        ox, oy = center
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (1, 1)]:
            self.surface.blit(outline, outline.get_rect(center=(ox + dx, oy + dy)))
        self.surface.blit(base, base.get_rect(center=center))

    def handle_input(self, event):
        """Handle Zoom and Pan events."""
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 3: # Right Click to Pan
                self.dragging = True
                self.last_mouse_pos = event.pos
            elif event.button == 4: # Wheel Up (Zoom In)
                self.scale = min(self.scale * 1.1, 150.0)
            elif event.button == 5: # Wheel Down (Zoom Out)
                self.scale = max(self.scale * 0.9, 20.0)
                
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 3:
                self.dragging = False
                
        elif event.type == pygame.MOUSEMOTION:
            if self.dragging:
                dx = event.pos[0] - self.last_mouse_pos[0]
                dy = event.pos[1] - self.last_mouse_pos[1]
                self.camera_x += dx
                self.camera_y += dy
                self.last_mouse_pos = event.pos

    def hex_to_pixel(self, row, col, ori) -> List[Tuple[float, float]]:
        vertices = get_triangle_vertices(row, col, ori)
        pixel_verts = []
        for vx, vy in vertices:
            px = vx * self.scale + self.camera_x + self.offset_x
            py = -vy * self.scale + self.camera_y + self.offset_y
            pixel_verts.append((px, py))
        return pixel_verts
        
    def center_camera(self, board: GameBoard, width: int, height: int):
        """Auto-center logic (can be called manually or on event)."""
        if not board.tiles: return
            
        all_x, all_y = [], []
        for pos in board.tiles.keys():
            row, col, ori = pos
            verts = get_triangle_vertices(row, col, ori)
            for vx, vy in verts:
                all_x.append(vx * self.scale)
                all_y.append(-vy * self.scale)
                
        if not all_x: return

        min_x, max_x = min(all_x), max(all_x)
        min_y, max_y = min(all_y), max(all_y)
        
        board_w = max_x - min_x
        board_h = max_y - min_y
        
        center_x = min_x + board_w / 2
        center_y = min_y + board_h / 2
        
        # Determine optimal scale if needed (fit to screen)? 
        # For now just center the position, keep current zoom
        
        screen_cx = width / 2
        screen_cy = height / 2
        
        self.camera_x = screen_cx - center_x
        self.camera_y = screen_cy - center_y
        self.offset_x = 0
        self.offset_y = 0

    def draw_tile(self, placed_tile: PlacedTile, is_ghost=False, alpha=255):
        row, col, ori = placed_tile.position
        vertices = self.hex_to_pixel(row, col, ori)
        
        # Determine styling
        if is_ghost:
            color = (255, 245, 160, 120)
            border_col = (255, 255, 255)
            text_col = (80, 80, 80)
        else:
            pid = placed_tile.player_id if placed_tile.player_id is not None else 0
            if self.player_colors_override:
                color = self.player_colors_override[pid % len(self.player_colors_override)]
            else:
                if isinstance(PLAYER_COLORS, dict):
                    color = PLAYER_COLORS.get(pid, (200, 200, 200))
                else:
                    color = PLAYER_COLORS[pid % len(PLAYER_COLORS)] if PLAYER_COLORS else (200, 200, 200)
            border_col = TILE_OUTLINE
            text_col = TILE_TEXT

        if is_ghost:
            ghost_surface = pygame.Surface(self.surface.get_size(), pygame.SRCALPHA)
            pygame.draw.polygon(ghost_surface, color, vertices)
            pygame.draw.aalines(ghost_surface, border_col, True, vertices)
            self.surface.blit(ghost_surface, (0, 0))
            return

        # === Premium Tile Rendering ===
        
        # === Premium Tile Rendering (with alpha support) ===
        # If alpha < 255, we render to a temp surface first
        use_alpha = alpha < 255
        if use_alpha:
            # Create temp surface for this tile
            min_x = min(v[0] for v in vertices) - 10
            max_x = max(v[0] for v in vertices) + 10
            min_y = min(v[1] for v in vertices) - 10
            max_y = max(v[1] for v in vertices) + 10
            
            tile_w = int(max_x - min_x)
            tile_h = int(max_y - min_y)
            if tile_w <= 0 or tile_h <= 0:
                use_alpha = False
            else:
                tile_surf = pygame.Surface((tile_w, tile_h), pygame.SRCALPHA)
                # Offset vertices to local coords
                local_verts = [(v[0] - min_x, v[1] - min_y) for v in vertices]
                target_surf = tile_surf
                render_verts = local_verts
        
        if not use_alpha:
            target_surf = self.surface
            render_verts = vertices
        
        # 1. Drop Shadow (offset and blurred effect via multiple layers)
        if not use_alpha:  # Skip shadows for transparent tiles (performance)
            for offset in [(5, 5), (4, 4), (3, 3)]:
                shadow_verts = [(x + offset[0], y + offset[1]) for x, y in vertices]
                shadow_alpha = 40 + (5 - offset[0]) * 15
                shadow_surf = pygame.Surface(self.surface.get_size(), pygame.SRCALPHA)
                pygame.draw.polygon(shadow_surf, (*TILE_SHADOW, shadow_alpha), shadow_verts)
                self.surface.blit(shadow_surf, (0, 0))

        # 2. Main tile fill
        pygame.draw.polygon(target_surf, color, render_verts)

        # 3. Inner highlight (subtle lighter layer)
        cx = sum(v[0] for v in render_verts) / 3
        cy = sum(v[1] for v in render_verts) / 3
        inner = [(x + (cx - x) * 0.15, y + (cy - y) * 0.15) for x, y in render_verts]
        pygame.draw.polygon(target_surf, self._shade(color, 1.12), inner)
        
        # 5. Outline (thick dark, then AA)
        pygame.draw.polygon(target_surf, TILE_OUTLINE, render_verts, 3)
        pygame.draw.aalines(target_surf, self._shade(TILE_OUTLINE, 0.7), True, render_verts)
        
        # 6. Vertex dots (metallic spheres)
        dot_radius = max(3, int(self.scale * 0.06))
        for vx, vy in render_verts:
            # Shadow
            pygame.draw.circle(target_surf, (20, 15, 10), (int(vx) + 1, int(vy) + 1), dot_radius)
            # Base
            pygame.draw.circle(target_surf, (180, 160, 120), (int(vx), int(vy)), dot_radius)
            # Highlight
            pygame.draw.circle(target_surf, (240, 230, 200), (int(vx) - 1, int(vy) - 1), max(1, dot_radius - 2))
        
        # Blit with alpha if needed
        if use_alpha:
            tile_surf.set_alpha(alpha)
            self.surface.blit(tile_surf, (min_x, min_y))
        
        # 3. Dynamic Text Scaling
        # Use smaller fonts at lower zoom levels
        if self.scale < 40:
            font = self.assets.font_tile_small
        elif self.scale < 70:
            font = self.assets.font_tile_small  # Stay small for better clarity
        else:
            font = self.assets.font_tile_large
              
        # Draw numbers - position them CLOSER to center to avoid overlap with adjacent tiles
        values = placed_tile.values
        cx = sum(v[0] for v in vertices) / 3
        cy = sum(v[1] for v in vertices) / 3
        
        for i, (vx, vy) in enumerate(vertices):
            # Position: 55% from vertex towards center
            tx = vx + (cx - vx) * 0.55
            ty = vy + (cy - vy) * 0.55
            
            # Simple high-contrast outline
            # Draw offsets in outline color, then center in text color
            txt = str(values[i])
            base = font.render(txt, True, text_col)
            outline = font.render(txt, True, TILE_TEXT_OUTLINE)
            
            # Thick outline
            for dx in [-2, 0, 2]:
                for dy in [-2, 0, 2]:
                    if dx == 0 and dy == 0: continue
                    self.surface.blit(outline, outline.get_rect(center=(tx + dx, ty + dy)))
            
            self.surface.blit(base, base.get_rect(center=(tx, ty)))

    def draw_grid(self, width: int, height: int):
        """Draw visible triangle grid overlay."""
        grid_surface = pygame.Surface((width, height), pygame.SRCALPHA)
        grid_color = (*GRID_COLOR[:3], 40) if len(GRID_COLOR) < 4 else GRID_COLOR
        
        # Calculate grid bounds based on camera
        rows_range = range(-20, 30)
        cols_range = range(-30, 40)
        
        for row in rows_range:
            for col in cols_range:
                for ori in [0, 1]:
                    verts = self.hex_to_pixel(row, col, ori)
                    # Check if any vertex is on screen
                    if any(0 <= v[0] <= width and 0 <= v[1] <= height for v in verts):
                        pygame.draw.aalines(grid_surface, grid_color, True, verts)
        
        self.surface.blit(grid_surface, (0, 0))

    def draw(self, board: GameBoard, screen_size: tuple = None):
        """Draw all tiles, optionally with grid and ghost trails."""
        # Update ghost fading
        self.update_ghosts()
        
        # Draw grid first if enabled
        if self.show_grid and screen_size:
            self.draw_grid(screen_size[0], screen_size[1])
        
        # Draw ghost trails (faded tiles from previous games)
        if self.ghost_enabled and self.ghost_trails:
            for ghost in self.ghost_trails:
                self._draw_ghost_tile(ghost)
        
        # Draw all current tiles
        for tile in board.tiles.values():
            self.draw_tile(tile, alpha=self.tile_alpha if self.transparent_mode else 255)

    def draw_ghosts(self, ghosts: List[Tuple[PlacedTile, int]]):
        for gt, label in ghosts:
            self.draw_tile(gt, is_ghost=True)
            # Draw label index
            row, col, ori = gt.position
            verts = self.hex_to_pixel(row, col, ori)
            cx = sum(v[0] for v in verts) / 3
            cy = sum(v[1] for v in verts) / 3
            
            lbl = self.assets.font_main.render(str(label), True, (255, 0, 0))
            self.surface.blit(lbl, lbl.get_rect(center=(cx, cy)))

    def _draw_ghost_tile(self, ghost: dict):
        """Draw a faded ghost tile from previous game."""
        row, col, ori = ghost['position']
        vertices = self.hex_to_pixel(row, col, ori)
        alpha = int(ghost['alpha'])
        
        # Get player color
        pid = ghost.get('player_id', 0) or 0
        if self.player_colors_override:
            color = self.player_colors_override[pid % len(self.player_colors_override)]
        else:
            color = PLAYER_COLORS.get(pid, (200, 200, 200)) if isinstance(PLAYER_COLORS, dict) else PLAYER_COLORS[pid % len(PLAYER_COLORS)]
        
        # Create ghost surface with alpha
        min_x = min(v[0] for v in vertices)
        max_x = max(v[0] for v in vertices)
        min_y = min(v[1] for v in vertices)
        max_y = max(v[1] for v in vertices)
        
        w = int(max_x - min_x) + 10
        h = int(max_y - min_y) + 10
        if w <= 0 or h <= 0:
            return
            
        ghost_surf = pygame.Surface((w, h), pygame.SRCALPHA)
        local_verts = [(v[0] - min_x + 5, v[1] - min_y + 5) for v in vertices]
        
        # Draw with alpha
        ghost_color = (*color[:3], alpha)
        pygame.draw.polygon(ghost_surf, ghost_color, local_verts)
        
        self.surface.blit(ghost_surf, (min_x - 5, min_y - 5))
