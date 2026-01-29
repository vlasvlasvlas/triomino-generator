"""
AI Strategies for Computer Players

Different strategies for playing Triominó automatically.
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import List, Optional, Tuple
from dataclasses import dataclass

from src.models import Triomino, Player, GameBoard, ValidPlacement


@dataclass
class ScoredMove:
    """A potential move with its calculated score."""
    tile: Triomino
    placement: ValidPlacement
    base_score: int
    bonus_score: int
    
    @property
    def total_score(self) -> int:
        return self.base_score + self.bonus_score
    
    def __repr__(self) -> str:
        bonus = f" +{self.bonus_score}" if self.bonus_score else ""
        return f"Move({self.tile} → ({self.placement.q},{self.placement.r}){bonus})"


class AIStrategy(ABC):
    """Base class for AI strategies."""
    
    name: str = "Base Strategy"
    
    @abstractmethod
    def choose_move(self, player: Player, board: GameBoard) -> Optional[ScoredMove]:
        """
        Choose the best move for the player.
        
        Args:
            player: The player to choose for
            board: Current game board
            
        Returns:
            ScoredMove or None if no valid moves
        """
        pass
    
    def get_all_valid_moves(self, player: Player, board: GameBoard) -> List[ScoredMove]:
        """Get all valid moves for a player with scores."""
        moves = []
        
        for tile in player.hand:
            placements = board.find_valid_placements(tile)
            for placement in placements:
                bonus = 0
                if placement.is_hexagon:
                    bonus = 50
                elif placement.is_bridge:
                    bonus = 40
                
                moves.append(ScoredMove(
                    tile=tile,
                    placement=placement,
                    base_score=tile.sum_value,
                    bonus_score=bonus
                ))
        
        return moves


class GreedyStrategy(AIStrategy):
    """
    Simple greedy strategy: always play the highest-scoring move.
    
    Prioritizes:
    1. Moves with bonuses (hexagon > bridge)
    2. Highest tile value
    """
    
    name = "Greedy"
    
    def choose_move(self, player: Player, board: GameBoard) -> Optional[ScoredMove]:
        moves = self.get_all_valid_moves(player, board)
        if not moves:
            return None
        
        # Sort by total score descending
        moves.sort(key=lambda m: m.total_score, reverse=True)
        return moves[0]


class BalancedStrategy(AIStrategy):
    """
    Balanced strategy: considers both immediate score and hand flexibility.
    
    Tries to avoid getting stuck with unmatchable tiles.
    """
    
    name = "Balanced"
    
    def choose_move(self, player: Player, board: GameBoard) -> Optional[ScoredMove]:
        moves = self.get_all_valid_moves(player, board)
        if not moves:
            return None
        
        # Score each move considering multiple factors
        scored = []
        for move in moves:
            score = move.total_score
            
            # Bonus for playing tiles with extreme values (harder to match later)
            if move.tile.sum_value >= 12:  # High value tiles
                score += 3
            elif move.tile.sum_value <= 3:  # Low value tiles
                score += 2
            
            # Bonus for hexagon/bridge (these are valuable)
            if move.placement.is_hexagon:
                score += 10
            elif move.placement.is_bridge:
                score += 5
            
            scored.append((score, move))
        
        scored.sort(key=lambda x: x[0], reverse=True)
        return scored[0][1]


class DefensiveStrategy(AIStrategy):
    """
    Defensive strategy: tries to avoid leaving good opportunities for opponents.
    
    Prefers moves that don't create easy hexagon/bridge opportunities.
    """
    
    name = "Defensive"
    
    def choose_move(self, player: Player, board: GameBoard) -> Optional[ScoredMove]:
        moves = self.get_all_valid_moves(player, board)
        if not moves:
            return None
        
        # For now, same as greedy but with slight preference for lower-value moves
        # to save high-value tiles for better opportunities
        moves.sort(key=lambda m: (
            -m.bonus_score,  # Still prioritize bonuses
            m.base_score     # But prefer lower base scores (ascending)
        ))
        return moves[0]


class RandomStrategy(AIStrategy):
    """
    Random strategy: picks a random valid move.
    
    Useful for testing and variety.
    """
    
    name = "Random"
    
    def choose_move(self, player: Player, board: GameBoard) -> Optional[ScoredMove]:
        import random
        moves = self.get_all_valid_moves(player, board)
        if not moves:
            return None
        return random.choice(moves)


# Default strategy
DEFAULT_STRATEGY = GreedyStrategy()


def get_strategy(name: str) -> AIStrategy:
    """Get a strategy by name."""
    strategies = {
        'greedy': GreedyStrategy(),
        'balanced': BalancedStrategy(),
        'defensive': DefensiveStrategy(),
        'random': RandomStrategy(),
    }
    return strategies.get(name.lower(), DEFAULT_STRATEGY)
