# Engine module
"""Game engine: rules, game loop, match simulation."""

from .rules import ScoreEvent, ScoreType, calculate_opening_score
from .game import TriominoGame, GameResult, RoundResult, TurnResult, TurnAction
from .match import MatchSimulator, MatchStats, quick_simulation

__all__ = [
    'ScoreEvent', 'ScoreType', 'calculate_opening_score',
    'TriominoGame', 'GameResult', 'RoundResult', 'TurnResult', 'TurnAction',
    'MatchSimulator', 'MatchStats', 'quick_simulation',
]
