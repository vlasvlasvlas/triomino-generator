#!/usr/bin/env python3
"""
🎮 TRIOMINÓ - War Games Edition

Simulador de partidas automáticas entre 2 computadoras.

Ejecutar:
    python main.py              # Simular 5 partidas con visualización
    python main.py --matches 10 # Simular 10 partidas
    python main.py --fast       # Sin visualización (solo estadísticas)
    python main.py --seed 42    # Seed fijo para reproducibilidad
"""
import argparse
import sys

from src.engine import TriominoGame, MatchSimulator
from src.visualization import visualize_game, GameRenderer


def run_visualized_simulation(num_matches: int = 5, 
                               animation_delay: float = 0.3,
                               seed: int = None):
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
    print(f"\n🤖 Computer 1 (Red) vs Computer 2 (Blue)")
    print(f"📊 Matches: {num_matches}")
    print(f"🎯 Target: 400 points")
    print("-" * 50)
    
    renderer = GameRenderer()
    renderer.setup_figure()
    renderer.animation_delay = animation_delay
    
    stats = {
        'wins': {'🔴 CPU-Alpha': 0, '🔵 CPU-Beta': 0},
        'total_rounds': 0,
        'highest_score': 0,
        'highest_scorer': ''
    }
    
    for match_num in range(1, num_matches + 1):
        print(f"\n🎯 Match {match_num}/{num_matches}...")
        
        match_seed = (seed + match_num) if seed else None
        game = TriominoGame(
            player_names=['🔴 CPU-Alpha', '🔵 CPU-Beta'],
            seed=match_seed
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


def run_fast_simulation(num_matches: int = 5, seed: int = None):
    """
    Run matches without visualization (faster).
    
    Args:
        num_matches: Number of games to play
        seed: Random seed for reproducibility
    """
    simulator = MatchSimulator(
        num_matches=num_matches,
        player_names=['🔴 CPU-Alpha', '🔵 CPU-Beta']
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
        default=5,
        help='Number of matches to simulate (default: 5)'
    )
    
    parser.add_argument(
        '-f', '--fast',
        action='store_true',
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
        default=0.3,
        help='Animation delay in seconds (default: 0.3)'
    )
    
    args = parser.parse_args()
    
    try:
        if args.fast:
            run_fast_simulation(
                num_matches=args.matches,
                seed=args.seed
            )
        else:
            run_visualized_simulation(
                num_matches=args.matches,
                animation_delay=args.delay,
                seed=args.seed
            )
    except KeyboardInterrupt:
        print("\n\n👋 Simulation cancelled by user.")
        sys.exit(0)


if __name__ == "__main__":
    main()
