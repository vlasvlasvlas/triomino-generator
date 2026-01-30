#!/usr/bin/env python3
"""
Generate plots from run logs in runs/run-*.json.
"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Dict, List

import matplotlib.pyplot as plt


def load_runs(input_dir: Path) -> List[Dict]:
    files = sorted(input_dir.glob("run-*.json"))
    runs = []
    for path in files:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
            data["_path"] = path
            runs.append(data)
    return runs


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def plot_run(run: Dict, output_dir: Path, show: bool = False) -> None:
    players = run.get("players", [])
    results = run.get("results", [])
    if not results:
        return

    wins = defaultdict(int)
    rounds = []
    scores_by_player = {p: [] for p in players}

    for match in results:
        winner = match.get("winner")
        if winner:
            wins[winner] += 1
        rounds.append(match.get("rounds_played", 0))
        final_scores = match.get("final_scores", {})
        for p in players:
            scores_by_player[p].append(final_scores.get(p, 0))

    # Plot wins
    plt.figure(figsize=(6, 4))
    names = list(wins.keys())
    values = [wins[n] for n in names]
    plt.bar(names, values, color="#1e88e5")
    plt.title("Wins per player")
    plt.ylabel("Wins")
    plt.tight_layout()
    wins_path = output_dir / "wins.png"
    plt.savefig(wins_path, dpi=150)
    if show:
        plt.show()
    plt.close()

    # Plot rounds per match
    plt.figure(figsize=(6, 4))
    plt.plot(range(1, len(rounds) + 1), rounds, marker="o", color="#43a047")
    plt.title("Rounds per match")
    plt.xlabel("Match")
    plt.ylabel("Rounds")
    plt.tight_layout()
    rounds_path = output_dir / "rounds.png"
    plt.savefig(rounds_path, dpi=150)
    if show:
        plt.show()
    plt.close()

    # Plot scores per match
    plt.figure(figsize=(6, 4))
    for p, scores in scores_by_player.items():
        plt.plot(range(1, len(scores) + 1), scores, marker="o", label=p)
    plt.title("Final scores per match")
    plt.xlabel("Match")
    plt.ylabel("Score")
    plt.legend()
    plt.tight_layout()
    scores_path = output_dir / "scores.png"
    plt.savefig(scores_path, dpi=150)
    if show:
        plt.show()
    plt.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Plot metrics from run logs.")
    parser.add_argument("--input", default="runs", help="Input directory with run-*.json files")
    parser.add_argument("--output", default="runs/plots", help="Output directory for plots")
    parser.add_argument("--show", action="store_true", help="Display plots interactively")
    args = parser.parse_args()

    input_dir = Path(args.input)
    output_base = Path(args.output)
    ensure_dir(output_base)

    runs = load_runs(input_dir)
    if not runs:
        print(f"No run-*.json files found in {input_dir}")
        return

    for run in runs:
        stem = run["_path"].stem
        out_dir = output_base / stem
        ensure_dir(out_dir)
        plot_run(run, out_dir, show=args.show)
        print(f"Saved plots to {out_dir}")


if __name__ == "__main__":
    main()
