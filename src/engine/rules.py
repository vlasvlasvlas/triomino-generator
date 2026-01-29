"""
Game Rules Engine

Implements all Triomino scoring rules and game logic.
"""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import Optional

from src.models.board import PlacementResult, BonusType


class ScoreType(Enum):
    """Types of scoring events."""
    TILE_PLACED = "tile_placed"
    TRIPLE_OPENING = "triple_opening"
    TRIPLE_ZERO_OPENING = "triple_zero_opening"
    HEXAGON_COMPLETE = "hexagon_complete"
    DOUBLE_HEXAGON = "double_hexagon"
    BRIDGE_FORMED = "bridge_formed"
    DRAW_PENALTY = "draw_penalty"
    THREE_DRAW_FAIL_PENALTY = "three_draw_fail"
    PASS_PENALTY = "pass_penalty"
    ROUND_WIN_BONUS = "round_win_bonus"
    OPPONENT_TILES_BONUS = "opponent_tiles"
    BLOCKED_WIN = "blocked_win"


# Point values according to official rules
POINTS = {
    ScoreType.TRIPLE_OPENING: 10,         # Bonus for opening with triple
    ScoreType.TRIPLE_ZERO_OPENING: 40,    # Special 0-0-0 opening (30 + 10)
    ScoreType.HEXAGON_COMPLETE: 50,       # Completing a hexagon
    ScoreType.DOUBLE_HEXAGON: 100,        # Completing two hexagons
    ScoreType.BRIDGE_FORMED: 40,          # Forming a bridge
    ScoreType.DRAW_PENALTY: -5,           # Per tile drawn from pool
    ScoreType.THREE_DRAW_FAIL_PENALTY: -25,  # Can't play after 3 draws
    ScoreType.PASS_PENALTY: -10,          # Passing when pool empty
    ScoreType.ROUND_WIN_BONUS: 25,        # Emptying hand
}

# Game constants
MAX_DRAWS_PER_TURN = 3
TARGET_SCORE = 400
INITIAL_TILES_2_PLAYERS = 9
INITIAL_TILES_3_4_PLAYERS = 7
INITIAL_TILES_5_6_PLAYERS = 6


@dataclass
class ScoreEvent:
    """A scoring event that occurred during the game."""
    score_type: ScoreType
    points: int
    description: str
    
    def __repr__(self) -> str:
        sign = "+" if self.points >= 0 else ""
        return f"{self.description}: {sign}{self.points}"


def get_initial_tile_count(num_players: int) -> int:
    """Get number of tiles each player starts with based on player count."""
    if num_players == 2:
        return INITIAL_TILES_2_PLAYERS
    elif num_players in (3, 4):
        return INITIAL_TILES_3_4_PLAYERS
    elif num_players in (5, 6):
        return INITIAL_TILES_5_6_PLAYERS
    else:
        raise ValueError(f"Invalid player count: {num_players}")


def calculate_opening_score(tile_value: int, is_triple: bool, 
                            is_triple_zero: bool) -> tuple[int, ScoreEvent]:
    """
    Calculate score for the opening move.
    
    Args:
        tile_value: Sum of tile's three values
        is_triple: True if tile has all same values
        is_triple_zero: True if tile is 0-0-0
        
    Returns:
        Tuple of (total_points, ScoreEvent)
    """
    if is_triple_zero:
        # Special case: 0-0-0 gets 40 points total (30 special + 10 bonus)
        return (40, ScoreEvent(
            ScoreType.TRIPLE_ZERO_OPENING,
            40,
            "Opening with 0-0-0"
        ))
    elif is_triple:
        # Triple opening: tile value + 10 bonus
        total = tile_value + POINTS[ScoreType.TRIPLE_OPENING]
        return (total, ScoreEvent(
            ScoreType.TRIPLE_OPENING,
            total,
            f"Opening with triple ({tile_value} + 10 bonus)"
        ))
    else:
        # No triple: just tile value
        return (tile_value, ScoreEvent(
            ScoreType.TILE_PLACED,
            tile_value,
            f"Opening tile (no triple)"
        ))


