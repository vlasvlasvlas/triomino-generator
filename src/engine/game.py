"""
Triomino Game Engine

Main game loop managing rounds, turns, and game state.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Callable
import random

from src.models import (
    Triomino, Player, GameBoard, PlacementResult, 
    ValidPlacement, create_shuffled_deck, get_starting_player
)
from src.engine.rules import (
    ScoreEvent, calculate_opening_score, calculate_placement_score,
    calculate_draw_failure_penalty, calculate_pass_penalty,
    calculate_round_win_bonus, calculate_blocked_win_bonus,
    get_initial_tile_count, MAX_DRAWS_PER_TURN, TARGET_SCORE,
    check_game_winner, get_final_winner
)


class TurnAction(Enum):
    """Types of actions a player can take on their turn."""
    PLACE_TILE = "place"
    DRAW_TILE = "draw"
    PASS = "pass"


class RoundEndReason(Enum):
    """How a round ended."""
    PLAYER_EMPTIED_HAND = "emptied_hand"
    GAME_BLOCKED = "blocked"


@dataclass
class TurnResult:
    """Result of a single turn."""
    player: Player
    action: TurnAction
    tile_placed: Optional[PlacedTile] = None
    tiles_drawn: int = 0
    points_earned: int = 0
    events: List[ScoreEvent] = field(default_factory=list)
    success: bool = True
    message: str = ""


@dataclass
class RoundResult:
    """Result of a complete round."""
    winner: Player
    reason: RoundEndReason
    winner_bonus: int = 0
    final_scores: dict = field(default_factory=dict)


@dataclass
class GameResult:
    """Final result of a complete game (multiple rounds)."""
    winner: Player
    rounds_played: int
    final_scores: dict = field(default_factory=dict)


# Import PlacedTile for type hints
from src.models.tile import PlacedTile


class TriominoGame:
    """
    Main game engine for Triomino.
    
    Manages the complete game flow:
    - Multiple rounds until someone reaches 400 points
    - Turn-based play with proper rule enforcement
    - Scoring and penalties
    """
    
    def __init__(self, player_names: List[str] = None, 
                 target_score: int = TARGET_SCORE,
                 seed: int = None):
        """
        Initialize a new game.
        
        Args:
            player_names: Names for the players (default: ["Computer 1", "Computer 2"])
            target_score: Points needed to trigger final round
            seed: Random seed for reproducibility
        """
        if player_names is None:
            player_names = ["Computer 1", "Computer 2"]
        
        if len(player_names) < 2 or len(player_names) > 6:
            raise ValueError("Need 2-6 players")
        
        self.players = [Player(name=name, is_computer=True) for name in player_names]
        self.target_score = target_score
        self.seed = seed
        
        # Game state
        self.board = GameBoard()
        self.pool: List[Triomino] = []
        self.current_player_idx = 0
        self.round_number = 0
        self.is_final_round = False
        self.game_over = False
        
        # Listeners for visualization
        self._on_tile_placed: Optional[Callable] = None
        self._on_turn_complete: Optional[Callable] = None
        self._on_round_complete: Optional[Callable] = None
    
    @property
    def current_player(self) -> Player:
        """Get the current player."""
        return self.players[self.current_player_idx]
    
    @property
    def num_players(self) -> int:
        """Number of players in the game."""
        return len(self.players)
    
    def setup_round(self) -> None:
        """Set up a new round: shuffle deck, deal tiles."""
        self.round_number += 1
        
        # Create and shuffle deck
        if self.seed is not None:
            self.pool = create_shuffled_deck(seed=self.seed + self.round_number)
        else:
            self.pool = create_shuffled_deck()
        
        # Reset board
        self.board = GameBoard()
        
        # Clear player hands (scores persist)
        for player in self.players:
            player.reset_for_new_round()
        
        # Deal tiles
        tiles_per_player = get_initial_tile_count(self.num_players)
        for player in self.players:
            player.draw_tiles(self.pool, tiles_per_player)
    
    def determine_starting_player(self) -> tuple[Player, Triomino, bool]:
        """
        Determine who starts and with which tile.
        
        Returns:
            Tuple of (starting_player, starting_tile, has_triple_bonus)
        """
        return get_starting_player(self.players)
    
    def play_opening(self) -> TurnResult:
        """
        Execute the opening move of a round.
        
        Returns:
            TurnResult for the opening move
        """
        starter, tile, has_triple = self.determine_starting_player()
        
        # Find this player's index
        self.current_player_idx = self.players.index(starter)
        
        # Remove tile from hand
        starter.play_tile(tile)
        
        # Place on board
        result = self.board.place_first_tile(
            tile=tile,
            player_id=self.current_player_idx,
            is_triple=has_triple
        )
        
        # Calculate score
        points, event = calculate_opening_score(
            tile.sum_value,
            tile.is_triple(),
            tile.is_triple_zero()
        )
        
        starter.add_score(points)
        
        return TurnResult(
            player=starter,
            action=TurnAction.PLACE_TILE,
            tile_placed=result.tile,
            points_earned=points,
            events=[event],
            message=f"{starter.name} opens with {tile}"
        )
    
    def find_best_move(self, player: Player) -> Optional[tuple[Triomino, ValidPlacement]]:
        """
        Find the best valid move for a player (greedy strategy).
        
        Returns:
            Tuple of (tile, placement) or None if no valid move
        """
        best_move = None
        best_score = -1
        
        for tile in player.hand:
            placements = self.board.find_valid_placements(tile)
            for placement in placements:
                # Calculate potential score
                score = tile.sum_value
                if placement.is_hexagon:
                    score += 50
                elif placement.is_bridge:
                    score += 40
                
                if score > best_score:
                    best_score = score
                    best_move = (tile, placement)
        
        return best_move
    
    def can_player_move(self, player: Player) -> bool:
        """Check if player has any valid moves."""
        for tile in player.hand:
            if self.board.find_valid_placements(tile):
                return True
        return False
    
    def play_turn(self) -> TurnResult:
        """
        Execute one player's turn.
        
        Returns:
            TurnResult describing what happened
        """
        player = self.current_player
        draws_made = 0
        
        # Try to find a valid move
        while True:
            move = self.find_best_move(player)
            
            if move:
                # Can place a tile
                tile, placement = move
                player.play_tile(tile)
                tile.rotation = placement.rotation
                
                result = self.board.place_tile(
                    tile=tile,
                    q=placement.q,
                    r=placement.r,
                    rotation=placement.rotation,
                    player_id=self.current_player_idx
                )
                
                # Calculate score
                points, events = calculate_placement_score(result, draws_made)
                player.add_score(points)
                
                # Notify listener
                if self._on_tile_placed:
                    self._on_tile_placed(result)
                
                return TurnResult(
                    player=player,
                    action=TurnAction.PLACE_TILE,
                    tile_placed=result.tile,
                    tiles_drawn=draws_made,
                    points_earned=points,
                    events=events,
                    message=f"{player.name} places {tile}"
                )
            
            # No valid move - try to draw
            if self.pool and draws_made < MAX_DRAWS_PER_TURN:
                player.draw_tiles(self.pool, 1)
                draws_made += 1
                continue
            
            # Can't draw anymore
            break
        
        # Failed to play after drawing
        if draws_made > 0:
            # Drew tiles but couldn't play
            points, event = calculate_draw_failure_penalty(draws_made)
            player.add_score(points)
            
            return TurnResult(
                player=player,
                action=TurnAction.DRAW_TILE,
                tiles_drawn=draws_made,
                points_earned=points,
                events=[event],
                success=False,
                message=f"{player.name} drew {draws_made} tiles but cannot play"
            )
        else:
            # Pass (pool empty)
            points, event = calculate_pass_penalty()
            player.add_score(points)
            
            return TurnResult(
                player=player,
                action=TurnAction.PASS,
                points_earned=points,
                events=[event],
                message=f"{player.name} passes"
            )
    
    def next_player(self) -> None:
        """Advance to the next player."""
        self.current_player_idx = (self.current_player_idx + 1) % self.num_players
    
    def check_round_end(self) -> Optional[RoundResult]:
        """
        Check if the round has ended.
        
        Returns:
            RoundResult if round ended, None otherwise
        """
        # Check if current player emptied their hand
        if self.current_player.has_empty_hand:
            winner = self.current_player
            
            # Calculate bonus
            opponent_values = [
                p.hand_value for p in self.players if p != winner
            ]
            bonus, events = calculate_round_win_bonus(opponent_values)
            winner.add_score(bonus)
            
            return RoundResult(
                winner=winner,
                reason=RoundEndReason.PLAYER_EMPTIED_HAND,
                winner_bonus=bonus,
                final_scores={p.name: p.score for p in self.players}
            )
        
        # Check if game is blocked (no one can move)
        if not self.pool:  # Pool is empty
            can_anyone_move = any(self.can_player_move(p) for p in self.players)
            if not can_anyone_move:
                # Find player with lowest hand value
                winner = min(self.players, key=lambda p: p.hand_value)
                
                # Calculate bonus
                opponent_values = [
                    p.hand_value for p in self.players if p != winner
                ]
                bonus, event = calculate_blocked_win_bonus(
                    winner.hand_value, opponent_values
                )
                winner.add_score(bonus)
                
                return RoundResult(
                    winner=winner,
                    reason=RoundEndReason.GAME_BLOCKED,
                    winner_bonus=bonus,
                    final_scores={p.name: p.score for p in self.players}
                )
        
        return None
    
    def check_game_end(self) -> bool:
        """Check if someone has reached the target score."""
        return any(p.score >= self.target_score for p in self.players)
    
    def play_round(self) -> RoundResult:
        """
        Play a complete round.
        
        Returns:
            RoundResult when round ends
        """
        self.setup_round()
        
        # Opening move
        opening = self.play_opening()
        if self._on_turn_complete:
            self._on_turn_complete(opening)
        
        # Check if opener won immediately (unlikely but possible)
        round_result = self.check_round_end()
        if round_result:
            return round_result
        
        self.next_player()
        
        # Main game loop
        consecutive_passes = 0
        max_passes = self.num_players * 2  # Safety limit
        
        while True:
            turn = self.play_turn()
            
            if self._on_turn_complete:
                self._on_turn_complete(turn)
            
            # Track consecutive passes for blocked detection
            if turn.action == TurnAction.PASS:
                consecutive_passes += 1
                if consecutive_passes >= max_passes:
                    # Force blocked game
                    break
            else:
                consecutive_passes = 0
            
            # Check round end
            round_result = self.check_round_end()
            if round_result:
                if self._on_round_complete:
                    self._on_round_complete(round_result)
                return round_result
            
            self.next_player()
        
        # Blocked game fallback
        winner = min(self.players, key=lambda p: p.hand_value)
        opponent_values = [p.hand_value for p in self.players if p != winner]
        bonus, _ = calculate_blocked_win_bonus(winner.hand_value, opponent_values)
        winner.add_score(bonus)
        
        return RoundResult(
            winner=winner,
            reason=RoundEndReason.GAME_BLOCKED,
            winner_bonus=bonus,
            final_scores={p.name: p.score for p in self.players}
        )
    
    def play_game(self) -> GameResult:
        """
        Play a complete game until someone wins.
        
        Returns:
            GameResult with final standings
        """
        while not self.game_over:
            round_result = self.play_round()
            
            # Check if this triggers final round
            if self.check_game_end():
                if not self.is_final_round:
                    self.is_final_round = True
                    # Current round was the final round
                else:
                    self.game_over = True
            
            # If we just finished the final round
            if self.is_final_round and self.round_number > 0:
                self.game_over = True
        
        # Determine winner (highest score at end of final round)
        winner = max(self.players, key=lambda p: p.score)
        
        return GameResult(
            winner=winner,
            rounds_played=self.round_number,
            final_scores={p.name: p.score for p in self.players}
        )
    
    def get_game_state(self) -> dict:
        """Get current game state for visualization."""
        return {
            'round': self.round_number,
            'current_player': self.current_player.name,
            'board_tiles': self.board.tile_count,
            'pool_remaining': len(self.pool),
            'is_final_round': self.is_final_round,
            'scores': {p.name: p.score for p in self.players},
            'hands': {p.name: p.hand_size for p in self.players}
        }
