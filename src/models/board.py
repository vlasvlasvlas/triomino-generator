"""
Game Board Model

Represents the triangular grid where tiles are placed.
Handles placement validation, neighbor detection, and bonus calculations.
"""
from __future__ import annotations
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass, field
from enum import Enum

from .tile import Triomino, PlacedTile, Edge


class BonusType(Enum):
    """Types of bonus points that can be earned."""
    NONE = 0
    BRIDGE = 40           # Matching 1 side + opposite vertex
    HEXAGON = 50          # Completing a 6-tile hexagon
    DOUBLE_HEXAGON = 100  # Completing two hexagons at once


@dataclass
class PlacementResult:
    """Result of attempting to place a tile."""
    success: bool
    tile: Optional[PlacedTile] = None
    base_points: int = 0           # Sum of tile values
    bonus_type: BonusType = BonusType.NONE
    bonus_points: int = 0
    total_points: int = 0
    message: str = ""
    
    @property
    def is_bridge(self) -> bool:
        return self.bonus_type == BonusType.BRIDGE
    
    @property
    def is_hexagon(self) -> bool:
        return self.bonus_type in (BonusType.HEXAGON, BonusType.DOUBLE_HEXAGON)


@dataclass 
class ValidPlacement:
    """A valid position and rotation for placing a tile."""
    q: int
    r: int
    rotation: int
    edges_matched: int  # How many edges match (1, 2, or 3)
    is_bridge: bool = False
    is_hexagon: bool = False


# Neighbor offsets for triangular grid
# For UP-pointing triangles (▲): (q + r) % 2 == 0
NEIGHBORS_UP = {
    0: (-1, 0),   # Left neighbor (edge 0)
    1: (0, 1),    # Bottom neighbor (edge 1)  
    2: (1, 0),    # Right neighbor (edge 2)
}

# For DOWN-pointing triangles (▼): (q + r) % 2 == 1
NEIGHBORS_DOWN = {
    0: (-1, 0),   # Left neighbor (edge 0)
    1: (0, -1),   # Top neighbor (edge 1)
    2: (1, 0),    # Right neighbor (edge 2)
}

# Opposite edge mapping (when two triangles share an edge)
OPPOSITE_EDGE = {0: 2, 1: 1, 2: 0}


