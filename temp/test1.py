from __future__ import annotations
import random
import math
import matplotlib.pyplot as plt
import time
from typing import List, Tuple, Dict

# Define constants for drawing, consistent with matplotlib visualization
SIZE = 180.0  # larger pieces for clearer visuals
H = SIZE * math.sqrt(3) / 2 # Height of an equilateral triangle

def axial_to_cart(q: int, r: int) -> Tuple[float, float]:
    """
    Translates axial coordinates (q, r) to Cartesian coordinates (x, y)
    for the *center* of the triangle cell.
    This mapping ensures proper alignment and spacing for the triangular grid.
    """
    # X-coordinate: q * side_length + r * half_side_length (for staggering)
    x = q * SIZE + r * SIZE * 0.5
    # Y-coordinate: r * triangle_height * 1.5 (for vertical stacking of rows)
    y = r * H * 1.5
    return x, y

def triangle_vertices(q: int, r: int) -> List[Tuple[float, float]]:
    """
    Calculates the Cartesian coordinates of the vertices for a triangle
    at axial coordinates (q, r).
    Triangle orientation is decided by (q + r) parity:
        even  → ▲   (up-pointing triangle)
        odd   → ▼   (down-pointing triangle)

    Returns the three vertices in a consistent order:
    [pointy_vertex_coord, base_left_vertex_coord, base_right_vertex_coord]
    This order aligns with Triomino.values (v0, v1, v2).
    """
    cx, cy = axial_to_cart(q, r) # Get the center point of the triangle

    is_up_triangle = ((q + r) % 2 == 0)

    if is_up_triangle: # ▲ up-pointing triangle
        # Vertices relative to the center (cx, cy)
        v0_coord = (cx, cy - H * 2 / 3)         # Top vertex (pointy)
        v1_coord = (cx - SIZE / 2, cy + H / 3)  # Bottom-left vertex
        v2_coord = (cx + SIZE / 2, cy + H / 3)  # Bottom-right vertex
    else: # ▼ down-pointing triangle
        # Vertices relative to the center (cx, cy)
        v0_coord = (cx, cy + H * 2 / 3)         # Bottom vertex (pointy)
        v1_coord = (cx - SIZE / 2, cy - H / 3)  # Top-left vertex
        v2_coord = (cx + SIZE / 2, cy - H / 3)  # Top-right vertex
    
    # Return in a consistent order: [pointy_vertex, base_left_vertex, base_right_vertex]
    return [v0_coord, v1_coord, v2_coord]


# Helper: full official Triomino set (56 tiles, numbers 0‑5 without order)
def full_deck() -> List["Triomino"]:
    """Generates a complete set of 56 unique Triomino tiles."""
    deck: List[Triomino] = []
    # Iterate through all unique combinations of three numbers from 0 to 5
    for a in range(6):
        for b in range(a, 6): # Ensure b >= a to avoid duplicates like (1,0,0) and (0,1,0)
            for c in range(b, 6): # Ensure c >= b
                deck.append(Triomino(a, b, c))
    return deck


# ────────────────────────────────────────────────────────────────────────────
# NEIGHBOUR VECTORS FOR OUR TRIANGULAR GRID
#
# We represent each triangle by integer cell (q, r).
#   (q + r) % 2 == 0  →  ▲  (apex up)
#   (q + r) % 2 == 1  →  ▼  (apex down)
#
# Edges are indexed 0‑1‑2 in COUNTER‑CLOCKWISE order starting at
# the edge that touches the *left‑hand* base vertex.
#
# Using that convention, the neighbour coordinates (dq, dr) and the
# edge that the neighbour must match are:
#
#   host ▲ (even):
#       edge‑0  ↔  ▼ neighbour at (q‑1, r)     via neighbour edge‑1
#       edge‑1  ↔  ▼ neighbour at (q,   r‑1)   via neighbour edge‑0
#       edge‑2  ↔  ▼ neighbour at (q,   r+1)   via neighbour edge‑2
#
#   host ▼ (odd):
#       edge‑0  ↔  ▲ neighbour at (q,   r+1)   via neighbour edge‑1
#       edge‑1  ↔  ▲ neighbour at (q+1, r)     via neighbour edge‑0
#       edge‑2  ↔  ▲ neighbour at (q,   r‑1)   via neighbour edge‑2
#
# The tables below encode only the (dq,dr); the edge‑mapping is held
# in OPPOSITE_EDGE_MAP so we can look it up quickly.
# ────────────────────────────────────────────────────────────────────────────
NEI = {
    # (dq, dr) for edges 0,1,2
    "up":  [(-1, 0), (+1, 0), (0, +1)],   # left, right, bottom neighbors for an 'up' triangle
    "down":[(0, -1), (0, +1), (+1, 0)]    # top-left, top-right, bottom-right neighbors for a 'down' triangle
}

