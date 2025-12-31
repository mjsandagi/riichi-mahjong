#!/usr/bin/env python3
"""
Riichi Mahjong - Main Entry Point

This is the main entry point for running the Riichi Mahjong game.

Usage:
    python main.py          # Start a CLI game
    python main.py --test   # Run a test game with all bots

The game uses a decoupled architecture where:
- GameEngine handles pure game logic (no I/O)
- Agents make decisions (human or AI)
- GameController orchestrates the game flow
- UI is separate and can be swapped (CLI, Web, etc.)
"""

import sys


def run_cli_game():
    """Run a CLI game with human player vs AI bots."""
    from backend.core.game_controller import CLIGameController
    from backend.ai import HumanCLIAgent, RandomAgent
    
    print("\n" + "="*50)
    print("       RIICHI MAHJONG - CLI Interface")
    print("="*50 + "\n")
    
    # Create controller
    controller = CLIGameController(["You (East)", "South", "West", "North"])
    
    # Human player at seat 0
    controller.set_agent(0, HumanCLIAgent("You"))
    
    # AI bots at other seats
    controller.set_agent(1, RandomAgent("South Bot"))
    controller.set_agent(2, RandomAgent("West Bot"))
    controller.set_agent(3, RandomAgent("North Bot"))
    
    # Run the game
    final_state = controller.run_game()
    
    return final_state


def run_test_game():
    """Run a test game with all AI players (no human input)."""
    from backend.core.game_controller import GameController
    from backend.core.game_state import GamePhase
    from backend.ai import RandomAgent
    
    print("\n" + "="*50)
    print("       RIICHI MAHJONG - Test Game (All Bots)")
    print("="*50 + "\n")
    
    # Create controller with all bots
    controller = GameController(["East Bot", "South Bot", "West Bot", "North Bot"])
    
    for i in range(4):
        controller.set_agent(i, RandomAgent(f"Bot {i}"))
    
    # Add simple event logging
    def log_event(event):
        print(f"  [{event.event_type.name}] {event.message}")
    
    controller.on_event(log_event)
    
    # Run the game
    final_state = controller.run_game()
    
    # Print results
    print("\n" + "="*50)
    print("GAME RESULTS:")
    print("="*50)
    
    if final_state.phase == GamePhase.GAME_OVER_WIN:
        winner = final_state.players[final_state.winner_index]
        print(f"Winner: {winner.name}")
        print(f"Yaku: {', '.join(final_state.winning_yaku)}")
    else:
        print("Result: Exhaustive Draw (No Winner)")
    
    print("\nFinal Scores:")
    for p in final_state.players:
        print(f"  {p.name}: {p.score}")
    
    return final_state


def run_simulation(num_games: int = 100):
    """Run multiple games for AI testing/statistics."""
    from backend.core.game_controller import GameController
    from backend.core.game_state import GamePhase
    from backend.ai import RandomAgent
    
    print(f"\nRunning {num_games} simulated games...")
    
    wins = [0, 0, 0, 0]
    draws = 0
    
    for i in range(num_games):
        controller = GameController()
        for j in range(4):
            controller.set_agent(j, RandomAgent(f"Bot {j}"))
        
        controller.turn_delay = 0  # No delays
        final_state = controller.run_game()
        
        if final_state.phase == GamePhase.GAME_OVER_WIN:
            wins[final_state.winner_index] += 1
        else:
            draws += 1
        
        if (i + 1) % 10 == 0:
            print(f"  Completed {i + 1}/{num_games} games...")
    
    print("\nSimulation Results:")
    print(f"  Total Games: {num_games}")
    print(f"  Draws: {draws} ({100*draws/num_games:.1f}%)")
    for i in range(4):
        print(f"  Player {i} Wins: {wins[i]} ({100*wins[i]/num_games:.1f}%)")


def main():
    """Main entry point."""
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        if arg == "--test":
            run_test_game()
        elif arg == "--simulate":
            num = int(sys.argv[2]) if len(sys.argv) > 2 else 100
            run_simulation(num)
        elif arg == "--help":
            print(__doc__)
        else:
            print(f"Unknown argument: {arg}")
            print("Use --help for usage information")
    else:
        run_cli_game()


if __name__ == "__main__":
    main()
