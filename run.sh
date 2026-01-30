#!/bin/bash

# 🎮 Triominó - Smart Launcher
# Simplifies running the game, training, or CLI tools.

# 1. Move to script directory to ensure relative paths work
cd "$(dirname "$0")"

# 2. Activate Virtual Environment (if it exists)
if [ -d "venv" ]; then
    source venv/bin/activate
elif [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# 3. Handle Arguments
MODE=${1:-gui} # Default to 'gui' if no argument provided

case $MODE in
    "gui"|"play")
        echo "🚀 Launching Graphical Interface..."
        python3 -m src.gui.main "${@:2}"
        ;;
    
    "train")
        echo "🧠 Starting Reinforcement Learning Training..."
        echo "   (Logs will be saved to tensorboard)"
        python3 -m src.rl.train "${@:2}"
        ;;

    "cli")
        echo "💻 Launching Legacy Terminal Mode..."
        python3 -m src.cli.play "${@:2}"
        ;;
    
    "help"|"--help"|"-h")
        echo "Usage: ./run.sh [mode] [options]"
        echo ""
        echo "Modes:"
        echo "  gui    : (Default) Run the new Visual Game"
        echo "  train  : Run RL Training loop"
        echo "  cli    : Run Legacy Terminal Game"
        echo ""
        ;;
    
    *)
        # If unknown command, assume it's an arg for GUI or just run GUI
        echo "🚀 Launching Graphical Interface..."
        python3 -m src.gui.main "$@"
        ;;
esac