def calculate_placement_score(result: PlacementResult, 
                              draws_made: int = 0) -> tuple[int, list[ScoreEvent]]:
    """
    Calculate final score for a tile placement.
    
    Args:
        result: The PlacementResult from board
        draws_made: Number of tiles drawn this turn
        
    Returns:
        Tuple of (net_points, list of ScoreEvents)
    """
    events = []
    
    # Base tile value
    events.append(ScoreEvent(
        ScoreType.TILE_PLACED,
        result.base_points,
        f"Tile placed"
    ))
    
    # Bonus points
    if result.bonus_type == BonusType.HEXAGON:
        events.append(ScoreEvent(
            ScoreType.HEXAGON_COMPLETE,
            50,
            "Hexagon completed!"
        ))
    elif result.bonus_type == BonusType.DOUBLE_HEXAGON:
        events.append(ScoreEvent(
            ScoreType.DOUBLE_HEXAGON,
            100,
            "Double hexagon completed!"
        ))
    elif result.bonus_type == BonusType.BRIDGE:
        events.append(ScoreEvent(
            ScoreType.BRIDGE_FORMED,
            40,
            "Bridge formed!"
        ))
    
    # Draw penalties
    if draws_made > 0:
        penalty = draws_made * POINTS[ScoreType.DRAW_PENALTY]
        events.append(ScoreEvent(
            ScoreType.DRAW_PENALTY,
            penalty,
            f"Drew {draws_made} tile(s)"
        ))
    
    total = sum(e.points for e in events)
    return (total, events)


def calculate_draw_failure_penalty(draws_made: int) -> tuple[int, ScoreEvent]:
    """
    Calculate penalty when player can't play after drawing.
    
    If player drew 3 tiles and still can't play: -25 penalty
    """
    if draws_made >= MAX_DRAWS_PER_TURN:
        return (POINTS[ScoreType.THREE_DRAW_FAIL_PENALTY], ScoreEvent(
            ScoreType.THREE_DRAW_FAIL_PENALTY,
            POINTS[ScoreType.THREE_DRAW_FAIL_PENALTY],
            "Cannot play after 3 draws"
        ))
    else:
        # Drew some tiles but fewer than 3
        penalty = draws_made * POINTS[ScoreType.DRAW_PENALTY]
        return (penalty, ScoreEvent(
            ScoreType.DRAW_PENALTY,
            penalty,
            f"Drew {draws_made} tile(s)"
        ))


def calculate_pass_penalty() -> tuple[int, ScoreEvent]:
    """Calculate penalty for passing when pool is empty."""
    return (POINTS[ScoreType.PASS_PENALTY], ScoreEvent(
        ScoreType.PASS_PENALTY,
        POINTS[ScoreType.PASS_PENALTY],
        "Pass (pool empty)"
    ))


def calculate_round_win_bonus(opponent_tile_values: list[int]) -> tuple[int, list[ScoreEvent]]:
    """
    Calculate bonus for winning a round by emptying hand.
    
    Args:
        opponent_tile_values: Sum of tile values for each opponent
        
    Returns:
        Tuple of (total_bonus, list of ScoreEvents)
    """
    events = []
    
    # +25 for winning
    events.append(ScoreEvent(
        ScoreType.ROUND_WIN_BONUS,
        25,
        "Round win bonus"
    ))
    
    # Add opponent tile values
    total_opponent = sum(opponent_tile_values)
    if total_opponent > 0:
        events.append(ScoreEvent(
            ScoreType.OPPONENT_TILES_BONUS,
            total_opponent,
            f"Opponent tiles value"
        ))
    
    total = sum(e.points for e in events)
    return (total, events)


def calculate_blocked_win_bonus(winner_hand_value: int, 
                                opponent_hand_values: list[int]) -> tuple[int, ScoreEvent]:
    """
    Calculate bonus for winning a blocked round (lowest hand value).
    
    Winner gets the sum of differences between their hand and each opponent's.
    No +25 bonus for blocked games.
    
    Args:
        winner_hand_value: Value of winner's remaining tiles
        opponent_hand_values: Values of each opponent's remaining tiles
        
    Returns:
        Tuple of (bonus, ScoreEvent)
    """
    total_difference = sum(opp - winner_hand_value for opp in opponent_hand_values)
    
    return (total_difference, ScoreEvent(
        ScoreType.BLOCKED_WIN,
        total_difference,
        f"Blocked game win (differences)"
    ))


def check_game_winner(scores: dict[str, int]) -> Optional[str]:
    """
    Check if any player has reached the target score (400).
    
    Note: Reaching 400 only triggers the final round.
    The winner is determined at the end of that round.
    
    Returns:
        Player name if someone reached 400, None otherwise
    """
    for player_name, score in scores.items():
        if score >= TARGET_SCORE:
            return player_name
    return None


def get_final_winner(scores: dict[str, int]) -> str:
    """Get the player with the highest score (for end of final round)."""
    return max(scores.keys(), key=lambda p: scores[p])
