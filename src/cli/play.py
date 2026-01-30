#!/usr/bin/env python3
"""
Triominó - Human vs AI Interactive Game (CLI)
"""
import sys
import os
import argparse
import random
import logging
from datetime import datetime
from typing import List, Optional, Tuple

from src.engine.game import TriominoGame, TurnAction, TurnResult
from src.engine.rules import calculate_pass_penalty, calculate_draw_failure_penalty
from src.ai.strategies import AIStrategy, get_strategy, ScoredMove
from src.models import Triomino, ValidPlacement, Player, GameBoard, create_shuffled_deck
from src.visualization.renderer import GameRenderer
import matplotlib.pyplot as plt

LOGGER = None


def setup_logger():
    os.makedirs("logs/cli", exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    log_path = os.path.join("logs", "cli", f"cli-{ts}.log")
    logger = logging.getLogger(f"triomino_cli_{ts}")
    logger.setLevel(logging.INFO)
    handler = logging.FileHandler(log_path, encoding="utf-8")
    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.propagate = False
    return logger

class HumanStrategy(AIStrategy):
    """
    Interactive strategy that asks the user for input via CLI.
    """
    def choose_move(self, player: Player, board: GameBoard) -> Optional[ScoredMove]:
        # This method is technically required by the Strategy interface, 
        # but for Human interactive play, we handle the choice in the main loop 
        # to allow for retries, drawing, etc.
        # Returning None signals "no move decided automatically".
        return None

def print_board(game: TriominoGame, renderer: GameRenderer):
    """Render the board graphically and simple stats in CLI."""
    # Update Graphic GUI
    renderer.draw_board(game.board, animate=True)
    renderer.update_info_panel(game)
    
    # CLI Stats
    print("\n" + "="*60)
    print(f" Round: {game.round_number} | Pool: {len(game.pool)} tiles")
    print(f" Scores: {game.players[0].name}: {game.players[0].score} | {game.players[1].name}: {game.players[1].score}")
    print("="*60 + "\n")


def print_hand(player: Player):
    """Show the player's hand with indices."""
    print(f"\nYour Hand ({len(player.hand)}):")
    for i, tile in enumerate(player.hand):
        print(f"  [{i}] {tile}")
    print("  [D] Draw Tile")
    print("  [P] Pass Turn")

def get_human_input(game: TriominoGame, player: Player, renderer: GameRenderer) -> TurnResult:
    """Handle the interactive turn loop for the human."""
    draws_made = 0
    
    while True:
        print_board(game, renderer)
        print_hand(player)
        
        # Check if we can play anything
        can_play = game.can_player_move(player)
        if not can_play and len(game.pool) == 0 and draws_made >= 3:
             print("\n⚠️ No moves possible and cannot draw more. You must PASS.")
        
        choice = input(f"\nTarget> ").strip().lower()
        
        if choice in ['q', 'quit', 'exit']:
            print("Thanks for playing!")
            sys.exit(0)
            
        if choice == 'd':
            # Draw
            if can_play:
                print("❌ You must play a tile if possible.")
                input("Press Enter...")
                continue
            if len(game.pool) == 0:
                print("❌ Pool is empty!")
                input("Press Enter...")
                continue
            if draws_made >= 3:
                print("❌ Max draws (3) reached!")
                input("Press Enter...")
                continue
                
            count = game.execute_draw(player)
            if count > 0:
                draws_made += 1
                drawn_tile = player.hand[-1]
                print(f"🀄 You drew: {drawn_tile}")
                if LOGGER:
                    LOGGER.info("Draw tile: player=%s draws_made=%s pool=%s",
                                player.name, draws_made, len(game.pool))
                # Check if playable?
            continue
            
        if choice == 'p':
            # Pass
            if can_play:
                print("❌ You must play a tile if possible.")
                input("Press Enter...")
                continue
            if len(game.pool) > 0 and draws_made < 3:
                 print("❌ You cannot pass yet! You must draw if you can't play.")
                 input("Press Enter...")
                 continue

            if draws_made > 0:
                points, event = calculate_draw_failure_penalty(draws_made)
            else:
                points, event = calculate_pass_penalty()
            player.add_score(points)
            print(f"⏭️  Passed turn ({points} pts).")
            if LOGGER:
                LOGGER.info("Pass: player=%s points=%s draws_made=%s",
                            player.name, points, draws_made)
            game.next_player()
            return TurnResult(player, TurnAction.PASS, None, draws_made, points, [event], "Passed")

        # Try tile index
        try:
            idx = int(choice)
            if idx < 0 or idx >= len(player.hand):
                print("❌ Invalid index.")
                continue
                
            tile = player.hand[idx]
            
            # Find valid placements
            placements = game.board.find_valid_placements(tile)
            if not placements:
                print(f"❌ Tile {tile} cannot be placed anywhere.")
                input("Press Enter...")
                continue
            
            # Create list of ghost tiles for visualization
            options = []
            for i, p in enumerate(placements):
                # Calculate score for display (optional)
                t_copy = tile.copy()
                t_copy.rotation = p.rotation
                # Ghost tile to draw
                from src.models import PlacedTile
                ghost = PlacedTile(
                    tile=t_copy,
                    q=p.row,
                    r=p.col,
                    player_id=game.players.index(player),
                    orientation=p.orientation
                )
                options.append((ghost, i + 1)) # 1-based index
            
            # Show ghosts on GUI
            renderer.draw_board(game.board, animate=False) # Clear previous ghosts
            renderer.draw_ghost_placements(options)
            
            # Ask user to choose
            print(f"\n🎯 Found {len(placements)} valid options. Look at the window!")
            print(f"   Enter number [1-{len(placements)}] to confirm, or 0 to cancel:")
            
            try:
                sel = int(input("Option> ").strip())
                if sel == 0:
                    renderer.draw_board(game.board) # Clear ghosts
                    continue
                if sel < 1 or sel > len(placements):
                    print("❌ Invalid option.")
                    renderer.draw_board(game.board)
                    continue
                
                selected_placement = placements[sel-1]
                
                print(f"✅ Placing {tile} at option {sel}...")
                renderer.draw_board(game.board) # Clear ghosts before animating? 
                # Actually execute_place will trigger next turn loop which calls print_board, 
                # so it will clean up naturally.
                
                res = game.execute_place(player, tile, selected_placement, draws_made)
                if LOGGER:
                    LOGGER.info("Place tile: player=%s tile=%s points=%s",
                                player.name, tile, res.points_earned)
                game.next_player()
                return res
                
            except ValueError:
                print("❌ Invalid input.")
                renderer.draw_board(game.board)
                continue
            
        except ValueError:
            print("❌ Invalid command. Use number to play, D to draw, P to pass.")

def main():
    global LOGGER
    LOGGER = setup_logger()

    parser = argparse.ArgumentParser(description="Triominó - Human vs AI")
    parser.add_argument("--difficulty", type=str, default="greedy", choices=["random", "greedy", "human"],
                      help="Opponent type: 'human', 'greedy', or 'random'")
    parser.add_argument("--name", type=str, default="Player 1", help="Your player name")
    parser.add_argument("--name2", type=str, default="Player 2", help="Second player name (for human vs human)")
    args = parser.parse_args()

    # Setup
    print("""
    ╔══════════════════════════════════════╗
    ║        TRIOMINÓ GRAPHICAL CLI        ║
    ╚══════════════════════════════════════╝
    """)
    
    player1_strategy = HumanStrategy()

    if LOGGER:
        LOGGER.info("CLI start difficulty=%s name1=%s name2=%s",
                    args.difficulty, args.name, args.name2)
    
    if args.difficulty == "human":
        player2_strategy = HumanStrategy()
        p2_name = args.name2
    else:
        player2_strategy = get_strategy(args.difficulty)
        p2_name = f"Bot-{args.difficulty.title()}"
    
    strategies = [player1_strategy, player2_strategy]
    
    game = TriominoGame(
        player_names=[args.name, p2_name],
        strategies=strategies,
        seed=random.randint(1, 10000)
    )
    
    # Init Renderer
    renderer = GameRenderer()
    renderer.setup_figure()
    plt.show(block=False)  # Show non-blocking
    
    game.setup_round()
    
    print("🎲 determining starting player...")
    opening_res = game.play_opening()
    print(f"📢 {opening_res.message}")
    print(f"   Points: {opening_res.points_earned}")
    
    # Update view after opening
    renderer.draw_board(game.board)
    renderer.update_info_panel(game)
    
    game.next_player()
    
    # Game Loop
    while not game.game_over:
        current = game.current_player
        current_strategy = game.strategies[game.current_player_idx]
        is_human = isinstance(current_strategy, HumanStrategy)
        
        print(f"\n>>> Turn: {current.name}")
        
        if is_human:
            # Human Turn (Any Human)
            get_human_input(game, current, renderer)
        else:
            # AI Turn
            print("🤖 AI is thinking...")
            plt.pause(0.5) # Thinking time
            turn_res = game.play_turn()
            
            # Update Render
            renderer.draw_board(game.board)
            renderer.update_info_panel(game, turn_res)
            
            print(f"   {turn_res.message}")
            if turn_res.points_earned > 0:
                print(f"   Matches: +{turn_res.points_earned} pts")
            if turn_res.tiles_drawn > 0:
                print(f"   (Drew {turn_res.tiles_drawn} tiles)")
            
            game.next_player()

            
        # Check Round/Game Status (simple check)
        # Typically check_round_end() is called inside play_turn() or manually?
        # Engine: play_turn returns Result. engine methods don't auto-check round end globally?
        # We need to call check_round_end().
        
        round_res = game.check_round_end()
        if round_res:
            print(f"\n🎉 ROUND OVER! Winner: {round_res.winner.name}")
            print(f"Reason: {round_res.reason}")
            print(f"Scores: {game.players[0].name}={game.players[0].score}, {game.players[1].name}={game.players[1].score}")
            game.game_over = True 
            
            # Keep window open
            renderer.show_match_result(round_res.winner.name, {})
            print("Close graphics window to finish.")
            plt.show(block=True)


if __name__ == "__main__":
    main()