class GameBoard:
    """
    The Triomino game board using axial coordinates.
    
    Coordinate system:
    - Uses axial (q, r) coordinates for triangular grid
    - Triangle orientation determined by (q + r) % 2:
        - 0 = Up-pointing triangle (▲)
        - 1 = Down-pointing triangle (▼)
    """
    
    def __init__(self):
        self.tiles: Dict[Tuple[int, int], PlacedTile] = {}
        self._move_history: List[PlacedTile] = []
    
    def is_empty(self) -> bool:
        """Check if no tiles have been placed."""
        return len(self.tiles) == 0
    
    def is_position_occupied(self, q: int, r: int) -> bool:
        """Check if a position already has a tile."""
        return (q, r) in self.tiles
    
    def get_tile_at(self, q: int, r: int) -> Optional[PlacedTile]:
        """Get the tile at a position, if any."""
        return self.tiles.get((q, r))
    
    def is_pointing_up(self, q: int, r: int) -> bool:
        """Determine if a triangle at (q, r) points up or down."""
        return (q + r) % 2 == 0
    
    def get_neighbors(self, q: int, r: int) -> Dict[int, Tuple[int, int]]:
        """Get neighbor positions for each edge of triangle at (q, r)."""
        if self.is_pointing_up(q, r):
            return {edge: (q + dq, r + dr) for edge, (dq, dr) in NEIGHBORS_UP.items()}
        else:
            return {edge: (q + dq, r + dr) for edge, (dq, dr) in NEIGHBORS_DOWN.items()}
    
    def get_adjacent_tiles(self, q: int, r: int) -> Dict[int, PlacedTile]:
        """Get placed tiles adjacent to position (q, r), keyed by edge index."""
        neighbors = self.get_neighbors(q, r)
        return {
            edge: self.tiles[pos] 
            for edge, pos in neighbors.items() 
            if pos in self.tiles
        }
    
    def get_open_positions(self) -> Set[Tuple[int, int]]:
        """Get all positions adjacent to placed tiles that are empty."""
        if self.is_empty():
            return {(0, 0)}  # Start at origin
        
        open_positions = set()
        for (q, r) in self.tiles:
            for edge, (nq, nr) in self.get_neighbors(q, r).items():
                if (nq, nr) not in self.tiles:
                    open_positions.add((nq, nr))
        return open_positions
    
    def _get_required_edges(self, q: int, r: int) -> Dict[int, Edge]:
        """
        Get the edges that must be matched at position (q, r).
        
        Returns dict of edge_index -> required Edge values.
        """
        adjacent = self.get_adjacent_tiles(q, r)
        required = {}
        
        for edge_idx, adj_tile in adjacent.items():
            # Get the edge of the adjacent tile that faces this position
            opp_edge_idx = OPPOSITE_EDGE[edge_idx]
            adj_edge = adj_tile.tile.get_edge(opp_edge_idx)
            # We need to match this edge (in reverse)
            required[edge_idx] = adj_edge
        
        return required
    
    def find_valid_placements(self, tile: Triomino) -> List[ValidPlacement]:
        """
        Find all valid positions and rotations for placing a tile.
        
        Returns list of ValidPlacement objects.
        """
        valid = []
        
        for (q, r) in self.get_open_positions():
            required_edges = self._get_required_edges(q, r)
            
            if not required_edges and not self.is_empty():
                continue  # Must connect to existing tiles
            
            # Try each rotation
            for rotation in range(3):
                tile.rotation = rotation
                
                # Check if all required edges match
                all_match = True
                for edge_idx, required_edge in required_edges.items():
                    tile_edge = tile.get_edge(edge_idx)
                    if not tile_edge.matches(required_edge):
                        all_match = False
                        break
                
                if all_match:
                    edges_matched = len(required_edges) if required_edges else 0
                    
                    # Check for bridge (matching 2+ edges from different "groups")
                    is_bridge = self._check_bridge(q, r, tile, required_edges)
                    
                    # Check for hexagon
                    is_hexagon = self._check_hexagon(q, r, tile)
                    
                    valid.append(ValidPlacement(
                        q=q, r=r, 
                        rotation=rotation,
                        edges_matched=edges_matched,
                        is_bridge=is_bridge,
                        is_hexagon=is_hexagon
                    ))
        
        tile.rotation = 0  # Reset rotation
        return valid
    
    def _check_bridge(self, q: int, r: int, tile: Triomino, 
                      required_edges: Dict[int, Edge]) -> bool:
        """
        Check if placement creates a bridge.
        
        A bridge is formed when a tile matches:
        - One complete side (2 vertex values)
        - AND the opposite point (1 vertex value touching other tiles)
        
        Essentially: matching 2 or more edges.
        """
        # Bridge requires matching at least 2 edges
        return len(required_edges) >= 2
    
    def _check_hexagon(self, q: int, r: int, tile: Triomino) -> bool:
        """
        Check if placement completes a hexagon.
        
        A hexagon is formed when 6 triangles surround a central point,
        and this tile is the 6th piece completing the circle.
        
        The center point should have the same value from all 6 triangles.
        """
        # Get the vertices of the tile at this position
        tile_vertices = self._get_vertex_positions(q, r)
        
        # For each vertex of this tile, check if it completes a hexagon
        for vertex_idx, vertex_pos in enumerate(tile_vertices):
            # Get all tiles that share this vertex
            tiles_at_vertex = self._get_tiles_sharing_vertex(vertex_pos, exclude=(q, r))
            
            # A hexagon needs exactly 5 other tiles at this vertex (6 total including this one)
            if len(tiles_at_vertex) == 5:
                # All values at this vertex must match
                vertex_value = tile.values[vertex_idx]
                all_match = all(
                    self._get_vertex_value_at_position(t, vertex_pos) == vertex_value
                    for t in tiles_at_vertex
                )
                if all_match:
                    return True
        
        return False
    
    def _get_vertex_positions(self, q: int, r: int) -> List[Tuple[float, float]]:
        """
        Get approximate vertex positions for the triangle at (q, r).
        Used for detecting shared vertices.
        """
        # Simplified vertex calculation for hexagon detection
        # This is a logical representation, not exact coordinates
        is_up = self.is_pointing_up(q, r)
        
        if is_up:
            return [
                (q + 0.5, r - 0.33),      # Top vertex (v0)
                (q - 0.5, r + 0.33),      # Bottom-left (v1)
                (q + 0.5, r + 0.33),      # Bottom-right (v2)
            ]
        else:
            return [
                (q + 0.5, r + 0.33),      # Bottom vertex (v0)
                (q - 0.5, r - 0.33),      # Top-left (v1)
                (q + 0.5, r - 0.33),      # Top-right (v2)
            ]
    
    def _get_tiles_sharing_vertex(self, vertex_pos: Tuple[float, float], 
                                   exclude: Tuple[int, int] = None) -> List[PlacedTile]:
        """Get all placed tiles that share a vertex position."""
        # Simplified: check tiles within logical range that could share this vertex
        sharing = []
        vx, vy = vertex_pos
        
        for (q, r), tile in self.tiles.items():
            if exclude and (q, r) == exclude:
                continue
            
            tile_vertices = self._get_vertex_positions(q, r)
            for tv in tile_vertices:
                if abs(tv[0] - vx) < 0.01 and abs(tv[1] - vy) < 0.01:
                    sharing.append(tile)
                    break
        
        return sharing
    
    def _get_vertex_value_at_position(self, placed_tile: PlacedTile, 
                                       vertex_pos: Tuple[float, float]) -> Optional[int]:
        """Get the value of a tile's vertex at a specific position."""
        tile_vertices = self._get_vertex_positions(placed_tile.q, placed_tile.r)
        
        for idx, tv in enumerate(tile_vertices):
            if abs(tv[0] - vertex_pos[0]) < 0.01 and abs(tv[1] - vertex_pos[1]) < 0.01:
                return placed_tile.tile.values[idx]
        
        return None
    
    def place_tile(self, tile: Triomino, q: int, r: int, 
                   rotation: int, player_id: Optional[int] = None) -> PlacementResult:
        """
        Place a tile on the board at position (q, r) with given rotation.
        
        Args:
            tile: The tile to place
            q, r: Board position
            rotation: Rotation (0, 1, or 2)
            player_id: ID of player placing the tile
            
        Returns:
            PlacementResult with success status and points earned
        """
        # Check if position is valid
        if self.is_position_occupied(q, r):
            return PlacementResult(
                success=False,
                message=f"Position ({q}, {r}) is already occupied"
            )
        
        # Check if this connects to existing tiles (unless first tile)
        if not self.is_empty():
            adjacent = self.get_adjacent_tiles(q, r)
            if not adjacent:
                return PlacementResult(
                    success=False,
                    message=f"Position ({q}, {r}) is not adjacent to any placed tiles"
                )
        
        # Set rotation and check edge matching
        tile.rotation = rotation
        required_edges = self._get_required_edges(q, r)
        
        for edge_idx, required_edge in required_edges.items():
            tile_edge = tile.get_edge(edge_idx)
            if not tile_edge.matches(required_edge):
                return PlacementResult(
                    success=False,
                    message=f"Edge {edge_idx} does not match: {tile_edge} vs {required_edge}"
                )
        
        # Valid placement - calculate points
        placed = PlacedTile(tile=tile.copy(), q=q, r=r, player_id=player_id)
        
        # Determine bonus
        is_bridge = self._check_bridge(q, r, tile, required_edges)
        is_hexagon = self._check_hexagon(q, r, tile)
        
        bonus_type = BonusType.NONE
        bonus_points = 0
        
        if is_hexagon:
            # TODO: Check for double hexagon
            bonus_type = BonusType.HEXAGON
            bonus_points = 50
        elif is_bridge:
            bonus_type = BonusType.BRIDGE
            bonus_points = 40
        
        base_points = tile.sum_value
        total_points = base_points + bonus_points
        
        # Add to board
        self.tiles[(q, r)] = placed
        self._move_history.append(placed)
        
        return PlacementResult(
            success=True,
            tile=placed,
            base_points=base_points,
            bonus_type=bonus_type,
            bonus_points=bonus_points,
            total_points=total_points,
            message=f"Placed {tile} at ({q}, {r})"
        )
    
    def place_first_tile(self, tile: Triomino, player_id: Optional[int] = None,
                         is_triple: bool = False) -> PlacementResult:
        """
        Place the first tile of the game at the origin.
        
        Args:
            tile: The starting tile
            player_id: ID of starting player
            is_triple: True if this is a triple tile (for bonus calculation)
            
        Returns:
            PlacementResult with bonus applied if applicable
        """
        if not self.is_empty():
            return PlacementResult(
                success=False,
                message="Board is not empty - cannot place first tile"
            )
        
        placed = PlacedTile(tile=tile.copy(), q=0, r=0, player_id=player_id)
        self.tiles[(0, 0)] = placed
        self._move_history.append(placed)
        
        base_points = tile.sum_value
        bonus_points = 0
        bonus_type = BonusType.NONE
        
        # Triple bonus
        if is_triple:
            if tile.is_triple_zero():
                bonus_points = 40  # Special 0-0-0 bonus
            else:
                bonus_points = 10  # Regular triple bonus
        
        return PlacementResult(
            success=True,
            tile=placed,
            base_points=base_points,
            bonus_type=bonus_type,
            bonus_points=bonus_points,
            total_points=base_points + bonus_points,
            message=f"First tile: {tile} placed at origin"
        )
    
    @property
    def tile_count(self) -> int:
        """Number of tiles on the board."""
        return len(self.tiles)
    
    @property
    def move_history(self) -> List[PlacedTile]:
        """List of placed tiles in order."""
        return self._move_history.copy()
    
    def get_bounds(self) -> Tuple[int, int, int, int]:
        """Get bounding box of placed tiles: (min_q, max_q, min_r, max_r)."""
        if self.is_empty():
            return (0, 0, 0, 0)
        
        qs = [pos[0] for pos in self.tiles.keys()]
        rs = [pos[1] for pos in self.tiles.keys()]
        return (min(qs), max(qs), min(rs), max(rs))
    
    def __repr__(self) -> str:
        return f"GameBoard({len(self.tiles)} tiles)"