# edge on host  →  edge on neighbour
#   0 ↔ 1 ,  1 ↔ 0 , 2 ↔ 2
OPPOSITE_EDGE_MAP: Dict[int, int] = {0: 1, 1: 0, 2: 2}


def edges_for(tri: "Triomino", is_up_orientation: bool) -> List[Tuple[int, int]]:
    """
    Return the three directed edges for this Triomino as (left‑to‑right) pairs
    in COUNTER‑CLOCKWISE order (edge‑0, edge‑1, edge‑2).

    The order is chosen so that two adjacent triangles share *exactly the same*
    (a, b) tuple on the common edge.
    """
    a, b, c = tri.values            # (pointy, base‑left, base‑right)

    if is_up_orientation:           # ▲
        # edge‑0 (left)   :  b → a
        # edge‑1 (right)  :  c → a
        # edge‑2 (bottom) :  c → b
        return [(b, a), (c, a), (c, b)]
    else:                           # ▼
        # edge‑0 (top‑left)  :  a → b
        # edge‑1 (top‑right) :  a → c
        # edge‑2 (top base)  :  b → c
        return [(a, b), (a, c), (b, c)]


def generate_demidegrama(seed: int | None = None,
                         max_steps: int = 56) -> List["PlacedPiece"]:
    """
    Simulate an *automatic* Triomino round that follows the real rule:
    a new tile can be placed only when a free edge matches both numbers
    of that border (rotation included).
    Stops when no legal move exists or max_steps is reached.
    Returns the list of PlacedPiece objects in the order they were placed.
    """
    if seed is not None:
        random.seed(seed) # Initialize the random number generator if a seed is provided

    # 1. Build and shuffle the deck
    deck = full_deck()
    random.shuffle(deck) # Randomize the order of tiles

    # 2. Find the highest triple (e.g., 5-5-5) to start the game
    # This ensures a consistent and valid starting point based on Triomino rules.
    start = max([tri for tri in deck if tri.values[0] == tri.values[1] == tri.values[2]],
                key=lambda t: t.values[0])
    deck.remove(start) # Remove the starting tile from the deck

    up_first = True  # Convention: the starting triple is an 'up' triangle (▲)
    # Initialize the list of placed pieces with the starting tile at (0,0)
    placed: list[PlacedPiece] = [PlacedPiece(start, 0, 0)]
    # Keep track of occupied grid positions to prevent placing tiles on top of each other
    occupied = {(0, 0): placed[0]}

    # Frontier: a list of open edges where new tiles can be placed.
    # Each entry is (q, r, edge_idx, required_pair), where:
    # - (q, r) is the axial coordinate of the host triangle
    # - edge_idx is the index of the open edge on the host triangle (0, 1, or 2)
    # - required_pair is the (v_left, v_right) tuple of values needed to match this edge
    frontier: list[Tuple[int, int, int, Tuple[int, int]]] = [
        (0, 0, e, pair) for e, pair in enumerate(edges_for(start, up_first))
    ]

    steps = 1 # Counter for the number of tiles placed
    # Continue as long as we haven't reached max_steps and there are tiles left in the deck
    while steps < max_steps and deck:
        random.shuffle(frontier) # Randomly pick an open edge to try and place a tile
        progress_made = False # Flag to check if a tile was successfully placed in this step

        # Iterate through the frontier to find a suitable placement
        for fq, fr, edge_idx, need_pair in frontier:
            # Determine the orientation of the host triangle
            host_up = ((fq + fr) % 2 == 0)
            ori = "up" if host_up else "down"

            # Calculate the axial coordinates of the potential neighbor position
            dq, dr = NEI[ori][edge_idx]
            nq, nr = fq + dq, fr + dr

            # If the neighbor position is already occupied, skip this frontier edge
            if (nq, nr) in occupied:
                continue

            # Search for a tile in the remaining deck that can match the 'need_pair'
            for tri in deck:
                for rot in range(3):
                    tri.rotate(rot)          # Rotate the tile in-place
                    neighbour_up = not host_up # The neighbor triangle will have the opposite orientation

                    # Get the edges of the current tile in its current rotation and orientation
                    edge_pairs = edges_for(tri, neighbour_up)

                    # Determine which edge of the *neighbor* tile (tri) needs to match the host's edge.
                    connecting_edge_on_neighbor = OPPOSITE_EDGE_MAP[edge_idx]

                    # Check if the edge values match (the two numbers forming the edge)
                    if edge_pairs[connecting_edge_on_neighbor] == need_pair:
                        # Legal placement!
                        new_piece = PlacedPiece(tri, nq, nr)
                        placed.append(new_piece)       # Add the new piece to the placed list
                        occupied[(nq, nr)] = new_piece # Mark the position as occupied
                        deck.remove(tri)               # Remove the tile from the deck

                        # Add the three new open edges of the newly placed piece to the frontier
                        new_edge_data = edges_for(tri, neighbour_up)
                        for e_idx_new, pair_new in enumerate(new_edge_data):
                            frontier.append((nq, nr, e_idx_new, pair_new))

                        # Remove the edge that is now closed (the one we just matched) from the frontier
                        frontier = [t for t in frontier
                                    if not (t[0] == fq and t[1] == fr and t[2] == edge_idx)]

                        progress_made = True # Indicate that a tile was placed
                        steps += 1           # Increment the step counter
                        break # Break from the rotation loop, as we found a match for this tile
                if progress_made:
                    break # Break from the deck iteration, as we found a tile for this frontier edge
            if progress_made:
                break # Break from the frontier iteration, as we made progress

        # If no progress was made in this entire step (no legal moves found for any frontier edge)
        if not progress_made:
            break  # The simulation is blocked, no more legal moves exist

    return placed


