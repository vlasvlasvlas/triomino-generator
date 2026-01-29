"""
Player Model

Represents a player in the Triomino game with their hand and score.
"""
from __future__ import annotations
from typing import List, Optional
from dataclasses import dataclass, field

from .tile import Triomino


@dataclass
class Player:
    """
    A player in the Triomino game.
    
    Attributes:
        name: Player identifier/name
        hand: List of tiles in player's hand
        score: Current cumulative score
        is_computer: True if this is an AI-controlled player
    """
    name: str
    hand: List[Triomino] = field(default_factory=list)
    score: int = 0
    is_computer: bool = True
    
    def draw_tiles(self, deck: List[Triomino], count: int) -> List[Triomino]:
        """
        Draw tiles from the deck into the player's hand.
        
        Args:
            deck: The pool of available tiles (will be modified)
            count: Number of tiles to draw
            
        Returns:
            List of tiles actually drawn (may be less if deck runs out)
        """
        drawn = []
        for _ in range(count):
            if not deck:
                break
            tile = deck.pop()
            self.hand.append(tile)
            drawn.append(tile)
        return drawn
    
    def play_tile(self, tile: Triomino) -> Optional[Triomino]:
        """
        Remove a tile from hand (when placing it on the board).
        
        Args:
            tile: The tile to play
            
        Returns:
            The tile if found and removed, None otherwise
        """
        for i, t in enumerate(self.hand):
            if t == tile:
                return self.hand.pop(i)
        return None
    
    def has_tile(self, tile: Triomino) -> bool:
        """Check if player has a specific tile in hand."""
        return any(t == tile for t in self.hand)
    
    @property
    def hand_value(self) -> int:
        """Sum of all tile values in hand."""
        return sum(t.sum_value for t in self.hand)
    
    @property
    def hand_size(self) -> int:
        """Number of tiles in hand."""
        return len(self.hand)
    
    @property
    def has_empty_hand(self) -> bool:
        """Check if player has no tiles left."""
        return len(self.hand) == 0
    
    def get_highest_triple(self) -> Optional[Triomino]:
        """Get the highest triple tile in hand, if any."""
        triples = [t for t in self.hand if t.is_triple()]
        if not triples:
            return None
        return max(triples, key=lambda t: t.sum_value)
    
    def get_highest_tile(self) -> Optional[Triomino]:
        """Get the tile with highest total value in hand."""
        if not self.hand:
            return None
        return max(self.hand, key=lambda t: t.sum_value)
    
    def add_score(self, points: int) -> None:
        """Add points to player's score (can be negative for penalties)."""
        self.score += points
    
    def reset_for_new_round(self) -> None:
        """Clear hand for a new round (score persists)."""
        self.hand.clear()
    
    def __repr__(self) -> str:
        return f"Player({self.name}, score={self.score}, hand={len(self.hand)} tiles)"
    
    def show_hand(self) -> str:
        """Get a string representation of the player's hand."""
        if not self.hand:
            return f"{self.name}: [empty]"
        tiles_str = ", ".join(str(t) for t in self.hand)
        return f"{self.name} ({self.hand_value} pts): [{tiles_str}]"


def get_starting_player(players: List[Player]) -> tuple[Player, Triomino, bool]:
    """
    Determine who starts the game based on highest triple rule.
    
    Returns:
        Tuple of (starting_player, starting_tile, has_triple_bonus)
    """
    # First, check for triples
    best_triple = None
    best_player = None
    
    for player in players:
        triple = player.get_highest_triple()
        if triple:
            if best_triple is None or triple.sum_value > best_triple.sum_value:
                best_triple = triple
                best_player = player
    
    if best_triple:
        return (best_player, best_triple, True)
    
    # No triples - use highest tile value
    best_tile = None
    best_player = None
    
    for player in players:
        tile = player.get_highest_tile()
        if tile:
            if best_tile is None or tile.sum_value > best_tile.sum_value:
                best_tile = tile
                best_player = player
    
    return (best_player, best_tile, False)
