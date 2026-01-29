"""
Game Visualization

Renders the Triomino game board using matplotlib.
Grid logic adapted from generator1.py for proper triangle alignment.
"""
from __future__ import annotations
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
import matplotlib.patheffects as pe
from typing import Dict, List, Tuple, Optional

from src.models import GameBoard, PlacedTile, Triomino, Player
from src.engine.game import TriominoGame, TurnResult, TurnAction


# Visual constants
SIDE = 1.0  # Triangle side length
H = np.sqrt(3) / 2 * SIDE  # Triangle height

# Colors
PLAYER_COLORS = {
    0: '#e53935',   # Red for player 1
    1: '#1e88e5',   # Blue for player 2
    2: '#43a047',   # Green for player 3
    3: '#fb8c00',   # Orange for player 4
    4: '#8e24aa',   # Purple for player 5
    5: '#00acc1',   # Cyan for player 6
}

GRID_COLOR = '#404040'
EDGE_COLOR = '#1a1a1a'
TEXT_COLOR = '#ffffff'
BG_COLOR = '#1a1a2e'


def get_triangle_coords(row: int, col: int, orientation: str) -> np.ndarray:
    """
    Get vertices for triangle at (row, col) with given orientation.
    
    Uses generator1.py coordinate system:
    - Row offset for staggered grid: (row % 2) * (side / 2)
    - 'up' triangles point upward (apex at top)
    - 'down' triangles point downward (apex at bottom)
    
    Args:
        row: Row index
        col: Column index
        orientation: 'up' or 'down'
        
    Returns:
        np.ndarray of 3 vertex coordinates
    """
    # Base position with row-based offset for staggered grid
    x0 = col * SIDE + (row % 2) * (SIDE / 2)
    y0 = row * H
    
    if orientation == 'up':
        # Up-pointing triangle: apex at top
        # v0: top, v1: bottom-left, v2: bottom-right
        return np.array([
            [x0 + SIDE/2, y0],           # Top apex (v0)
            [x0, y0 + H],                 # Bottom-left (v1)
            [x0 + SIDE, y0 + H]           # Bottom-right (v2)
        ])
    else:  # 'down'
        # Down-pointing triangle: apex at bottom
        # v0: bottom, v1: top-left, v2: top-right
        return np.array([
            [x0 + SIDE/2, y0 + 2*H],     # Bottom apex (v0)
            [x0, y0 + H],                 # Top-left (v1)
            [x0 + SIDE, y0 + H]           # Top-right (v2)
        ])


def axial_to_grid(q: int, r: int) -> Tuple[int, int, str]:
    """
    Convert axial coordinates (q, r) to grid coordinates (row, col, orientation).
    
    In our axial system:
    - (q + r) % 2 == 0 means up-pointing
    - (q + r) % 2 == 1 means down-pointing
    
    The mapping needs to preserve adjacency relationships.
    """
    # Map axial to row/col with proper offsets
    row = r
    col = q
    orientation = 'up' if (q + r) % 2 == 0 else 'down'
    
    return row, col, orientation


def get_triangle_vertices_axial(q: int, r: int) -> np.ndarray:
    """
    Get triangle vertices for axial coordinate (q, r).
    
    Uses the generator1.py grid system for proper alignment.
    """
    row, col, orientation = axial_to_grid(q, r)
    return get_triangle_coords(row, col, orientation)


