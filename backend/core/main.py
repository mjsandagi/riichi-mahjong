"""
Main entry point for the Riichi Mahjong CLI game.

This module provides the main() function to start a CLI game
using the new decoupled architecture.

Usage:
    python -m backend.core.main
    
Or from the project root:
    python main.py
"""

from .game_controller import CLIGameController
from ..ai import HumanCLIAgent, RandomAgent


def main():
    """
    Start a CLI game of Riichi Mahjong.
    
    Player 0 (East) is the human player.
    Players 1-3 are random AI bots.
    """
    print("\n=== RIICHI MAHJONG ===\n")
    
    # Create controller with player names
    controller = CLIGameController(["You (East)", "South", "West", "North"])
    
    # Set up agents
    controller.set_agent(0, HumanCLIAgent("You"))
    controller.set_agent(1, RandomAgent("South Bot", call_rate=0.2, riichi_rate=0.9))
    controller.set_agent(2, RandomAgent("West Bot", call_rate=0.2, riichi_rate=0.9))
    controller.set_agent(3, RandomAgent("North Bot", call_rate=0.2, riichi_rate=0.9))
    
    # Configure delays for human viewing
    controller.turn_delay = 0.5
    
    # Run the game
    final_state = controller.run_game()
    
    return final_state


def test_shanten():
    """Test function for shanten calculator (legacy)."""
    from .tiles import Suit, Tile, Rank
    from .shanten import ShantenCalculator
    
    calc = ShantenCalculator()

    # 1. Create a Tenpai Hand (13 tiles, waiting for 1)
    # Hand: 123m 456m 789m 11p 55s (Waiting for 1p or 5s)
    hand = [
        Tile(Suit.MAN, Rank.ONE), Tile(Suit.MAN, Rank.TWO), Tile(Suit.MAN, Rank.THREE),
        Tile(Suit.MAN, Rank.FOUR), Tile(Suit.MAN, Rank.FIVE), Tile(Suit.MAN, Rank.SIX),
        Tile(Suit.MAN, Rank.SEVEN), Tile(Suit.MAN, Rank.EIGHT), Tile(Suit.MAN, Rank.NINE),
        Tile(Suit.PIN, Rank.ONE), Tile(Suit.PIN, Rank.ONE),
        Tile(Suit.SOU, Rank.FIVE), Tile(Suit.SOU, Rank.FIVE),
    ]

    shanten = calc.calculate_shanten(hand)
    print(f"Hand Shanten: {shanten}") 
    # Expected: 0 (Tenpai)

    # 2. Add the winning tile (1p)
    hand.append(Tile(Suit.PIN, Rank.ONE))
    shanten = calc.calculate_shanten(hand)
    print(f"Winning Hand Shanten: {shanten}")
    # Expected: -1 (Agari)


if __name__ == "__main__":
    main()