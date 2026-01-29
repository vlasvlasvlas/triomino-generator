"""
Game Board Model

Uses generator1.py's coordinate system: (row, col, orientation)
where orientation is 'up' or 'down'.
"""
from __future__ import annotations
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
import numpy as np

from .tile import Triomino, PlacedTile, Edge


class BonusType(Enum):
    NONE = 0
    BRIDGE = 40
    HEXAGON = 50
    DOUBLE_HEXAGON = 100


@dataclass
class PlacementResult:
    success: bool
    tile: Optional[PlacedTile] = None
    base_points: int = 0
    bonus_type: BonusType = BonusType.NONE  # Deprecated: use bridge_count/hexagon_count
    bonus_points: int = 0
    total_points: int = 0
    message: str = ""
    bridge_count: int = 0
    hexagon_count: int = 0
    
    @property
    def is_bridge(self) -> bool:
        return self.bridge_count > 0
    
    @property
    def is_hexagon(self) -> bool:
        return self.hexagon_count > 0


@dataclass 
class ValidPlacement:
    row: int
    col: int
    orientation: str  # 'up' or 'down'
    rotation: int
    edges_matched: int
    bridge_count: int = 0
    hexagon_count: int = 0
    
    @property
    def position(self) -> Tuple[int, int, str]:
        return (self.row, self.col, self.orientation)

    @property
    def is_bridge(self) -> bool:
        return self.bridge_count > 0

    @property
    def is_hexagon(self) -> bool:
        return self.hexagon_count > 0


# Grid constants (from generator1.py)
SIDE = 1.0
H = np.sqrt(3) / 2 * SIDE


def get_triangle_vertices(row: int, col: int, orientation: str) -> np.ndarray:
    """
    Get vertices for triangle at (row, col, orientation).
    From generator1.py - this is the CORRECT way to compute positions.
    """
    x0 = col * SIDE + (row % 2) * (SIDE / 2)
    y0 = row * H
    
    if orientation == 'up':
        return np.array([
            (x0 + SIDE/2, y0),       # Top (v0)
            (x0, y0 + H),             # Bottom-left (v1)
            (x0 + SIDE, y0 + H)       # Bottom-right (v2)
        ])
    else:  # 'down'
        return np.array([
            (x0 + SIDE/2, y0 + 2*H), # Bottom (v0)
            (x0, y0 + H),             # Top-left (v1)
            (x0 + SIDE, y0 + H)       # Top-right (v2)
        ])


def get_edges(vertices: np.ndarray) -> Set[frozenset]:
    """Get edges as sets of vertex pairs (from generator1.py)."""
    pts = [(round(pt[0], 5), round(pt[1], 5)) for pt in vertices]
    edges = set()
    for k in range(3):
        edge = frozenset([pts[k], pts[(k+1) % 3]])
        edges.add(edge)
    return edges


def _round_vertex(pt: Tuple[float, float]) -> Tuple[float, float]:
    return (round(pt[0], 5), round(pt[1], 5))


def triangles_are_adjacent(pos1: Tuple[int, int, str], 
                            pos2: Tuple[int, int, str]) -> bool:
    """
    Check if two triangles share an edge (from generator1.py approach).
    Two triangles are adjacent if they share exactly one complete edge.
    """
    v1 = get_triangle_vertices(*pos1)
    v2 = get_triangle_vertices(*pos2)
    e1 = get_edges(v1)
    e2 = get_edges(v2)
    shared = e1 & e2
    return len(shared) == 1


def get_shared_edge_index(pos1: Tuple[int, int, str], 
                           pos2: Tuple[int, int, str]) -> Optional[Tuple[int, int]]:
    """
    Get which edge indices are shared between two adjacent triangles.
    Returns (edge_idx_of_pos1, edge_idx_of_pos2) or None if not adjacent.
    """
    v1 = get_triangle_vertices(*pos1)
    v2 = get_triangle_vertices(*pos2)
    
    pts1 = [(round(pt[0], 5), round(pt[1], 5)) for pt in v1]
    pts2 = [(round(pt[0], 5), round(pt[1], 5)) for pt in v2]
    
    for i in range(3):
        edge1 = frozenset([pts1[i], pts1[(i+1) % 3]])
        for j in range(3):
            edge2 = frozenset([pts2[j], pts2[(j+1) % 3]])
            if edge1 == edge2:
                return (i, j)
    return None