# Replacement: Triomino class
class Triomino:
    """Single triangular tile with three integer values and a rotation."""
    def __init__(self, a: int, b: int, c: int):
        # Store values in canonical order (v0,v1,v2) and rotation index
        # The _base tuple ensures the original values are preserved.
        self._base: Tuple[int, int, int] = (a, b, c)
        self.rot: int = 0  # Current rotation: 0, 1, or 2 (0=no rotation, 1=120deg, 2=240deg clockwise)

    @property
    def values(self) -> Tuple[int, int, int]:
        """
        Returns the values of the triomino in its current rotated orientation.
        The order is consistent with triangle_vertices:
        (value at pointy vertex, value at base-left vertex, value at base-right vertex)
        """
        v = self._base
        r = self.rot % 3 # Ensure rotation is within 0, 1, 2
        if r == 0:
            return v # No rotation
        elif r == 1:
            return (v[2], v[0], v[1])  # Rotate once clockwise (v0->v1, v1->v2, v2->v0)
        else:  # r == 2
            return (v[1], v[2], v[0])  # Rotate twice clockwise

    def rotate(self, k: int = 1) -> None:
        """Rotate the triomino clockwise by *k* steps (each step = 120°)."""
        self.rot = (self.rot + k) % 3

    def __repr__(self) -> str:
        """String representation of the Triomino tile."""
        return f"Triomino{self.values}@{self.rot}"

# Helper container that stores a Triomino plus its grid position
class PlacedPiece:
    """Represents a Triomino tile that has been placed on the game board."""
    def __init__(self, tri: Triomino, q: int, r: int):
        self.tri = tri # The Triomino object itself
        self.q = q     # Axial q-coordinate
        self.r = r     # Axial r-coordinate

    def vertices(self) -> List[Tuple[float, float]]:
        """
        Returns the Cartesian coordinates of the vertices of this placed triangle.
        Relies on the global triangle_vertices() function.
        """
        return triangle_vertices(self.q, self.r)

    def __repr__(self):
        """String representation of the placed piece."""
        return f"Placed({self.tri}, q={self.q}, r={self.r})"

