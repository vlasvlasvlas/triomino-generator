"""
Match Simulator

Runs multiple games between computer players and collects statistics.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Callable
import time

from src.engine.game import TriominoGame, GameResult, RoundResult, TurnResult


@dataclass
class MatchStats:
    """Statistics for a series of matches."""
    total_matches: int = 0
    wins_per_player: dict = field(default_factory=dict)
    total_rounds: int = 0
    total_turns: int = 0
    avg_rounds_per_match: float = 0.0
    highest_score: int = 0
    highest_scorer: str = ""
    
    def update_from_game(self, result: GameResult):
        """Update stats from a game result."""
        self.total_matches += 1
        self.total_rounds += result.rounds_played
        
        winner_name = result.winner.name
        self.wins_per_player[winner_name] = self.wins_per_player.get(winner_name, 0) + 1
        
        for player_name, score in result.final_scores.items():
            if score > self.highest_score:
                self.highest_score = score
                self.highest_scorer = player_name
        
        self.avg_rounds_per_match = self.total_rounds / self.total_matches
    
    def print_summary(self):
        """Print a summary of the match statistics."""
        print("\n" + "=" * 50)
        print("📊 MATCH STATISTICS")
        print("=" * 50)
        print(f"Total matches played: {self.total_matches}")
        print(f"Total rounds played: {self.total_rounds}")
        print(f"Average rounds per match: {self.avg_rounds_per_match:.1f}")
        print(f"\n🏆 Wins per player:")
        for player, wins in sorted(self.wins_per_player.items(), key=lambda x: -x[1]):
            pct = (wins / self.total_matches) * 100
            print(f"   {player}: {wins} wins ({pct:.1f}%)")
        print(f"\n⭐ Highest score: {self.highest_score} ({self.highest_scorer})")
        print("=" * 50)


@dataclass
class MatchResult:
    """Result of a simulated match."""
    game_result: GameResult
    duration_seconds: float
    turns_played: int
    
    def __repr__(self) -> str:
        winner = self.game_result.winner.name
        rounds = self.game_result.rounds_played
        return f"Match: {winner} wins in {rounds} rounds ({self.duration_seconds:.2f}s)"


class MatchSimulator:
    """
    Simulates multiple Triomino matches between computer players.
    
    "War Games" style - watch computers battle it out!
    """
    
    def __init__(self, num_matches: int = 5,
                 player_names: List[str] = None,
                 target_score: int = 400):
        """
        Initialize the match simulator.
        
        Args:
            num_matches: Number of complete games to simulate
            player_names: Names for the players
            target_score: Points needed to win
        """
        if player_names is None:
            player_names = ["🔴 CPU-Alpha", "🔵 CPU-Beta"]
        
        self.num_matches = num_matches
        self.player_names = player_names
        self.target_score = target_score
        
        self.stats = MatchStats()
        self.results: List[MatchResult] = []
        
        # Callbacks for visualization
        self.on_match_start: Optional[Callable] = None
        self.on_match_end: Optional[Callable] = None
        self.on_round_start: Optional[Callable] = None
        self.on_round_end: Optional[Callable] = None
        self.on_turn: Optional[Callable] = None
    
    def run_single_match(self, match_number: int, seed: int = None) -> MatchResult:
        """
        Run a single complete game.
        
        Args:
            match_number: Current match number (1-indexed)
            seed: Random seed for reproducibility
            
        Returns:
            MatchResult with game data
        """
        start_time = time.time()
        turns_count = 0
        
        game = TriominoGame(
            player_names=self.player_names,
            target_score=self.target_score,
            seed=seed
        )
        
        # Set up callbacks
        def on_turn(turn: TurnResult):
            nonlocal turns_count
            turns_count += 1
            if self.on_turn:
                self.on_turn(match_number, turn)
        
        game._on_turn_complete = on_turn
        
        if self.on_round_end:
            game._on_round_complete = lambda r: self.on_round_end(match_number, r)
        
        if self.on_match_start:
            self.on_match_start(match_number, game)
        
        # Play the game
        result = game.play_game()
        
        duration = time.time() - start_time
        
        match_result = MatchResult(
            game_result=result,
            duration_seconds=duration,
            turns_played=turns_count
        )
        
        if self.on_match_end:
            self.on_match_end(match_number, match_result)
        
        return match_result
    
    def run_simulation(self, visualize: bool = False, 
                       base_seed: int = None) -> MatchStats:
        """
        Run all matches in the simulation.
        
        Args:
            visualize: If True, use visualization callbacks
            base_seed: Base seed for reproducibility
            
        Returns:
            MatchStats with aggregate statistics
        """
        print("\n" + "🎮" * 20)
        print("   TRIOMINÓ - WAR GAMES SIMULATION")
        print("🎮" * 20)
        print(f"\nPlayers: {', '.join(self.player_names)}")
        print(f"Matches to play: {self.num_matches}")
        print(f"Target score: {self.target_score} points")
        print("-" * 50)
        
        for i in range(self.num_matches):
            match_num = i + 1
            seed = (base_seed + i) if base_seed else None
            
            print(f"\n🎯 Match {match_num}/{self.num_matches}...")
            
            result = self.run_single_match(match_num, seed)
            self.results.append(result)
            self.stats.update_from_game(result.game_result)
            
            # Print match result
            winner = result.game_result.winner.name
            scores = result.game_result.final_scores
            rounds = result.game_result.rounds_played
            
            print(f"   Winner: {winner}")
            print(f"   Rounds: {rounds}")
            print(f"   Scores: {scores}")
            print(f"   Duration: {result.duration_seconds:.2f}s")
        
        self.stats.print_summary()
        return self.stats


def quick_simulation(num_matches: int = 5, seed: int = None) -> MatchStats:
    """Quick way to run a simulation."""
    sim = MatchSimulator(num_matches=num_matches)
    return sim.run_simulation(base_seed=seed)


if __name__ == "__main__":
    # Quick test
    quick_simulation(num_matches=3, seed=42)
