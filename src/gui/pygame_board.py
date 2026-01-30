"""
Pygame Board Renderer.
"""
import pygame
import math
from typing import Tuple, List, Optional
from src.models import GameBoard, PlacedTile
from src.models.board import get_triangle_vertices, SIDE, H
from src.gui.assets import Assets, PLAYER_COLORS, GRID_COLOR, TEXT_COLOR, HIGHLIGHT_COLOR, BLACK

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
        
        # Camera Interaction State
        self.dragging = False
        self.last_mouse_pos = (0, 0)

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
            color = (255, 255, 100)
            border_col = (255, 255, 255)
            text_col = (50, 50, 50)
        else:
            pid = placed_tile.player_id if placed_tile.player_id is not None else 0
            if self.player_colors_override:
                color = self.player_colors_override[pid % len(self.player_colors_override)]
            else:
                color = PLAYER_COLORS.get(pid, (200, 200, 200))
            border_col = (30, 30, 30)
            text_col = (255, 255, 255)

        # 1. Fill (Aliased)
        pygame.draw.polygon(self.surface, color, vertices)
        
        # 2. AA Outline (Smooth)
        pygame.draw.aalines(self.surface, border_col, True, vertices)
        
        # 3. Thick Outline (for style) if needed, but AA lines are usually 1px. 
        # To make it thick and smooth is hard in pure pygame. 
        # We compromise: Draw thick aliased line BEHIND, or just stick to AA line for crisp look.
        # Let's try drawing a slightly darker Aliased line for weight, then AA on top?
        # Or just the AA line for "Modern/Flat" look.
        # User said "Horrible", often meaning "Jagged". AA fixes Jagged.
        
        # 3. Dynamic Text Scaling
        # We need a font that matches current scale.
        # Approx: scale 60 -> size 18. Ratio ~0.3
        font_size = int(self.scale * 0.35)
        font_size = max(10, min(font_size, 60)) # Clamp
        
        # IMPORTANT: efficient font rendering check
        # creating specific size font every frame is slow.
        # But for Python/Pygame prototype it's okay-ish or cache it.
        # Let's use SysFont efficiently? No, SysFont reloads.
        # For now, let's use the assets' fixed font but trigger a reload if scale changes wildly?
        # Better: Just use 3 tiers: Small, Medium, Large.
        
        if self.scale < 40:
             font = self.assets.font_small
        elif self.scale < 80:
             font = self.assets.font_main
        else:
             font = self.assets.font_subtitle
             
        # Draw numbers
        values = placed_tile.values
        cx = sum(v[0] for v in vertices) / 3
        cy = sum(v[1] for v in vertices) / 3
        
        for i, (vx, vy) in enumerate(vertices):
            # Position: 25% from vertex towards center
            tx = vx + (cx - vx) * 0.32
            ty = vy + (cy - vy) * 0.32
            
            # Text Shadow (Soft)
            if not is_ghost and self.scale > 30: # Don't draw shadow if tiny
                shadow = font.render(str(values[i]), True, (0,0,0, 100))
                self.surface.blit(shadow, shadow.get_rect(center=(tx+1, ty+1)))

            txt_surf = font.render(str(values[i]), True, text_col)
            # AA Font is default true in SysFont("xxx", size, bold=True) usually
            
            rect = txt_surf.get_rect(center=(tx, ty))
            self.surface.blit(txt_surf, rect)

    def draw(self, board: GameBoard):
        # Draw all tiles
        for tile in board.tiles.values():
            self.draw_tile(tile)

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
