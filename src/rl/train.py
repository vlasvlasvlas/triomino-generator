"""
Training Script for Triomino RL Agent
With friendly, explained metrics output
"""
import os
import sys
import gymnasium as gym
from sb3_contrib import MaskablePPO
from sb3_contrib.common.wrappers import ActionMasker
from stable_baselines3.common.callbacks import BaseCallback, CheckpointCallback
from stable_baselines3.common.monitor import Monitor

from src.rl.env import TriominoEnv


def mask_fn(env: gym.Env) -> list:
    return env.unwrapped.action_masks()


class FriendlyMetricsCallback(BaseCallback):
    """
    Custom callback that prints friendly, explained metrics during training.
    """
    
    def __init__(self, verbose=1):
        super().__init__(verbose)
        self.episode_count = 0
        self.total_wins = 0
        self.total_losses = 0
        
    def _on_step(self) -> bool:
        # Check if episode ended
        if self.locals.get("dones") is not None:
            for i, done in enumerate(self.locals["dones"]):
                if done:
                    self.episode_count += 1
                    
                    # Get info from environment
                    infos = self.locals.get("infos", [{}])
                    info = infos[i] if i < len(infos) else {}
                    
                    # Track wins
                    if info.get("won", False):
                        self.total_wins += 1
                    else:
                        self.total_losses += 1
                    
                    # Print friendly update every 10 episodes
                    if self.episode_count % 10 == 0:
                        self._print_friendly_update()
        
        return True
    
    def _print_friendly_update(self):
        """Print metrics with explanations."""
        print("\n" + "="*60)
        print(f"📊 TRAINING PROGRESS - Episode {self.episode_count}")
        print("="*60)
        
        # Win rate
        total_games = self.total_wins + self.total_losses
        if total_games > 0:
            win_rate = (self.total_wins / total_games) * 100
            trend = "📈 Mejorando!" if win_rate > 50 else "📉 Aprendiendo..."
            print(f"\n🏆 WIN RATE: {win_rate:.1f}%  {trend}")
            print(f"   → Ganadas: {self.total_wins} | Perdidas: {self.total_losses}")
            print(f"   ℹ️  Objetivo: >50% significa que el agente gana más de lo que pierde")
        
        # Get SB3 logger values if available
        if hasattr(self.model, "logger") and self.model.logger is not None:
            logs = self.model.logger.name_to_value
            
            # Explained loss
            if "train/loss" in logs:
                loss = logs["train/loss"]
                print(f"\n📉 LOSS (Pérdida): {loss:.4f}")
                print(f"   ℹ️  Debería BAJAR con el tiempo. Mide el error del modelo.")
            
            # Policy loss
            if "train/policy_gradient_loss" in logs:
                pg_loss = logs["train/policy_gradient_loss"]
                print(f"\n🎯 POLICY LOSS: {pg_loss:.4f}")
                print(f"   ℹ️  Qué tan bien elige acciones. Debería estabilizarse cerca de 0.")
            
            # Value loss
            if "train/value_loss" in logs:
                v_loss = logs["train/value_loss"]
                print(f"\n💰 VALUE LOSS: {v_loss:.4f}")
                print(f"   ℹ️  Qué tan bien predice recompensas futuras. Debería BAJAR.")
            
            # Entropy
            if "train/entropy_loss" in logs:
                entropy = -logs["train/entropy_loss"]  # Negate because it's stored as loss
                print(f"\n🎲 ENTROPY (Exploración): {entropy:.4f}")
                print(f"   ℹ️  Qué tan aleatorio es. Alto=explora, Bajo=explota lo aprendido.")
            
            # Approx KL
            if "train/approx_kl" in logs:
                kl = logs["train/approx_kl"]
                status = "✅ OK" if kl < 0.02 else "⚠️ Alto (updates muy agresivos)"
                print(f"\n📏 KL DIVERGENCE: {kl:.4f}  {status}")
                print(f"   ℹ️  Mide cuánto cambia la política. Debe ser bajo (<0.02).")
        
        print("\n" + "="*60)
        print("💡 TIP: Para ver gráficos detallados ejecutá:")
        print("   tensorboard --logdir logs/triomino_rl/")
        print("="*60 + "\n")


def main():
    print("""
╔═══════════════════════════════════════════════════════════════╗
║           🧠 TRIOMINO RL TRAINING                             ║
║                                                               ║
║  El agente aprenderá a jugar Triominó contra un oponente.     ║
║  Verás métricas explicadas cada 10 episodios.                 ║
║                                                               ║
║  Presioná Ctrl+C para detener y guardar el modelo.            ║
╚═══════════════════════════════════════════════════════════════╝
    """)
    
    # Create log dirs
    log_dir = "logs/triomino_rl/"
    models_dir = "models/triomino_rl/"
    os.makedirs(log_dir, exist_ok=True)
    os.makedirs(models_dir, exist_ok=True)

    print("📦 Inicializando entorno...")
    env = TriominoEnv()
    env = Monitor(env, log_dir)
    env = ActionMasker(env, mask_fn)
    print("✅ Entorno listo!")

    print("\n🔧 Configurando modelo MaskablePPO...")
    model = MaskablePPO(
        "MultiInputPolicy",
        env,
        verbose=0,  # Disable default verbose, we use custom callback
        tensorboard_log=log_dir,
        learning_rate=3e-4,
        n_steps=2048,
        batch_size=64,
        gamma=0.99,
        gae_lambda=0.95,
        clip_range=0.2,
        ent_coef=0.01,
    )
    print("✅ Modelo configurado!")

    # Callbacks
    checkpoint_callback = CheckpointCallback(
        save_freq=10000,
        save_path=models_dir,
        name_prefix="ppo_triomino"
    )
    friendly_callback = FriendlyMetricsCallback()

    print("\n" + "🚀 COMENZANDO ENTRENAMIENTO...")
    print("   (Esto puede tomar varios minutos)\n")
    
    try:
        model.learn(
            total_timesteps=100_000,
            callback=[checkpoint_callback, friendly_callback],
            progress_bar=True
        )
    except KeyboardInterrupt:
        print("\n\n⏹️  Entrenamiento interrumpido por el usuario.")
    
    # Save final model
    final_path = f"{models_dir}/final_model"
    model.save(final_path)
    print(f"\n✅ Modelo guardado en: {final_path}")
    print("\n🎉 ¡Entrenamiento completo!")
    print("   Podés usar este modelo en el juego seleccionando dificultad 'PPO Agent'.")


if __name__ == "__main__":
    main()
