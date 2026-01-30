"""
Game Visualization

Renders the Triomino game board using matplotlib.
Uses generator1.py coordinate system: (row, col, orientation).
"""
from __future__ import annotations
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
import matplotlib.patheffects as pe
from typing import Dict, List, Tuple, Optional

from src.models import GameBoard, PlacedTile, Player
from src.models.board import get_triangle_vertices, SIDE, H
from src.engine.game import TriominoGame, TurnResult


# Colors
PLAYER_COLORS = {
    0: '#e53935',   # Red
    1: '#1e88e5',   # Blue
    2: '#43a047',   # Green
    3: '#fb8c00',   # Orange
}

GRID_COLOR = '#404040'
EDGE_COLOR = '#1a1a1a'
TEXT_COLOR = '#ffffff'
BG_COLOR = '#1a1a2e'


class GameRenderer:
    """Renders the Triomino game board."""
    
    def __init__(self, figsize: Tuple[int, int] = (14, 10)):
        self.figsize = figsize
        self.fig = None
        self.ax_board = None
        self.ax_info = None
        self.animation_delay = 0.3
        
    def setup_figure(self):
        plt.style.use('dark_background')
        self.fig = plt.figure(figsize=self.figsize, facecolor=BG_COLOR)
        
        self.ax_board = self.fig.add_axes([0.02, 0.05, 0.70, 0.90])
        self.ax_board.set_facecolor(BG_COLOR)
        self.ax_board.set_aspect('equal')
        self.ax_board.axis('off')
        
        self.ax_info = self.fig.add_axes([0.74, 0.05, 0.24, 0.90])
        self.ax_info.set_facecolor('#16213e')
        self.ax_info.axis('off')
        
        plt.ion()
    
    def draw_background_grid(self, min_row: int, max_row: int, 
                              min_col: int, max_col: int, margin: int = 3):
        """Draw background grid."""
        for row in range(min_row - margin, max_row + margin + 1):
            for col in range(min_col - margin, max_col + margin + 1):
                for ori in ['up', 'down']:
                    vertices = get_triangle_vertices(row, col, ori)
                    poly = Polygon(
                        vertices,
                        facecolor='none',
                        edgecolor=GRID_COLOR,
                        linewidth=0.5,
                        alpha=0.3,
                        zorder=1
                    )
                    self.ax_board.add_patch(poly)
    
    def draw_tile(self, placed_tile: PlacedTile):
        """Draw a single tile."""
        row, col, ori = placed_tile.position
        vertices = get_triangle_vertices(row, col, ori)
        
        player_id = placed_tile.player_id or 0
        color = PLAYER_COLORS.get(player_id, PLAYER_COLORS[0])
        
        # Draw triangle
        poly = Polygon(
            vertices,
            facecolor=color,
            edgecolor=EDGE_COLOR,
            linewidth=2,
            zorder=2
        )
        self.ax_board.add_patch(poly)
        
        # Draw numbers
        values = placed_tile.values
        center = vertices.mean(axis=0)
        
        for i, (vx, vy) in enumerate(vertices):
            offset = 0.35
            tx = vx + (center[0] - vx) * offset
            ty = vy + (center[1] - vy) * offset
            
            text = self.ax_board.text(
                tx, ty, str(values[i]),
                fontsize=9, fontweight='bold',
                color=TEXT_COLOR, ha='center', va='center',
                zorder=3
            )
            text.set_path_effects([
                pe.withStroke(linewidth=2, foreground='black')
            ])

    def draw_ghost_placements(self, placed_list: List[Tuple[PlacedTile, int]]):
        """
        Draw semi-transparent 'ghost' tiles to show valid options to the user.
        placed_list: List of (PlacedTile, label_index)
        """
        # Remove any existing ghosts (identified by specific zorder or tag? 
        # For simplicity, we assume we redraw board to clear, but here we just add patches)
        # To clear ghosts specifically would require tracking them. 
        # Easier strategy: Main loop redraws board (clearing everything), then draws ghosts.
        
        for p_tile, label in placed_list:
            row, col, ori = p_tile.position
            vertices = get_triangle_vertices(row, col, ori)
            
            # Draw faded triangle
            poly = Polygon(
                vertices,
                facecolor='#FFFF00', # Yellow highlight
                edgecolor='white',
                linewidth=2,
                alpha=0.4,
                zorder=10
            )
            self.ax_board.add_patch(poly)
            
            # Draw Selection Label (Values: 1, 2, 3...)
            center = vertices.mean(axis=0)
            text = self.ax_board.text(
                center[0], center[1], str(label),
                fontsize=14, fontweight='bold',
                color='#ffffff', ha='center', va='center',
                zorder=11
            )
            text.set_path_effects([
                pe.withStroke(linewidth=3, foreground='black')
            ])
            
        self.fig.canvas.draw()
        self.fig.canvas.flush_events()
    
    def draw_board(self, board: GameBoard, animate: bool = True):
        """Draw complete board."""
        self.ax_board.cla()
        self.ax_board.set_facecolor(BG_COLOR)
        self.ax_board.axis('off')
        
        if board.is_empty():
            return
        
        # Get bounds
        min_row, max_row, min_col, max_col = board.get_bounds()
        self.draw_background_grid(min_row, max_row, min_col, max_col)
        
        # Draw tiles
        for placed_tile in board.tiles.values():
            self.draw_tile(placed_tile)
        
        # Auto-scale
        all_coords = []
        for pos in board.tiles.keys():
            vertices = get_triangle_vertices(*pos)
            all_coords.extend(vertices)
        
        all_coords = np.array(all_coords)
        margin = 3 * SIDE
        self.ax_board.set_xlim(all_coords[:,0].min() - margin, 
                               all_coords[:,0].max() + margin)
        self.ax_board.set_ylim(all_coords[:,1].min() - margin, 
                               all_coords[:,1].max() + margin)
        
        if animate:
            self.fig.canvas.draw()
            self.fig.canvas.flush_events()
    
    def update_info_panel(self, game: TriominoGame, 
                          last_turn: Optional[TurnResult] = None):
        """Update info panel."""
        self.ax_info.cla()
        self.ax_info.set_facecolor('#16213e')
        self.ax_info.axis('off')
        
        y = 0.95
        lh = 0.045
        
        self.ax_info.text(0.5, y, "TRIOMINO", fontsize=14, fontweight='bold',
                          ha='center', transform=self.ax_info.transAxes, color='#f0f0f0')
        y -= lh * 1.5
        
        round_text = f"Round {game.round_number}"
        if game.is_final_round:
            round_text += " - FINAL"
        self.ax_info.text(0.5, y, round_text, fontsize=11, ha='center',
                          transform=self.ax_info.transAxes, color='#b0b0b0')
        y -= lh * 2
        
        self.ax_info.text(0.5, y, "--- PLAYERS ---", fontsize=10, ha='center',
                          transform=self.ax_info.transAxes, color='#808080')
        y -= lh * 1.2
        
        for i, player in enumerate(game.players):
            color = PLAYER_COLORS.get(i, '#ffffff')
            prefix = "> " if i == game.current_player_idx else "  "
            name = player.name.replace('🔴 ', '').replace('🔵 ', '')
            
            self.ax_info.text(0.1, y, f"{prefix}{name}", fontsize=10,
                              transform=self.ax_info.transAxes, color=color, fontweight='bold')
            self.ax_info.text(0.9, y, f"{player.score}", fontsize=10,
                              transform=self.ax_info.transAxes, ha='right', color=color)
            y -= lh * 0.8
            
            self.ax_info.text(0.15, y, f"Hand: {player.hand_size} tiles", fontsize=8,
                              transform=self.ax_info.transAxes, color='#909090')
            y -= lh * 1.2
        
        y -= lh * 0.5
        self.ax_info.text(0.5, y, f"Pool: {len(game.pool)} tiles", fontsize=10,
                          ha='center', transform=self.ax_info.transAxes, color='#f0f0f0')
        
        if last_turn and last_turn.points_earned != 0:
            y -= lh * 1.5
            sign = "+" if last_turn.points_earned > 0 else ""
            color = '#4caf50' if last_turn.points_earned > 0 else '#f44336'
            self.ax_info.text(0.5, y, f"{sign}{last_turn.points_earned} pts", fontsize=12,
                              ha='center', transform=self.ax_info.transAxes, 
                              color=color, fontweight='bold')
        
        self.fig.canvas.draw()
        self.fig.canvas.flush_events()
    
    def show_match_result(self, winner: str, scores: dict):
        """Show winner."""
        winner = winner.replace('🔴 ', '').replace('🔵 ', '')
        self.ax_info.text(0.5, 0.15, "*** WINNER ***", fontsize=14, fontweight='bold',
                          ha='center', transform=self.ax_info.transAxes, color='#ffd700')
        self.ax_info.text(0.5, 0.08, winner, fontsize=12, ha='center',
                          transform=self.ax_info.transAxes, color='#ffffff', fontweight='bold')
        self.fig.canvas.draw()
        self.fig.canvas.flush_events()
    
    def close(self):
        plt.ioff()
        plt.close(self.fig)


def visualize_game(game: TriominoGame, animation_delay: float = 0.3):
    """Set up visualization for a game."""
    renderer = GameRenderer()
    renderer.setup_figure()
    renderer.animation_delay = animation_delay
    
    def on_turn(turn: TurnResult):
        renderer.draw_board(game.board)
        renderer.update_info_panel(game, turn)
    
    game._on_turn_complete = on_turn
    return renderer