def draw_demidegrama(pieces: List["PlacedPiece"], face: str = "#e10600", edge: str = "white",
                     animate: bool = True, animation_delay: float = 0.05,
                     draw_numbers: bool = True):
    """
    Draws the placed Triomino pieces using matplotlib, with optional animation.
    It also draws a background triangular grid and numbers on the vertices.
    """
    fig, ax = plt.subplots(figsize=(10, 10)) # Create a figure and a set of subplots, larger for better view
    ax.set_aspect("equal") # Ensure equal aspect ratio so triangles are not distorted
    ax.axis("off") # Turn off the axis labels and ticks

    # Determine the extent of the grid based on placed pieces
    if pieces:
        qs = [p.q for p in pieces]
        rs = [p.r for p in pieces]
        min_q, max_q = min(qs), max(qs)
        min_r, max_r = min(rs), max(rs)
    else:
        min_q, max_q = -5, 5 # Default range if no pieces
        min_r, max_r = -5, 5

    # Expand the grid slightly beyond the placed pieces for better visual context
    grid_margin = 3
    min_q -= grid_margin
    max_q += grid_margin
    min_r -= grid_margin
    max_r += grid_margin

    # Draw the background triangular grid
    for q in range(min_q, max_q + 1):
        for r in range(min_r, max_r + 1):
            # Only draw grid cells that are within a reasonable distance
            # This prevents drawing an excessively large grid for sparse patterns
            # The condition abs(q) + abs(r) + abs(-q - r) is related to cube coordinates distance from origin
            # Adjusted to use the new coordinate system's distance logic
            center_x, center_y = axial_to_cart(q, r)
            if math.sqrt(center_x**2 + center_y**2) > max(abs(max_q), abs(max_r)) * SIZE * 1.5:
                continue

            verts = triangle_vertices(q, r)
            grid_poly = plt.Polygon(verts, closed=True,
                                    facecolor='lightgray', edgecolor='#dddddd', linewidth=0.5, alpha=0.3)
            ax.add_patch(grid_poly)

    # Autoscale the view to fit all placed pieces and the grid
    # Get all x and y coordinates of the triangle centers for scaling
    all_qs = [q for q in range(min_q, max_q + 1)]
    all_rs = [r for r in range(min_r, max_r + 1)]
    all_coords = [axial_to_cart(q, r) for q in all_qs for r in all_rs]
    if all_coords:
        xs, ys = zip(*all_coords)
        m = SIZE * 1.5 # Margin for the plot limits, slightly larger
        ax.set_xlim(min(xs) - m, max(xs) + m)
        ax.set_ylim(min(ys) - m, max(ys) + m)

    # Enable interactive mode for animation
    plt.ion()
    plt.show() # Show the initial empty grid

    # Draw the pieces one by one with animation
    for i, p in enumerate(pieces):
        verts = p.vertices()
        poly = plt.Polygon(verts, closed=True,
                           facecolor=face, edgecolor=edge, linewidth=1.2)
        ax.add_patch(poly)

        if draw_numbers: # Draw numbers on vertices
            # Get the values of the triomino in its current rotation
            tri_values = p.tri.values # (pointy_val, base_left_val, base_right_val)
            # Get the Cartesian coordinates of the vertices
            tri_coords = p.vertices() # [pointy_coord, base_left_coord, base_right_coord]

            # Place text for each vertex value
            for j in range(3):
                x, y = tri_coords[j]
                val = tri_values[j]
                
                # Adjust text position slightly towards the center of the triangle
                # This ensures numbers are inside the tile and readable.
                cx, cy = sum(v[0] for v in tri_coords)/3, sum(v[1] for v in tri_coords)/3
                
                # Calculate vector from center to vertex
                vec_x, vec_y = x - cx, y - cy
                
                # Normalize vector and scale to move inward
                vec_len = math.sqrt(vec_x**2 + vec_y**2)
                if vec_len > 0:
                    norm_vec_x, norm_vec_y = vec_x / vec_len, vec_y / vec_len
                else:
                    norm_vec_x, norm_vec_y = 0, 0 # Avoid division by zero for coincident points

                # Move inward by a fraction of the distance from center to vertex
                inward_offset_factor = 0.25 # Adjust this value (0 to 1) to control how far inward
                
                text_x = x - norm_vec_x * (SIZE * inward_offset_factor)
                text_y = y - norm_vec_y * (SIZE * inward_offset_factor)

                ax.text(text_x, text_y, str(val),
                        color='white', fontsize=14, ha='center', va='center',
                        weight='bold')

        plt.draw() # Redraw the canvas to show the newly added piece and numbers
        if animate and i < len(pieces) - 1: # Don't pause after the last piece
            plt.pause(animation_delay) # Pause for animation effect

    plt.ioff() # Turn off interactive mode
    plt.show() # Keep the final plot open until closed manually

if __name__ == "__main__":
    # Generate the Triomino placement
    pcs = generate_demidegrama(seed=42, max_steps=56)
    print(f"Placed {len(pcs)} tiles.") # Print the number of tiles placed
    # Draw the generated demidegrama with animation and numbers
    draw_demidegrama(pcs, animate=True, animation_delay=0.05, draw_numbers=True)
