"""
Triomino Deck Generator

Creates the official 56-tile Triomino deck.
Rules: Numbers 0-5, clockwise ascending order only (no mirrors).
"""
from __future__ import annotations
from typing import List
import random

from .tile import Triomino


def create_full_deck() -> List[Triomino]:
    """
    Generate the complete set of 56 unique Triomino tiles.
    
    The 56 tiles follow these rules:
    - Each tile has 3 vertex values from 0-5
    - Values are in clockwise ascending order (a <= b <= c)
    - This means 0-1-2 exists but 0-2-1 does NOT exist
    
    Composition:
    - 6 Triples: (0,0,0) through (5,5,5)
    - 15 Doubles: two same values + one different
    - 35 Singles: all different values
    
    Total: 56 tiles
    """
    deck: List[Triomino] = []
    
    # Generate all valid combinations where a <= b <= c
    for a in range(6):
        for b in range(a, 6):
            for c in range(b, 6):
                deck.append(Triomino(a, b, c))
    
    assert len(deck) == 56, f"Expected 56 tiles, got {len(deck)}"
    return deck


def create_shuffled_deck(seed: int | None = None) -> List[Triomino]:
    """Create a shuffled deck, optionally with a fixed seed for reproducibility."""
    if seed is not None:
        random.seed(seed)
    
    deck = create_full_deck()
    random.shuffle(deck)
    return deck


def get_deck_statistics() -> dict:
    """Get statistics about the deck composition."""
    deck = create_full_deck()
    
    triples = [t for t in deck if t.is_triple()]
    doubles = [t for t in deck if not t.is_triple() and len(set(t.values)) == 2]
    singles = [t for t in deck if len(set(t.values)) == 3]
    
    return {
        "total": len(deck),
        "triples": len(triples),
        "doubles": len(doubles),
        "singles": len(singles),
        "triples_list": [str(t) for t in triples],
        "max_value_tile": max(deck, key=lambda t: t.sum_value),
        "min_value_tile": min(deck, key=lambda t: t.sum_value),
    }


# Convenience function for quick access
def print_all_tiles():
    """Print all 56 tiles organized by type."""
    deck = create_full_deck()
    
    print("=" * 50)
    print("TRIOMINO DECK - 56 TILES")
    print("=" * 50)
    
    # Triples
    triples = [t for t in deck if t.is_triple()]
    print(f"\n🎯 TRIPLES ({len(triples)}):")
    print("  " + ", ".join(str(t) for t in triples))
    
    # Doubles (two same values)
    doubles = [t for t in deck if not t.is_triple() and len(set(t.values)) == 2]
    print(f"\n🎲 DOUBLES ({len(doubles)}):")
    for i in range(0, len(doubles), 6):
        print("  " + ", ".join(str(t) for t in doubles[i:i+6]))
    
    # Singles (all different)
    singles = [t for t in deck if len(set(t.values)) == 3]
    print(f"\n🃏 SINGLES ({len(singles)}):")
    for i in range(0, len(singles), 6):
        print("  " + ", ".join(str(t) for t in singles[i:i+6]))
    
    print("\n" + "=" * 50)


if __name__ == "__main__":
    print_all_tiles()
    stats = get_deck_statistics()
    print(f"\nMax value tile: {stats['max_value_tile']} = {stats['max_value_tile'].sum_value} pts")
    print(f"Min value tile: {stats['min_value_tile']} = {stats['min_value_tile'].sum_value} pts")
