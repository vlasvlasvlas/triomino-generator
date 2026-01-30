"""
Triomino Reinforcement Learning Environment

Compatible with Gymnasium and Stable-Baselines3.
"""
import gymnasium as gym
import numpy as np
from gymnasium import spaces
from typing import Optional, Tuple, Dict, Any, List

from src.engine.game import TriominoGame, TurnAction
from src.ai.strategies import get_strategy
from src.models import Triomino, PlacedTile
from src.engine.rules import ScoreType, calculate_pass_penalty, calculate_draw_failure_penalty

# Constants
MAX_HAND_SIZE = 30  # Max potential hand size (usually much lower)
GRID_SIZE = 64      # Fixed grid size for observation (centered)
CHANNELS = 4        # Occupied, v0, v1, v2

class TriominoEnv(gym.Env):
    """
    RL Environment for Triomino.
    
    Action Space:
        Discrete(MAX_HAND_SIZE + 2)
        - 0..N-1: Play tile at index i in hand (greedy placement)
        - N: Draw tile
        - N+1: Pass
        
    Observation Space:
        Dict:
        - "board": (channels, height, width) grid
        - "hand": (MAX_HAND_SIZE, 3) tile values
        - "hand_mask": (MAX_HAND_SIZE,) 1 if tile exists, 0 otherwise
        - "state": (scores, pool_size, opponent_hand_size, ...)
    """
    metadata = {"render_modes": ["human", "ansi"]}
    
    def __init__(self, render_mode: Optional[str] = None):
        super().__init__()
        self.render_mode = render_mode
        self.game = None
        self.current_player_idx = 0  # 0 for RL agent, 1 for Opponent
        
        # Actions: Select any of the cards in hand (up to limit), or Draw, or Pass
        self.action_space = spaces.Discrete(MAX_HAND_SIZE + 2)
        self.DRAW_ACTION = MAX_HAND_SIZE
        self.PASS_ACTION = MAX_HAND_SIZE + 1
        
        # Observation
        self.observation_space = spaces.Dict({
            # Board: 4 channels x 64 x 64
            # Ch 0: Occupied (1 or 0)
            # Ch 1-3: Vertex values normalized (val/5.0)
            "board": spaces.Box(low=0, high=1, shape=(CHANNELS, GRID_SIZE, GRID_SIZE), dtype=np.float32),
            
            # Hand: Up to MAX_HAND_SIZE tiles, each with 3 values
            "hand": spaces.Box(low=0, high=1, shape=(MAX_HAND_SIZE, 3), dtype=np.float32),
            
            # Mask needed to know which hand slots are real
            "hand_mask": spaces.Box(low=0, high=1, shape=(MAX_HAND_SIZE,), dtype=np.float32),
            
            # Scalar game state
            # [my_score_norm, opp_score_norm, pool_norm, my_hand_size_norm, opp_hand_size_norm, draws_left_norm]
            "state": spaces.Box(low=-1, high=1, shape=(6,), dtype=np.float32)
        })

    def reset(self, seed: Optional[int] = None, options: Optional[Dict] = None) -> Tuple[Dict, Dict]:
        super().reset(seed=seed)
        
        # Initialize new game
        self.game = TriominoGame(
            player_names=["RL-Agent", "Opponent"],
            seed=seed,
            strategies=[get_strategy("greedy"), get_strategy("greedy")]
        )
        self.game.setup_round()
        
        self.draws_current_turn = 0
        
        # Play opening automatically
        self.game.play_opening()
        
        # Fast forward to Agent's turn if Opponent started
        while self.game.current_player_idx != 0 and not self.game.game_over:
            self._play_opponent_turn()
            self.game.check_round_end()
            self.game.next_player()
            
        return self._get_observation(), {}

    def step(self, action: int) -> Tuple[Dict, float, bool, bool, Dict]:
        if self.game.game_over:
            return self._get_observation(), 0, True, False, {}
            
        reward = 0
        terminated = False
        truncated = False
        info = {}
        
        player = self.game.players[0]
        
        # Execute Action
        if action == self.DRAW_ACTION:
            # DRAW
            count = self.game.execute_draw(player)
            if count > 0:
                reward += -2.0  # Penalty for drawing
                self.draws_current_turn += 1
            else:
                reward += -5.0 # Invalid draw attempt (empty pool?)
            
        elif action == self.PASS_ACTION:
            # PASS - End Turn
            # Penalty (25 points is standard strict penalty for passing)
            # But let's make it proportional to potential? No, fixed.
            if self.draws_current_turn > 0:
                points, _ = calculate_draw_failure_penalty(self.draws_current_turn)
            else:
                points, _ = calculate_pass_penalty()
            player.add_score(points)
            reward += points

            # Round check
            round_res = self.game.check_round_end()
            if round_res:
                if round_res.winner == player:
                    reward += 100.0
                terminated = True
            else:
                # End turn logic
                self.game.next_player()
                self.draws_current_turn = 0
                self._play_opponent_loop()
            
        else:
            # PLAY TILE
            hand_idx = action
            if hand_idx >= len(player.hand):
                # Invalid action (should be masked out usually)
                reward += -100.0
                terminated = True
            else:
                tile = player.hand[hand_idx]
                placements = self.game.board.find_valid_placements(tile)
                
                if not placements:
                    # Invalid move (should be masked)
                    reward += -50.0
                else:
                    # Valid move - Greedy placement logic
                    def calculate_greedy_score(tile, p):
                        # Create temporary copy to get values with correct rotation
                        t_copy = tile.copy()
                        t_copy.rotation = p.rotation
                        score = sum(t_copy.values)
                        if p.bridge_count > 0: score += 40
                        if p.hexagon_count > 0: score += 50
                        return score

                    best_p = max(placements, key=lambda p: calculate_greedy_score(tile, p))
                    
                    # Execute placement
                    turn_res = self.game.execute_place(player, tile, best_p, self.draws_current_turn)
                    reward += turn_res.points_earned
                    
                    # Round check
                    round_res = self.game.check_round_end()
                    if round_res:
                        if round_res.winner == player:
                            reward += 100.0
                        terminated = True
                    else:
                        # Turn complete
                        self.game.next_player()
                        self.draws_current_turn = 0
                        self._play_opponent_loop()
        
        if self.game.game_over:
            terminated = True
            
        return self._get_observation(), reward, terminated, truncated, info

    def _play_opponent_loop(self):
        """Play opponent moves until it's agent's turn again or game over."""
        while self.game.current_player_idx != 0 and not self.game.game_over:
            self._play_opponent_turn()
            
            res = self.game.check_round_end()
            if res:
                self.game.game_over = True
                break
            
            # If start player was opponent, loop might need to check strict turn order
            # But check_round_end handles logic. 
            # We just need to ensure we stop if it's our turn.
            if self.game.current_player_idx == 0:
                break
            
            # Actually play_turn already called next_player if internally managed?
            # No, play_turn returns Result. We must call next_player manually in the loop usually.
            # But wait, `play_turn` in game.py handles ONE player's turn fully.
            # It does NOT call next_player().
            if not res: # Only next player if round not ended
                self.game.next_player()

    def _play_opponent_turn(self):
        """Execute one full turn for opponent."""
        self.game.play_turn()

    def action_masks(self) -> List[bool]:
        """Compute action mask for valid moves."""
        player = self.game.players[0]
        mask = [False] * (MAX_HAND_SIZE + 2)
        
        # 1. Tile actions
        # Can play if valid placement exists
        can_play_any = False
        for i, tile in enumerate(player.hand):
            if i >= MAX_HAND_SIZE: break
            if self.game.board.find_valid_placements(tile):
                mask[i] = True
                can_play_any = True
                
        # 2. Draw action
        # Valid if pool not empty AND draws < 3
        # In Triomino, if you CAN play, you usually MUST play? 
        # Standard rules: If you can't play, you must draw.
        # Can you draw if you CAN play? Often yes (strategic).
        # We allow it unless max draws reached.
        # MAX_DRAWS usually 3.
        if len(self.game.pool) > 0 and self.draws_current_turn < 3 and not can_play_any:
             mask[self.DRAW_ACTION] = True
             
        # 3. Pass action
        # Valid only if:
        # A) Pool empty AND no moves
        # B) Draws == 3 AND no moves
        # Basically: If you can't play and can't draw (or drew max).
        
        cant_draw = (len(self.game.pool) == 0) or (self.draws_current_turn >= 3)
        
        if not can_play_any and cant_draw:
             mask[self.PASS_ACTION] = True
             
        return mask

    def _get_observation(self) -> Dict[str, Any]:
        """Convert game state to tensors."""
        # 1. Board Grid
        grid = np.zeros((CHANNELS, GRID_SIZE, GRID_SIZE), dtype=np.float32)
        
        # Map board coordinates (cube/offset) to grid
        # Center is (GRID_SIZE/2, GRID_SIZE/2)
        center_q, center_r = GRID_SIZE // 2, GRID_SIZE // 2
        
        # We need a reference point. Let's assume (7,7) is center?
        # Or just use q,r relative to first tile.
        # Board coordinates are arbitrary infinite grid.
        # We'll center on the centroid of placed tiles.
        
        if self.game.board.tiles:
            min_q = min(t.q for t in self.game.board.tiles.values())
            max_q = max(t.q for t in self.game.board.tiles.values())
            min_r = min(t.r for t in self.game.board.tiles.values())
            max_r = max(t.r for t in self.game.board.tiles.values())
            
            mid_q = (min_q + max_q) // 2
            mid_r = (min_r + max_r) // 2
        else:
            mid_q, mid_r = 7, 7 # Default start
            
        offset_q = center_q - mid_q
        offset_r = center_r - mid_r
        
        for pos, placed in self.game.board.tiles.items():
            q, r, ori = pos
            gq = q + offset_q
            gr = r + offset_r
            
            if 0 <= gq < GRID_SIZE and 0 <= gr < GRID_SIZE:
                # Channel 0: Occupied
                grid[0, gq, gr] = 1.0
                # Channels 1-3: Values
                v = placed.values
                grid[1, gq, gr] = v[0] / 5.0
                grid[2, gq, gr] = v[1] / 5.0
                grid[3, gq, gr] = v[2] / 5.0
                
        # 2. Hand
        hand = np.zeros((MAX_HAND_SIZE, 3), dtype=np.float32)
        hand_mask = np.zeros((MAX_HAND_SIZE,), dtype=np.float32)
        player = self.game.players[0]
        
        for i, tile in enumerate(player.hand):
            if i >= MAX_HAND_SIZE: break
            hand[i] = [v/5.0 for v in tile.values]
            hand_mask[i] = 1.0
            
        # 3. Scalar State
        state = np.array([
            player.score / 400.0,
            self.game.players[1].score / 400.0,
            len(self.game.pool) / 56.0,
            len(player.hand) / 20.0,
            len(self.game.players[1].hand) / 20.0,
            0.0 # draws left (omitted for now)
        ], dtype=np.float32)
        
        return {
            "board": grid,
            "hand": hand,
            "hand_mask": hand_mask,
            "state": state
        }