class GameRenderer:
    """
    Renders the Triomino game board with animations.
    
    Uses generator1.py grid coordinate system for proper triangle alignment.
    """
    
    def __init__(self, figsize: Tuple[int, int] = (14, 10)):
        self.figsize = figsize
        self.fig = None
        self.ax_board = None
        self.ax_info = None
        
        # Animation settings
        self.animation_delay = 0.3
        self.show_grid = True
        
    def setup_figure(self):
        """Create the figure and axes."""
        plt.style.use('dark_background')
        
        self.fig = plt.figure(figsize=self.figsize, facecolor=BG_COLOR)
        
        # Main board area (left 75%)
        self.ax_board = self.fig.add_axes([0.02, 0.05, 0.70, 0.90])
        self.ax_board.set_facecolor(BG_COLOR)
        self.ax_board.set_aspect('equal')
        self.ax_board.axis('off')
        
        # Info panel (right 25%)
        self.ax_info = self.fig.add_axes([0.74, 0.05, 0.24, 0.90])
        self.ax_info.set_facecolor('#16213e')
        self.ax_info.axis('off')
        
        plt.ion()
    
    def draw_background_grid(self, center_q: int = 0, center_r: int = 0, 
                              radius: int = 8):
        """Draw the background triangular grid (like generator1.py)."""
        if not self.show_grid:
            return
        
        for row in range(-radius, radius + 1):
            for col in range(-radius, radius + 1):
                # Draw both up and down triangles at each position
                for orientation in ['up', 'down']:
                    vertices = get_triangle_coords(row + center_r, col + center_q, orientation)
                    poly = Polygon(
                        vertices,
                        facecolor='none',
                        edgecolor=GRID_COLOR,
                        linewidth=0.5,
                        alpha=0.3,
                        zorder=1
                    )
                    self.ax_board.add_patch(poly)
    
    def draw_tile(self, placed_tile: PlacedTile, animate: bool = True):
        """Draw a single placed tile using generator1.py grid system."""
        q, r = placed_tile.q, placed_tile.r
        row, col, orientation = axial_to_grid(q, r)
        vertices = get_triangle_coords(row, col, orientation)
        
        # Get player color
        player_id = placed_tile.player_id or 0
        color = PLAYER_COLORS.get(player_id, PLAYER_COLORS[0])
        
        # Draw filled triangle
        poly = Polygon(
            vertices,
            facecolor=color,
            edgecolor=EDGE_COLOR,
            linewidth=2,
            zorder=2
        )
        self.ax_board.add_patch(poly)
        
        # Draw numbers at vertices
        values = placed_tile.tile.values
        center = vertices.mean(axis=0)
        
        for i, (vx, vy) in enumerate(vertices):
            # Position text between vertex and center
            offset = 0.35
            tx = vx + (center[0] - vx) * offset
            ty = vy + (center[1] - vy) * offset
            
            text = self.ax_board.text(
                tx, ty, str(values[i]),
                fontsize=9,
                fontweight='bold',
                color=TEXT_COLOR,
                ha='center',
                va='center',
                zorder=3
            )
            text.set_path_effects([
                pe.withStroke(linewidth=2, foreground='black')
            ])
        
        if animate:
            self.fig.canvas.draw()
            self.fig.canvas.flush_events()
            plt.pause(self.animation_delay)
    
    def draw_board(self, board: GameBoard, animate: bool = True):
        """Draw the complete board state."""
        self.ax_board.cla()
        self.ax_board.set_facecolor(BG_COLOR)
        self.ax_board.axis('off')
        
        if board.is_empty():
            return
        
        # Get bounds and draw background grid
        bounds = board.get_bounds()
        min_q, max_q, min_r, max_r = bounds
        center_q = (min_q + max_q) // 2
        center_r = (min_r + max_r) // 2
        
        self.draw_background_grid(center_q, center_r)
        
        # Draw all placed tiles
        for placed_tile in board.tiles.values():
            self.draw_tile(placed_tile, animate=False)
        
        # Auto-scale view
        all_coords = []
        for (q, r) in board.tiles.keys():
            row, col, orientation = axial_to_grid(q, r)
            vertices = get_triangle_coords(row, col, orientation)
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
        """Update the info panel with game state."""
        self.ax_info.cla()
        self.ax_info.set_facecolor('#16213e')
        self.ax_info.axis('off')
        
        y = 0.95
        line_height = 0.045
        
        # Title
        self.ax_info.text(0.5, y, "TRIOMINO", fontsize=14, 
                          fontweight='bold', ha='center',
                          transform=self.ax_info.transAxes,
                          color='#f0f0f0')
        y -= line_height * 1.5
        
        # Round info
        round_text = f"Round {game.round_number}"
        if game.is_final_round:
            round_text += " - FINAL"
        self.ax_info.text(0.5, y, round_text, fontsize=11, 
                          ha='center', transform=self.ax_info.transAxes,
                          color='#b0b0b0')
        y -= line_height * 2
        
        # Players
        self.ax_info.text(0.5, y, "--- PLAYERS ---", fontsize=10, 
                          ha='center', transform=self.ax_info.transAxes,
                          color='#808080')
        y -= line_height * 1.2
        
        for i, player in enumerate(game.players):
            color = PLAYER_COLORS.get(i, '#ffffff')
            
            # Current player indicator
            prefix = "> " if i == game.current_player_idx else "  "
            
            # Clean player name (remove emojis that cause font issues)
            clean_name = player.name.replace('🔴 ', '').replace('🔵 ', '')
            if i == 0:
                clean_name = "[RED] " + clean_name
            else:
                clean_name = "[BLUE] " + clean_name
            
            # Player name and score
            self.ax_info.text(0.1, y, f"{prefix}{clean_name}", fontsize=10, 
                              transform=self.ax_info.transAxes,
                              color=color, fontweight='bold')
            self.ax_info.text(0.9, y, f"{player.score}", fontsize=10, 
                              transform=self.ax_info.transAxes,
                              ha='right', color=color)
            y -= line_height * 0.8
            
            # Hand info
            self.ax_info.text(0.15, y, f"Hand: {player.hand_size} tiles ({player.hand_value} pts)", 
                              fontsize=8, transform=self.ax_info.transAxes,
                              color='#909090')
            y -= line_height * 1.2
        
        # Pool info
        y -= line_height * 0.5
        self.ax_info.text(0.5, y, "--- POOL ---", fontsize=10, 
                          ha='center', transform=self.ax_info.transAxes,
                          color='#808080')
        y -= line_height
        self.ax_info.text(0.5, y, f"{len(game.pool)} tiles remaining", fontsize=10, 
                          ha='center', transform=self.ax_info.transAxes,
                          color='#f0f0f0')
        y -= line_height * 1.5
        
        # Last action
        if last_turn:
            self.ax_info.text(0.5, y, "--- LAST MOVE ---", fontsize=10, 
                              ha='center', transform=self.ax_info.transAxes,
                              color='#808080')
            y -= line_height
            
            # Clean the message
            action_text = last_turn.message
            action_text = action_text.replace('🔴 ', '').replace('🔵 ', '')
            if len(action_text) > 35:
                action_text = action_text[:32] + "..."
            
            self.ax_info.text(0.5, y, action_text, fontsize=9, 
                              ha='center', transform=self.ax_info.transAxes,
                              color='#f0f0f0')
            y -= line_height * 0.8
            
            if last_turn.points_earned != 0:
                sign = "+" if last_turn.points_earned > 0 else ""
                points_color = '#4caf50' if last_turn.points_earned > 0 else '#f44336'
                self.ax_info.text(0.5, y, f"{sign}{last_turn.points_earned} points", 
                                  fontsize=10, ha='center',
                                  transform=self.ax_info.transAxes,
                                  color=points_color, fontweight='bold')
        
        self.fig.canvas.draw()
        self.fig.canvas.flush_events()
    
    def show_match_result(self, winner: str, scores: dict):
        """Display match result overlay."""
        # Clean winner name
        clean_winner = winner.replace('🔴 ', '').replace('🔵 ', '')
        
        self.ax_info.text(0.5, 0.15, "*** WINNER ***", fontsize=14, 
                          fontweight='bold', ha='center',
                          transform=self.ax_info.transAxes,
                          color='#ffd700')
        self.ax_info.text(0.5, 0.08, clean_winner, fontsize=12, 
                          ha='center', transform=self.ax_info.transAxes,
                          color='#ffffff', fontweight='bold')
        
        self.fig.canvas.draw()
        self.fig.canvas.flush_events()
    
    def close(self):
        """Close the figure."""
        plt.ioff()
        plt.close(self.fig)


def visualize_game(game: TriominoGame, animation_delay: float = 0.3):
    """
    Visualize a game with live updates.
    """
    renderer = GameRenderer()
    renderer.setup_figure()
    renderer.animation_delay = animation_delay
    
    def on_turn(turn: TurnResult):
        renderer.draw_board(game.board)
        renderer.update_info_panel(game, turn)
    
    game._on_turn_complete = on_turn
    
    return renderer


if __name__ == "__main__":
    # Test visualization
    game = TriominoGame(seed=42)
    renderer = visualize_game(game, animation_delay=0.5)
    
    result = game.play_game()
    
    renderer.show_match_result(
        result.winner.name,
        result.final_scores
    )
    
    plt.pause(3)
    renderer.close()
