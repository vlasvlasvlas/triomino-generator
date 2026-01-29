# AI module
"""AI strategies for computer players."""

from .strategies import (
    AIStrategy, GreedyStrategy, BalancedStrategy, 
    DefensiveStrategy, RandomStrategy, ScoredMove, get_strategy
)

__all__ = [
    'AIStrategy', 'GreedyStrategy', 'BalancedStrategy',
    'DefensiveStrategy', 'RandomStrategy', 'ScoredMove', 'get_strategy',
]
