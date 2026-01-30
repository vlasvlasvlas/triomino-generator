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
        return f"Move({self.tile} → ({self.placement.row},{self.placement.col}){bonus})"


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
                bonus = (placement.hexagon_count * 50) + (placement.bridge_count * 40)
                
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
            if move.placement.hexagon_count > 0:
                score += 10
            elif move.placement.bridge_count > 0:
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

class RLStrategy(AIStrategy):
    """
    RL strategy: uses a trained MaskablePPO model to select a tile,
    then plays the best-scoring placement for that tile.
    """

    name = "RL"

    def __init__(self, model_path: str = "models/triomino_rl/final_model.zip"):
        self.model_path = model_path
        self.model = None
        self._load_error = None
        self.game = None

    def set_game(self, game) -> None:
        self.game = game

    def _ensure_model(self) -> None:
        if self.model is not None or self._load_error is not None:
            return
        try:
            from sb3_contrib import MaskablePPO
            self.model = MaskablePPO.load(self.model_path)
        except Exception as exc:
            self._load_error = exc

    def _build_observation(self, player_idx: int):
        import numpy as np
        MAX_HAND_SIZE = 30
        GRID_SIZE = 64
        CHANNELS = 4

        grid = np.zeros((CHANNELS, GRID_SIZE, GRID_SIZE), dtype=np.float32)

        center_q, center_r = GRID_SIZE // 2, GRID_SIZE // 2
        if self.game.board.tiles:
            min_q = min(t.q for t in self.game.board.tiles.values())
            max_q = max(t.q for t in self.game.board.tiles.values())
            min_r = min(t.r for t in self.game.board.tiles.values())
            max_r = max(t.r for t in self.game.board.tiles.values())
            mid_q = (min_q + max_q) // 2
            mid_r = (min_r + max_r) // 2
        else:
            mid_q, mid_r = 7, 7

        offset_q = center_q - mid_q
        offset_r = center_r - mid_r

        for pos, placed in self.game.board.tiles.items():
            q, r, _ = pos
            gq = q + offset_q
            gr = r + offset_r
            if 0 <= gq < GRID_SIZE and 0 <= gr < GRID_SIZE:
                grid[0, gq, gr] = 1.0
                v = placed.values
                grid[1, gq, gr] = v[0] / 5.0
                grid[2, gq, gr] = v[1] / 5.0
                grid[3, gq, gr] = v[2] / 5.0

        hand = np.zeros((MAX_HAND_SIZE, 3), dtype=np.float32)
        hand_mask = np.zeros((MAX_HAND_SIZE,), dtype=np.float32)
        player = self.game.players[player_idx]
        for i, tile in enumerate(player.hand):
            if i >= MAX_HAND_SIZE:
                break
            hand[i] = [v / 5.0 for v in tile.values]
            hand_mask[i] = 1.0

        state = np.array([
            player.score / 400.0,
            self.game.players[1 - player_idx].score / 400.0,
            len(self.game.pool) / 56.0,
            len(player.hand) / 20.0,
            len(self.game.players[1 - player_idx].hand) / 20.0,
            0.0,
        ], dtype=np.float32)

        return {
            "board": grid,
            "hand": hand,
            "hand_mask": hand_mask,
            "state": state,
        }

    def _build_action_mask(self, player_idx: int):
        MAX_HAND_SIZE = 30
        mask = [False] * (MAX_HAND_SIZE + 2)
        player = self.game.players[player_idx]
        can_play_any = False
        for i, tile in enumerate(player.hand):
            if i >= MAX_HAND_SIZE:
                break
            if self.game.board.find_valid_placements(tile):
                mask[i] = True
                can_play_any = True

        # Draw only when no valid moves (rule)
        if len(self.game.pool) > 0 and not can_play_any:
            mask[MAX_HAND_SIZE] = True

        # Pass only when no moves and cannot draw
        if not can_play_any and len(self.game.pool) == 0:
            mask[MAX_HAND_SIZE + 1] = True

        return mask

    def choose_move(self, player: Player, board: GameBoard) -> Optional[ScoredMove]:
        if not self.game:
            return GreedyStrategy().choose_move(player, board)

        self._ensure_model()
        if self.model is None:
            return GreedyStrategy().choose_move(player, board)

        player_idx = self.game.players.index(player)
        obs = self._build_observation(player_idx)
        mask = self._build_action_mask(player_idx)

        try:
            action, _ = self.model.predict(obs, deterministic=True, action_masks=mask)
        except Exception:
            return GreedyStrategy().choose_move(player, board)

        MAX_HAND_SIZE = 30
        if action >= MAX_HAND_SIZE:
            return None

        if action >= len(player.hand):
            return None

        tile = player.hand[action]
        placements = board.find_valid_placements(tile)
        if not placements:
            return None

        def score_placement(p):
            t_copy = tile.copy()
            t_copy.rotation = p.rotation
            score = sum(t_copy.values)
            score += p.bridge_count * 40
            score += p.hexagon_count * 50
            return score

        best = max(placements, key=score_placement)
        bonus = (best.hexagon_count * 50) + (best.bridge_count * 40)
        return ScoredMove(tile=tile, placement=best, base_score=tile.sum_value, bonus_score=bonus)


# Default strategy
DEFAULT_STRATEGY = GreedyStrategy()


def get_strategy(name: str) -> AIStrategy:
    """Get a strategy by name."""
    strategies = {
        'greedy': GreedyStrategy(),
        'balanced': BalancedStrategy(),
        'defensive': DefensiveStrategy(),
        'random': RandomStrategy(),
        'rl': RLStrategy(),
    }
    return strategies.get(name.lower(), DEFAULT_STRATEGY)
