#!/usr/bin/env python3
"""
🎮 TRIOMINÓ - War Games Edition

Simulador de partidas automáticas entre 2 computadoras.

Ejecutar:
    python main.py              # Simular 5 partidas con visualización
    python main.py --matches 10 # Simular 10 partidas
    python main.py --fast       # Sin visualización (solo estadísticas)
    python main.py --seed 42    # Seed fijo para reproducibilidad
    python main.py --config config/default.json  # Config centralizado
"""
import argparse
import sys
from typing import List, Optional

from src.engine import TriominoGame, MatchSimulator
from src.visualization import visualize_game, GameRenderer
from src.config import load_config
from src.ai.strategies import get_strategy, AIStrategy


def run_visualized_simulation(num_matches: int = 5, 
                               animation_delay: float = 0.3,
                               seed: int = None,
                               player_names: Optional[List[str]] = None,
                               strategies: Optional[List[AIStrategy]] = None,
                               target_score: int = 400):
    """
    Run matches with live visualization.
    
    Args:
        num_matches: Number of games to play
        animation_delay: Delay between animations (seconds)
        seed: Random seed for reproducibility
    """
    import matplotlib.pyplot as plt
    
    print("\n" + "🎮" * 20)
    print("   TRIOMINÓ - WAR GAMES EDITION")
    print("🎮" * 20)
    if player_names is None:
        player_names = ['CPU-Alpha', 'CPU-Beta']
    if strategies is None:
        strategies = [get_strategy("greedy") for _ in player_names]
    if len(strategies) != len(player_names):
        raise ValueError("Number of strategies must match number of players")

    print(f"\n🤖 {' vs '.join(player_names)}")
    print(f"📊 Matches: {num_matches}")
    print(f"🎯 Target: {target_score} points")
    print("-" * 50)
    
    renderer = GameRenderer()
    renderer.setup_figure()
    renderer.animation_delay = animation_delay
    
    stats = {
        'wins': {name: 0 for name in player_names},
        'total_rounds': 0,
        'highest_score': 0,
        'highest_scorer': ''
    }
    
    for match_num in range(1, num_matches + 1):
        print(f"\n🎯 Match {match_num}/{num_matches}...")
        
        match_seed = (seed + match_num) if seed else None
        game = TriominoGame(
            player_names=player_names,
            seed=match_seed,
            target_score=target_score,
            strategies=strategies
        )
        
        # Set up visualization callbacks
        last_turn = None
        
        def on_turn(turn):
            nonlocal last_turn
            last_turn = turn
            renderer.draw_board(game.board)
            renderer.update_info_panel(game, turn)
        
        game._on_turn_complete = on_turn
        
        # Play the game
        result = game.play_game()
        
        # Update stats
        winner = result.winner.name
        stats['wins'][winner] = stats['wins'].get(winner, 0) + 1
        stats['total_rounds'] += result.rounds_played
        
        for name, score in result.final_scores.items():
            if score > stats['highest_score']:
                stats['highest_score'] = score
                stats['highest_scorer'] = name
        
        # Show result
        print(f"   🏆 Winner: {winner}")
        print(f"   📊 Scores: {result.final_scores}")
        print(f"   ⏱️  Rounds: {result.rounds_played}")
        
        renderer.show_match_result(winner, result.final_scores)
        plt.pause(1.5)
    
    # Print final summary
    print("\n" + "=" * 50)
    print("📊 FINAL STATISTICS")
    print("=" * 50)
    for player, wins in stats['wins'].items():
        pct = (wins / num_matches) * 100
        print(f"   {player}: {wins} wins ({pct:.0f}%)")
    print(f"\n   Average rounds per match: {stats['total_rounds']/num_matches:.1f}")
    print(f"   Highest score: {stats['highest_score']} ({stats['highest_scorer']})")
    print("=" * 50)
    
    print("\n🎮 Simulation complete! Close the window to exit.")
    plt.ioff()
    plt.show()


def run_fast_simulation(num_matches: int = 5, seed: int = None,
                        player_names: Optional[List[str]] = None,
                        strategy_names: Optional[List[str]] = None,
                        target_score: int = 400,
                        log_enabled: bool = False,
                        log_dir: str = "runs"):
    """
    Run matches without visualization (faster).
    
    Args:
        num_matches: Number of games to play
        seed: Random seed for reproducibility
    """
    if player_names is None:
        player_names = ['CPU-Alpha', 'CPU-Beta']
    simulator = MatchSimulator(
        num_matches=num_matches,
        player_names=player_names,
        target_score=target_score,
        strategy_names=strategy_names,
        log_enabled=log_enabled,
        log_dir=log_dir
    )
    
    stats = simulator.run_simulation(base_seed=seed)
    return stats


def main():
    parser = argparse.ArgumentParser(
        description='🎮 Triominó War Games - Computer vs Computer simulation',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                    # 5 matches with visualization
  python main.py --matches 10       # 10 matches
  python main.py --fast             # No visualization
  python main.py --seed 42          # Reproducible results
  python main.py --delay 0.1        # Faster animation
        """
    )
    
    parser.add_argument(
        '-m', '--matches',
        type=int,
        default=None,
        help='Number of matches to simulate'
    )
    
    parser.add_argument(
        '-f', '--fast',
        action='store_true',
        default=None,
        help='Fast mode - no visualization'
    )
    
    parser.add_argument(
        '-s', '--seed',
        type=int,
        default=None,
        help='Random seed for reproducibility'
    )
    
    parser.add_argument(
        '-d', '--delay',
        type=float,
        default=None,
        help='Animation delay in seconds'
    )

    parser.add_argument(
        '-c', '--config',
        type=str,
        default=None,
        help='Path to config JSON (default: config/default.json)'
    )
    
    args = parser.parse_args()
    
    try:
        config = load_config(args.config)
        simulation = config.get("simulation", {})
        logging_cfg = config.get("logging", {})
        players = config.get("players", [])
        if not players:
            players = [
                {"name": "CPU-Alpha", "strategy": "greedy"},
                {"name": "CPU-Beta", "strategy": "greedy"}
            ]
        player_names = [p.get("name", f"Player {i+1}") for i, p in enumerate(players)]
        strategy_names = [p.get("strategy", "greedy") for p in players]
        strategies = [get_strategy(name) for name in strategy_names]

        matches = args.matches if args.matches is not None else simulation.get("matches", 5)
        seed = args.seed if args.seed is not None else simulation.get("seed")
        delay = args.delay if args.delay is not None else simulation.get("delay", 0.3)
        fast = args.fast if args.fast is not None else simulation.get("fast", False)
        target_score = config.get("game", {}).get("target_score", 400)
        log_enabled = logging_cfg.get("enabled", False)
        log_dir = logging_cfg.get("run_dir", "runs")

        if fast:
            run_fast_simulation(
                num_matches=matches,
                seed=seed,
                player_names=player_names,
                strategy_names=strategy_names,
                target_score=target_score,
                log_enabled=log_enabled,
                log_dir=log_dir
            )
        else:
            run_visualized_simulation(
                num_matches=matches,
                animation_delay=delay,
                seed=seed,
                player_names=player_names,
                strategies=strategies,
                target_score=target_score
            )
    except KeyboardInterrupt:
        print("\n\n👋 Simulation cancelled by user.")
        sys.exit(0)


if __name__ == "__main__":
    main()
