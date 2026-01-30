"""
Triomino Tile Model

Represents a single triangular tile with three vertex values (0-5).
Handles rotation and edge matching logic.
"""
from __future__ import annotations
from typing import Tuple, List, Optional
from dataclasses import dataclass


@dataclass(frozen=True)
class Edge:
    """Represents one edge of a triomino with two vertex values."""
    v1: int
    v2: int
    
    def matches(self, other: Edge) -> bool:
        """Check if this edge matches another edge (values must match in reverse order)."""
        return self.v1 == other.v2 and self.v2 == other.v1
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Edge):
            return False
        return self.v1 == other.v1 and self.v2 == other.v2
    
    def __hash__(self) -> int:
        return hash((self.v1, self.v2))
    
    def __repr__(self) -> str:
        return f"({self.v1}-{self.v2})"


class Triomino:
    """
    A triangular tile with three vertex values.
    
    Vertex positions (when pointing up ▲):
        - v0: top vertex
        - v1: bottom-left vertex  
        - v2: bottom-right vertex
    
    Edge indices:
        - edge 0: left side (v0 to v1)
        - edge 1: bottom side (v1 to v2)
        - edge 2: right side (v2 to v0)
    
    Rotation: 0, 1, or 2 steps (each step = 120° clockwise)
    """
    
    def __init__(self, a: int, b: int, c: int):
        """
        Create a triomino with values a, b, c.
        Values are stored as provided; deck generation ensures canonical ordering.
        """
        if not all(0 <= v <= 5 for v in (a, b, c)):
            raise ValueError(f"Values must be 0-5, got {a}, {b}, {c}")
        
        # Store base values (immutable)
        self._base: Tuple[int, int, int] = (a, b, c)
        self._rotation: int = 0
    
    @property
    def values(self) -> Tuple[int, int, int]:
        """Get current vertex values after rotation (v0, v1, v2)."""
        a, b, c = self._base
        r = self._rotation % 3
        if r == 0:
            return (a, b, c)
        elif r == 1:
            return (c, a, b)  # 120° clockwise
        else:  # r == 2
            return (b, c, a)  # 240° clockwise

    def get_values(self, orientation: str = "up") -> Tuple[int, int, int]:
        """
        Get vertex values considering rotation.
        
        For triangles at the same grid position:
        - UP: v0=top, v1=bottom-left, v2=bottom-right
        - DOWN: v0=bottom, v1=top-left, v2=top-right
        
        Vertices 1 and 2 are at the SAME geometric positions for UP and DOWN,
        so no swap is needed. The values map directly.
        """
        return self.values
    
    @property
    def rotation(self) -> int:
        """Current rotation state (0, 1, or 2)."""
        return self._rotation
    
    @rotation.setter
    def rotation(self, value: int) -> None:
        """Set rotation to a specific value."""
        self._rotation = value % 3
    
    def rotate(self, steps: int = 1) -> Triomino:
        """Rotate clockwise by given steps. Returns self for chaining."""
        self._rotation = (self._rotation + steps) % 3
        return self
    
    def copy(self) -> Triomino:
        """Create a copy of this tile with the same rotation."""
        t = Triomino(*self._base)
        t._rotation = self._rotation
        return t
    
    def get_edge(self, edge_index: int, orientation: str = "up") -> Edge:
        """
        Get the edge at the given index (0, 1, or 2).
        
        For an up-pointing triangle (▲):
            - edge 0: left side (v0 → v1)
            - edge 1: bottom side (v1 → v2)
            - edge 2: right side (v2 → v0)
        """
        v0, v1, v2 = self.get_values(orientation)
        if edge_index == 0:
            return Edge(v0, v1)  # left
        elif edge_index == 1:
            return Edge(v1, v2)  # bottom
        else:  # edge_index == 2
            return Edge(v2, v0)  # right
    
    def get_all_edges(self, orientation: str = "up") -> List[Edge]:
        """Get all three edges for a given orientation."""
        return [self.get_edge(i, orientation) for i in range(3)]
    
    @property
    def sum_value(self) -> int:
        """Sum of all three vertex values (score when placed)."""
        return sum(self._base)
    
    def is_triple(self) -> bool:
        """Check if all three values are the same."""
        a, b, c = self._base
        return a == b == c
    
    def is_triple_zero(self) -> bool:
        """Check if this is the 0-0-0 tile."""
        return self._base == (0, 0, 0)
    
    def find_rotation_for_edge_match(self, edge_index: int, target_edge: Edge,
                                     orientation: str = "up") -> Optional[int]:
        """
        Find a rotation that makes the specified edge match the target.
        
        Args:
            edge_index: Which edge of this tile should match (0, 1, or 2)
            target_edge: The edge values we need to match against
            
        Returns:
            Rotation value (0, 1, or 2) if match possible, None otherwise
        """
        original_rotation = self._rotation
        for r in range(3):
            self._rotation = r
            if self.get_edge(edge_index, orientation).matches(target_edge):
                self._rotation = original_rotation
                return r
        self._rotation = original_rotation
        return None
    
    def __eq__(self, other: object) -> bool:
        """Two tiles are equal if they have the same base values (ignoring rotation)."""
        if not isinstance(other, Triomino):
            return False
        # Compare sorted base values to handle different orderings
        return sorted(self._base) == sorted(other._base)
    
    def __hash__(self) -> int:
        return hash(tuple(sorted(self._base)))
    
    def __repr__(self) -> str:
        v = self.values
        base = f"[{v[0]}-{v[1]}-{v[2]}]"
        if self._rotation != 0:
            return f"Triomino{base}@r{self._rotation}"
        return f"Triomino{base}"
    
    def __str__(self) -> str:
        v = self.values
        return f"{v[0]}-{v[1]}-{v[2]}"

@dataclass
class PlacedTile:
    """A tile that has been placed on the board at a specific position.
    
    IMPORTANT: The tile is copied at construction time to freeze its rotation.
    This prevents corruption when the original tile's rotation changes during
    subsequent move searches.
    """
    tile: Triomino
    q: int  # Row in new system
    r: int  # Col in new system
    player_id: Optional[int] = None
    orientation: str = 'up'  # 'up' or 'down'
    
    def __post_init__(self):
        # Make a copy of the tile to freeze its current rotation state
        self.tile = self.tile.copy()
    
    @property
    def row(self) -> int:
        return self.q
    
    @property
    def col(self) -> int:
        return self.r
    
    @property
    def position(self) -> Tuple[int, int, str]:
        return (self.q, self.r, self.orientation)

    @property
    def values(self) -> Tuple[int, int, int]:
        return self.tile.get_values(self.orientation)

    def get_edge(self, edge_index: int) -> Edge:
        return self.tile.get_edge(edge_index, self.orientation)
    
    def __repr__(self) -> str:
        arrow = "▲" if self.orientation == 'up' else "▼"
        player = f" P{self.player_id}" if self.player_id is not None else ""
        return f"Placed({self.tile} at ({self.q},{self.r}){arrow}{player})"

