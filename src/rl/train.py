"""
Training Script for Triomino RL Agent
"""
import os
import gymnasium as gym
from sb3_contrib import MaskablePPO
from sb3_contrib.common.wrappers import ActionMasker
from stable_baselines3.common.callbacks import CheckpointCallback, EvalCallback
from stable_baselines3.common.monitor import Monitor

from src.rl.env import TriominoEnv

def mask_fn(env: gym.Env) -> list:
    return env.unwrapped.action_masks()

def main():
    # Create log dirs
    log_dir = "logs/triomino_rl/"
    models_dir = "models/triomino_rl/"
    os.makedirs(log_dir, exist_ok=True)
    os.makedirs(models_dir, exist_ok=True)

    # Initialize environment
    env = TriominoEnv()
    env = Monitor(env, log_dir)
    env = ActionMasker(env, mask_fn)  # Wrap for masking

    # Define model
    # Use MultiInputPolicy because observation is a Dict
    model = MaskablePPO(
        "MultiInputPolicy",
        env,
        verbose=1,
        tensorboard_log=log_dir,
        learning_rate=3e-4,
        n_steps=2048,
        batch_size=64,
        gamma=0.99,
        gae_lambda=0.95,
        clip_range=0.2,
        ent_coef=0.01,
    )

    # Callbacks
    checkpoint_callback = CheckpointCallback(
        save_freq=10000,
        save_path=models_dir,
        name_prefix="ppo_triomino"
    )

    print("Starting training...")
    try:
        model.learn(
            total_timesteps=100_000, # Initial small run
            callback=checkpoint_callback,
            progress_bar=True
        )
    except KeyboardInterrupt:
        print("Training interrupted manually.")
    
    # Save final model
    model.save(f"{models_dir}/final_model")
    print("Training complete. Model saved.")

if __name__ == "__main__":
    main()