class GameBoard:
    """
    Triomino game board using generator1.py coordinate system.
    
    Position format: (row, col, orientation)
    - row: vertical row (0, 1, 2, ...)
    - col: horizontal column (0, 1, 2, ...)
    - orientation: 'up' or 'down'
    """
    
    def __init__(self):
        self.tiles: Dict[Tuple[int, int, str], PlacedTile] = {}
        self._move_history: List[PlacedTile] = []
        self._adjacency_cache: Dict[Tuple[int, int, str], List[Tuple[int, int, str]]] = {}
    
    def is_empty(self) -> bool:
        return len(self.tiles) == 0
    
    def is_position_occupied(self, row: int, col: int, orientation: str) -> bool:
        return (row, col, orientation) in self.tiles
    
    def get_tile_at(self, row: int, col: int, orientation: str) -> Optional[PlacedTile]:
        return self.tiles.get((row, col, orientation))
    
    def _get_potential_neighbors(self, row: int, col: int, orientation: str) -> List[Tuple[int, int, str]]:
        """Get all positions that could potentially be neighbors."""
        positions = []
        # Check nearby cells (within distance 1-2)
        for dr in range(-1, 2):
            for dc in range(-1, 2):
                for ori in ['up', 'down']:
                    pos = (row + dr, col + dc, ori)
                    if pos != (row, col, orientation):
                        positions.append(pos)
        return positions
    
    def get_neighbors(self, row: int, col: int, orientation: str) -> List[Tuple[int, int, str]]:
        """Get all adjacent positions (positions that share an edge)."""
        pos = (row, col, orientation)
        
        if pos in self._adjacency_cache:
            return self._adjacency_cache[pos]
        
        neighbors = []
        for potential in self._get_potential_neighbors(row, col, orientation):
            if triangles_are_adjacent(pos, potential):
                neighbors.append(potential)
        
        self._adjacency_cache[pos] = neighbors
        return neighbors
    
    def get_adjacent_tiles(self, row: int, col: int, orientation: str) -> Dict[Tuple[int, int, str], PlacedTile]:
        """Get placed tiles adjacent to a position."""
        neighbors = self.get_neighbors(row, col, orientation)
        return {
            n: self.tiles[n]
            for n in neighbors
            if n in self.tiles
        }
    
    def get_open_positions(self) -> Set[Tuple[int, int, str]]:
        """Get all empty positions adjacent to placed tiles."""
        if self.is_empty():
            return {(7, 7, 'up')}  # Start in middle of grid
        
        open_positions = set()
        for pos in self.tiles:
            for neighbor in self.get_neighbors(*pos):
                if neighbor not in self.tiles:
                    open_positions.add(neighbor)
        return open_positions
    
    def _check_edge_match(self, tile: Triomino, my_pos: Tuple[int, int, str],
                          adj_tile: PlacedTile, adj_pos: Tuple[int, int, str]) -> bool:
        """Check if edges match between tile at my_pos and adj_tile at adj_pos."""
        edge_indices = get_shared_edge_index(my_pos, adj_pos)
        if edge_indices is None:
            return False
        
        my_edge_idx, adj_edge_idx = edge_indices
        my_edge = tile.get_edge(my_edge_idx)
        adj_edge = adj_tile.tile.get_edge(adj_edge_idx)
        
        return my_edge.matches(adj_edge)
    
    def find_valid_placements(self, tile: Triomino) -> List[ValidPlacement]:
        """Find all valid positions and rotations for a tile."""
        valid = []
        
        for pos in self.get_open_positions():
            row, col, orientation = pos
            adjacent = self.get_adjacent_tiles(row, col, orientation)
            
            if not adjacent and not self.is_empty():
                continue
            
            # Try each rotation
            for rotation in range(3):
                tile.rotation = rotation
                
                # Check all edges match
                all_match = True
                for adj_pos, adj_tile in adjacent.items():
                    if not self._check_edge_match(tile, pos, adj_tile, adj_pos):
                        all_match = False
                        break
                
                if all_match:
                    edges_matched = len(adjacent)
                    is_bridge = edges_matched >= 2
                    
                    valid.append(ValidPlacement(
                        row=row, col=col, orientation=orientation,
                        rotation=rotation,
                        edges_matched=edges_matched,
                        is_bridge=is_bridge,
                        is_hexagon=False  # TODO: implement
                    ))
        
        tile.rotation = 0
        return valid
    
    def place_tile(self, tile: Triomino, row: int, col: int, orientation: str,
                   rotation: int, player_id: Optional[int] = None) -> PlacementResult:
        """Place a tile at the given position."""
        pos = (row, col, orientation)
        
        if pos in self.tiles:
            return PlacementResult(success=False, message="Position occupied")
        
        if not self.is_empty():
            adjacent = self.get_adjacent_tiles(row, col, orientation)
            if not adjacent:
                return PlacementResult(success=False, message="Not adjacent to any tile")
            
            tile.rotation = rotation
            for adj_pos, adj_tile in adjacent.items():
                if not self._check_edge_match(tile, pos, adj_tile, adj_pos):
                    return PlacementResult(success=False, message="Edges don't match")
        
        # Valid placement
        tile.rotation = rotation
        placed = PlacedTile(
            tile=tile.copy(), 
            q=row,  # Using q for row
            r=col,  # Using r for col
            player_id=player_id,
            orientation=orientation
        )
        
        self.tiles[pos] = placed
        self._move_history.append(placed)
        
        # Calculate bonus
        edges_matched = len(self.get_adjacent_tiles(row, col, orientation))
        is_bridge = edges_matched >= 2
        
        bonus_type = BonusType.BRIDGE if is_bridge else BonusType.NONE
        bonus_points = 40 if is_bridge else 0
        base_points = tile.sum_value
        
        return PlacementResult(
            success=True,
            tile=placed,
            base_points=base_points,
            bonus_type=bonus_type,
            bonus_points=bonus_points,
            total_points=base_points + bonus_points,
            message=f"Placed {tile} at ({row}, {col}, {orientation})"
        )
    
    def place_first_tile(self, tile: Triomino, player_id: Optional[int] = None,
                         is_triple: bool = False) -> PlacementResult:
        """Place the first tile at the center."""
        if not self.is_empty():
            return PlacementResult(success=False, message="Board not empty")
        
        pos = (7, 7, 'up')  # Center of grid
        placed = PlacedTile(
            tile=tile.copy(),
            q=7, r=7,
            player_id=player_id,
            orientation='up'
        )
        
        self.tiles[pos] = placed
        self._move_history.append(placed)
        
        base_points = tile.sum_value
        bonus_points = 0
        if is_triple:
            bonus_points = 40 if tile.is_triple_zero() else 10
        
        return PlacementResult(
            success=True,
            tile=placed,
            base_points=base_points,
            bonus_points=bonus_points,
            total_points=base_points + bonus_points,
            message=f"First tile: {tile}"
        )
    
    @property
    def tile_count(self) -> int:
        return len(self.tiles)
    
    @property
    def move_history(self) -> List[PlacedTile]:
        return self._move_history.copy()
    
    def get_bounds(self) -> Tuple[int, int, int, int]:
        if self.is_empty():
            return (7, 7, 7, 7)
        rows = [pos[0] for pos in self.tiles.keys()]
        cols = [pos[1] for pos in self.tiles.keys()]
        return (min(rows), max(rows), min(cols), max(cols))
    
    def __repr__(self) -> str:
        return f"GameBoard({len(self.tiles)} tiles)"
