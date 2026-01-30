# 🎮 Triominó Professional Edition

> **A State-of-the-Art implementation of the Triominó board game with premium Pygame graphics, Reinforcement Learning agents, and AI training capabilities.**

![Python](https://img.shields.io/badge/python-3.11+-yellow.svg)
![Pygame](https://img.shields.io/badge/pygame-2.6+-green.svg)
![RL](https://img.shields.io/badge/AI-MaskablePPO-red.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

---

## ✨ Features

### 🎨 Premium Visual Interface
- **60 FPS Rendering** with anti-aliased vector graphics
- **6 Color Themes**: Classic, Ocean, Sunset, Nature, Cyber, Pastel
- **5 Backgrounds**: Midnight, Deep Ocean, Forest, Void, Slate
- **Ghost Placement System**: Visual guides show valid moves
- **Interactive Camera**: Zoom (scroll) and Pan (right-click drag)

### 🤖 AI & Reinforcement Learning
- **Multiple AI Strategies**: Greedy, Random, PPO-trained agents
- **Built-in Training**: Launch RL training directly from the menu
- **TensorBoard Integration**: Monitor training metrics in real-time
- **Action Masking**: Ensures only valid moves are considered

### 👥 Game Modes
| Mode | Description |
|------|-------------|
| **Human vs AI** | Challenge the AI at various difficulties |
| **Human vs Human** | Local hotseat with hand-hiding "curtain" |
| **Bot vs Bot** | Watch AIs battle (infinite mode for training) |

---

## 🚀 Quick Start

### Installation
```bash
git clone https://github.com/your-repo/triomino-generator.git
cd triomino-generator
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Play
```bash
./run.sh
```

### Train RL Agent
**Option A: From Menu**
Click the "🧠 Train RL Agent" button in the main menu.

**Option B: Command Line**
```bash
./run.sh train
```

### Monitor Training
```bash
tensorboard --logdir logs/triomino_rl/
```

---

## 🎮 Controls

| Input | Action |
|-------|--------|
| **Left Click (Hand)** | Select tile |
| **Left Click (Ghost)** | Place tile |
| **Right Click + Drag** | Pan camera |
| **Mouse Wheel** | Zoom in/out |
| **N** | Toggle Night Mode (Bot vs Bot) |
| **G** | Toggle Ghost Trails (Bot vs Bot) |
| **↑/↓** | Speed up/slow down (Bot vs Bot) |
| **M** | Mute/Unmute sounds |
| **ESC** | Return to menu |

---

## 📁 Project Structure

```
triomino-generator/
├── src/
│   ├── engine/          # Core game logic (rules, validation, scoring)
│   ├── gui/             # Pygame interface
│   │   ├── main.py      # Application entry point
│   │   ├── pygame_board.py  # Board rendering
│   │   └── assets.py    # Themes, colors, fonts
│   ├── ai/              # AI strategies (Greedy, Random, Human wrapper)
│   ├── rl/              # Reinforcement Learning
│   │   ├── env.py       # Gymnasium environment
│   │   └── train.py     # Training script (MaskablePPO)
│   └── cli/             # Legacy terminal interface
├── models/              # Saved RL checkpoints
├── logs/                # Training logs + tensorboard
├── run.sh               # Master launcher script
└── requirements.txt
```

---

## 🧠 RL Training Details

| Parameter | Value |
|-----------|-------|
| Algorithm | MaskablePPO (sb3-contrib) |
| Policy | MultiInputPolicy |
| Learning Rate | 3e-4 |
| Steps per Update | 2048 |
| Batch Size | 64 |
| Entropy Coefficient | 0.01 |

### Observation Space
- Board state (placed tiles)
- Player hand (current tiles)
- Legal action mask

### Reward Shaping
- Points earned from placements
- Bonus for winning
- Penalty for invalid moves (masked out)

---

## 🛠️ Troubleshooting

| Issue | Solution |
|-------|----------|
| `pkg_resources` warning | Harmless, ignore it |
| Training button does nothing | Install `sb3-contrib`: `pip install sb3-contrib` |
| Window closes immediately | Run from terminal to see error logs |
| No sound | Check M key isn't muting |

---

## 📜 Logs

Logs are saved automatically:
- `logs/gui/` - GUI session logs
- `logs/triomino_rl/` - Training metrics
- `models/triomino_rl/` - Model checkpoints

---

## 📄 License

MIT License - See LICENSE file for details.

---

*Built with ❤️ using Python, Pygame, and Stable-Baselines3*
