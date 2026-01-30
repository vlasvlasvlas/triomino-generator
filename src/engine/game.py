"""
Triomino Game Engine

Main game loop managing rounds, turns, and game state.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Callable

from src.models import (
    Triomino, Player, GameBoard, PlacementResult, 
    ValidPlacement, create_shuffled_deck, get_starting_player
)
from src.models.tile import PlacedTile
from src.engine.rules import (
    ScoreEvent, calculate_opening_score, calculate_placement_score,
    calculate_draw_failure_penalty, calculate_pass_penalty,
    calculate_round_win_bonus, calculate_blocked_win_bonus,
    get_initial_tile_count, MAX_DRAWS_PER_TURN, TARGET_SCORE
)
from src.ai.strategies import AIStrategy, get_strategy


class TurnAction(Enum):
    PLACE_TILE = "place"
    DRAW_TILE = "draw"
    PASS = "pass"


class RoundEndReason(Enum):
    PLAYER_EMPTIED_HAND = "emptied_hand"
    GAME_BLOCKED = "blocked"


@dataclass
class TurnResult:
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
    winner: Player
    reason: RoundEndReason
    winner_bonus: int = 0
    final_scores: dict = field(default_factory=dict)


@dataclass
class GameResult:
    winner: Player
    rounds_played: int
    final_scores: dict = field(default_factory=dict)


class TriominoGame:
    """Main game engine for Triomino."""
    
    def __init__(self, player_names: List[str] = None, 
                 target_score: int = TARGET_SCORE,
                 seed: int = None,
                 strategies: Optional[List[AIStrategy]] = None):
        if player_names is None:
            player_names = ["Computer 1", "Computer 2"]
        
        self.players = [Player(name=name, is_computer=True) for name in player_names]
        if strategies is None:
            strategies = [get_strategy("greedy") for _ in self.players]
        if len(strategies) != len(self.players):
            raise ValueError("Number of strategies must match number of players")
        self.strategies = strategies
        for strat in self.strategies:
            if hasattr(strat, "set_game"):
                strat.set_game(self)
        self.target_score = target_score
        self.seed = seed
        
        self.board = GameBoard()
        self.pool: List[Triomino] = []
        self.current_player_idx = 0
        self.round_number = 0
        self.is_final_round = False
        self.final_round_triggered = False
        self.game_over = False
        
        self._on_tile_placed: Optional[Callable] = None
        self._on_turn_complete: Optional[Callable] = None
        self._on_round_complete: Optional[Callable] = None
    
    @property
    def current_player(self) -> Player:
        return self.players[self.current_player_idx]
    
    @property
    def num_players(self) -> int:
        return len(self.players)
    
    def setup_round(self) -> None:
        self.round_number += 1
        
        if self.seed is not None:
            self.pool = create_shuffled_deck(seed=self.seed + self.round_number)
        else:
            self.pool = create_shuffled_deck()
        
        self.board = GameBoard()
        
        for player in self.players:
            player.reset_for_new_round()
        
        tiles_per_player = get_initial_tile_count(self.num_players)
        for player in self.players:
            player.draw_tiles(self.pool, tiles_per_player)
    
    def determine_starting_player(self) -> tuple[Player, Triomino, bool]:
        return get_starting_player(self.players)
    
    def play_opening(self) -> TurnResult:
        starter, tile, has_triple = self.determine_starting_player()
        self.current_player_idx = self.players.index(starter)
        
        starter.play_tile(tile)
        result = self.board.place_first_tile(
            tile=tile,
            player_id=self.current_player_idx,
            is_triple=has_triple
        )
        
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
        """Find best valid move using the player's configured strategy."""
        idx = self.players.index(player)
        strategy = self.strategies[idx]
        move = strategy.choose_move(player, self.board)
        if not move:
            return None
        return (move.tile, move.placement)
    
    def can_player_move(self, player: Player) -> bool:
        for tile in player.hand:
            if self.board.find_valid_placements(tile):
                return True
        return False
    
    
    def execute_place(self, player: Player, tile: Triomino, placement: ValidPlacement, draws_made: int = 0) -> TurnResult:
        """Execute a placement action atomatically."""
        # Ensure rotation is set correctly on the tile copy
        tile.rotation = placement.rotation
        
        result = self.board.place_tile(
            tile=tile,
            row=placement.row,
            col=placement.col,
            orientation=placement.orientation,
            rotation=placement.rotation,
            player_id=self.players.index(player)
        )

        if not result.success:
            return TurnResult(
                player=player,
                action=TurnAction.PLACE_TILE,
                tile_placed=None,
                tiles_drawn=draws_made,
                points_earned=0,
                events=[],
                success=False,
                message=result.message
            )

        player.play_tile(tile)
        
        points, events = calculate_placement_score(result, draws_made)
        player.add_score(points)
        
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
        
    def execute_draw(self, player: Player) -> int:
        """Draw a tile from pool. Returns count drawn (0 or 1)."""
        if self.pool:
            player.draw_tiles(self.pool, 1)
            return 1
        return 0

    def play_turn(self) -> TurnResult:
        player = self.current_player
        draws_made = 0
        
        while True:
            move = self.find_best_move(player)
            
            if move:
                tile, placement = move
                return self.execute_place(player, tile, placement, draws_made)

            
            if self.pool and draws_made < MAX_DRAWS_PER_TURN:
                count = self.execute_draw(player)
                draws_made += count

                continue
            
            break
        
        if draws_made > 0:
            points, event = calculate_draw_failure_penalty(draws_made)
            player.add_score(points)
            
            return TurnResult(
                player=player,
                action=TurnAction.DRAW_TILE,
                tiles_drawn=draws_made,
                points_earned=points,
                events=[event],
                success=False,
                message=f"{player.name} drew {draws_made} but can't play"
            )
        else:
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
        self.current_player_idx = (self.current_player_idx + 1) % self.num_players
    
    def check_round_end(self) -> Optional[RoundResult]:
        if self.current_player.has_empty_hand:
            winner = self.current_player
            opponent_values = [p.hand_value for p in self.players if p != winner]
            bonus, events = calculate_round_win_bonus(opponent_values)
            winner.add_score(bonus)
            
            return RoundResult(
                winner=winner,
                reason=RoundEndReason.PLAYER_EMPTIED_HAND,
                winner_bonus=bonus,
                final_scores={p.name: p.score for p in self.players}
            )
        
        if not self.pool:
            can_anyone_move = any(self.can_player_move(p) for p in self.players)
            if not can_anyone_move:
                winner = min(self.players, key=lambda p: p.hand_value)
                opponent_values = [p.hand_value for p in self.players if p != winner]
                bonus, event = calculate_blocked_win_bonus(winner.hand_value, opponent_values)
                winner.add_score(bonus)
                
                return RoundResult(
                    winner=winner,
                    reason=RoundEndReason.GAME_BLOCKED,
                    winner_bonus=bonus,
                    final_scores={p.name: p.score for p in self.players}
                )
        
        return None
    
    def check_game_end(self) -> bool:
        return any(p.score >= self.target_score for p in self.players)
    
    def play_round(self) -> RoundResult:
        self.setup_round()
        
        opening = self.play_opening()
        if self._on_turn_complete:
            self._on_turn_complete(opening)
        
        round_result = self.check_round_end()
        if round_result:
            return round_result
        
        self.next_player()
        
        consecutive_passes = 0
        max_passes = self.num_players * 2
        
        while True:
            turn = self.play_turn()
            
            if self._on_turn_complete:
                self._on_turn_complete(turn)
            
            if turn.action == TurnAction.PASS:
                consecutive_passes += 1
                if consecutive_passes >= max_passes:
                    break
            else:
                consecutive_passes = 0
            
            round_result = self.check_round_end()
            if round_result:
                if self._on_round_complete:
                    self._on_round_complete(round_result)
                return round_result
            
            self.next_player()
        
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
        while not self.game_over:
            if self.final_round_triggered:
                self.is_final_round = True

            round_result = self.play_round()
            
            # If we just played the final round, the game ends now
            if self.is_final_round:
                self.game_over = True
                break

            # Trigger final round if someone reaches target
            if self.check_game_end():
                self.final_round_triggered = True
        
        winner = max(self.players, key=lambda p: p.score)
        
        return GameResult(
            winner=winner,
            rounds_played=self.round_number,
            final_scores={p.name: p.score for p in self.players}
        )
    
    def get_game_state(self) -> dict:
        return {
            'round': self.round_number,
            'current_player': self.current_player.name,
            'board_tiles': self.board.tile_count,
            'pool_remaining': len(self.pool),
            'is_final_round': self.is_final_round,
            'scores': {p.name: p.score for p in self.players},
            'hands': {p.name: p.hand_size for p in self.players}
        }
